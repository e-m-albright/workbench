"""Compare live vendor configuration directly with canonical Workbench sources."""

from __future__ import annotations

import hashlib
import re
import shutil
import tomllib
from collections.abc import Iterable
from pathlib import Path

from workbench.codex import expected_codex_rules_md, merge_codex_config, merge_codex_rules
from workbench.core import (
    AGENTS,
    DATA_REL,
    RETIRED_AGENT_SHELL_FILES,
    RETIRED_PI_EXTENSIONS,
    RETIRED_PI_PROVIDERS,
    RETIRED_PI_SANDBOX_PROFILES,
    RETIRED_PI_SETTINGS,
    RETIRED_PI_STATE_PATHS,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
    ROOT,
    WorkbenchError,
    _list_plugins,
    _settings,
    _string_array,
    ensure_hard_deny_policy,
    ensure_private_path_policy,
)
from workbench.mcp import active_mcp, merge_mcp, retired_mcp_names
from workbench.native_config import _check_source, render_harness
from workbench.preview import preview_sync
from workbench.profiles import WORK_PI, WORK_PI_EXTENSIONS, Profile
from workbench.sync import (
    _canonical_hooks,
    _canonical_shell_fragments,
    _canonical_skills,
    merge_claude_settings,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare(source: Path, destination: Path, label: str, findings: list[str]) -> None:
    if not destination.exists():
        findings.append(f"DRIFT {label}: missing {destination}")
    elif _digest(source) != _digest(destination):
        source_label = source.relative_to(ROOT) if source.is_relative_to(ROOT) else source
        findings.append(f"DRIFT {label}: differs from {source_label}")


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


def _check_skills(
    skill_root: Path,
    vendor: str,
    findings: list[str],
    external: list[str],
    *,
    profile: Profile = "personal",
) -> None:
    canonical = _canonical_skills(profile)
    managed_names = set(canonical)
    personal_names = set(_canonical_skills("personal")) if profile == "work" else set()
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
    for name in deployed.keys() - managed_names:
        if name in RETIRED_SKILLS:
            findings.append(f"DRIFT retired {vendor} skill still present: {name}")
        elif name in personal_names:
            findings.append(f"DRIFT personal {vendor} skill present in work profile: {name}")
        else:
            external.append(f"EXTERNAL {vendor} skill: {name}")


def _check_pi_native_skills(
    skill_root: Path, findings: list[str], external: list[str], profile: Profile = "personal"
) -> None:
    """Pi-native skills may be external, but shared copies are duplicate drift."""
    canonical = _canonical_skills(profile)
    personal_names = set(_canonical_skills("personal")) if profile == "work" else set()
    deployed = {path.parent.name for path in skill_root.glob("*/SKILL.md")}
    for name in sorted(deployed):
        if name in canonical:
            findings.append(f"DRIFT duplicate Pi skill shadows shared skill: {name}")
        elif name in RETIRED_SKILLS:
            findings.append(f"DRIFT retired pi skill still present: {name}")
        elif name in personal_names:
            findings.append(f"DRIFT personal pi skill present in work profile: {name}")
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


def _check_pi_packages(
    pi_home: Path, declared: list[str], findings: list[str], external: list[str]
) -> None:
    # Only canonical exact npm pins are checked; this verifies metadata, not package integrity.
    for source in declared:
        pin = re.fullmatch(
            r"npm:((?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*)"
            r"@(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)",
            source,
        )
        if pin is None:
            external.append(
                f"NOTE Pi package version unverified (requires an exact npm pin): {source}"
            )
            continue
        name, expected_version = pin.groups()
        manifest = pi_home / "npm/node_modules" / name / "package.json"
        label = f"DRIFT Pi package {name}"
        if not manifest.exists():
            findings.append(f"{label}: missing installed metadata {manifest}")
            continue
        try:
            installed = _settings(manifest)
        except (WorkbenchError, UnicodeError):
            findings.append(f"{label}: malformed installed metadata {manifest}")
            continue
        version = installed.get("version")
        if installed.get("name") != name or not isinstance(version, str) or not version:
            findings.append(f"{label}: malformed installed name/version metadata {manifest}")
        elif version != expected_version:
            findings.append(f"{label}: installed version {version}; expected {expected_version}")


def _check_claude(
    home: Path,
    data: Path,
    findings: list[str],
    external: list[str],
    profile: Profile = "personal",
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
    reconciled = merge_claude_settings(settings, data, profile)
    for key in settings.keys() | reconciled.keys():
        if settings.get(key) != reconciled.get(key):
            findings.append(f"DRIFT Claude settings.{key}")
    claude_root = home / ".claude.json"
    _check_private_mode(claude_root, "Claude root configuration", findings)
    if profile == "personal":
        desktop_path = home / "Library/Application Support/Claude/claude_desktop_config.json"
        _check_private_mode(desktop_path, "Claude Desktop configuration", findings)
        desktop = _settings(desktop_path)
        _check_mcp(
            desktop.get("mcpServers"),
            "desktop",
            "Claude Desktop MCP",
            findings,
            external,
        )
        desktop_defaults = _settings(AGENTS / "claude/desktop-preferences.json").get(
            "preferences", {}
        )
        live_preferences = desktop.get("preferences", {})
        if not isinstance(desktop_defaults, dict) or not isinstance(live_preferences, dict):
            findings.append("DRIFT Claude Desktop preferences is not an object")
        else:
            for key in desktop_defaults.keys() - live_preferences.keys():
                findings.append(f"DRIFT Claude Desktop preference missing: {key}")
    _check_agents("claude", home / ".claude/agents", findings, external)
    return _settings(claude_root).get("mcpServers", {})


def _check_pi(
    home: Path,
    findings: list[str],
    external: list[str],
    profile: Profile = "personal",
) -> None:
    pi_home = home / ".pi/agent"
    source = AGENTS / "pi" if profile == "personal" else WORK_PI
    if not shutil.which("pi"):
        findings.append("DRIFT Pi CLI is not installed or not on PATH")
    sessions = pi_home / "sessions"
    if sessions.is_symlink():
        findings.append(f"DRIFT Pi session path is a symlink: {sessions}")
    elif sessions.exists():
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
    if profile == "personal":
        _compare(
            AGENTS / "pi/inference-router.json",
            pi_home / "inference-router.json",
            "Pi inference router",
            findings,
        )
    elif (pi_home / "inference-router.json").exists():
        findings.append("DRIFT personal Pi inference router present in work profile")
    managed_settings = _settings(source / "settings.json")
    findings.extend(
        _managed_value_errors(
            _settings(pi_home / "settings.json"),
            managed_settings,
            "Pi settings",
        )
    )
    _check_pi_packages(pi_home, managed_settings.get("packages", []), findings, external)
    live_settings = _settings(pi_home / "settings.json")
    if profile == "work":
        personal_settings = _settings(AGENTS / "pi/settings.json")
        for name in sorted(personal_settings.keys() - _settings(source / "settings.json").keys()):
            if name in live_settings:
                findings.append(f"DRIFT personal Pi setting present in work profile: {name}")
    for name in sorted(RETIRED_PI_SETTINGS):
        if name in live_settings:
            findings.append(f"DRIFT retired Pi setting still present: {name}")
    for filename, nested_key in (("models.json", "providers"),):
        actual = _settings(pi_home / filename)
        expected = _settings(source / filename)
        if nested_key:
            actual = actual.get(nested_key, {})
            expected = expected.get(nested_key, {})
        findings.extend(_managed_value_errors(actual, expected, f"Pi {filename}"))
        if isinstance(actual, dict) and isinstance(expected, dict):
            personal_providers = (
                _settings(AGENTS / "pi/models.json").get("providers", {})
                if profile == "work" and filename == "models.json"
                else {}
            )
            for name in sorted(actual.keys() - expected.keys()):
                if filename == "models.json" and name in RETIRED_PI_PROVIDERS:
                    findings.append(f"DRIFT retired Pi provider still present: {name}")
                elif name in personal_providers:
                    findings.append(f"DRIFT personal Pi provider present in work profile: {name}")
                else:
                    external.append(f"EXTERNAL Pi {filename} entry: {name}")

    all_extensions = {path.name: path for path in (AGENTS / "pi/extensions").glob("*.ts")}
    expected_extensions = (
        all_extensions
        if profile == "personal"
        else {name: all_extensions[name] for name in WORK_PI_EXTENSIONS}
    )
    deployed_extensions = {path.name: path for path in (pi_home / "extensions").glob("*.ts")}
    for name, source in expected_extensions.items():
        _compare(source, pi_home / "extensions" / name, f"Pi extension {name}", findings)
    for name in sorted(deployed_extensions.keys() - expected_extensions.keys()):
        if name in RETIRED_PI_EXTENSIONS:
            findings.append(f"DRIFT retired pi extension still present: {name}")
        elif profile == "work" and name in all_extensions:
            findings.append(f"DRIFT personal Pi extension present in work profile: {name}")
        else:
            external.append(f"EXTERNAL Pi extension: {name}")

    expected_helpers = {path.name: path for path in (AGENTS / "pi/extensions/lib").glob("*.ts")}
    deployed_helpers = {path.name: path for path in (pi_home / "extensions/lib").glob("*.ts")}
    for name, source in expected_helpers.items():
        _compare(source, pi_home / "extensions/lib" / name, f"Pi extension helper {name}", findings)
    for name in sorted(deployed_helpers.keys() - expected_helpers.keys()):
        if f"lib/{name}" in RETIRED_PI_EXTENSIONS:
            findings.append(f"DRIFT retired Pi extension helper still present: {name}")
        else:
            external.append(f"EXTERNAL Pi extension helper: {name}")
    for agent in sorted((AGENTS / "pi/agents").glob("*.md")):
        _compare(agent, pi_home / "agents" / agent.name, f"Pi agent {agent.name}", findings)


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


def _check_mcp(
    actual: object,
    target: str,
    label: str,
    findings: list[str],
    external: list[str],
    *,
    include_active: bool = True,
) -> None:
    if not isinstance(actual, dict):
        findings.append(f"DRIFT {label} configuration is not an object")
        actual = {}
    merged = merge_mcp(actual, target, include_active=include_active)
    for name, value in merged.items():
        if actual.get(name) != value:
            findings.append(f"DRIFT {label} {name}")
    for name in actual.keys() - merged.keys():
        reason = "retired" if name in retired_mcp_names() else "untargeted"
        findings.append(f"DRIFT {reason} {label} still present: {name}")
    desired = active_mcp(target) if include_active else {}
    for name in actual.keys() & merged.keys() - desired.keys():
        external.append(f"EXTERNAL {label}: {name}")


def _check_harness(home: Path, vendor: str, findings: list[str]) -> None:
    """Verify the same derived configuration that sync renders, without repair."""
    home = home.resolve()
    path = home / DATA_REL / "native/harness/manifest.json"
    try:
        _check_source(path, home)
        actual = _settings(path)
        shell_finding = "DRIFT shell projection manifest"
        if (
            actual.get("shell") != {"links": [], "files": [], "read": []}
            and shell_finding not in findings
        ):
            findings.append(shell_finding)
        expected = render_harness(home, vendor)
        if actual.get(vendor) != expected.manifest:
            findings.append(f"DRIFT {vendor} projection manifest")
        for source, content in expected.contents.items():
            _check_source(source, home)
            _compare_text(
                content, source, f"{vendor} projection {source.relative_to(home)}", findings
            )
    except (OSError, ValueError, WorkbenchError) as exc:
        findings.append(f"DRIFT {vendor} projection cannot be verified: {exc}")


def drift(
    home: Path,
    vendors: Iterable[str],
    *,
    verify_plugins: bool = True,
    profile: Profile = "personal",
) -> int:
    findings: list[str] = []
    external: list[str] = []
    selected = tuple(vendors)
    data = home / DATA_REL
    if selected:
        for name, fragment in _canonical_shell_fragments().items():
            _compare(fragment, data / "shell" / name, f"shell fragment {name}", findings)
        for name in RETIRED_AGENT_SHELL_FILES:
            if (data / "shell" / name).exists():
                findings.append(f"DRIFT retired agent bridge still present: {name}")
        for name in RETIRED_PI_SANDBOX_PROFILES:
            if (data / "sandbox" / name).exists():
                findings.append(f"DRIFT retired Pi sandbox profile still present: {name}")
    if selected:
        hard_deny = home / ".config/workbench/hard-deny-paths"
        if not hard_deny.is_file():
            findings.append(f"DRIFT invariant agent denylist is missing: {hard_deny}")
        _check_private_mode(hard_deny, "Invariant agent denylist", findings)
        for filename, ensure in (
            ("hard-deny-paths", ensure_hard_deny_policy),
            ("private-paths", ensure_private_path_policy),
        ):
            path = home / ".config/workbench" / filename
            if path.is_symlink():
                findings.append(f"DRIFT {filename}: policy must not be a symlink")
                continue
            with preview_sync() as plan:
                ensure(path)
            if path in plan.files:
                findings.append(f"DRIFT {filename}: missing or obsolete required exclusions")
            _check_private_mode(path, f"Agent {filename}", findings)
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
        _check_harness(home, vendor, findings)
        if vendor == "pi":
            for relative in RETIRED_PI_STATE_PATHS:
                path = home / relative
                if path.exists() or path.is_symlink():
                    findings.append(f"DRIFT retired Pi state still present: {path}")
            _check_pi(home, findings, external, profile)
            _check_skills(
                home / ".agents/skills",
                vendor,
                findings,
                external,
                profile=profile,
            )
            _check_pi_native_skills(home / ".pi/agent/skills", findings, external, profile)
            continue
        if vendor == "claude":
            mcp = _check_claude(home, data, findings, external, profile)
            skill_root = home / ".claude/skills"
        else:
            mcp = _check_codex(home, findings, external)
            skill_root = home / ".agents/skills"

        _check_mcp(
            mcp,
            vendor,
            f"{vendor} MCP",
            findings,
            external,
            include_active=profile == "personal",
        )

        _check_skills(skill_root, vendor, findings, external, profile=profile)
        if verify_plugins and profile == "personal":
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
