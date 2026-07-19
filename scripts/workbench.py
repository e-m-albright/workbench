#!/usr/bin/env python3
"""Deploy and verify the personal Claude Code and Codex workbench."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
DATA_REL = Path(".local/share/workbench")
CODEX_APPENDIX = """\

## Codex-Specific

- This project uses AGENTS.md as its primary instruction file.
- When CODEX.md exists at a project root, it is a symlink to AGENTS.md.
- Follow the same verification, testing, and minimal-change conventions as Claude Code.
"""
RETIRED_SUBAGENTS = {"docs-scribe", "legacy-modernizer"}
RETIRED_SKILLS = {"agentic-e2e-debugging", "converge"}
VENDORS = ("claude", "codex")
VENDOR_CHOICES = (*VENDORS, "all")

# Sandbox policy deployed to (and drift-checked against) ~/.claude/settings.json.
# Single source so `sync` (the writer) and `check` (the verifier) never diverge.
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
            "~/.ssh", "~/.gnupg", "~/.aws", "~/.config/gcloud",
            "~/Library/Keychains",
        ],
        "denyWrite": [
            "~/.ssh", "~/.gnupg", "~/.aws", "~/.config/gcloud",
            "~/Library/Keychains",
        ],
    },
    "excludedCommands": [
        "git push", "git push *",
        "git fetch", "git fetch *",
        "git pull", "git pull *",
        "gh", "gh *",
    ],
}

WORKBENCH_BANNER = """\
██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
██║ █╗ ██║██║   ██║██████╔╝█████╔╝ ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
██║███╗██║██║   ██║██╔══██╗██╔═██╗ ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
 ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
"""
RUBY_STOPS = ((255, 184, 194), (230, 57, 86), (165, 9, 47), (101, 0, 24))


class WorkbenchError(RuntimeError):
    """A source or deployed configuration cannot be handled safely."""


class CliUsageError(RuntimeError):
    """An argparse usage failure that should use the visual renderer."""


class VisualArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


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


def _registry() -> dict[str, object]:
    raw = load_json(AGENTS / "shared/mcp-servers.json", {})
    if not isinstance(raw, dict):
        raise WorkbenchError("MCP registry must be a JSON object")
    return raw


def retired_mcp_names(registry: Mapping[str, object] | None = None) -> set[str]:
    names: set[str] = set()
    for key in registry if registry is not None else _registry():
        match = re.fullmatch(r"_(.+)_disabled", key)
        if match:
            names.add(match.group(1))
    return names


def active_mcp(
    target: str, registry: Mapping[str, object] | None = None
) -> dict[str, dict[str, object]]:
    if registry is None:
        registry = _registry()
    servers: dict[str, dict[str, object]] = {}
    for name, value in registry.items():
        if name.startswith("$") or not isinstance(value, dict):
            continue
        targets = value.get("targets", [])
        if isinstance(targets, list) and target in targets:
            servers[name] = {
                key: item for key, item in value.items() if key != "targets"
            }
    return servers


def merge_mcp(existing: Mapping[str, object], target: str) -> dict[str, object]:
    registry = _registry()
    retired = retired_mcp_names(registry)
    desired = active_mcp(target, registry)
    managed = {
        name
        for name, value in registry.items()
        if not name.startswith("$") and isinstance(value, dict)
    }
    kept = {
        name: value
        for name, value in existing.items()
        if name not in retired and (name not in managed or name in desired)
    }
    return {**kept, **desired}


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
        raise WorkbenchError(
            f"{vendor} plugin list failed: {result.stderr.strip()}"
        )
    return _installed_plugins(vendor, result.stdout)


def _sync_plugins(vendor: str, home: Path) -> None:
    desired = _string_array(AGENTS / vendor / "plugins.json")
    if not shutil.which(vendor):
        raise WorkbenchError(f"{vendor} is required to deploy {vendor} plugins")
    installed = _list_plugins(vendor, home)
    for plugin in desired:
        if plugin in installed:
            continue
        command = [vendor, "plugin", "install", plugin, "--scope", "user"]
        if vendor == "codex":
            command = [vendor, "plugin", "add", plugin, "--json"]
        subprocess.run(command, check=True, env=_home_env(home))


def _canonical_hooks() -> dict[str, Path]:
    """Hook name -> source path, shared by sync (writer) and check (verifier)."""
    return {
        hook.name: hook for hook in sorted((AGENTS / "shared/hooks").glob("*.sh"))
    }


def _install_runtime_files(home: Path) -> Path:
    data = home / DATA_REL
    hooks = _canonical_hooks()
    hook_dir = data / "hooks"
    if hook_dir.exists():
        for deployed in hook_dir.iterdir():
            if deployed.is_file() and deployed.name not in hooks:
                deployed.unlink()
    for name, hook in hooks.items():
        copy_file(hook, hook_dir / name, executable=True)
    copy_file(
        AGENTS / "claude/statusline.sh",
        data / "claude/statusline.sh",
        executable=True,
    )
    return data


def _sync_skills(vendor: str, home: Path) -> None:
    skill_names = sorted(
        path.parent.name for path in (AGENTS / "skills").glob("*/SKILL.md")
    )
    if not shutil.which("npx"):
        raise WorkbenchError("npx is required to deploy skills")
    env = _home_env(home)
    # The npx skills CLI names the claude agent "claude-code"; that external id
    # stays at this subprocess boundary — everything else speaks "claude".
    agent_id = "claude-code" if vendor == "claude" else vendor
    # Remove the full current set too (not just retirements) so a renamed or
    # relocated skill can't leave a stale copy behind from a prior deploy.
    removals = sorted(set(skill_names) | RETIRED_SKILLS)
    if removals:
        subprocess.run(
            ["npx", "skills", "remove", *removals, "-a", agent_id, "-g", "-y"],
            check=False,
            env=env,
        )
    subprocess.run(
        [
            "npx",
            "skills",
            "add",
            str(AGENTS / "skills"),
            "-s",
            "*",
            "-a",
            agent_id,
            "-g",
            "-y",
            "--copy",
        ],
        check=True,
        env=env,
    )
    skill_roots = [home / ".agents/skills"]
    if vendor == "claude":
        skill_roots.append(home / ".claude/skills")
    for root in skill_roots:
        for name in RETIRED_SKILLS:
            retired = root / name
            if retired.is_symlink() or retired.is_file():
                retired.unlink()
            elif retired.exists():
                shutil.rmtree(retired)


def _frontmatter_field(text: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*([^\n]+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def _subagent_fields(path: Path) -> tuple[str, str, str, list[str] | None]:
    content = path.read_text()
    parts = content.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise WorkbenchError(f"invalid subagent frontmatter: {path}")
    frontmatter, body = parts[1], parts[2].strip()
    name = _frontmatter_field(frontmatter, "name")
    description = _frontmatter_field(frontmatter, "description")
    if not name or not description or not body:
        raise WorkbenchError(f"incomplete subagent: {path}")
    raw_tools = _frontmatter_field(frontmatter, "tools")
    tools = (
        [tool.strip() for tool in raw_tools.split(",") if tool.strip()]
        if raw_tools is not None
        else None
    )
    return name, description, body, tools


# Claude write-capable tools whose absence from a `tools:` restriction marks
# a subagent as read-only for Codex rendering purposes.
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def _render_codex_subagent(path: Path) -> str:
    name, description, instructions, tools = _subagent_fields(path)
    lines = [
        f"name = {json.dumps(name)}",
        f"description = {json.dumps(description)}",
    ]
    # Codex agent TOML has no per-tool allowlist equivalent to Claude's
    # `tools:` frontmatter, but its subagent schema does accept `sandbox_mode`
    # with "read-only" | "workspace-write" (verified against the codex
    # 0.144.4 binary: the subagent frontmatter parser enumerates
    # model_reasoning_effort, sandbox_mode, developer_instructions). Render
    # read-only sandboxing when the source restricts tools to a
    # non-writing set.
    if tools is not None and not (_WRITE_TOOLS & set(tools)):
        lines.append('sandbox_mode = "read-only"')
    lines.append(f"developer_instructions = {json.dumps(instructions)}")
    lines.append("")
    return "\n".join(lines)


def _sync_subagents(vendor: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    if vendor == "codex":
        for stale in destination.glob("*.md*"):
            stale.unlink()
    for name in RETIRED_SUBAGENTS:
        for suffix in (".md", ".md.bak", ".toml", ".toml.bak"):
            retired = destination / f"{name}{suffix}"
            if retired.exists():
                retired.unlink()
    for source in sorted((AGENTS / "subagents").glob("*.md")):
        if vendor == "claude":
            copy_file(source, destination / source.name)
        else:
            write_text(
                destination / f"{source.stem}.toml",
                _render_codex_subagent(source),
            )


def managed_claude_settings(data: Path) -> dict[str, Any]:
    """Workbench-managed keys of ~/.claude/settings.json.

    Single source for `sync` (the writer) and `check` (the verifier) so the
    two commands can never diverge on what "managed" means.
    """
    plugins = _string_array(AGENTS / "claude/plugins.json")
    return {
        "enabledPlugins": {name: True for name in plugins},
        "permissions": _settings(AGENTS / "claude/permissions.json"),
        "hooks": _settings(AGENTS / "shared/hooks.json").get("hooks", {}),
        "statusLine": {
            "type": "command",
            "command": str(data / "claude/statusline.sh"),
        },
        "voiceEnabled": True,
        "preferredNotifChannel": "auto",
        "defaultMode": "auto",
        "sandbox": CLAUDE_SANDBOX,
    }


def expected_codex_rules_md() -> str:
    """Canonical ~/.codex/AGENTS.md content, shared by sync and check."""
    return (AGENTS / "shared/rules.md").read_text().rstrip() + CODEX_APPENDIX


def sync_claude(
    home: Path, *, deploy_skills: bool, deploy_plugins: bool = False
) -> None:
    data = _install_runtime_files(home)
    claude_home = home / ".claude"
    copy_file(AGENTS / "shared/rules.md", claude_home / "CLAUDE.md")

    settings_path = claude_home / "settings.json"
    settings = _settings(settings_path)
    managed = managed_claude_settings(data)

    existing_permissions = settings.get("permissions", {})
    if not isinstance(existing_permissions, dict):
        existing_permissions = {}
    # Legacy-location cleanup: defaultMode now lives at the settings top level;
    # a stale nested copy would shadow the managed value.
    existing_permissions.pop("defaultMode", None)
    settings.update(managed)
    settings["permissions"] = {**existing_permissions, **managed["permissions"]}
    write_json(settings_path, settings)

    claude_root = home / ".claude.json"
    root_settings = _settings(claude_root)
    live_mcp = root_settings.get("mcpServers", {})
    if not isinstance(live_mcp, dict):
        live_mcp = {}
    root_settings["mcpServers"] = merge_mcp(live_mcp, "claude")
    write_json(claude_root, root_settings)

    _sync_claude_desktop(home)
    _sync_subagents("claude", claude_home / "agents")
    if deploy_skills:
        _sync_skills("claude", home)
    if deploy_plugins:
        _sync_plugins("claude", home)


def _desktop_mcp() -> dict[str, dict[str, object]]:
    raw = {**active_mcp("claude"), **active_mcp("desktop")}
    result: dict[str, dict[str, object]] = {}
    for name, config in raw.items():
        if config.get("type") == "http" and isinstance(config.get("url"), str):
            args: list[str] = ["-y", "mcp-remote", str(config["url"])]
            headers = config.get("headers", {})
            if isinstance(headers, dict):
                args.extend(f"--header={key}:{value}" for key, value in headers.items())
            result[name] = {"command": "npx", "args": args}
        else:
            result[name] = config
    return result


def _sync_claude_desktop(home: Path) -> None:
    path = home / "Library/Application Support/Claude/claude_desktop_config.json"
    settings = _settings(path)
    live_mcp = settings.get("mcpServers", {})
    if not isinstance(live_mcp, dict):
        live_mcp = {}
    kept = {
        name: value
        for name, value in live_mcp.items()
        if name not in retired_mcp_names()
    }
    settings["mcpServers"] = {**kept, **_desktop_mcp()}

    source = _settings(AGENTS / "claude/desktop-preferences.json")
    defaults = source.get("preferences", {})
    existing = settings.get("preferences", {})
    if not isinstance(defaults, dict) or not isinstance(existing, dict):
        raise WorkbenchError("Claude Desktop preferences must be JSON objects")
    settings["preferences"] = {**defaults, **existing}
    write_json(path, settings)


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return (
            "{"
            + ", ".join(
                f"{json.dumps(str(k))} = {_toml_value(v)}" for k, v in value.items()
            )
            + "}"
        )
    raise WorkbenchError(f"unsupported TOML value type: {type(value).__name__}")


def _render_mcp(servers: Mapping[str, object]) -> str:
    lines: list[str] = []
    for name, raw in sorted(servers.items()):
        lines.append(f"[mcp_servers.{name}]")
        if isinstance(raw, dict):
            lines.extend(f"{key} = {_toml_value(value)}" for key, value in raw.items())
        lines.append("")
    return "\n".join(lines)


def _drop_tables(text: str, prefixes: tuple[str, ...]) -> str:
    # Ceiling: line-based, not TOML-aware. A multi-line string whose body
    # contains a line that looks like a table header will be mis-parsed;
    # the round-trip tomllib guard in merge_codex_config catches the
    # corruption and aborts instead of writing it. Upgrade path: rewrite on
    # top of a real TOML parser/emitter (e.g. tomlkit) that preserves
    # comments and formatting.
    result: list[str] = []
    dropping = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("["):
            dropping = any(stripped.startswith(prefix) for prefix in prefixes)
        if not dropping:
            result.append(line)
    return "".join(result).rstrip()


def merge_codex_config(text: str) -> str:
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise WorkbenchError(f"invalid Codex TOML: {exc}") from exc

    existing = parsed.get("mcp_servers", {})
    if not isinstance(existing, dict):
        existing = {}
    servers = merge_mcp(existing, "codex")
    cleaned = _drop_tables(text, ("[mcp_servers", "[tui"))
    status = tomllib.loads((AGENTS / "codex/statusline.toml").read_text())
    existing_tui = parsed.get("tui", {})
    if not isinstance(existing_tui, dict):
        existing_tui = {}
    tui_values = {**existing_tui, **status}
    tui = "[tui]\n" + "\n".join(
        f"{key} = {_toml_value(value)}" for key, value in tui_values.items()
    )
    fallback = 'project_doc_fallback_filenames = ["CODEX.md"]'
    if "project_doc_fallback_filenames" not in parsed:
        cleaned = f"{fallback}\n\n{cleaned}" if cleaned else fallback
    defaults = []
    if "sandbox_mode" not in parsed:
        defaults.append('sandbox_mode = "workspace-write"')
    if "approval_policy" not in parsed:
        defaults.append('approval_policy = "on-request"')
    if defaults:
        cleaned = "\n".join(defaults) + (f"\n\n{cleaned}" if cleaned else "")
    blocks = [part for part in (cleaned, _render_mcp(servers).rstrip(), tui) if part]
    merged = "\n\n".join(blocks) + "\n"
    try:
        tomllib.loads(merged)
    except tomllib.TOMLDecodeError as exc:
        raise WorkbenchError(f"generated invalid Codex TOML: {exc}") from exc
    return merged


def sync_codex(
    home: Path, *, deploy_skills: bool, deploy_plugins: bool = False
) -> None:
    _install_runtime_files(home)
    codex_home = home / ".codex"
    write_text(codex_home / "AGENTS.md", expected_codex_rules_md())

    live_rules = codex_home / "rules/default.rules"
    source_rules = AGENTS / "codex/default.rules"
    existing_rules = live_rules.read_text() if live_rules.exists() else ""
    write_text(live_rules, merge_codex_rules(source_rules.read_text(), existing_rules))

    config = codex_home / "config.toml"
    existing = config.read_text() if config.exists() else ""
    write_text(config, merge_codex_config(existing))
    for profile in sorted((AGENTS / "codex/profiles").glob("*.toml")):
        copy_file(profile, codex_home / f"{profile.stem}.config.toml")
    copy_file(AGENTS / "shared/hooks.json", codex_home / "hooks.json")
    _sync_subagents("codex", codex_home / "agents")
    if deploy_skills:
        _sync_skills("codex", home)
    if deploy_plugins:
        _sync_plugins("codex", home)


def merge_codex_rules(canonical: str, live: str) -> str:
    """Preserve local approvals without retaining known policy bypasses.

    Codex appends interactively approved rules wherever the cursor lands, so
    unknown prefix_rule lines are harvested from the whole live file — not
    just the locally-approved section — deduped against the canonical rules,
    and re-homed under the marker.
    """
    canonical_lines = set(canonical.splitlines())
    marker = "# --- Locally approved additions ---"
    unsafe_fragments = (
        '"--no-verify"',
        '["git", "reset", "--hard"]',
        '["git", "push", "--force"]',
        '["git", "push", "-f"]',
        '["rm", "-rf"]',
        '["rm", "-fr"]',
    )
    additions: list[str] = []
    for line in live.splitlines():
        if (
            line.startswith("prefix_rule(")
            and line not in canonical_lines
            and line not in additions
            and not any(fragment in line for fragment in unsafe_fragments)
        ):
            additions.append(line)
    result = canonical.rstrip()
    if additions:
        result += f"\n\n{marker}\n" + "\n".join(additions)
    return result + "\n"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare(source: Path, destination: Path, label: str, findings: list[str]) -> None:
    if not destination.exists():
        findings.append(f"DRIFT {label}: missing {destination}")
    elif _digest(source) != _digest(destination):
        findings.append(f"DRIFT {label}: differs from {source.relative_to(ROOT)}")


def _compare_text(
    expected: str, destination: Path, label: str, findings: list[str]
) -> None:
    if not destination.exists():
        findings.append(f"DRIFT {label}: missing {destination}")
    elif destination.read_text() != expected:
        findings.append(f"DRIFT {label}")


def _managed_value_errors(
    actual: object, expected: object, label: str
) -> list[str]:
    if not isinstance(expected, dict):
        return [] if actual == expected else [f"DRIFT {label}"]
    if not isinstance(actual, dict):
        return [f"DRIFT {label} is not an object"]
    errors: list[str] = []
    for key, value in expected.items():
        errors.extend(
            _managed_value_errors(actual.get(key), value, f"{label}.{key}")
        )
    return errors


def _check_skills(
    skill_root: Path, vendor: str, findings: list[str], external: list[str]
) -> None:
    canonical = {
        path.parent.name: path.parent
        for path in (AGENTS / "skills").glob("*/SKILL.md")
    }
    deployed = {
        path.parent.name: path.parent for path in skill_root.glob("*/SKILL.md")
    }
    for name, source_root in canonical.items():
        if name not in deployed:
            findings.append(f"DRIFT {vendor} skill missing: {name}")
            continue
        for source in source_root.rglob("*"):
            if source.is_file():
                relative = source.relative_to(source_root)
                _compare(
                    source,
                    deployed[name] / relative,
                    f"{vendor} skill {name}/{relative}",
                    findings,
                )
    for name in deployed.keys() - canonical.keys():
        if name in RETIRED_SKILLS:
            findings.append(f"DRIFT retired {vendor} skill still present: {name}")
        else:
            external.append(f"EXTERNAL {vendor} skill: {name}")


def _check_subagents(
    vendor: str, destination: Path, findings: list[str], external: list[str]
) -> None:
    expected: dict[str, str] = {}
    for source in (AGENTS / "subagents").glob("*.md"):
        if vendor == "claude":
            expected[source.name] = source.read_text()
        else:
            expected[f"{source.stem}.toml"] = _render_codex_subagent(source)
    for name, content in expected.items():
        _compare_text(content, destination / name, f"{vendor} subagent {name}", findings)
    if destination.exists():
        suffix = ".md" if vendor == "claude" else ".toml"
        for deployed in destination.glob(f"*{suffix}"):
            if deployed.name in expected:
                continue
            if deployed.stem in RETIRED_SUBAGENTS:
                findings.append(
                    f"DRIFT retired {vendor} subagent still present: {deployed.stem}"
                )
            else:
                external.append(f"EXTERNAL {vendor} subagent: {deployed.stem}")
        if vendor == "codex":
            for stale in destination.glob("*.md*"):
                findings.append(f"DRIFT codex non-native subagent: {stale.name}")


def _plugin_inventory(vendor: str, home: Path) -> dict[str, bool] | None:
    """Installed plugin id -> enabled state, or None when the CLI is absent."""
    if not shutil.which(vendor):
        return None
    return _list_plugins(vendor, home)


def _check_plugins(
    vendor: str, home: Path, findings: list[str], external: list[str]
) -> None:
    declared = _string_array(AGENTS / vendor / "plugins.json")
    inventory = _plugin_inventory(vendor, home)
    if inventory is None:
        external.append(f"NOTE {vendor} plugins unverified (CLI not found)")
        return
    for plugin in declared:
        if plugin not in inventory:
            findings.append(f"DRIFT {vendor} plugin missing: {plugin}")
        elif not inventory[plugin]:
            findings.append(f"DRIFT {vendor} plugin disabled: {plugin}")
    for plugin in sorted(set(inventory) - set(declared)):
        external.append(f"EXTERNAL {vendor} plugin: {plugin}")


def _check_claude(
    home: Path, data: Path, findings: list[str], external: list[str]
) -> object:
    """Verify Claude-managed state; returns the live MCP mapping."""
    _compare(
        AGENTS / "shared/rules.md",
        home / ".claude/CLAUDE.md",
        "Claude rules",
        findings,
    )
    _compare(
        AGENTS / "claude/statusline.sh",
        data / "claude/statusline.sh",
        "Claude statusline",
        findings,
    )
    settings = _settings(home / ".claude/settings.json")
    findings.extend(
        _managed_value_errors(
            settings, managed_claude_settings(data), "Claude settings"
        )
    )
    desktop = _settings(
        home / "Library/Application Support/Claude/claude_desktop_config.json"
    )
    findings.extend(
        _managed_value_errors(
            desktop.get("mcpServers"), _desktop_mcp(), "Claude Desktop MCP"
        )
    )
    desktop_defaults = _settings(
        AGENTS / "claude/desktop-preferences.json"
    ).get("preferences", {})
    live_preferences = desktop.get("preferences", {})
    if not isinstance(desktop_defaults, dict) or not isinstance(
        live_preferences, dict
    ):
        findings.append("DRIFT Claude Desktop preferences is not an object")
    else:
        for key in desktop_defaults.keys() - live_preferences.keys():
            findings.append(f"DRIFT Claude Desktop preference missing: {key}")
    _check_subagents("claude", home / ".claude/agents", findings, external)
    return _settings(home / ".claude.json").get("mcpServers", {})


def _check_codex(
    home: Path, findings: list[str], external: list[str]
) -> object:
    """Verify Codex-managed state; returns the live MCP mapping."""
    _compare_text(
        expected_codex_rules_md(),
        home / ".codex/AGENTS.md",
        "Codex rules",
        findings,
    )
    config_path = home / ".codex/config.toml"
    parsed = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    if config_path.exists():
        _compare_text(
            merge_codex_config(config_path.read_text()),
            config_path,
            "Codex config",
            findings,
        )
    else:
        findings.append(f"DRIFT Codex config: missing {config_path}")
    for profile in sorted((AGENTS / "codex/profiles").glob("*.toml")):
        _compare(
            profile,
            home / ".codex" / f"{profile.stem}.config.toml",
            f"Codex profile {profile.stem}",
            findings,
        )
    _compare(
        AGENTS / "shared/hooks.json",
        home / ".codex/hooks.json",
        "Codex hooks",
        findings,
    )
    source_rules = (AGENTS / "codex/default.rules").read_text()
    rules_path = home / ".codex/rules/default.rules"
    live_rules = rules_path.read_text() if rules_path.exists() else ""
    _compare_text(
        merge_codex_rules(source_rules, live_rules),
        rules_path,
        "Codex command rules",
        findings,
    )
    _check_subagents("codex", home / ".codex/agents", findings, external)
    return parsed.get("mcp_servers", {})


def check(
    home: Path, vendors: Iterable[str], *, verify_plugins: bool = True
) -> int:
    findings: list[str] = []
    external: list[str] = []
    data = home / DATA_REL
    hooks = _canonical_hooks()
    for name, hook in hooks.items():
        _compare(hook, data / "hooks" / name, f"hook {name}", findings)
    hook_root = data / "hooks"
    if hook_root.exists():
        for deployed in hook_root.iterdir():
            if deployed.is_file() and deployed.name not in hooks:
                findings.append(f"DRIFT retired runtime hook still present: {deployed.name}")

    for vendor in vendors:
        if vendor == "claude":
            mcp = _check_claude(home, data, findings, external)
            skill_root = home / ".claude/skills"
        else:
            mcp = _check_codex(home, findings, external)
            skill_root = home / ".agents/skills"

        if not isinstance(mcp, dict):
            findings.append(f"DRIFT {vendor} MCP configuration is not an object")
            mcp = {}
        expected_mcp = active_mcp(vendor)
        for name, value in expected_mcp.items():
            if mcp.get(name) != value:
                findings.append(f"DRIFT {vendor} MCP {name}")
        for name in retired_mcp_names() & set(mcp):
            findings.append(f"DRIFT retired {vendor} MCP still present: {name}")
        for name in set(mcp) - set(expected_mcp):
            external.append(f"EXTERNAL {vendor} MCP: {name}")

        _check_skills(skill_root, vendor, findings, external)
        if verify_plugins:
            _check_plugins(vendor, home, findings, external)

    for message in findings:
        print(message)
    for message in external:
        print(message)
    if findings:
        print(
            f"\n{len(findings)} managed drift item(s); {len(external)} external item(s)"
        )
        return 1
    print(
        f"OK managed configuration matches workbench; {len(external)} external item(s)"
    )
    return 0


def _markdown_link_errors(root: Path) -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in sorted(root.rglob("*.md")):
        fenced = False
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            for match in link_pattern.finditer(line):
                raw = match.group(1).split("#", 1)[0].strip().strip("<>")
                if not raw or "://" in raw or raw.startswith(("mailto:", "/")):
                    continue
                if not (path.parent / raw).resolve().exists():
                    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
                    errors.append(f"broken local link: {relative}:{line_number}: {raw}")
    return errors


def lint() -> int:
    errors: list[str] = []
    description_chars = 0
    for path in sorted(AGENTS.rglob("*.json")):
        try:
            load_json(path)
        except WorkbenchError as exc:
            errors.append(str(exc))
    try:
        tomllib.loads((AGENTS / "codex/statusline.toml").read_text())
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"invalid Codex statusline TOML: {exc}")

    for entry in sorted((AGENTS / "skills").iterdir()):
        if entry.is_dir() and not (entry / "SKILL.md").exists():
            errors.append(
                f"skill directory without SKILL.md: {entry.relative_to(ROOT)}"
            )

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
            errors.append(
                f"invalid Codex rule syntax: {rules_path.relative_to(ROOT)}:{number}"
            )

    names: set[str] = set()
    for skill in sorted((AGENTS / "skills").glob("*/SKILL.md")):
        content = skill.read_text()
        name = _frontmatter_field(content, "name")
        if not name:
            errors.append(f"missing skill name: {skill.relative_to(ROOT)}")
            continue
        if name != skill.parent.name:
            errors.append(f"skill name/path mismatch: {skill.parent.name} != {name}")
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        names.add(name)
        raw_description = _frontmatter_field(content, "description")
        if not raw_description:
            errors.append(f"missing skill description: {skill.relative_to(ROOT)}")
            continue
        if ": " in raw_description and not (
            raw_description.startswith('"') and raw_description.endswith('"')
        ):
            errors.append(f"skill description with colon must be quoted: {name}")
        length = len(raw_description.strip('"'))
        description_chars += length
        if length > 280:
            errors.append(f"skill description exceeds 280 chars: {name} ({length})")

    if description_chars > 5_000:
        errors.append(
            f"skill descriptions exceed 5000-char context budget: {description_chars}"
        )

    for script in sorted(AGENTS.rglob("*.sh")):
        result = subprocess.run(
            ["bash", "-n", str(script)], capture_output=True, text=True
        )
        if result.returncode:
            errors.append(result.stderr.strip())
    errors.extend(_markdown_link_errors(ROOT))
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        return 1
    print(f"OK {len(names)} skills, JSON, TOML, and shell syntax")
    return 0


def _vendors(raw: str) -> tuple[str, ...]:
    if raw == "all":
        return VENDORS
    if raw not in VENDORS:
        raise WorkbenchError(f"unsupported vendor: {raw}")
    return (raw,)


def _styled(value: str, code: str) -> str:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR") is not None:
        return value
    return f"\033[{code}m{value}\033[0m"


def _gradient_color(
    position: float, stops: tuple[tuple[int, int, int], ...]
) -> tuple[int, int, int]:
    position = min(max(position, 0.0), 1.0)
    segment = position * (len(stops) - 1)
    index = min(int(segment), len(stops) - 2)
    fraction = segment - index
    start, end = stops[index], stops[index + 1]
    return tuple(
        round(start[channel] + (end[channel] - start[channel]) * fraction)
        for channel in range(3)
    )


def gradient_banner(*, color: bool | None = None) -> str:
    """Render the Workbench wordmark with a horizontal ruby gradient."""
    lines = WORKBENCH_BANNER.rstrip().splitlines()
    if color is None:
        color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    if not color:
        return "\n".join(lines)
    width = max(map(len, lines))
    rendered: list[str] = []
    for line in lines:
        parts: list[str] = []
        for column, character in enumerate(line):
            red, green, blue = _gradient_color(
                column / max(1, width - 1), RUBY_STOPS
            )
            parts.append(f"\033[38;2;{red};{green};{blue}m{character}")
        rendered.append("".join(parts) + "\033[0m")
    return "\n".join(rendered)


def _panel(title: str, rows: list[tuple[str, str]], width: int) -> str:
    """Render the same rounded, two-column help panel used by Dotfiles."""
    inner_width = width - 2
    content_width = inner_width - 2
    left_width = min(max(len(left) for left, _ in rows), content_width // 2)
    right_width = content_width - left_width - 2
    title_bar = f"─ {title} "
    lines = [f"╭{title_bar}{'─' * (inner_width - len(title_bar))}╮"]
    for left, description in rows:
        wrapped = textwrap.wrap(description, width=right_width) or [""]
        for index, chunk in enumerate(wrapped):
            raw_left = left if index == 0 else ""
            padded_left = f"{raw_left:<{left_width}}"
            padded_chunk = f"{chunk:<{right_width}}"
            if raw_left.startswith("  "):
                padded_left = _styled(padded_left, "2")
                padded_chunk = _styled(padded_chunk, "2")
            elif raw_left:
                padded_left = _styled(padded_left, "1;36")
            lines.append(f"│ {padded_left}  {padded_chunk} │")
    lines.append(f"╰{'─' * inner_width}╯")
    return "\n".join(lines)


def _help_width() -> int:
    return max(72, shutil.get_terminal_size((80, 24)).columns)


def _subcommands(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    # Accepted tradeoff: the help renderer introspects argparse internals
    # (_actions, _SubParsersAction) so the parser stays the single source of
    # command metadata. Confined to this helper and the two renderers below;
    # covered by the CLI help tests.
    return next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )


def _command_rows(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    subparsers = _subcommands(parser)
    descriptions = {
        action.dest: action.help for action in subparsers._choices_actions
    }
    rows: list[tuple[str, str]] = []
    for name, command_parser in subparsers.choices.items():
        label = name
        positionals = [
            action
            for action in command_parser._actions
            if not action.option_strings and action.choices
        ]
        if positionals:
            choices = "|".join(str(choice) for choice in positionals[0].choices)
            label += f" [{choices}]"
        rows.append((label, descriptions[name]))

        options = [
            action
            for action in command_parser._actions
            if action.option_strings and action.dest != "help"
        ]
        for index, action in enumerate(options):
            branch = "└" if index == len(options) - 1 else "├"
            rows.append((f"  {branch} {action.option_strings[0]}", action.help))
    return rows


def _error_panel(message: str) -> str:
    return _panel("Error", [("×", message)], _help_width())


def print_help(
    parser: argparse.ArgumentParser, *, stream=None, error: str | None = None
) -> None:
    """Render the branded front door in the same visual grammar as Dotfiles."""
    stream = stream or sys.stdout
    width = _help_width()
    print(gradient_banner(), file=stream)
    print(file=stream)
    if error:
        print(_error_panel(error), file=stream)
    print(
        _styled(" Usage: ", "1") + "workbench [OPTIONS] COMMAND [ARGS]...",
        file=stream,
    )
    print(file=stream)
    print(
        " Portable agent intelligence: deploy and verify Claude Code and Codex configuration.",
        file=stream,
    )
    print(" The shorter `wb` launcher is equivalent to `workbench`.", file=stream)
    print(file=stream)
    print(
        _panel("Options", [("--help", "Show this message and exit.")], width),
        file=stream,
    )
    print(
        _panel(
            "Configuration — deploy, verify, and validate",
            _command_rows(parser),
            width,
        ),
        file=stream,
    )


def print_command_help(
    parser: argparse.ArgumentParser,
    command: str,
    *,
    stream=None,
    error: str | None = None,
) -> None:
    stream = stream or sys.stdout
    sub = _subcommands(parser).choices[command]
    positionals = [
        action
        for action in sub._actions
        if not action.option_strings and action.choices
    ]
    options = [
        action
        for action in sub._actions
        if action.option_strings and action.dest != "help"
    ]
    usage = f"workbench {command}"
    if positionals:
        usage += " [" + "|".join(str(c) for c in positionals[0].choices) + "]"
    if options:
        usage += " [OPTIONS]"
    rows = [(action.dest, action.help or "") for action in positionals]
    rows += [(action.option_strings[0], action.help or "") for action in options]
    rows = rows or [("no arguments", "")]
    if error:
        print(_error_panel(error), file=stream)
    print(_styled(" Usage: ", "1") + usage, file=stream)
    print(file=stream)
    print(f" {sub.description}", file=stream)
    print(file=stream)
    print(_panel("Arguments and options", rows, _help_width()), file=stream)


def build_parser() -> argparse.ArgumentParser:
    parser = VisualArgumentParser(
        prog="workbench",
        description=(
            "Portable agent intelligence: deploy and verify Claude Code and Codex configuration.\n"
            "The shorter `wb` launcher is equivalent to `workbench`."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sync_parser = sub.add_parser(
        "sync",
        help="deploy canonical configuration",
        description="Deploy Workbench-managed configuration to one or both vendors.",
    )
    sync_parser.add_argument(
        "vendor",
        nargs="?",
        choices=VENDOR_CHOICES,
        default="all",
        help="vendor to reconcile (default: all)",
    )
    sync_parser.add_argument(
        "--no-skills",
        action="store_true",
        help="skip shared-skill installation",
    )
    sync_parser.add_argument(
        "--no-plugins",
        action="store_true",
        help="skip declared-plugin installation",
    )
    check_parser = sub.add_parser(
        "check",
        help="report managed drift and external additions",
        description=(
            "Compare live vendor configuration directly with canonical Workbench sources."
        ),
    )
    check_parser.add_argument(
        "vendor",
        nargs="?",
        choices=VENDOR_CHOICES,
        default="all",
        help="vendor to inspect (default: all)",
    )
    check_parser.add_argument(
        "--no-plugins",
        action="store_true",
        help="skip declared-plugin verification",
    )
    sub.add_parser(
        "lint",
        help="validate canonical repository sources",
        description="Validate skills, local links, JSON, TOML, and shell syntax.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = sys.argv[1:] if argv is None else argv
    if not raw_argv or raw_argv in (["-h"], ["--help"]):
        print_help(parser)
        return 0
    commands = _subcommands(parser).choices
    requested_command = next(
        (value for value in raw_argv if value in commands), None
    )
    if requested_command and any(value in {"-h", "--help"} for value in raw_argv):
        print_command_help(parser, requested_command)
        return 0
    try:
        args = parser.parse_args(raw_argv)
    except CliUsageError as exc:
        if requested_command:
            print_command_help(
                parser, requested_command, stream=sys.stderr, error=str(exc)
            )
        else:
            print_help(parser, stream=sys.stderr, error=str(exc))
        return 2
    home = Path(os.environ.get("WORKBENCH_HOME", Path.home()))

    try:
        if args.command == "lint":
            return lint()
        vendors = _vendors(args.vendor)
        if args.command == "check":
            return check(home, vendors, verify_plugins=not args.no_plugins)
        for vendor in vendors:
            if vendor == "claude":
                sync_claude(
                    home,
                    deploy_skills=not args.no_skills,
                    deploy_plugins=not args.no_plugins,
                )
            else:
                sync_codex(
                    home,
                    deploy_skills=not args.no_skills,
                    deploy_plugins=not args.no_plugins,
                )
        print("OK workbench synchronized")
        return 0
    except (WorkbenchError, OSError, subprocess.CalledProcessError) as exc:
        print(_error_panel(str(exc)), file=sys.stderr)
        if args.command in commands:
            print_command_help(parser, args.command, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
