"""Shared constants, error type, and filesystem primitives for the workbench CLI."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "agents"
DATA_REL = Path(".local/share/workbench")
CODEX_APPENDIX = """\

## Codex-Specific

- This project uses AGENTS.md as its primary instruction file.
- When CODEX.md exists at a project root, it is a symlink to AGENTS.md.
- Follow the same verification, testing, and minimal-change conventions as Claude Code.
"""
# Vercel's skills deploy CLI, pinned so `sync` never executes whatever npm
# happens to serve as latest. Bump deliberately: `npm view skills version`.
SKILLS_CLI = "skills@1.5.19"
# Retired capabilities: name -> why. Each mapping is both the enforcement list
# (sync removes, drift flags) and the record of the decision — the single
# source for anything code can turn off. Tool/approach rejections with no code
# switch stay in docs/decisions/tombstones.md.
RETIRED_SUBAGENTS = {
    "docs-scribe": (
        "ordinary documentation updates gain too little from an isolated"
        " context beyond project rules and the project-files skill"
    ),
    "legacy-modernizer": (
        "planning, execution, testing, and dependency skills already cover"
        " incremental modernization without another overlapping trigger"
    ),
}
RETIRED_SKILLS = {
    "agentic-e2e-debugging": (
        "its browser/service/commit workflow overlapped systematic-debugging"
        " plus browser-tooling and assumed authority that does not generalize"
    ),
    "converge": (
        "its metric engine, language packs, and prescriptive loop overlapped"
        " the code-health lenses and project-owned gates"
    ),
}
VENDORS = ("claude", "codex", "pi")
VENDOR_CHOICES = (*VENDORS, "all")

# Sandbox policy deployed to (and drift-checked against) ~/.claude/settings.json.
# Single source so `sync` (the writer) and `drift` (the verifier) never diverge.
#
# The catastrophe guards — rm -rf, disk erase, git reset --hard, --no-verify, …
# — live in permissions.json plus the guard hooks and are independent of this
# block. This layer is *containment*: it caps writes and secret reads on the
# default sandboxed path. Two deliberate escape valves keep containment from
# breaking safe work:
#   - filesystem.allowWrite re-opens regenerable tool caches (uv, pip, …) so the
#     Python check gate runs in-sandbox instead of failing on ~/.cache.
#   - excludedCommands runs network git and gh *entirely* outside the sandbox
#     (SSH auth and Go-TLS both break inside Seatbelt). Patterns are whole-command
#     globs — "git push" alone matches only a bare command, so each verb needs a
#     "<verb> *" form to catch real invocations like `git push origin main`.
#     These still pass through the permission rules and guard hooks, so a
#     force-push or reset --hard stays blocked; only containment is lifted.
#   - allowUnsandboxedCommands is True so the long tail of sandbox-incompatible
#     commands (other network tools) retries outside via the escape hatch,
#     gated by the auto-mode classifier — restoring autonomy without a blanket
#     bypass. The catastrophe guards above still apply to every retry.
CLAUDE_SANDBOX = {
    "enabled": True,
    "failIfUnavailable": True,
    "allowUnsandboxedCommands": True,
    "filesystem": {
        "allowWrite": ["~/.cache"],
        "denyRead": [
            "~/.ssh",
            "~/.gnupg",
            "~/.aws",
            "~/.config/gcloud",
            "~/Library/Keychains",
        ],
        "denyWrite": [
            "~/.ssh",
            "~/.gnupg",
            "~/.aws",
            "~/.config/gcloud",
            "~/Library/Keychains",
        ],
    },
    "excludedCommands": [
        "git push",
        "git push *",
        "git fetch",
        "git fetch *",
        "git pull",
        "git pull *",
        "gh",
        "gh *",
    ],
}


class WorkbenchError(RuntimeError):
    """A source or deployed configuration cannot be handled safely."""


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchError(f"invalid JSON: {path}: {exc}") from exc


def _backup(path: Path) -> None:
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))


def write_text(path: Path, content: str, *, executable: bool = False) -> bool:
    current = path.read_text() if path.exists() else None
    if current == content:
        if executable:
            path.chmod(path.stat().st_mode | 0o111)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    _backup(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content)
    if executable:
        tmp.chmod(tmp.stat().st_mode | 0o111)
    tmp.replace(path)
    return True


def write_json(path: Path, value: Any) -> bool:
    return write_text(path, json.dumps(value, indent=2) + "\n")


def copy_file(source: Path, destination: Path, *, executable: bool = False) -> bool:
    return write_text(destination, source.read_text(), executable=executable)


def _settings(path: Path) -> dict[str, Any]:
    raw = load_json(path, {})
    if not isinstance(raw, dict):
        raise WorkbenchError(f"settings must be a JSON object: {path}")
    return raw


def _string_array(path: Path) -> list[str]:
    raw = load_json(path, [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise WorkbenchError(f"expected a string array: {path}")
    return raw


def _frontmatter_field(text: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*([^\n]+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _installed_plugins(vendor: str, output: str) -> dict[str, bool]:
    """Map installed plugin id -> enabled state from vendor CLI JSON output.

    Both vendor CLIs expose an ``enabled`` boolean per installed plugin
    (verified against claude and codex 0.144.4 `plugin list --json`), so
    verification can require declared plugins to be installed AND enabled.
    """
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        raise WorkbenchError(f"invalid {vendor} plugin inventory: {exc}") from exc
    if vendor == "claude":
        if not isinstance(parsed, list):
            raise WorkbenchError("Claude plugin inventory must be an array")
        return {
            item["id"]: bool(item.get("enabled", True))
            for item in parsed
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
    if not isinstance(parsed, dict) or not isinstance(parsed.get("installed"), list):
        raise WorkbenchError("Codex plugin inventory must contain installed plugins")
    return {
        item["pluginId"]: bool(item.get("enabled", True))
        for item in parsed["installed"]
        if isinstance(item, dict) and isinstance(item.get("pluginId"), str)
    }


def _home_env(home: Path) -> dict[str, str]:
    return {**os.environ, "HOME": str(home)}


def _list_plugins(vendor: str, home: Path) -> dict[str, bool]:
    result = subprocess.run(
        [vendor, "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        env=_home_env(home),
    )
    if result.returncode:
        raise WorkbenchError(f"{vendor} plugin list failed: {result.stderr.strip()}")
    return _installed_plugins(vendor, result.stdout)


def _vendors(raw: str) -> tuple[str, ...]:
    if raw == "all":
        return VENDORS
    if raw not in VENDORS:
        raise WorkbenchError(f"unsupported vendor: {raw}")
    return (raw,)
