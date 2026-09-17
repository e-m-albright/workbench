"""Derive restricted preferences and code assets from the installed harness."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

from workbench.codex import _toml_value
from workbench.core import write_json, write_text

PI_KEYS = {
    "defaultProvider",
    "defaultModel",
    "defaultThinkingLevel",
    "doubleEscapeAction",
    "treeFilterMode",
    "tuiMode",
    "defaultPreset",
    "theme",
    "quietStartup",
    "collapseChangelog",
    "hideThinkingBlock",
    "showHardwareCursor",
    "editorPaddingX",
    "autocompleteMaxVisible",
    "steeringMode",
    "followUpMode",
    "transport",
    "enabledModels",
}
CLAUDE_KEYS = {
    "model",
    "outputStyle",
    "effortLevel",
    "autoUpdatesChannel",
    "autoMemoryEnabled",
    "skipWorkflowUsageWarning",
    "preferredNotifChannel",
    "agentPushNotifEnabled",
    "skipAutoPermissionPrompt",
    "voiceEnabled",
    "defaultMode",
    "language",
    "theme",
    "showTurnDuration",
    "spinnerTipsEnabled",
    "terminalProgressBarEnabled",
    "alwaysThinkingEnabled",
}
CODEX_KEYS = {
    "model",
    "model_reasoning_effort",
    "model_reasoning_summary",
    "model_verbosity",
    "service_tier",
    "personality",
    "project_doc_fallback_filenames",
    "project_doc_max_bytes",
    "approval_policy",
    "approvals_reviewer",
    "sandbox_mode",
}
TUI_KEYS = {
    "theme",
    "status_line",
    "notifications",
    "notification_method",
    "notification_condition",
    "status_line_use_colors",
    "terminal_title",
    "model_availability_nux",
}
HOOK_NAMES = ("guard-sensitive-file.sh", "guard-destructive-shell.sh")
DATA = ".local/share/workbench"


def _check_source(path, home):
    if ".." in path.parts or not path.is_relative_to(home):
        raise ValueError("Harness assets must be installed below the host home")
    for part in (path, *path.parents):
        if part == home:
            break
        if part.is_symlink():
            raise ValueError(f"Harness asset must not traverse a symlink: {path}")


def _json(path, home):
    _check_source(path, home)
    value = json.loads(path.read_text()) if path.is_file() else {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a configuration object: {path}")
    return value


def _toml(path, home):
    _check_source(path, home)
    return tomllib.loads(path.read_text()) if path.is_file() else {}


def _select(value, keys):
    return {key: item for key, item in value.items() if key in keys}


def _marketplace_sources(p, manifest, root, enabled):
    # Vendor discovery validates source directories even for cached installations.
    for item in _json(manifest, p.home).get("plugins", []):
        source = item.get("source")
        if item.get("name") not in enabled or not isinstance(source, str):
            continue
        relative = Path(source)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        path = root / relative
        if path.is_dir():
            p.grant(path)


class Projection:
    def __init__(self, home, vendor):
        self.home, self.vendor = home, vendor
        self.root = home / DATA / "native/harness"
        self.manifest = {"links": [], "files": [], "read": []}

    def grant(self, source):
        # Never turn an installed asset symlink into a grant on an unrelated tree.
        _check_source(source, self.home)
        value = str(source.resolve(strict=True))
        if value not in self.manifest["read"]:
            self.manifest["read"].append(value)

    def link(self, relative):
        source = self.home / relative
        if source.exists() or source.is_symlink():
            self.grant(source)
            self.manifest["links"].append({"path": relative, "target": str(source.resolve())})

    def file(self, relative, value, *, toml=False):
        source = self.root / self.vendor / relative
        _check_source(source, self.home)
        if toml:
            write_text(source, "".join(f"{k} = {_toml_value(v)}\n" for k, v in value.items()))
        else:
            write_json(source, value)
        self.manifest["files"].append({"path": relative, "source": str(source)})
        self.grant(source)


def _hooks(value):
    allowed = {f"bash $HOME/{DATA}/hooks/{name}" for name in HOOK_NAMES}
    result = {}
    for event, groups in value.get("hooks", {}).items():
        kept = []
        for group in groups:
            commands = [
                dict(hook)
                for hook in group.get("hooks", [])
                if hook.get("type") == "command"
                and hook.get("command") in allowed
                and set(hook) <= {"type", "command", "timeout"}
            ]
            if commands:
                kept.append({"matcher": group.get("matcher", ""), "hooks": commands})
        if kept:
            result[event] = kept
    return {"hooks": result}


def _hook_trust(home, config, original, projected):
    """Trust only unchanged guard records; their home is bound by the launcher."""
    result = {}
    for event, groups in projected["hooks"].items():
        original_groups = original.get("hooks", {}).get(event, [])
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
        for group_index, group in enumerate(groups):
            for hook_index, hook in enumerate(group["hooks"]):
                for old_group_index, old_group in enumerate(original_groups):
                    if old_group.get("matcher", "") != group.get("matcher", ""):
                        continue
                    for old_hook_index, old_hook in enumerate(old_group.get("hooks", [])):
                        if old_hook != hook:
                            continue
                        key = f"{home}/.codex/hooks.json:{snake}:{old_group_index}:{old_hook_index}"
                        value = config.get("hooks", {}).get("state", {}).get(key, {})
                        if isinstance(value.get("enabled"), bool) and re.fullmatch(
                            r"[a-fA-F0-9]{64}", value.get("trusted_hash", "")
                        ):
                            target = (
                                "__WORKBENCH_AGENT_HOME__/.codex/hooks.json:"
                                f"{snake}:{group_index}:{hook_index}"
                            )
                            result[target] = _select(value, {"enabled", "trusted_hash"})
    return result


def _models(p):
    store = _json(p.home / ".pi/agent/models-store.json", p.home)
    result = {}
    compat_keys = {
        "cacheControlFormat",
        "forceAdaptiveThinking",
        "requiresReasoningContentOnAssistantMessages",
        "sendSessionAffinityHeaders",
        "supportsAdditionalTools",
        "supportsDeveloperRole",
        "supportsMidConvoEffort",
        "supportsMidConvoSystemMessages",
        "supportsOpenAIGrammarTools",
        "supportsTemperature",
        "supportsToolSearch",
        "thinkingFormat",
    }
    for provider, value in store.items():
        models = []
        for model in value.get("models", []):
            endpoint = urlsplit(model.get("baseUrl", ""))
            if (
                endpoint.scheme != "https"
                or endpoint.username
                or endpoint.password
                or endpoint.query
                or endpoint.fragment
            ):
                continue
            entry = _select(
                model,
                {
                    "id",
                    "name",
                    "api",
                    "provider",
                    "baseUrl",
                    "reasoning",
                    "input",
                    "contextWindow",
                    "maxTokens",
                },
            )
            for key, keys in (
                ("cost", {"input", "output", "cacheRead", "cacheWrite"}),
                ("thinkingLevelMap", {"off", "minimal", "low", "medium", "high", "xhigh", "max"}),
                ("compat", compat_keys),
            ):
                if key in model:
                    entry[key] = _select(model[key], keys)
            models.append(entry)
        result[provider] = {
            **_select(value, {"checkedAt", "lastModified", "etag"}),
            "models": models,
        }
    if store:
        p.file(".pi/agent/models-store.json", result)


def _pi(p):
    _models(p)
    config = _json(p.home / ".pi/agent/settings.json", p.home)
    settings = _select(config, PI_KEYS)
    if isinstance(config.get("safeGit"), dict):
        settings["safeGit"] = _select(config["safeGit"], {"promptLevel", "enabledByDefault"})
    packages = [
        item
        for item in config.get("packages", [])
        if isinstance(item, str) and re.fullmatch(r"npm:[@a-zA-Z0-9_./+~-]+", item)
    ]
    if packages:
        settings["packages"] = packages
        for name in ("node_modules", "package.json", "package-lock.json"):
            p.link(f".pi/agent/npm/{name}")
    p.file(".pi/agent/settings.json", settings)
    for relative in (
        ".pi/agent/AGENTS.md",
        ".pi/agent/extensions",
        ".pi/agent/skills",
        ".pi/agent/prompts",
        ".pi/agent/themes",
        ".pi/agent/keybindings.json",
        ".agents/skills",
        ".pi/agent/permission-policy.json",
    ):
        p.link(relative)
    presets = _json(p.home / ".pi/agent/presets.json", p.home)
    p.file(
        ".pi/agent/presets.json",
        {
            name: _select(value, {"thinkingLevel", "tools", "instructions", "model", "provider"})
            for name, value in presets.items()
            if isinstance(value, dict)
        },
    )
    router = _json(p.home / ".pi/agent/inference-router.json", p.home)
    if router:
        p.file(
            ".pi/agent/inference-router.json",
            {
                key: _select(value, {"provider", "model"}) if isinstance(value, dict) else value
                for key, value in router.items()
                if key in {"defaultMode", "frontier", "private"}
            },
        )


def _claude(p):
    config = _json(p.home / ".claude/settings.json", p.home)
    settings = _select(config, CLAUDE_KEYS)
    if isinstance(config.get("permissions"), dict):
        settings["permissions"] = _select(config["permissions"], {"deny"})
    for key, keys in (("tui", TUI_KEYS), ("voice", {"enabled", "mode"})):
        if isinstance(config.get(key), dict):
            settings[key] = _select(config[key], keys)
    settings.update(_hooks(config))
    statusline = p.home / DATA / "claude/statusline.sh"
    if statusline.is_file():
        p.grant(statusline)
        settings["statusLine"] = {"type": "command", "command": str(statusline)}
    installed = _json(p.home / ".claude/plugins/installed_plugins.json", p.home)
    plugins = {}
    for name, records in installed.get("plugins", {}).items():
        if config.get("enabledPlugins", {}).get(name) is not True:
            continue
        kept = []
        for record in records:
            source = Path(record.get("installPath", ""))
            cache = p.home / ".claude/plugins/cache"
            if (
                record.get("scope") != "user"
                or not source.is_dir()
                or not source.resolve().is_relative_to(cache.resolve())
            ):
                continue
            p.grant(source)
            kept.append(
                _select(
                    record,
                    {
                        "scope",
                        "installPath",
                        "version",
                        "installedAt",
                        "lastUpdated",
                        "gitCommitSha",
                    },
                )
            )
        if kept:
            plugins[name] = kept
    settings["enabledPlugins"] = dict.fromkeys(plugins, True)
    p.file(
        ".claude/plugins/installed_plugins.json",
        {
            "version": installed.get("version", 2),
            "plugins": plugins,
        },
    )
    known = _json(p.home / ".claude/plugins/known_marketplaces.json", p.home)
    marketplaces = {}
    for name in {plugin.rsplit("@", 1)[-1] for plugin in plugins}:
        item = known.get(name, {})
        source = item.get("source", {})
        location = Path(item.get("installLocation", ""))
        manifest = location / ".claude-plugin/marketplace.json"
        if (
            source.get("source") == "github"
            and re.fullmatch(r"[\w.-]+/[\w.-]+", source.get("repo", ""))
            and location.is_relative_to(p.home / ".claude/plugins")
            and manifest.is_file()
        ):
            p.grant(manifest)
            enabled = {plugin.split("@", 1)[0] for plugin in plugins if plugin.endswith(f"@{name}")}
            _marketplace_sources(p, manifest, location, enabled)
            marketplaces[name] = {
                "source": _select(source, {"source", "repo"}),
                "installLocation": str(location),
            }
    p.file(".claude/plugins/known_marketplaces.json", marketplaces)
    p.file(".claude/settings.json", settings)
    for relative in (
        ".claude/CLAUDE.md",
        ".claude/skills",
        ".claude/commands",
        ".claude/agents",
    ):
        p.link(relative)


def _codex(p):
    path = p.home / ".codex/config.toml"
    config = _toml(path, p.home)
    settings = _select(config, CODEX_KEYS)
    # Feature toggles are booleans, never environment values or connector grants.
    settings["features"] = {
        key: value
        for key, value in config.get("features", {}).items()
        if isinstance(value, bool) and key != "apps"
    }
    if "tui" in config:
        settings["tui"] = _select(config["tui"], TUI_KEYS)
    if "profiles" in config:
        settings["profiles"] = {
            name: _select(value, CODEX_KEYS) for name, value in config["profiles"].items()
        }
    # Remote apps are still controlled by the existing launcher override.
    plugins = {}
    for name, value in config.get("plugins", {}).items():
        if not isinstance(value, dict) or value.get("enabled") is not True:
            continue
        if not re.fullmatch(r"[\w.-]+@[\w.-]+", name):
            continue
        plugin, marketplace = name.split("@")
        if plugin in {".", ".."} or marketplace in {".", ".."}:
            continue
        directory = p.home / ".codex/plugins/cache" / marketplace / plugin
        found = False
        for version in directory.glob("*"):
            if (
                not version.name.startswith(".")
                and version.is_dir()
                and not version.is_symlink()
                and (version / ".codex-plugin/plugin.json").is_file()
            ):
                p.link(str(version.relative_to(p.home)))
                found = True
        if found:
            plugins[name] = {"enabled": True}
    if plugins:
        settings["plugins"] = plugins
    marketplaces = {}
    for name, item in config.get("marketplaces", {}).items():
        source = Path(item.get("source", ""))
        roots = (p.home / ".codex/.tmp/bundled-marketplaces", p.home / ".cache/codex-runtimes")
        manifest = source / ".agents/plugins/marketplace.json"
        if (
            item.get("source_type") == "local"
            and manifest.is_file()
            and any(source.is_relative_to(root) for root in roots)
        ):
            p.grant(manifest)
            enabled = {plugin.split("@", 1)[0] for plugin in plugins if plugin.endswith(f"@{name}")}
            _marketplace_sources(p, manifest, source, enabled)
            marketplaces[name] = {"source_type": "local", "source": str(source)}
    if marketplaces:
        settings["marketplaces"] = marketplaces
    original_hooks = _json(p.home / ".codex/hooks.json", p.home)
    projected_hooks = _hooks(original_hooks)
    trust = _hook_trust(p.home, config, original_hooks, projected_hooks)
    if trust:
        settings["hooks"] = {"state": trust}
    p.file(".codex/config.toml", settings, toml=True)
    p.file(".codex/hooks.json", projected_hooks)
    for relative in (
        ".codex/AGENTS.md",
        ".codex/rules",
        ".codex/agents",
        ".agents/skills",
    ):
        p.link(relative)
    # Codex seeds and refreshes .system itself; keep its parent writable in isolated state.
    for skill in (p.home / ".codex/skills").glob("*"):
        if not skill.name.startswith("."):
            p.link(str(skill.relative_to(p.home)))
    for path in (p.home / ".codex").glob("*.config.toml"):
        p.file(
            f".codex/{path.name}",
            _select(_toml(path, p.home), CODEX_KEYS),
            toml=True,
        )


def install_harness(home: Path, vendor: str | None = None) -> None:
    """Refresh derived preferences and exact code grants from the installed harness."""
    home = home.resolve()
    path = home / DATA / "native/harness/manifest.json"
    manifest = {
        name: {"links": [], "files": [], "read": []} for name in ("pi", "claude", "codex", "shell")
    }
    manifest.update(_json(path, home))
    for name, project in (("pi", _pi), ("claude", _claude), ("codex", _codex)):
        if vendor is not None and vendor != name:
            continue
        p = Projection(home, name)
        project(p)
        for hook in HOOK_NAMES:
            p.link(f"{DATA}/hooks/{hook}")
        manifest[name] = p.manifest
    manifest["shell"] = {"links": [], "files": [], "read": []}
    write_json(path, manifest)
