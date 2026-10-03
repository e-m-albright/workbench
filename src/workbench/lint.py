"""Validate canonical repository sources: skills, links, JSON, TOML, shell."""

from __future__ import annotations

import html
import os
import re
import subprocess
import tomllib
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote

import yaml

from workbench.core import (
    AGENTS,
    RETIRED_PI_EXTENSIONS,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
    ROOT,
    WorkbenchError,
    load_json,
)
from workbench.external_skills import OVERLAYS, ExternalSkill, external_skills

# Single source for the skill-description context budget; the test suite
# imports these rather than re-deriving the rule.
PER_SKILL_DESCRIPTION_LIMIT = 280
DESCRIPTION_BUDGET = 5_800


def _frontmatter_mapping(text: str, path: Path) -> dict[str, object]:
    if not text.startswith("---\n"):
        raise WorkbenchError(f"missing opening frontmatter delimiter: {path}")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise WorkbenchError(f"missing closing frontmatter delimiter: {path}")
    try:
        raw = yaml.safe_load(text[4:closing])
    except yaml.YAMLError as exc:
        raise WorkbenchError(f"invalid YAML frontmatter: {path}: {exc}") from exc
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise WorkbenchError(f"frontmatter must be a string-keyed object: {path}")
    return raw


def _markdown_sources(root: Path) -> Iterator[Path]:
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(
            name
            for name in folders
            if not name.startswith(".") and name not in {"node_modules", "tmp", "artifacts"}
        )
        for name in sorted(files):
            if name.endswith(".md"):
                yield Path(directory) / name


def _markdown_prose(path: Path) -> Iterator[tuple[int, str]]:
    """Yield source lines outside fenced examples, preserving diagnostic positions."""
    fence = ""
    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, tail = match.groups()
            if not fence:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not tail.strip():
                fence = ""
            continue
        if not fence:
            yield number, line


def _markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    for _, line in _markdown_prose(path):
        anchors.update(re.findall(r'\b(?:id|name)=["\']([^"\']+)["\']', line))
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if not heading:
            continue
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", heading[1])
        title = html.unescape(re.sub(r"<[^>]+>", "", title)).lower()
        slug = re.sub(r"[^\w\s-]", "", title).replace(" ", "-")
        anchor, suffix = slug, 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{slug}-{suffix}"
        anchors.add(anchor)
    return anchors


def _markdown_link_errors(root: Path, *, repository_root: Path | None = None) -> list[str]:
    """Validate local links and, when supplied, this repository's public references offline."""
    errors: list[str] = []
    heading_cache: dict[Path, set[str]] = {}
    skills = (root / "agents/skills").resolve()
    for path in _markdown_sources(root):
        for line_number, line in _markdown_prose(path):
            for match in re.finditer(r"\[[^]]+\]\(([^)]+)\)", line):
                raw = match[1].strip().strip("<>")
                repository_link = raw.startswith(
                    "https://github.com/e-m-albright/workbench/blob/main/"
                )
                if repository_link and repository_root is not None:
                    name, _, fragment = unquote(raw.split("/blob/main/", 1)[1]).partition("#")
                    target = repository_root / name
                elif "://" in raw or raw.startswith("mailto:"):
                    continue
                else:
                    name, _, fragment = unquote(raw).partition("#")
                    target = (
                        (root / name.lstrip("/") if name.startswith("/") else path.parent / name)
                        if name
                        else path
                    )
                target = target.resolve()
                location = f"{path.relative_to(root)}:{line_number}: {raw}"
                if (
                    not repository_link
                    and path.resolve().is_relative_to(skills)
                    and not target.is_relative_to(skills)
                ):
                    errors.append(f"skill link leaves deployed tree: {location}")
                elif not target.exists():
                    # External wrappers reference files from their verified upstream archive.
                    if not path.is_relative_to(root / "agents/external-skills"):
                        errors.append(f"broken local link: {location}")
                elif fragment and target.suffix == ".md" and target.is_file():
                    if target not in heading_cache:
                        heading_cache[target] = _markdown_anchors(target)
                    if fragment not in heading_cache[target]:
                        errors.append(f"broken local heading: {location}")
    return errors


def _playbook_structure_errors(root: Path) -> list[str]:
    """Require subject placement and short scope overviews, not a document register."""
    playbook = root / "playbook"
    errors = []
    if not (playbook / "README.md").is_file():
        errors.append("playbook overview missing: playbook/README.md")
    for path in sorted(playbook.glob("*.md")):
        if path.name not in {"README.md", "watchlist.md"}:
            errors.append(f"place knowledge under a subject: {path.relative_to(root)}")
    if not playbook.is_dir():
        return errors
    for path in sorted(playbook.iterdir()):
        if path.is_dir() and not (path / "README.md").is_file():
            errors.append(f"subject overview missing: {path.relative_to(root)}/README.md")
    return errors


def _retired_source_errors() -> list[str]:
    paths = [
        *(AGENTS / "pi/extensions" / name for name in RETIRED_PI_EXTENSIONS),
        *(AGENTS / "subagents" / f"{name}.md" for name in RETIRED_SUBAGENTS),
    ]
    return [
        f"retired source remains canonical: {path.relative_to(ROOT)}"
        for path in paths
        if path.exists()
    ]


def _external_skill_errors(registered: list[ExternalSkill]) -> list[str]:
    errors: list[str] = []
    names: set[str] = set()
    archive_identities: set[tuple[str, str]] = set()
    for skill in registered:
        if skill.name in names:
            errors.append(f"duplicate external skill name: {skill.name}")
        names.add(skill.name)
        identity = (skill.url, skill.sha256)
        if identity in archive_identities:
            errors.append(f"duplicate external skill archive: {skill.url}")
        archive_identities.add(identity)
        if skill.name in RETIRED_SKILLS:
            errors.append(f"retired skill remains in external registry: {skill.name}")
    return errors


def lint() -> int:
    errors = _retired_source_errors()
    for path in sorted(AGENTS.rglob("*.json")):
        try:
            load_json(path)
        except WorkbenchError as exc:
            errors.append(str(exc))
    for toml_path in sorted(AGENTS.rglob("*.toml")):
        try:
            tomllib.loads(toml_path.read_text())
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"invalid TOML: {toml_path.relative_to(ROOT)}: {exc}")

    for entry in sorted((AGENTS / "skills").iterdir()):
        if entry.is_dir() and not (entry / "SKILL.md").exists():
            errors.append(f"skill directory without SKILL.md: {entry.relative_to(ROOT)}")

    # A reference file carrying SKILL.md frontmatter keys is demoted-skill
    # debris: the skill body moved under references/ but kept its metadata.
    debris_keys = ("name", "description", "disable-model-invocation", "allowed-tools")
    for reference in sorted((AGENTS / "skills").glob("*/references/*.md")):
        text = reference.read_text()
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        for key in debris_keys:
            if re.search(rf"^{key}:", parts[1], re.MULTILINE):
                errors.append(
                    "demoted-skill frontmatter in reference file: "
                    f"{reference.relative_to(ROOT)} ({key}:)"
                )
                break

    rule_pattern = re.compile(
        r'prefix_rule\(pattern=\["[^"]+"(?:,\s*"[^"]+")*\], decision="[a-z_-]+"\)'
    )
    rules_path = AGENTS / "codex/default.rules"
    for number, line in enumerate(rules_path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not rule_pattern.fullmatch(stripped):
            errors.append(f"invalid Codex rule syntax: {rules_path.relative_to(ROOT)}:{number}")

    names: set[str] = set()
    descriptions: dict[str, str] = {}
    for skill in sorted((AGENTS / "skills").glob("*/SKILL.md")):
        content = skill.read_text()
        try:
            frontmatter = _frontmatter_mapping(content, skill)
        except WorkbenchError as exc:
            errors.append(str(exc))
            continue
        name_value = frontmatter.get("name")
        if not isinstance(name_value, str) or not name_value:
            errors.append(f"missing skill name: {skill.relative_to(ROOT)}")
            continue
        name = name_value
        if name != skill.parent.name:
            errors.append(f"skill name/path mismatch: {skill.parent.name} != {name}")
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        names.add(name)
        description_value = frontmatter.get("description")
        if not isinstance(description_value, str) or not description_value:
            errors.append(f"missing skill description: {skill.relative_to(ROOT)}")
            continue
        length = len(description_value)
        descriptions[name] = description_value
        if length > PER_SKILL_DESCRIPTION_LIMIT:
            errors.append(
                f"skill description exceeds {PER_SKILL_DESCRIPTION_LIMIT} chars: {name} ({length})"
            )

    external_count = 0
    try:
        registered = external_skills(AGENTS / "shared/external-skills.json")
    except WorkbenchError as exc:
        errors.append(str(exc))
        registered = []
    errors.extend(_external_skill_errors(registered))
    external_names: set[str] = set()
    for skill in registered:
        external_count += 1
        external_names.add(skill.name)
        overlay = OVERLAYS / skill.name / "SKILL.md"
        if not overlay.is_file():
            errors.append(f"external skill wrapper missing: {overlay.relative_to(ROOT)}")
            continue
        try:
            frontmatter = _frontmatter_mapping(overlay.read_text(), overlay)
        except WorkbenchError as exc:
            errors.append(str(exc))
            continue
        if frontmatter.get("name") != skill.name:
            errors.append(f"external skill wrapper name mismatch: {skill.name}")
        description = frontmatter.get("description")
        if description != skill.description:
            errors.append(f"external skill wrapper description mismatch: {skill.name}")
            continue
        length = len(skill.description)
        descriptions[skill.name] = skill.description
        if length > PER_SKILL_DESCRIPTION_LIMIT:
            errors.append(
                f"skill description exceeds {PER_SKILL_DESCRIPTION_LIMIT} chars: "
                f"{skill.name} ({length})"
            )
    if OVERLAYS.is_dir():
        for overlay in OVERLAYS.iterdir():
            if overlay.is_dir() and overlay.name not in external_names:
                errors.append(f"unregistered external skill wrapper: {overlay.relative_to(ROOT)}")

    names.update(external_names)
    description_chars = sum(map(len, descriptions.values()))
    if description_chars > DESCRIPTION_BUDGET:
        errors.append(
            f"skill descriptions exceed {DESCRIPTION_BUDGET}-char context budget: "
            f"{description_chars}"
        )

    for script in sorted(AGENTS.rglob("*.sh")):
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        if result.returncode:
            errors.append(result.stderr.strip())
    errors.extend(_markdown_link_errors(ROOT, repository_root=ROOT))
    errors.extend(_playbook_structure_errors(ROOT))
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        return 1
    print(
        f"OK {len(names)} skills ({external_count} external), Markdown links, "
        "subject placement, JSON, TOML, and shell syntax"
    )
    return 0
