"""Restricted agents inherit harness preferences and code, never host state."""

import json
import tomllib
from pathlib import Path

import pytest

from workbench.native_config import install_harness


def test_codex_preserves_its_writable_builtin_skill_directory(tmp_path):
    home = tmp_path / "home"
    for relative in (".codex/skills/.system/builtin/SKILL.md", ".codex/skills/custom/SKILL.md"):
        path = home / relative
        path.parent.mkdir(parents=True)
        path.write_text("skill code")
    install_harness(home)
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    links = {item["path"] for item in manifest["codex"]["links"]}
    assert ".codex/skills" not in links
    assert ".codex/skills/.system" not in links
    assert ".codex/skills/custom" in links


@pytest.mark.parametrize(
    "relative", [".pi/agent/settings.json", ".codex/config.toml", ".claude/settings.json"]
)
def test_projection_rejects_configuration_symlinks(tmp_path, relative):
    home = tmp_path / "home"
    secret = tmp_path / "private-config"
    secret.write_text('{"defaultModel": "private-secret"}')
    source = home / relative
    source.parent.mkdir(parents=True)
    source.symlink_to(secret)
    with pytest.raises(ValueError, match="symlink"):
        install_harness(home)


def test_claude_marketplace_grants_only_enabled_plugin_sources(tmp_path):
    home = tmp_path / "home"
    marketplace = home / ".claude/plugins/marketplaces/official"
    installed = home / ".claude/plugins/cache/official/example/v1"
    installed.mkdir(parents=True)
    code = marketplace / "plugins/example"
    code.mkdir(parents=True)
    write_json(home, ".claude/settings.json", {"enabledPlugins": {"example@official": True}})
    write_json(
        home,
        ".claude/plugins/installed_plugins.json",
        {"plugins": {"example@official": [{"scope": "user", "installPath": str(installed)}]}},
    )
    write_json(
        home,
        ".claude/plugins/known_marketplaces.json",
        {
            "official": {
                "source": {"source": "github", "repo": "example/plugins"},
                "installLocation": str(marketplace),
            }
        },
    )
    write_json(
        home,
        str((marketplace / ".claude-plugin/marketplace.json").relative_to(home)),
        {
            "plugins": [
                {"name": "example", "source": "./plugins/example"},
                {"name": "disabled", "source": "./plugins/disabled"},
            ]
        },
    )
    install_harness(home)
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    assert str(code) in manifest["claude"]["read"]
    assert str(marketplace) not in manifest["claude"]["read"]


def write_json(home, relative, value):
    path = home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def output(home, vendor, relative):
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    entry = next(row for row in manifest[vendor]["files"] if row["path"] == relative)
    return Path(entry["source"]).read_text()


def test_preferences_are_shared_without_credentials_or_conversation_state(tmp_path):
    home = tmp_path / "home"
    write_json(
        home,
        ".pi/agent/settings.json",
        {
            "defaultModel": "chosen-model",
            "tuiMode": "fullscreen",
            "theme": "dark",
            "env": {"TOKEN": "private-secret"},
            "shellCommandPrefix": "cat private-history",
        },
    )
    write_json(
        home,
        ".claude/settings.json",
        {
            "model": "chosen-claude",
            "outputStyle": "Concise",
            "effortLevel": "high",
            "env": {"TOKEN": "private-secret"},
            "apiKeyHelper": "cat private-secret",
            "permissions": {"additionalDirectories": ["/private-records"]},
        },
    )
    write_json(
        home,
        ".claude.json",
        {"history": "private-history", "mcpServers": {"secret": {}}},
    )
    codex = home / ".codex/config.toml"
    codex.parent.mkdir(parents=True)
    codex.write_text(
        'model = "chosen-codex"\nmodel_reasoning_effort = "high"\n'
        '[tui]\ntheme = "dark"\n'
        '[mcp_servers.private]\ncommand = "private-secret"\n'
        '[projects."/private-records"]\ntrust_level = "trusted"\n'
        '[shell_environment_policy.set]\nTOKEN = "private-secret"\n'
    )
    install_harness(home)
    pi = json.loads(output(home, "pi", ".pi/agent/settings.json"))
    assert pi["defaultModel"] == "chosen-model"
    assert pi["tuiMode"] == "fullscreen"
    assert "shellCommandPrefix" not in pi
    claude = json.loads(output(home, "claude", ".claude/settings.json"))
    assert claude["model"] == "chosen-claude"
    assert claude["outputStyle"] == "Concise"
    assert claude["effortLevel"] == "high"
    codex = tomllib.loads(output(home, "codex", ".codex/config.toml"))
    assert codex["model"] == "chosen-codex"
    assert codex["model_reasoning_effort"] == "high"
    assert codex["tui"]["theme"] == "dark"
    for path in (home / ".local/share/workbench/native/harness").rglob("*"):
        if path.is_file():
            assert "private-secret" not in path.read_text()
            assert "private-history" not in path.read_text()
            assert "/private-records" not in path.read_text()


def test_code_assets_are_read_only_links_and_state_is_never_granted(tmp_path):
    home = tmp_path / "home"
    for relative in (
        ".agents/skills/example/SKILL.md",
        ".claude/CLAUDE.md",
        ".codex/AGENTS.md",
        ".pi/agent/AGENTS.md",
        ".pi/agent/extensions/welcome.ts",
        ".pi/agent/prompts/check.md",
        ".local/share/workbench/hooks/guard-sensitive-file.sh",
    ):
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("managed code")
    install_harness(home)
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    for vendor in ("pi", "claude", "codex"):
        assert manifest[vendor]["links"]
        assert str(home) not in manifest[vendor]["read"]
        assert str(home / ".codex") not in manifest[vendor]["read"]
        assert str(home / ".claude") not in manifest[vendor]["read"]
        assert str(home / ".pi/agent") not in manifest[vendor]["read"]
        assert all(Path(row["target"]).is_absolute() for row in manifest[vendor]["links"])
    pi_links = {row["path"] for row in manifest["pi"]["links"]}
    assert ".pi/agent/extensions" in pi_links
    assert ".pi/agent/prompts" in pi_links
    assert ".agents/skills" in pi_links
    assert manifest["shell"] == {"links": [], "files": [], "read": []}


def test_claude_plugins_preserve_installed_code_without_other_project_records(tmp_path):
    home = tmp_path / "home"
    plugin = home / ".claude/plugins/cache/official/example/v1"
    plugin.mkdir(parents=True)
    (plugin / "README.md").write_text("plugin source")
    write_json(home, ".claude/settings.json", {"enabledPlugins": {"example@official": True}})
    write_json(
        home,
        ".claude/plugins/installed_plugins.json",
        {
            "version": 2,
            "plugins": {
                "example@official": [
                    {"scope": "user", "installPath": str(plugin), "version": "v1"},
                    {
                        "scope": "project",
                        "projectPath": "/private-records",
                        "installPath": str(plugin),
                    },
                ],
                "disabled@official": [{"scope": "user", "installPath": "/private-records"}],
            },
        },
    )
    install_harness(home)
    ledger = json.loads(output(home, "claude", ".claude/plugins/installed_plugins.json"))
    assert list(ledger["plugins"]) == ["example@official"]
    assert len(ledger["plugins"]["example@official"]) == 1
    assert ledger["plugins"]["example@official"][0]["installPath"] == str(plugin)
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    assert str(plugin) in manifest["claude"]["read"]
    assert str(home / ".claude/plugins") not in manifest["claude"]["read"]


def test_refresh_follows_changed_preferences_and_does_not_copy_auth(tmp_path):
    home = tmp_path / "home"
    write_json(home, ".pi/agent/settings.json", {"defaultModel": "first"})
    write_json(home, ".pi/agent/auth.json", {"secret": "private-secret"})
    install_harness(home)
    write_json(home, ".pi/agent/settings.json", {"defaultModel": "second"})
    install_harness(home)
    assert json.loads(output(home, "pi", ".pi/agent/settings.json"))["defaultModel"] == "second"
    manifest = (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    assert "auth.json" not in manifest


def test_hooks_only_keep_known_guards_and_never_private_shell_helpers(tmp_path):
    home = tmp_path / "home"
    value = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                "bash $HOME/.local/share/workbench/hooks/guard-sensitive-file.sh"
                            ),
                        },
                        {"type": "command", "command": "cat /private-records"},
                    ],
                }
            ]
        }
    }
    write_json(home, ".claude/settings.json", value)
    write_json(home, ".codex/hooks.json", value)
    install_harness(home)
    for vendor, relative in [
        ("claude", ".claude/settings.json"),
        ("codex", ".codex/hooks.json"),
    ]:
        text = output(home, vendor, relative)
        assert "/private-records" not in text
        assert "guard-sensitive-file.sh" in text


def test_codex_plugin_grants_exclude_staging_disabled_and_appserver_state(tmp_path):
    home = tmp_path / "home"
    for relative in (
        ".codex/plugins/cache/official/example/v1",
        ".codex/plugins/cache/official/example/.tmp-secret",
        ".codex/plugins/cache/official/disabled/v1",
    ):
        write_json(home, relative + "/.codex-plugin/plugin.json", {"name": "example"})
    write_json(
        home,
        ".codex/plugins/.plugin-appserver/state.json",
        {"secret": "private-secret"},
    )
    (home / ".codex/config.toml").write_text(
        '[plugins."example@official"]\nenabled = true\n'
        '[plugins."disabled@official"]\nenabled = false\n'
    )
    install_harness(home)
    manifest = json.loads(
        (home / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    grants = manifest["codex"]["read"]
    assert str(home / ".codex/plugins/cache/official/example/v1") in grants
    assert not any(
        "disabled" in path or ".tmp-secret" in path or ".plugin-appserver" in path
        for path in grants
    )
    assert str(home / ".codex/plugins/cache") not in grants


def test_catalogue_keeps_selected_model_without_provider_credentials(tmp_path):
    home = tmp_path / "home"
    write_json(
        home,
        ".pi/agent/models-store.json",
        {
            "openai-codex": {
                "checkedAt": 123,
                "auth": "private-secret",
                "models": [
                    {
                        "id": "chosen-model",
                        "name": "Chosen model",
                        "baseUrl": "https://api.example.com/v1",
                        "contextWindow": 262144,
                        "headers": {"Authorization": "private-secret"},
                        "apiKey": "private-secret",
                        "compat": {"supportsToolSearch": True, "secret": "private-secret"},
                    },
                    {
                        "id": "credential-in-url",
                        "baseUrl": "https://user:private-secret@example.com/v1",
                    },
                ],
            }
        },
    )
    install_harness(home)
    text = output(home, "pi", ".pi/agent/models-store.json")
    assert "private-secret" not in text
    assert "credential-in-url" not in text
    model = json.loads(text)["openai-codex"]["models"][0]
    assert model["id"] == "chosen-model"
    assert model["contextWindow"] == 262144
    assert model["compat"] == {"supportsToolSearch": True}


def test_asset_symlink_cannot_grant_a_private_directory(tmp_path):
    home = tmp_path / "home"
    private = home / "private-records"
    private.mkdir(parents=True)
    (home / ".pi/agent").mkdir(parents=True)
    (home / ".pi/agent/extensions").symlink_to(private, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        install_harness(home)


def test_statusline_and_features_remain_shared_and_hook_trust_is_relocated(tmp_path):
    home = tmp_path / "home"
    statusline = home / ".local/share/workbench/claude/statusline.sh"
    statusline.parent.mkdir(parents=True)
    statusline.write_text("statusline code")
    hook = {
        "type": "command",
        "command": "bash $HOME/.local/share/workbench/hooks/guard-sensitive-file.sh",
        "timeout": 5,
    }
    write_json(
        home,
        ".codex/hooks.json",
        {"hooks": {"PreToolUse": [{"matcher": "Edit|Write", "hooks": [hook]}]}},
    )
    (home / ".codex/config.toml").write_text(
        "[features]\njs_repl = true\napps = true\n"
        f'[hooks.state."{home}/.codex/hooks.json:pre_tool_use:0:0"]\n'
        f'trusted_hash = "{"a" * 64}"\nenabled = true\n'
    )
    install_harness(home)
    settings = json.loads(output(home, "claude", ".claude/settings.json"))
    assert settings["statusLine"]["command"] == str(statusline)
    config = tomllib.loads(output(home, "codex", ".codex/config.toml"))
    assert config["features"] == {"js_repl": True}
    trust = config["hooks"]["state"]
    key = "__WORKBENCH_AGENT_HOME__/.codex/hooks.json:pre_tool_use:0:0"
    assert trust == {key: {"trusted_hash": "a" * 64, "enabled": True}}
