"""Compare live vendor configuration directly with canonical Workbench sources."""

from __future__ import annotations

import hashlib
import shutil
import tomllib
from collections.abc import Iterable
from pathlib import Path

from workbench.codex import expected_codex_rules_md, merge_codex_config, merge_codex_rules
from workbench.core import (
    AGENTS,
    DATA_REL,
    RETIRED_PI_EXTENSIONS,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
    ROOT,
    _list_plugins,
    _settings,
    _string_array,
)
from workbench.mcp import _desktop_mcp, active_mcp, retired_mcp_names
from workbench.sync import _canonical_hooks, _canonical_shell_fragments, managed_claude_settings


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare(source: Path, destination: Path, label: str, findings: list[str]) -> None:
    if not destination.exists():
        findings.append(f"DRIFT {label}: missing {destination}")
    elif _digest(source) != _digest(destination):
        findings.append(f"DRIFT {label}: differs from {source.relative_to(ROOT)}")


def _compare_text(expected: str, destination: Path, label: str, findings: list[str]) -> None:
    if not destination.exists():
        findings.append(f"DRIFT {label}: missing {destination}")
    elif destination.read_text() != expected:
        findings.append(f"DRIFT {label}")


def _check_private_mode(path: Path, label: str, findings: list[str]) -> None:
    if path.exists() and path.stat().st_mode & 0o077:
        findings.append(f"DRIFT {label} is accessible to other local users: {path}")


def _managed_value_errors(actual: object, expected: object, label: str) -> list[str]:
    if not isinstance(expected, dict):
        return [] if actual == expected else [f"DRIFT {label}"]
    if not isinstance(actual, dict):
        return [f"DRIFT {label} is not an object"]
    errors: list[str] = []
    for key, value in expected.items():
        errors.extend(_managed_value_errors(actual.get(key), value, f"{label}.{key}"))
    return errors


def _check_skills(skill_root: Path, vendor: str, findings: list[str], external: list[str]) -> None:
    canonical = {path.parent.name: path.parent for path in (AGENTS / "skills").glob("*/SKILL.md")}
    deployed = {path.parent.name: path.parent for path in skill_root.glob("*/SKILL.md")}
    for name, source_root in canonical.items():
        if name not in deployed:
            findings.append(f"DRIFT {vendor} skill missing: {name}")
            continue
        source_files = {
            source.relative_to(source_root) for source in source_root.rglob("*") if source.is_file()
        }
        deployed_files = {
            path.relative_to(deployed[name]) for path in deployed[name].rglob("*") if path.is_file()
        }
        for relative in sorted(source_files):
            _compare(
                source_root / relative,
                deployed[name] / relative,
                f"{vendor} skill {name}/{relative}",
                findings,
            )
        for relative in sorted(deployed_files - source_files):
            findings.append(f"DRIFT {vendor} skill {name}: unexpected file {relative}")
    for name in deployed.keys() - canonical.keys():
        if name in RETIRED_SKILLS:
            findings.append(f"DRIFT retired {vendor} skill still present: {name}")
        else:
            external.append(f"EXTERNAL {vendor} skill: {name}")


def _check_pi_native_skills(skill_root: Path, findings: list[str], external: list[str]) -> None:
    """Pi-native skills may be external, but shared copies are duplicate drift."""
    canonical = {path.parent.name for path in (AGENTS / "skills").glob("*/SKILL.md")}
    deployed = {path.parent.name for path in skill_root.glob("*/SKILL.md")}
    for name in sorted(deployed):
        if name in canonical:
            findings.append(f"DRIFT duplicate Pi skill shadows shared skill: {name}")
        elif name in RETIRED_SKILLS:
            findings.append(f"DRIFT retired pi skill still present: {name}")
        else:
            external.append(f"EXTERNAL pi skill: {name}")


def _check_agents(vendor: str, destination: Path, findings: list[str], external: list[str]) -> None:
    if not destination.exists():
        return
    native_suffix = ".md" if vendor == "claude" else ".toml"
    for deployed in destination.iterdir():
        if not deployed.is_file():
            continue
        name = deployed.name.split(".", 1)[0]
        if name in RETIRED_SUBAGENTS:
            findings.append(f"DRIFT retired {vendor} agent still present: {name}")
        elif deployed.suffix == native_suffix:
            external.append(f"EXTERNAL {vendor} agent: {deployed.stem}")


def _plugin_inventory(vendor: str, home: Path) -> dict[str, bool] | None:
    """Installed plugin id -> enabled state, or None when the CLI is absent."""
    if not shutil.which(vendor):
        return None
    return _list_plugins(vendor, home)


def _check_plugins(vendor: str, home: Path, findings: list[str], external: list[str]) -> None:
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


def _check_claude(home: Path, data: Path, findings: list[str], external: list[str]) -> object:
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
        _managed_value_errors(settings, managed_claude_settings(data), "Claude settings")
    )
    claude_root = home / ".claude.json"
    desktop_path = home / "Library/Application Support/Claude/claude_desktop_config.json"
    _check_private_mode(claude_root, "Claude root configuration", findings)
    _check_private_mode(desktop_path, "Claude Desktop configuration", findings)
    desktop = _settings(desktop_path)
    findings.extend(
        _managed_value_errors(desktop.get("mcpServers"), _desktop_mcp(), "Claude Desktop MCP")
    )
    desktop_defaults = _settings(AGENTS / "claude/desktop-preferences.json").get("preferences", {})
    live_preferences = desktop.get("preferences", {})
    if not isinstance(desktop_defaults, dict) or not isinstance(live_preferences, dict):
        findings.append("DRIFT Claude Desktop preferences is not an object")
    else:
        for key in desktop_defaults.keys() - live_preferences.keys():
            findings.append(f"DRIFT Claude Desktop preference missing: {key}")
    _check_agents("claude", home / ".claude/agents", findings, external)
    return _settings(claude_root).get("mcpServers", {})


def _check_pi(home: Path, findings: list[str], external: list[str]) -> None:
    pi_home = home / ".pi/agent"
    if not shutil.which("pi"):
        findings.append("DRIFT Pi CLI is not installed or not on PATH")
    sessions = pi_home / "sessions"
    if sessions.exists():
        for path in (sessions, *sessions.rglob("*")):
            if path.is_symlink():
                findings.append(f"DRIFT Pi session path is a symlink: {path}")
                continue
            if path.stat().st_mode & 0o077:
                kind = "directory" if path.is_dir() else "file"
                findings.append(
                    f"DRIFT Pi session {kind} is accessible to other local users: {path}"
                )
    _compare(AGENTS / "shared/rules.md", pi_home / "AGENTS.md", "Pi rules", findings)
    _compare(
        AGENTS / "pi/permission-policy.json",
        pi_home / "permission-policy.json",
        "Pi permission policy",
        findings,
    )
    findings.extend(
        _managed_value_errors(
            _settings(pi_home / "settings.json"),
            _settings(AGENTS / "pi/settings.json"),
            "Pi settings",
        )
    )
    for filename, nested_key in (
        ("models.json", "providers"),
        ("presets.json", None),
    ):
        actual = _settings(pi_home / filename)
        expected = _settings(AGENTS / "pi" / filename)
        if nested_key:
            actual = actual.get(nested_key, {})
            expected = expected.get(nested_key, {})
        findings.extend(_managed_value_errors(actual, expected, f"Pi {filename}"))
        if isinstance(actual, dict) and isinstance(expected, dict):
            for name in sorted(actual.keys() - expected.keys()):
                external.append(f"EXTERNAL Pi {filename} entry: {name}")

    expected_extensions = {path.name: path for path in (AGENTS / "pi/extensions").glob("*.ts")}
    deployed_extensions = {path.name: path for path in (pi_home / "extensions").glob("*.ts")}
    for name, source in expected_extensions.items():
        _compare(source, pi_home / "extensions" / name, f"Pi extension {name}", findings)
    for name in sorted(deployed_extensions.keys() - expected_extensions.keys()):
        if name in RETIRED_PI_EXTENSIONS:
            findings.append(f"DRIFT retired pi extension still present: {name}")
        else:
            external.append(f"EXTERNAL Pi extension: {name}")


def _check_codex(home: Path, findings: list[str], external: list[str]) -> object:
    """Verify Codex-managed state; returns the live MCP mapping."""
    _compare_text(
        expected_codex_rules_md(),
        home / ".codex/AGENTS.md",
        "Codex rules",
        findings,
    )
    config_path = home / ".codex/config.toml"
    _check_private_mode(config_path, "Codex configuration", findings)
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
    _check_agents("codex", home / ".codex/agents", findings, external)
    return parsed.get("mcp_servers", {})


def drift(home: Path, vendors: Iterable[str], *, verify_plugins: bool = True) -> int:
    findings: list[str] = []
    external: list[str] = []
    selected = tuple(vendors)
    data = home / DATA_REL
    if selected:
        for name, fragment in _canonical_shell_fragments().items():
            _compare(fragment, data / "shell" / name, f"shell fragment {name}", findings)
    if {"claude", "codex"} & set(selected):
        hooks = _canonical_hooks()
        for name, hook in hooks.items():
            _compare(hook, data / "hooks" / name, f"hook {name}", findings)
        hook_root = data / "hooks"
        if hook_root.exists():
            for deployed in hook_root.iterdir():
                # sync keeps one .bak beside a replaced hook; that backup is not drift.
                if deployed.suffix == ".bak":
                    continue
                if deployed.is_file() and deployed.name not in hooks:
                    findings.append(f"DRIFT retired runtime hook still present: {deployed.name}")

    for vendor in selected:
        if vendor == "pi":
            _check_pi(home, findings, external)
            _check_skills(home / ".agents/skills", vendor, findings, external)
            _check_pi_native_skills(home / ".pi/agent/skills", findings, external)
            continue
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

    # NOTE lines record skipped verification, not external additions; keep
    # them out of the external count so the summary line stays honest.
    notes = [message for message in external if message.startswith("NOTE ")]
    external = [message for message in external if not message.startswith("NOTE ")]
    for message in findings:
        print(message)
    for message in external:
        print(message)
    for message in notes:
        print(message)
    suffix = f"; {len(notes)} note(s)" if notes else ""
    if findings:
        print(f"\n{len(findings)} managed drift item(s); {len(external)} external item(s){suffix}")
        return 1
    print(f"OK managed configuration matches workbench; {len(external)} external item(s){suffix}")
    return 0
