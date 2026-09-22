"""Deploy Workbench-managed configuration into Claude Code and Codex."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

from workbench.codex import expected_codex_rules_md, merge_codex_config, merge_codex_rules
from workbench.core import (
    AGENTS,
    CLAUDE_SANDBOX,
    DATA_REL,
    RETIRED_AGENT_SHELL_FILES,
    RETIRED_PI_EXTENSIONS,
    RETIRED_PI_PRESETS,
    RETIRED_PI_PROVIDERS,
    RETIRED_PI_SANDBOX_PROFILES,
    RETIRED_PI_SETTINGS,
    RETIRED_PI_STATE_PATHS,
    RETIRED_SKILLS,
    RETIRED_SUBAGENTS,
    WorkbenchError,
    _home_env,
    _list_plugins,
    _settings,
    _string_array,
    copy_file,
    ensure_private_path_policy,
    write_json,
    write_text,
)
from workbench.external_skills import external_skill_source, external_skills
from workbench.mcp import merge_mcp
from workbench.native_config import install_harness
from workbench.profiles import WORK_PI, WORK_PI_EXTENSIONS, WORK_SKILL_EXCLUDES, Profile


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
    """Shared launcher runtime; dotfiles sources only agent-launchers.zsh."""
    return {
        path.name: path
        for path in sorted((AGENTS / "shared/shell").iterdir())
        if path.suffix in {".zsh", ".py", ".mjs"}
    }


def _retire_agent_runtime(home: Path) -> None:
    """Remove obsolete weaker boundaries while retaining owner recovery copies."""
    data = home / DATA_REL
    for directory, names in (
        ("sandbox", RETIRED_PI_SANDBOX_PROFILES),
        ("shell", RETIRED_AGENT_SHELL_FILES),
    ):
        for name in names:
            retired = data / directory / name
            if retired.exists():
                copy_file(retired, retired.with_name(name + ".bak"))
                _remove_deployed_path(retired)


def _canonical_skills(profile: Profile = "personal") -> dict[str, Path]:
    """Skill name -> canonical source tree, shared by sync and drift."""
    skills = {path.parent.name: path.parent for path in (AGENTS / "skills").glob("*/SKILL.md")}
    if profile == "work":
        return {name: path for name, path in skills.items() if name not in WORK_SKILL_EXCLUDES}
    return skills


def _install_runtime_files(home: Path, *, deploy_shell: bool = True) -> Path:
    data = home / DATA_REL
    if deploy_shell:
        for name, fragment in _canonical_shell_fragments().items():
            copy_file(fragment, data / "shell" / name)
        _retire_agent_runtime(home)
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


def _managed_skill_sources(home: Path, profile: Profile = "personal") -> dict[str, Path]:
    """Resolve profile-approved skill trees; external pins are personal-only."""
    sources = _canonical_skills(profile)
    if profile == "personal":
        for skill in external_skills():
            sources[skill.name] = external_skill_source(home, skill)
    return sources


def _sync_skill_tree(root: Path, home: Path, profile: Profile = "personal") -> None:
    managed = _managed_skill_sources(home, profile)
    removed = set(RETIRED_SKILLS)
    if profile == "work":
        removed |= set(_canonical_skills("personal")) - set(managed)
        removed |= {skill.name for skill in external_skills()}
    for name in removed:
        _remove_deployed_path(root / name)
    for name, source in managed.items():
        _replace_tree(source, root / name)


def _sync_skills(vendor: str, home: Path, profile: Profile = "personal") -> None:
    if vendor not in {"claude", "codex"}:
        raise WorkbenchError(f"unsupported skill target: {vendor}")
    root = home / (".claude/skills" if vendor == "claude" else ".agents/skills")
    _sync_skill_tree(root, home, profile)


def _remove_retired_subagents(destination: Path) -> None:
    for name in RETIRED_SUBAGENTS:
        for suffix in (".md", ".md.bak", ".toml", ".toml.bak"):
            _remove_deployed_path(destination / f"{name}{suffix}")


def merge_claude_settings(
    existing: dict[str, Any], data: Path, profile: Profile = "personal"
) -> dict[str, Any]:
    """Reconcile owned entries while retaining owner plugins and hook commands.

    Single source for `sync` (the writer) and `drift` (the verifier) so the
    two commands can never diverge on what "managed" means.
    """
    declared_plugins = _string_array(AGENTS / "claude/plugins.json")
    plugins = declared_plugins if profile == "personal" else []
    managed = {
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
    result = {**existing, **managed}
    retained_plugins = existing.get("enabledPlugins", {})
    retained_plugins = retained_plugins if isinstance(retained_plugins, dict) else {}
    result["enabledPlugins"] = {
        **{key: value for key, value in retained_plugins.items() if key not in declared_plugins},
        **managed["enabledPlugins"],
    }
    retained_permissions = existing.get("permissions", {})
    result["permissions"] = {
        **(retained_permissions if isinstance(retained_permissions, dict) else {}),
        **managed["permissions"],
    }
    result["permissions"].pop("defaultMode", None)

    hooks = {}
    existing_hooks = existing.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        raise WorkbenchError("Claude hooks must be an object")
    for event, groups in existing_hooks.items():
        if not isinstance(groups, list):
            raise WorkbenchError(f"Claude hook event {event} must contain a list")
        kept = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise WorkbenchError(f"Claude hook event {event} has an invalid group")
            if any(
                not isinstance(hook, dict)
                or (hook.get("type") == "command" and not isinstance(hook.get("command"), str))
                for hook in group["hooks"]
            ):
                raise WorkbenchError(f"Claude hook event {event} has an invalid hook")
            commands = [
                hook
                for hook in group.get("hooks", [])
                if not (
                    hook.get("type") == "command"
                    and hook.get("command", "").startswith(
                        "bash $HOME/.local/share/workbench/hooks/"
                    )
                )
            ]
            if commands:
                kept.append({**group, "hooks": commands})
        if kept:
            hooks[event] = kept
    for event, groups in managed["hooks"].items():
        hooks.setdefault(event, []).extend(groups)
    result["hooks"] = hooks
    return result


def sync_claude(
    home: Path,
    *,
    deploy_skills: bool,
    deploy_plugins: bool,
    profile: Profile = "personal",
) -> None:
    data = _install_runtime_files(home, deploy_shell=profile == "personal")
    claude_home = home / ".claude"
    copy_file(AGENTS / "shared/rules.md", claude_home / "CLAUDE.md")

    settings_path = claude_home / "settings.json"
    settings = _settings(settings_path)
    write_json(settings_path, merge_claude_settings(settings, data, profile))

    claude_root = home / ".claude.json"
    root_settings = _settings(claude_root)
    live_mcp = root_settings.get("mcpServers", {})
    if not isinstance(live_mcp, dict):
        live_mcp = {}
    root_settings["mcpServers"] = merge_mcp(
        live_mcp, "claude", include_active=profile == "personal"
    )
    write_json(claude_root, root_settings, mode=0o600)

    if profile == "personal":
        _sync_claude_desktop(home)
    _remove_retired_subagents(claude_home / "agents")
    if deploy_skills:
        _sync_skills("claude", home, profile)
    if deploy_plugins and profile == "personal":
        _sync_plugins("claude", home)
    if profile == "personal":
        install_harness(home, "claude")


def _sync_claude_desktop(home: Path) -> None:
    path = home / "Library/Application Support/Claude/claude_desktop_config.json"
    settings = _settings(path)
    live_mcp = settings.get("mcpServers", {})
    if not isinstance(live_mcp, dict):
        live_mcp = {}
    settings["mcpServers"] = merge_mcp(live_mcp, "desktop")

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
    install_harness(home, "codex")


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
    retired_keys: set[str] | None = None,
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
        retained = {
            key: value for key, value in existing.items() if key not in (retired_keys or set())
        }
        desired = {**retained, **desired}
    if destination.is_symlink():
        destination.unlink()
    write_json(destination, desired)


def _remove_deployed_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _sync_pi_skills(home: Path, profile: Profile = "personal") -> None:
    """Deploy shared skills once where Pi and Codex both discover them."""
    managed_names = set(_canonical_skills(profile))
    if profile == "personal":
        managed_names |= {skill.name for skill in external_skills()}
    _sync_skill_tree(home / ".agents/skills", home, profile)
    cleanup_names = managed_names | set(RETIRED_SKILLS)
    if profile == "work":
        cleanup_names |= set(_canonical_skills("personal"))
    for name in sorted(cleanup_names):
        # Older Workbench versions copied shared skills here too. Pi discovers
        # both roots, so retaining those copies produces a collision warning.
        _remove_deployed_path(home / ".pi/agent/skills" / name)


def _harden_pi_session_permissions(destination: Path) -> None:
    """Keep persisted conversations private without inspecting or owning them."""
    sessions = destination / "sessions"
    if not sessions.exists() and not sessions.is_symlink():
        return

    def harden(descriptor: int) -> None:
        metadata = os.fstat(descriptor)
        directory = stat.S_ISDIR(metadata.st_mode)
        if not directory and not stat.S_ISREG(metadata.st_mode):
            raise WorkbenchError("Pi session paths must be regular files or directories")
        os.fchmod(descriptor, 0o700 if directory else 0o600)
        if directory:
            for name in os.listdir(descriptor):
                child = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
                )
                try:
                    harden(child)
                finally:
                    os.close(child)

    # Descriptor-relative traversal never follows a replaced root or nested symlink.
    try:
        root = os.open(sessions, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            harden(root)
        finally:
            os.close(root)
    except OSError as exc:
        raise WorkbenchError(f"Cannot safely harden Pi session paths: {sessions}: {exc}") from exc


def sync_pi(
    home: Path,
    *,
    deploy_skills: bool,
    deploy_plugins: bool,
    profile: Profile = "personal",
) -> None:
    """Deploy Pi's transparent local configuration; packages remain settings-owned."""
    del deploy_plugins  # Pi packages are declared in settings.json, not a separate plugin registry.
    if profile == "personal":
        for name, fragment in _canonical_shell_fragments().items():
            copy_file(fragment, home / DATA_REL / "shell" / name)
        _retire_agent_runtime(home)
        ensure_private_path_policy(home / ".config/workbench/private-paths")
    source = AGENTS / "pi" if profile == "personal" else WORK_PI
    destination = home / ".pi/agent"
    _harden_pi_session_permissions(destination)
    for path in RETIRED_PI_STATE_PATHS:
        _remove_deployed_path(home / path)
    _replace_pi_file(AGENTS / "shared/rules.md", destination / "AGENTS.md")
    retired_settings = set(RETIRED_PI_SETTINGS)
    if profile == "work":
        retired_settings |= set(_settings(AGENTS / "pi/settings.json")) - set(
            _settings(WORK_PI / "settings.json")
        )
    _merge_pi_object(
        source / "settings.json",
        destination / "settings.json",
        retired_keys=retired_settings,
    )
    _merge_pi_object(
        source / "models.json",
        destination / "models.json",
        nested_key="providers",
        retired_nested_keys=set(RETIRED_PI_PROVIDERS)
        | (
            set(_settings(AGENTS / "pi/models.json").get("providers", {}))
            if profile == "work"
            else set()
        ),
    )
    _merge_pi_object(
        source / "presets.json",
        destination / "presets.json",
        retired_keys=set(RETIRED_PI_PRESETS),
    )
    if profile == "personal":
        _replace_pi_file(source / "inference-router.json", destination / "inference-router.json")
    else:
        _remove_deployed_path(destination / "inference-router.json")
    _replace_pi_file(AGENTS / "pi/permission-policy.json", destination / "permission-policy.json")
    for name in RETIRED_PI_EXTENSIONS:
        retired = destination / "extensions" / name
        _remove_deployed_path(retired)
        _remove_deployed_path(retired.with_name(f"{retired.name}.bak"))
    extensions = {path.name: path for path in (AGENTS / "pi/extensions").glob("*.ts")}
    selected_extensions = set(extensions) if profile == "personal" else WORK_PI_EXTENSIONS
    if profile == "work":
        for name in set(extensions) - selected_extensions:
            _remove_deployed_path(destination / "extensions" / name)
    for name in sorted(selected_extensions):
        _replace_pi_file(extensions[name], destination / "extensions" / name)
    # Helper modules live one level down: Pi loads every top-level extensions/*.ts
    # as an extension, and ignores a subdirectory with no index or manifest.
    for helper in sorted((AGENTS / "pi/extensions/lib").glob("*.ts")):
        _replace_pi_file(helper, destination / "extensions/lib" / helper.name)
    if deploy_skills:
        _sync_pi_skills(home, profile)
    if profile == "personal":
        install_harness(home, "pi")
