"""One-time setup for the standalone native terminal boundary."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from workbench.core import (
    AGENTS,
    DATA_REL,
    WorkbenchError,
    copy_file,
    ensure_hard_deny_policy,
    ensure_private_path_policy,
    write_json,
)
from workbench.native_config import install_harness
from workbench.native_dependencies import patch_forge


def _binary(name: str) -> Path:
    found = shutil.which(name)
    if not found:
        raise WorkbenchError(f"Native sandbox requires {name}; install it through the host setup")
    return Path(found).resolve(strict=True)


def _agent(home: Path, vendor: str, node: Path) -> tuple[dict, Path] | None:
    """Prefer Claude's native install, whose stable launcher survives auto-update."""
    launcher = home / ".local/bin/claude"
    if vendor != "claude" or not (launcher.exists() or launcher.is_symlink()):
        found = shutil.which(vendor)
        if not found:
            return None
        launcher = Path(found)
    if vendor == "claude" and launcher.is_symlink():
        try:
            target = launcher.resolve(strict=True)
        except OSError as error:
            raise WorkbenchError("Claude launcher is broken; reinstall Claude Code") from error
        if target.parent.name == "versions" and target.parent.parent.name == "claude":
            # Auto-update replaces the version file, so record the link and admit
            # the versions directory; each launch resolves the current target.
            stable = launcher.parent.resolve() / launcher.name
            return {"command": [str(stable)], "read": [str(target.parent)]}, stable
    binary = launcher.resolve(strict=True)
    package = next(
        (parent for parent in binary.parents if (parent / "package.json").is_file()),
        binary.parent,
    )
    command = [str(node), str(binary)] if vendor == "pi" else [str(binary)]
    return {"command": command, "read": [str(package)]}, binary


def _safe_bootstrap(home: Path, *paths: Path) -> None:
    """Executables, their link directories, and loader trees must resist managed writes."""
    writable = [
        home / name
        for name in (
            "code/public",
            "Desktop",
            "Downloads",
            f"{DATA_REL}/agent-state",
            f"{DATA_REL}/model-auth",
        )
    ]
    for path in paths:
        for loader in {path.parent.resolve(), path.resolve().parent}:
            for root in writable:
                if loader.is_relative_to(root.resolve()):
                    raise WorkbenchError(
                        "Unsafe bootstrap tool location overlaps managed writable paths; "
                        "install Node, npm, and agent CLIs outside public code, scratch, "
                        "and managed state"
                    )


def installed_browser(home: Path) -> str | None:
    """Use the host's installed Playwright Headless Shell; never download at launch."""
    candidates = list(
        (home / "Library/Caches/ms-playwright").glob(
            "chromium_headless_shell-*/chrome-headless-shell-mac-*/chrome-headless-shell"
        )
    )
    candidates = [path for path in candidates if path.is_file() and os.access(path, os.X_OK)]
    return (
        str(max(candidates, key=lambda path: path.stat().st_mtime).resolve())
        if candidates
        else None
    )


def prepare(home: Path | None = None) -> None:
    """Install locked upstream dependencies and copies, without provider credentials."""
    home = (home or Path.home()).resolve()
    node, npm = _binary("node"), _binary("npm")
    agents: dict[str, object] = {}
    executables = []
    for vendor in ("codex", "claude", "pi"):
        found = _agent(home, vendor, node)
        if found:
            agents[vendor], executable = found
            executables.append(executable)
    _safe_bootstrap(
        home,
        node,
        npm,
        *executables,
        home / DATA_REL / "shell/native-sandbox.mjs",
        home / DATA_REL / "native/node_modules/bootstrap",
    )
    runtime = home / DATA_REL / "native"
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    for vendor in agents:
        (home / DATA_REL / "model-auth" / vendor).mkdir(parents=True, exist_ok=True, mode=0o700)
    ensure_private_path_policy(home / ".config/workbench/private-paths")
    ensure_hard_deny_policy(home / ".config/workbench/hard-deny-paths")
    # Keep one preparer from publishing readiness during another's npm ci.
    # The persistent lock file must not be unlinked: waiters must share its inode.
    with (runtime / "prepare.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise WorkbenchError("Native runtime is already being prepared; retry later") from error
        _install_runtime(home, runtime, node, npm, agents)


def _install_runtime(
    home: Path, runtime: Path, node: Path, npm: Path, agents: dict[str, object]
) -> None:
    # A failed reinstall must never advertise a partially prepared runtime.
    (runtime / "tools.json").unlink(missing_ok=True)
    for name in ("package.json", "package-lock.json"):
        copy_file(AGENTS / "shared/sandbox" / name, runtime / name)
    subprocess.run(
        [str(npm), "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        cwd=runtime,
        env={"HOME": str(home), "PATH": f"{node.parent}:/opt/homebrew/bin:/usr/bin:/bin"},
        check=True,
    )
    patch_forge(runtime)
    for probe in ("verify-forge.cjs", "verify-zod.cjs"):
        subprocess.run(
            [str(node), str(AGENTS / "shared/sandbox" / probe), str(runtime)], check=True
        )
    for name in ("native-sandbox.py", "native-sandbox.mjs"):
        copy_file(AGENTS / "shared/shell" / name, home / DATA_REL / "shell" / name)
    install_harness(home)
    write_json(
        runtime / "tools.json",
        {"node": str(node), "agents": agents, "browser": installed_browser(Path.home())},
    )


def _credential_bytes(path: Path) -> bytes:
    if any(parent.is_symlink() for parent in path.parents):
        raise WorkbenchError("Model login directories must not traverse symlinks")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
            or metadata.st_nlink != 1
            or metadata.st_size > 1024 * 1024
        ):
            raise WorkbenchError("Model login file must be a small owner-only regular file")
        value = stream.read(1024 * 1024 + 1)
    if len(value) > 1024 * 1024:
        raise WorkbenchError("Model login file exceeds the size limit")
    return value


def _credential_value(raw: bytes) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise WorkbenchError("Model login file must contain an object")
    return value


def _credential_json(path: Path) -> dict:
    return _credential_value(_credential_bytes(path))


LOGIN_FILES = {"codex": "auth.json", "pi": "auth.json", "claude": ".credentials.json"}


def _token(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_login(vendor: str, value: dict) -> bool:
    if vendor == "claude":
        credential = value.get("claudeAiOauth")
        return isinstance(credential, dict) and _token(credential.get("accessToken"))
    if vendor == "codex":
        tokens = value.get("tokens")
        return _token(value.get("OPENAI_API_KEY")) or (
            isinstance(tokens, dict) and _token(tokens.get("access_token"))
        )
    return any(
        isinstance(item, dict) and item.get("type") == "oauth" and _token(item.get("access"))
        for item in value.values()
    )


def _private_directory(path: Path, home: Path) -> None:
    for parent in reversed((path, *path.parents)):
        if parent == home or not parent.is_relative_to(home):
            continue
        if parent.is_symlink():
            raise WorkbenchError("Model login directories must not traverse symlinks")
        parent.mkdir(exist_ok=True, mode=0o700)
    if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise WorkbenchError("Model login directory must be owner-only")


def _source_login(home: Path, vendor: str) -> dict:
    if vendor == "claude":
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if result.returncode:
            return {}
        try:
            credential = json.loads(result.stdout).get("claudeAiOauth")
        except (ValueError, AttributeError) as error:
            raise WorkbenchError("Claude model login is not a valid credential object") from error
        return {"claudeAiOauth": credential} if isinstance(credential, dict) else {}
    source = home / (".codex/auth.json" if vendor == "codex" else ".pi/agent/auth.json")
    if not source.exists():
        return {}
    value = _credential_json(source)
    if vendor == "pi":
        # Command-backed keys can invoke host credential tools; do not import them.
        return {
            key: item
            for key, item in value.items()
            if isinstance(item, dict) and item.get("type") == "oauth"
        }
    return value


def authorize(
    home: Path | None = None,
    *,
    vendor: str | None = None,
    replace: bool = False,
) -> dict[str, bool]:
    """Enroll logins; replacement requires an explicit vendor and preserves a backup."""
    home = (home or Path.home()).resolve()
    if vendor is not None and vendor not in LOGIN_FILES:
        raise WorkbenchError("Choose codex, claude, or pi for model login enrollment")
    if replace and vendor is None:
        raise WorkbenchError("Replacing a model login requires an explicit vendor")
    enrolled = {}
    for name in [vendor] if vendor else LOGIN_FILES:
        destination = home / DATA_REL / "model-auth" / name / LOGIN_FILES[name]
        exists = destination.exists() or destination.is_symlink()
        previous_raw = _credential_bytes(destination) if exists else None
        previous = (
            _credential_value(previous_raw) if previous_raw is not None and not replace else None
        )
        if exists and not replace:
            # Presence is not proof of validity, and may contain a refreshed schema.
            enrolled[name] = bool(previous) and (name != "claude" or _has_login(name, previous))
            continue
        value = _source_login(home, name)
        if not _has_login(name, value):
            if vendor is not None:
                raise WorkbenchError(f"No reusable {name} model login; sign in natively first")
            enrolled[name] = False
            continue
        _private_directory(destination.parent, home)
        if replace and exists:
            backups = home / ".local/state/workbench/backups"
            _private_directory(backups, home)
            backup_root = Path(tempfile.mkdtemp(prefix="model-login-", dir=backups))
            backup = backup_root / name / LOGIN_FILES[name]
            _private_directory(backup.parent, home)
            # Preserve exact bytes, including tokens rotated by the native harness.
            with os.fdopen(
                os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
            ) as target:
                target.write(previous_raw or b"")
        fd, temporary = tempfile.mkstemp(prefix=".enroll-", dir=destination.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(value, stream)
                stream.write("\n")
            Path(temporary).replace(destination)
        finally:
            Path(temporary).unlink(missing_ok=True)
        enrolled[name] = True
    return enrolled


def _status_json(path: Path) -> dict:
    """Read only bounded control manifests, never token or conversation files."""
    if any(parent.is_symlink() for parent in path.parents):
        raise WorkbenchError("Managed status paths must not traverse symlinks")
    if not path.exists():
        return {}
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)) as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 1024 * 1024:
            raise WorkbenchError("Managed status manifest must be a small regular file")
        raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise WorkbenchError("Managed status manifest exceeds the size limit")
        value = json.loads(raw)
    if not isinstance(value, dict):
        raise WorkbenchError("Managed status manifest must contain an object")
    return value


def status(
    home: Path | None = None,
    *,
    vendor: str | None = None,
    cwd: Path | None = None,
) -> dict:
    """Inspect preparation and file metadata without authenticating or reading sessions."""
    home = (home or Path.home()).resolve()
    root = (cwd or Path.cwd()).resolve()
    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            root = candidate
            break
    if vendor is not None and vendor not in LOGIN_FILES:
        raise WorkbenchError("Choose codex, claude, or pi for managed status")
    runtime = home / DATA_REL
    tools = _status_json(runtime / "native/tools.json")
    projection = _status_json(runtime / "native/harness/manifest.json")
    state = runtime / "agent-state" / hashlib.sha256(os.fsencode(root)).hexdigest()[:20] / "home"
    result = {
        "runtime_path": str(runtime / "native"),
        "workspace_path": str(root),
        "state_path": str(state),
        "state_exists": state.is_dir(),
        "agents": {},
    }
    for name in [vendor] if vendor else LOGIN_FILES:
        token = runtime / "model-auth" / name / LOGIN_FILES[name]
        metadata = token.lstat() if token.exists() or token.is_symlink() else None
        login = "absent"
        if metadata:
            login = (
                "present; authentication unverified"
                if (
                    stat.S_ISREG(metadata.st_mode)
                    and metadata.st_uid == os.getuid()
                    and not metadata.st_mode & 0o077
                )
                else "unsafe file metadata; enrollment required"
            )
        command = tools.get("agents", {}).get(name, {}).get("command", [])
        result["agents"][name] = {
            "login_path": str(token),
            "login": login,
            "executable_ready": bool(command)
            and all(
                isinstance(part, str) and Path(part).is_file() and os.access(part, os.X_OK)
                for part in command
            ),
            "projection_path": str(runtime / "native/harness" / name),
            "projection_present": name in projection,
            "admitted_asset_roots": len(projection.get(name, {}).get("read", [])),
        }
    return result


def run_agent(vendor: str, location: str, args: list[str]) -> int:
    """The installed script enters containment without importing checkout code."""
    launcher = Path.home() / DATA_REL / "shell/native-sandbox.py"
    if not launcher.is_file():
        raise WorkbenchError("Native runtime is not prepared; run workbench native prepare")
    return subprocess.run(
        ["/usr/bin/python3", "-I", "-S", str(launcher), vendor, location, *args],
        check=False,
    ).returncode
