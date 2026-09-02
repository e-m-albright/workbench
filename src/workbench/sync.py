"""Deploy Workbench-managed configuration into Claude Code and Codex."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from workbench.codex import expected_codex_rules_md, merge_codex_config, merge_codex_rules
from workbench.core import (
    AGENTS,
    CLAUDE_SANDBOX,
    DATA_REL,
    RETIRED_PI_EXTENSIONS,
    RETIRED_PI_PROVIDERS,
    RETIRED_PI_STATE_PATHS,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
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
            # Codex has no enable subcommand; a disabled codex plugin stays a
            # drift finding the owner resolves in the vendor UI.
            if not installed[plugin] and vendor == "claude":
                subprocess.run(
                    [vendor, "plugin", "enable", plugin], check=True, env=_home_env(home)
                )
            continue
        command = [vendor, "plugin", "install", plugin, "--scope", "user"]
        if vendor == "codex":
            command = [vendor, "plugin", "add", plugin, "--json"]
        subprocess.run(command, check=True, env=_home_env(home))


def _canonical_hooks() -> dict[str, Path]:
    """Hook name -> source path, shared by sync (writer) and drift (verifier)."""
    return {hook.name: hook for hook in sorted((AGENTS / "shared/hooks").glob("*.sh"))}


def _canonical_shell_fragments() -> dict[str, Path]:
    """Shell fragments (agent launchers) sourced by the dotfiles zshrc."""
    return {f.name: f for f in sorted((AGENTS / "shared/shell").glob("*.zsh"))}


def _canonical_skills() -> dict[str, Path]:
    """Skill name -> canonical source tree, shared by sync and drift."""
    return {path.parent.name: path.parent for path in (AGENTS / "skills").glob("*/SKILL.md")}


def _install_runtime_files(home: Path) -> Path:
    data = home / DATA_REL
    for name, fragment in _canonical_shell_fragments().items():
        copy_file(fragment, data / "shell" / name)
    hooks = _canonical_hooks()
    hook_dir = data / "hooks"
    if hook_dir.exists():
        for deployed in hook_dir.iterdir():
            # Keep the one .bak beside a replaced *current* hook — drift skips
            # it and README promises it survives. A retired hook's backup goes
            # with the hook.
            if deployed.suffix == ".bak" and deployed.name.removesuffix(".bak") in hooks:
                continue
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


def _tree_files(root: Path) -> dict[Path, bytes]:
    if not root.is_dir() or root.is_symlink():
        return {}
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _replace_tree(source: Path, destination: Path) -> None:
    """Stage one local tree, then swap it into place without a network gap."""
    if _tree_files(source) == _tree_files(destination):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(destination.name + ".tmp")
    backup = destination.with_name(destination.name + ".bak")
    _remove_deployed_path(staged)
    _remove_deployed_path(backup)
    shutil.copytree(source, staged)
    if destination.exists() or destination.is_symlink():
        destination.replace(backup)
    try:
        staged.replace(destination)
    except OSError:
        if backup.exists() or backup.is_symlink():
            backup.replace(destination)
        raise
    _remove_deployed_path(backup)


def _sync_skill_tree(root: Path) -> None:
    for name in RETIRED_SKILLS:
        _remove_deployed_path(root / name)
    for name, source in _canonical_skills().items():
        _replace_tree(source, root / name)


def _sync_skills(vendor: str, home: Path) -> None:
    if vendor not in {"claude", "codex"}:
        raise WorkbenchError(f"unsupported skill target: {vendor}")
    root = home / (".claude/skills" if vendor == "claude" else ".agents/skills")
    _sync_skill_tree(root)


def _remove_retired_subagents(destination: Path) -> None:
    for name in RETIRED_SUBAGENTS:
        for suffix in (".md", ".md.bak", ".toml", ".toml.bak"):
            _remove_deployed_path(destination / f"{name}{suffix}")


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
        # Built-in style (Claude Code >= 2.1.237): lead with the result, skip
        # preamble. Pairs with the plain-English rule in shared/rules.md to
        # counter the Fable/Opus jargon drift.
        "outputStyle": "Concise",
        "sandbox": CLAUDE_SANDBOX,
    }


def sync_claude(home: Path, *, deploy_skills: bool, deploy_plugins: bool) -> None:
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
    write_json(claude_root, root_settings, mode=0o600)

    _sync_claude_desktop(home)
    _remove_retired_subagents(claude_home / "agents")
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
    write_json(path, settings, mode=0o600)


def sync_codex(home: Path, *, deploy_skills: bool, deploy_plugins: bool) -> None:
    _install_runtime_files(home)
    codex_home = home / ".codex"
    write_text(codex_home / "AGENTS.md", expected_codex_rules_md())

    live_rules = codex_home / "rules/default.rules"
    source_rules = AGENTS / "codex/default.rules"
    existing_rules = live_rules.read_text() if live_rules.exists() else ""
    write_text(live_rules, merge_codex_rules(source_rules.read_text(), existing_rules))

    config = codex_home / "config.toml"
    existing = config.read_text() if config.exists() else ""
    write_text(config, merge_codex_config(existing), mode=0o600)
    for profile in sorted((AGENTS / "codex/profiles").glob("*.toml")):
        copy_file(profile, codex_home / f"{profile.stem}.config.toml")
    if copy_file(AGENTS / "shared/hooks.json", codex_home / "hooks.json"):
        # Codex records trust against each hook's hash, so a changed hooks.json
        # is skipped until re-trusted — drift's byte comparison cannot see that.
        print("NOTE codex hooks changed; run /hooks in Codex to re-trust them")
    _remove_retired_subagents(codex_home / "agents")
    if deploy_skills:
        _sync_skills("codex", home)
    if deploy_plugins:
        _sync_plugins("codex", home)


def _replace_pi_file(source: Path, destination: Path) -> None:
    """Deploy a real file so a broken repository symlink cannot disable Pi."""
    if destination.is_symlink():
        destination.unlink()
    copy_file(source, destination)


def sync_rules(home: Path, vendor: str) -> None:
    """Deploy only global instructions without reconciling unrelated configuration."""
    source = AGENTS / "shared/rules.md"
    if vendor == "claude":
        copy_file(source, home / ".claude/CLAUDE.md")
    elif vendor == "codex":
        write_text(home / ".codex/AGENTS.md", expected_codex_rules_md())
    elif vendor == "pi":
        _replace_pi_file(source, home / ".pi/agent/AGENTS.md")
    else:
        raise WorkbenchError(f"unsupported vendor for rules sync: {vendor}")


def _merge_pi_object(
    source: Path,
    destination: Path,
    *,
    nested_key: str | None = None,
    retired_nested_keys: set[str] | None = None,
) -> None:
    desired = _settings(source)
    existing = _settings(destination)
    if nested_key:
        desired_nested = desired.get(nested_key, {})
        existing_nested = existing.get(nested_key, {})
        if not isinstance(desired_nested, dict) or not isinstance(existing_nested, dict):
            raise WorkbenchError(f"Pi {nested_key} must be JSON objects")
        retained = {
            key: value
            for key, value in existing_nested.items()
            if key not in (retired_nested_keys or set())
        }
        desired = {**existing, **desired, nested_key: {**retained, **desired_nested}}
    else:
        desired = {**existing, **desired}
    if destination.is_symlink():
        destination.unlink()
    write_json(destination, desired)


def _remove_deployed_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _sync_pi_skills(home: Path) -> None:
    """Deploy shared skills once where Pi and Codex both discover them."""
    canonical = _canonical_skills()
    _sync_skill_tree(home / ".agents/skills")
    for name in sorted(set(canonical) | set(RETIRED_SKILLS)):
        # Older Workbench versions copied shared skills here too. Pi discovers
        # both roots, so retaining those copies produces a collision warning.
        _remove_deployed_path(home / ".pi/agent/skills" / name)


def _harden_pi_session_permissions(destination: Path) -> None:
    """Keep persisted conversations private without inspecting or owning them."""
    sessions = destination / "sessions"
    if not sessions.exists():
        return
    sessions.chmod(0o700)
    for path in sessions.rglob("*"):
        path.chmod(0o700 if path.is_dir() else 0o600)


def sync_pi(home: Path, *, deploy_skills: bool, deploy_plugins: bool) -> None:
    """Deploy Pi's transparent local configuration; packages remain settings-owned."""
    del deploy_plugins  # Pi packages are declared in settings.json, not a separate plugin registry.
    for name, fragment in _canonical_shell_fragments().items():
        copy_file(fragment, home / DATA_REL / "shell" / name)
    source = AGENTS / "pi"
    destination = home / ".pi/agent"
    _harden_pi_session_permissions(destination)
    for path in RETIRED_PI_STATE_PATHS:
        _remove_deployed_path(home / path)
    _replace_pi_file(AGENTS / "shared/rules.md", destination / "AGENTS.md")
    _merge_pi_object(source / "settings.json", destination / "settings.json")
    _merge_pi_object(
        source / "models.json",
        destination / "models.json",
        nested_key="providers",
        retired_nested_keys=set(RETIRED_PI_PROVIDERS),
    )
    _merge_pi_object(source / "presets.json", destination / "presets.json")
    _replace_pi_file(source / "inference-router.json", destination / "inference-router.json")
    _replace_pi_file(source / "permission-policy.json", destination / "permission-policy.json")
    for name in RETIRED_PI_EXTENSIONS:
        _remove_deployed_path(destination / "extensions" / name)
    for extension in sorted((source / "extensions").glob("*.ts")):
        _replace_pi_file(extension, destination / "extensions" / extension.name)
    # Helper modules live one level down: Pi loads every top-level extensions/*.ts
    # as an extension, and ignores a subdirectory with no index or manifest.
    for helper in sorted((source / "extensions/lib").glob("*.ts")):
        _replace_pi_file(helper, destination / "extensions/lib" / helper.name)
    if deploy_skills:
        _sync_pi_skills(home)
