"""Deploy Workbench-managed configuration into Claude Code and Codex."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from workbench.codex import (
    _render_codex_subagent,
    expected_codex_rules_md,
    merge_codex_config,
    merge_codex_rules,
)
from workbench.core import (
    AGENTS,
    CLAUDE_SANDBOX,
    DATA_REL,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
    SKILLS_CLI,
    WorkbenchError,
    _home_env,
    _list_plugins,
    _settings,
    _string_array,
    copy_file,
    write_json,
    write_text,
)
from workbench.mcp import _desktop_mcp, merge_mcp, retired_mcp_names


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
    """Hook name -> source path, shared by sync (writer) and drift (verifier)."""
    return {hook.name: hook for hook in sorted((AGENTS / "shared/hooks").glob("*.sh"))}


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
    skill_names = sorted(path.parent.name for path in (AGENTS / "skills").glob("*/SKILL.md"))
    if not shutil.which("npx"):
        raise WorkbenchError("npx is required to deploy skills")
    env = _home_env(home)
    # The npx skills CLI names the claude agent "claude-code"; that external id
    # stays at this subprocess boundary — everything else speaks "claude".
    agent_id = "claude-code" if vendor == "claude" else vendor
    # Remove the full current set too (not just retirements) so a renamed or
    # relocated skill can't leave a stale copy behind from a prior deploy.
    removals = sorted(set(skill_names) | set(RETIRED_SKILLS))
    if removals:
        subprocess.run(
            ["npx", SKILLS_CLI, "remove", *removals, "-a", agent_id, "-g", "-y"],
            check=False,
            env=env,
        )
    subprocess.run(
        [
            "npx",
            SKILLS_CLI,
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

    Single source for `sync` (the writer) and `drift` (the verifier) so the
    two commands can never diverge on what "managed" means.
    """
    plugins = _string_array(AGENTS / "claude/plugins.json")
    return {
        "enabledPlugins": dict.fromkeys(plugins, True),
        "permissions": _settings(AGENTS / "claude/permissions.json"),
        "hooks": _settings(AGENTS / "shared/hooks.json").get("hooks", {}),
        "statusLine": {
            "type": "command",
            "command": str(data / "claude/statusline.sh"),
        },
        "voiceEnabled": True,
        "preferredNotifChannel": "auto",
        "defaultMode": "auto",
        "autoMemoryEnabled": False,
        "sandbox": CLAUDE_SANDBOX,
    }


def sync_claude(home: Path, *, deploy_skills: bool, deploy_plugins: bool = False) -> None:
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


def _sync_claude_desktop(home: Path) -> None:
    path = home / "Library/Application Support/Claude/claude_desktop_config.json"
    settings = _settings(path)
    live_mcp = settings.get("mcpServers", {})
    if not isinstance(live_mcp, dict):
        live_mcp = {}
    kept = {name: value for name, value in live_mcp.items() if name not in retired_mcp_names()}
    settings["mcpServers"] = {**kept, **_desktop_mcp()}

    source = _settings(AGENTS / "claude/desktop-preferences.json")
    defaults = source.get("preferences", {})
    existing = settings.get("preferences", {})
    if not isinstance(defaults, dict) or not isinstance(existing, dict):
        raise WorkbenchError("Claude Desktop preferences must be JSON objects")
    settings["preferences"] = {**defaults, **existing}
    write_json(path, settings)


def sync_codex(home: Path, *, deploy_skills: bool, deploy_plugins: bool = False) -> None:
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


def _replace_pi_file(source: Path, destination: Path) -> None:
    """Deploy a real file so a broken repository symlink cannot disable Pi."""
    if destination.is_symlink():
        destination.unlink()
    copy_file(source, destination)


def _merge_pi_object(source: Path, destination: Path, *, nested_key: str | None = None) -> None:
    desired = _settings(source)
    existing = _settings(destination)
    if nested_key:
        desired_nested = desired.get(nested_key, {})
        existing_nested = existing.get(nested_key, {})
        if not isinstance(desired_nested, dict) or not isinstance(existing_nested, dict):
            raise WorkbenchError(f"Pi {nested_key} must be JSON objects")
        desired = {**existing, **desired, nested_key: {**existing_nested, **desired_nested}}
    else:
        desired = {**existing, **desired}
    if destination.is_symlink():
        destination.unlink()
    write_json(destination, desired)


def _sync_pi_skills(home: Path) -> None:
    destination = home / ".pi/agent/skills"
    destination.mkdir(parents=True, exist_ok=True)
    canonical = {path.parent.name: path.parent for path in (AGENTS / "skills").glob("*/SKILL.md")}
    for name in sorted(set(canonical) | set(RETIRED_SKILLS)):
        deployed = destination / name
        if deployed.is_symlink() or deployed.is_file():
            deployed.unlink()
        elif deployed.exists():
            shutil.rmtree(deployed)
    for name, source in canonical.items():
        shutil.copytree(source, destination / name)


def _harden_pi_session_permissions(destination: Path) -> None:
    """Keep persisted conversations private without inspecting or owning them."""
    sessions = destination / "sessions"
    if not sessions.exists():
        return
    sessions.chmod(0o700)
    for path in sessions.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)


def sync_pi(home: Path, *, deploy_skills: bool, deploy_plugins: bool = False) -> None:
    """Deploy Pi's transparent local configuration; packages remain settings-owned."""
    del deploy_plugins  # Pi packages are declared in settings.json, not a separate plugin registry.
    source = AGENTS / "pi"
    destination = home / ".pi/agent"
    _harden_pi_session_permissions(destination)
    _replace_pi_file(AGENTS / "shared/rules.md", destination / "AGENTS.md")
    _merge_pi_object(source / "settings.json", destination / "settings.json")
    _merge_pi_object(source / "models.json", destination / "models.json", nested_key="providers")
    _merge_pi_object(source / "presets.json", destination / "presets.json")
    _replace_pi_file(source / "permission-policy.json", destination / "permission-policy.json")
    for extension in sorted((source / "extensions").glob("*.ts")):
        _replace_pi_file(extension, destination / "extensions" / extension.name)
    if deploy_skills:
        _sync_pi_skills(home)
