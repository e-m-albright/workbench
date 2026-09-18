"""One-time setup for the standalone native terminal boundary."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from workbench.core import (
    AGENTS,
    DATA_REL,
    WorkbenchError,
    copy_file,
    ensure_private_path_policy,
    write_json,
)
from workbench.native_config import install_harness


def _binary(name: str) -> Path:
    found = shutil.which(name)
    if not found:
        raise WorkbenchError(f"Native sandbox requires {name}; install it through the host setup")
    return Path(found).resolve(strict=True)


def prepare(home: Path | None = None) -> None:
    """Install locked upstream dependencies and copies, without provider credentials."""
    home = (home or Path.home()).resolve()
    node, npm = _binary("node"), _binary("npm")
    agents: dict[str, object] = {}
    for vendor in ("codex", "claude", "pi"):
        if not shutil.which(vendor):
            continue
        binary = _binary(vendor)
        package = next(
            (parent for parent in binary.parents if (parent / "package.json").is_file()),
            binary.parent,
        )
        agents[vendor] = {
            "command": [str(node), str(binary)] if vendor == "pi" else [str(binary)],
            "read": [str(package)],
        }
    runtime = home / DATA_REL / "native"
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    for vendor in agents:
        (home / DATA_REL / "model-auth" / vendor).mkdir(parents=True, exist_ok=True, mode=0o700)
    ensure_private_path_policy(home / ".config/workbench/private-paths")
    for name in ("package.json", "package-lock.json"):
        copy_file(AGENTS / "shared/sandbox" / name, runtime / name)
    subprocess.run(
        [str(npm), "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        cwd=runtime,
        env={"HOME": str(home), "PATH": f"{node.parent}:/opt/homebrew/bin:/usr/bin:/bin"},
        check=True,
    )
    for name in ("native-sandbox.py", "native-sandbox.mjs"):
        copy_file(AGENTS / "shared/shell" / name, home / DATA_REL / "shell" / name)
    install_harness(home)
    write_json(runtime / "tools.json", {"node": str(node), "agents": agents})


def _credential_json(path: Path) -> dict:
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)) as stream:
        metadata = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise WorkbenchError("Model login file must be an owner-only regular file")
        value = json.load(stream)
    if not isinstance(value, dict):
        raise WorkbenchError("Model login file must contain an object")
    return value


def _has_login(vendor: str, value: dict) -> bool:
    if vendor == "claude":
        credential = value.get("claudeAiOauth")
        return isinstance(credential, dict) and bool(credential.get("accessToken"))
    return bool(value)


def authorize(home: Path | None = None) -> dict[str, bool]:
    """Seed shared model-only caches once; never replace refreshed native credentials."""
    home = (home or Path.home()).resolve()
    store = home / DATA_REL / "model-auth"
    enrolled: dict[str, bool] = dict.fromkeys(("codex", "pi", "claude"), False)
    for vendor, filename in (
        ("codex", "auth.json"),
        ("pi", "auth.json"),
        ("claude", ".credentials.json"),
    ):
        destination = store / vendor / filename
        exists = destination.exists() or destination.is_symlink()
        if exists and _has_login(vendor, _credential_json(destination)):
            enrolled[vendor] = True
            continue
        if vendor == "claude":
            result = subprocess.run(
                [
                    "/usr/bin/security",
                    "find-generic-password",
                    "-s",
                    "Claude Code-credentials",
                    "-w",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode:
                continue
            credential = json.loads(result.stdout).get("claudeAiOauth")
            value = {"claudeAiOauth": credential} if isinstance(credential, dict) else {}
        else:
            source = home / (".codex/auth.json" if vendor == "codex" else ".pi/agent/auth.json")
            if not source.exists():
                continue
            value = _credential_json(source)
            if vendor == "pi":
                # Command-backed keys can invoke host credential tools; do not import them.
                value = {
                    key: item
                    for key, item in value.items()
                    if isinstance(item, dict) and item.get("type") == "oauth"
                }
        if not _has_login(vendor, value):
            continue
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with os.fdopen(
            os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | (os.O_TRUNC if exists else os.O_EXCL),
                0o600,
            ),
            "w",
        ) as stream:
            json.dump(value, stream)
            stream.write("\n")
        enrolled[vendor] = True
    return enrolled


def run_agent(vendor: str, location: str, args: list[str]) -> int:
    """The installed script enters containment without importing checkout code."""
    launcher = Path.home() / DATA_REL / "shell/native-sandbox.py"
    if not launcher.is_file():
        raise WorkbenchError("Native runtime is not prepared; run workbench native prepare")
    return subprocess.run(
        ["/usr/bin/python3", "-I", "-S", str(launcher), vendor, location, *args],
        check=False,
    ).returncode
