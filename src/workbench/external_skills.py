"""Pinned external-skill registry, cache, and safe archive extraction."""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from workbench.core import AGENTS, WorkbenchError, load_json

REGISTRY = AGENTS / "shared/external-skills.json"
OVERLAYS = AGENTS / "external-skills"
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
PROVENANCE_FILE = "provenance.json"


@dataclass(frozen=True)
class ExternalSkill:
    name: str
    version: str
    description: str
    url: str
    sha256: str
    archive_root: str
    source_repo: str


def external_skills(path: Path = REGISTRY) -> list[ExternalSkill]:
    """Load the reviewed registry, raising a concise schema error."""
    raw = load_json(path)
    if not isinstance(raw, dict) or set(raw) != {"$comment", "skills"}:
        raise WorkbenchError("external skill registry must contain only $comment and skills")
    if not isinstance(raw["$comment"], str) or not isinstance(raw["skills"], list):
        raise WorkbenchError(
            "external skill registry $comment must be text and skills must be a list"
        )
    required = set(ExternalSkill.__dataclass_fields__)
    result: list[ExternalSkill] = []
    for index, value in enumerate(raw["skills"]):
        if not isinstance(value, dict) or set(value) != required:
            raise WorkbenchError(
                f"external skill registry entry {index} must contain exactly {sorted(required)}"
            )
        if not all(isinstance(value[key], str) and value[key] for key in required):
            raise WorkbenchError(
                f"external skill registry entry {index} values must be nonempty text"
            )
        skill = ExternalSkill(**value)
        if len(skill.sha256) != 64 or any(char not in "0123456789abcdef" for char in skill.sha256):
            raise WorkbenchError(f"external skill {skill.name} has an invalid SHA-256")
        name = PurePosixPath(skill.name)
        root = PurePosixPath(skill.archive_root)
        if name.is_absolute() or len(name.parts) != 1 or name.parts[0] in {"", ".", ".."}:
            raise WorkbenchError(f"external skill has an invalid name: {skill.name}")
        if root.is_absolute() or len(root.parts) != 1 or root.parts[0] in {"", ".", ".."}:
            raise WorkbenchError(f"external skill {skill.name} has an invalid archive_root")
        if not skill.url.startswith("https://") or not skill.source_repo.startswith("https://"):
            raise WorkbenchError(f"external skill {skill.name} URLs must use HTTPS")
        result.append(skill)
    return result


def cache_directory(home: Path, skill: ExternalSkill) -> Path:
    return home / ".cache/workbench/external-skills" / skill.name / skill.sha256


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(
    url: str,
    destination: Path,
    *,
    opener: Callable[..., BinaryIO] = urllib.request.urlopen,
) -> None:
    try:
        response = opener(url, timeout=30)
        with response, destination.open("wb") as output:
            total = 0
            while chunk := response.read(min(1024 * 1024, MAX_ARCHIVE_BYTES + 1 - total)):
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise WorkbenchError(
                        f"external skill archive exceeds {MAX_ARCHIVE_BYTES} bytes: {url}"
                    )
                output.write(chunk)
    except WorkbenchError:
        raise
    except OSError as exc:
        raise WorkbenchError(f"could not download external skill archive {url}: {exc}") from exc


def _safe_members(archive: zipfile.ZipFile, skill: ExternalSkill) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_ENTRIES:
        raise WorkbenchError(f"external skill {skill.name} archive has too many entries")
    seen: set[PurePosixPath] = set()
    expanded = 0
    safe: list[zipfile.ZipInfo] = []
    for member in members:
        raw = member.filename.replace("\\", "/")
        path = PurePosixPath(raw)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise WorkbenchError(f"unsafe path in external skill {skill.name} archive: {raw}")
        normalized = PurePosixPath(*[part for part in path.parts if part not in {"", "."}])
        if not normalized.parts or normalized.parts[0] != skill.archive_root:
            raise WorkbenchError(
                f"external skill {skill.name} archive entry is outside {skill.archive_root}: {raw}"
            )
        if normalized in seen:
            raise WorkbenchError(f"duplicate path in external skill {skill.name} archive: {raw}")
        seen.add(normalized)
        mode = member.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise WorkbenchError(f"symlink in external skill {skill.name} archive: {raw}")
        # Many ZIP writers store Unix permission bits without a file-type bit.
        if not (member.is_dir() or stat.S_ISREG(mode) or stat.S_IFMT(mode) == 0):
            raise WorkbenchError(f"special file in external skill {skill.name} archive: {raw}")
        expanded += member.file_size
        if expanded > MAX_EXPANDED_BYTES:
            raise WorkbenchError(
                f"external skill {skill.name} expands beyond {MAX_EXPANDED_BYTES} bytes"
            )
        safe.append(member)
    return safe


def _extract(archive_path: Path, destination: Path, skill: ExternalSkill) -> dict[str, str]:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = _safe_members(archive, skill)
            root = destination / skill.archive_root
            for member in members:
                relative = PurePosixPath(member.filename.replace("\\", "/")).relative_to(
                    skill.archive_root
                )
                target = root.joinpath(*relative.parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except (OSError, zipfile.BadZipFile) as exc:
        raise WorkbenchError(f"invalid external skill archive for {skill.name}: {exc}") from exc
    if not (destination / skill.archive_root / "SKILL.md").is_file():
        raise WorkbenchError(
            f"external skill {skill.name} archive lacks {skill.archive_root}/SKILL.md"
        )
    return _tree_manifest(destination / skill.archive_root)


def _archive_manifest(archive_path: Path, skill: ExternalSkill) -> dict[str, str]:
    """Hash the safe archive payload so provenance is anchored to pinned bytes."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            result: dict[str, str] = {}
            for member in _safe_members(archive, skill):
                if member.is_dir():
                    continue
                relative = PurePosixPath(member.filename.replace("\\", "/")).relative_to(
                    skill.archive_root
                )
                digest = hashlib.sha256()
                with archive.open(member) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                result[relative.as_posix()] = digest.hexdigest()
            return result
    except (OSError, zipfile.BadZipFile) as exc:
        raise WorkbenchError(f"invalid external skill archive for {skill.name}: {exc}") from exc


def _tree_manifest(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        return {}
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            return {}
        if path.is_file():
            result[path.relative_to(root).as_posix()] = _sha256(path)
    return result


def _provenance(skill: ExternalSkill, files: dict[str, str]) -> dict[str, object]:
    return {**asdict(skill), "files": files}


def validated_cached_skill(home: Path, skill: ExternalSkill) -> Path | None:
    """Return a cache tree only when archive, provenance, and extracted bytes agree."""
    cache = cache_directory(home, skill)
    archive = cache / "archive.zip"
    tree = cache / "tree"
    provenance = cache / PROVENANCE_FILE
    try:
        if (
            not cache.is_dir()
            or cache.is_symlink()
            or not archive.is_file()
            or archive.is_symlink()
            or archive.stat().st_size > MAX_ARCHIVE_BYTES
            or _sha256(archive) != skill.sha256
            or not provenance.is_file()
            or provenance.is_symlink()
        ):
            return None
        recorded = json.loads(provenance.read_text())
        files = _tree_manifest(tree)
        archived_files = _archive_manifest(archive, skill)
    except (OSError, json.JSONDecodeError, WorkbenchError):
        return None
    if (
        "SKILL.md" not in archived_files
        or files != archived_files
        or recorded != _provenance(skill, archived_files)
    ):
        return None
    return tree


def cached_external_skill(
    home: Path,
    skill: ExternalSkill,
    *,
    opener: Callable[..., BinaryIO] = urllib.request.urlopen,
) -> Path:
    """Populate or repair one checksum-addressed cache and return its skill tree."""
    valid = validated_cached_skill(home, skill)
    if valid is not None:
        return valid

    cache = cache_directory(home, skill)
    parent = cache.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{skill.sha256}.", dir=parent))
    try:
        archive = stage / "archive.zip"
        cached_archive = cache / "archive.zip"
        if (
            cached_archive.is_file()
            and not cached_archive.is_symlink()
            and cached_archive.stat().st_size <= MAX_ARCHIVE_BYTES
            and _sha256(cached_archive) == skill.sha256
        ):
            shutil.copyfile(cached_archive, archive)
        else:
            _download(skill.url, archive, opener=opener)
            actual = _sha256(archive)
            if actual != skill.sha256:
                raise WorkbenchError(
                    f"external skill {skill.name} checksum mismatch: "
                    f"expected {skill.sha256}, got {actual}"
                )
        extracted = stage / "extracted"
        files = _extract(archive, extracted, skill)
        (stage / PROVENANCE_FILE).write_text(
            json.dumps(_provenance(skill, files), indent=2, sort_keys=True) + "\n"
        )
        (extracted / skill.archive_root).replace(stage / "tree")
        extracted.rmdir()

        backup = cache.with_name(cache.name + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        if cache.exists():
            cache.replace(backup)
        try:
            stage.replace(cache)
        except OSError:
            if backup.exists():
                backup.replace(cache)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return cache / "tree"


def _overlay_manifest(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        return {}
    files = _tree_manifest(root)
    actual_files = {path for path in root.rglob("*") if path.is_file()}
    if len(files) != len(actual_files):
        raise WorkbenchError(f"external skill overlay contains a symlink: {root}")
    return files


def _composed_manifest(source: Path, overlay: Path) -> dict[str, str]:
    return {**_tree_manifest(source), **_overlay_manifest(overlay)}


def validated_external_skill_source(
    home: Path,
    skill: ExternalSkill,
    *,
    overlays: Path = OVERLAYS,
) -> Path | None:
    """Return the offline managed composition when cache and local overlay agree."""
    source = validated_cached_skill(home, skill)
    if source is None:
        return None
    overlay = overlays / skill.name
    if not overlay.is_dir():
        return source
    managed = cache_directory(home, skill) / "managed"
    try:
        expected = _composed_manifest(source, overlay)
        return managed if _tree_manifest(managed) == expected else None
    except OSError:
        return None


def external_skill_source(
    home: Path,
    skill: ExternalSkill,
    *,
    opener: Callable[..., BinaryIO] = urllib.request.urlopen,
    overlays: Path = OVERLAYS,
) -> Path:
    """Compose a verified upstream runtime with its small reviewed local overlay."""
    source = cached_external_skill(home, skill, opener=opener)
    overlay = overlays / skill.name
    if not overlay.is_dir():
        return source
    valid = validated_external_skill_source(home, skill, overlays=overlays)
    if valid is not None:
        return valid

    cache = cache_directory(home, skill)
    managed = cache / "managed"
    stage = Path(tempfile.mkdtemp(prefix=".managed.", dir=cache))
    backup = cache / ".managed.bak"
    try:
        shutil.copytree(source, stage / "tree")
        for path in sorted(overlay.rglob("*")):
            if path.is_symlink():
                raise WorkbenchError(f"external skill overlay contains a symlink: {path}")
            if not path.is_file():
                continue
            target = stage / "tree" / path.relative_to(overlay)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        if backup.exists():
            shutil.rmtree(backup)
        if managed.exists():
            managed.replace(backup)
        try:
            (stage / "tree").replace(managed)
        except OSError:
            if backup.exists():
                backup.replace(managed)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return managed
