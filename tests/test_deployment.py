"""Exercise deployment contracts through their command and filesystem boundaries."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tomllib

import pytest

from workbench import cli, core, drift, lint, mcp, sync


@pytest.mark.parametrize("target", ["claude", "desktop", "codex"])
def test_exa_is_retired_without_removing_external_mcp_servers(target):
    existing = {"exa": {"command": "old-exa"}, "external": {"command": "keep"}}
    assert "exa" in mcp.retired_mcp_names()
    assert "exa" not in mcp.active_mcp(target)
    assert mcp.merge_mcp(existing, target) == {"external": {"command": "keep"}}


def test_sync_removes_exa_from_existing_configs_and_drift_flags_reintroduction(tmp_path):
    external = {"external": {"command": "keep"}}
    servers = {"exa": {"command": "old-exa"}, **external}
    claude = tmp_path / ".claude.json"
    desktop = tmp_path / "Library/Application Support/Claude/claude_desktop_config.json"
    codex = tmp_path / ".codex/config.toml"
    desktop.parent.mkdir(parents=True)
    codex.parent.mkdir(parents=True)
    for path in (claude, desktop):
        path.write_text(json.dumps({"mcpServers": servers}))
    codex.write_text(
        '[mcp_servers.exa]\ncommand = "old-exa"\n[mcp_servers.external]\ncommand = "keep"\n'
    )

    sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False)
    sync.sync_codex(tmp_path, deploy_skills=False, deploy_plugins=False)
    deployed = {
        "claude": json.loads(claude.read_text())["mcpServers"],
        "desktop": json.loads(desktop.read_text())["mcpServers"],
        "codex": tomllib.loads(codex.read_text())["mcp_servers"],
    }
    for target, actual in deployed.items():
        assert actual == external
        findings, additions = [], []
        drift._check_mcp(actual, target, "MCP", findings, additions)
        assert findings == []
        drift._check_mcp(servers, target, "MCP", findings, additions)
        assert any("exa" in finding for finding in findings)


@pytest.mark.parametrize("target", ["claude", "desktop", "codex"])
def test_retired_chrome_devtools_uses_its_real_server_name(target):
    assert mcp.merge_mcp({"chrome-devtools": {"command": "retired"}}, target) == {}


def test_work_profile_sync_is_fail_closed_and_drift_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    assert cli.main(["sync", "all", "--profile", "work"]) == 0

    assert not (tmp_path / ".codex").exists()
    assert not (tmp_path / "Library/Application Support/Claude").exists()
    claude_root = json.loads((tmp_path / ".claude.json").read_text())
    assert "exa" not in claude_root.get("mcpServers", {})
    claude_settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert not any(
        name.endswith("@claude-plugins-official")
        for name in claude_settings.get("enabledPlugins", {})
    )

    pi_home = tmp_path / ".pi/agent"
    pi_settings = json.loads((pi_home / "settings.json").read_text())
    assert "defaultProvider" not in pi_settings
    assert "defaultModel" not in pi_settings
    assert pi_settings.get("packages", []) == []
    assert not (pi_home / "inference-router.json").exists()
    assert json.loads((pi_home / "models.json").read_text()).get("providers", {}) == {}
    assert {path.name for path in (pi_home / "extensions").glob("*.ts")} == {
        "activity-title.ts",
        "clipboard.ts",
        "footer.ts",
        "permission-policy.ts",
        "presets.ts",
        "safe-git.ts",
        "welcome.ts",
        "worker.ts",
        "workspace-files.ts",
    }
    assert {path.name for path in (tmp_path / ".local/share/workbench/shell").iterdir()} == {
        "agent-launchers.zsh",
        "agent-sandbox.zsh",
        "native-sandbox.mjs",
        "native-sandbox.py",
    }
    manifest = json.loads(
        (tmp_path / ".local/share/workbench/native/harness/manifest.json").read_text()
    )
    assert manifest["claude"]["files"]
    assert manifest["pi"]["files"]
    assert (tmp_path / ".config/workbench/hard-deny-paths").is_file()
    assert not (tmp_path / ".agents/skills/paseo-management").exists()
    assert not (tmp_path / ".agents/skills/archify").exists()
    assert drift.drift(tmp_path, ("claude", "pi"), verify_plugins=False, profile="work") == 0


def test_pi_drift_requires_installed_metadata_even_when_the_package_declaration_matches(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=False, deploy_plugins=False)
    pi_home = tmp_path / ".pi/agent"
    assert json.loads((pi_home / "settings.json").read_text())["packages"] == [
        "npm:pi-agent-browser-native@0.6.15"
    ]

    findings = []
    drift._check_pi(tmp_path, findings, [])

    manifest = pi_home / "npm/node_modules/pi-agent-browser-native/package.json"
    assert findings == [
        f"DRIFT Pi package pi-agent-browser-native: missing installed metadata {manifest}"
    ]


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        (
            b'{"name":"pi-agent-browser-native","version":"0.6.14"}',
            "installed version 0.6.14; expected 0.6.15",
        ),
        (b"{invalid", "malformed installed metadata"),
        (b"[]", "malformed installed metadata"),
        (b"\xff", "malformed installed metadata"),
        (b'{"name":"another-package","version":"0.6.15"}', "malformed installed name/version"),
        (b'{"name":"pi-agent-browser-native","version":15}', "malformed installed name/version"),
        (b'{"name":"pi-agent-browser-native"}', "malformed installed name/version"),
    ],
)
def test_pi_drift_checks_realized_package_metadata(tmp_path, monkeypatch, metadata, expected):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=False, deploy_plugins=False)
    pi_home = tmp_path / ".pi/agent"
    manifest = pi_home / "npm/node_modules/pi-agent-browser-native/package.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(metadata)
    core.write_json(
        pi_home / "npm/package.json", {"dependencies": {"pi-agent-browser-native": "0.6.15"}}
    )

    findings = []
    drift._check_pi(tmp_path, findings, [])

    assert len(findings) == 1
    assert findings[0].startswith(f"DRIFT Pi package pi-agent-browser-native: {expected}")


def test_pi_drift_accepts_matching_installed_version_and_ignores_unmanaged_packages(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=False, deploy_plugins=False)
    npm_root = tmp_path / ".pi/agent/npm"
    core.write_json(
        npm_root / "node_modules/pi-agent-browser-native/package.json",
        {"name": "pi-agent-browser-native", "version": "0.6.15"},
    )
    external = npm_root / "node_modules/owner-package/package.json"
    external.parent.mkdir()
    external.write_text("owner-managed metadata need not be inspected\n")

    findings = []
    drift._check_pi(tmp_path, findings, [])

    assert findings == []
    assert external.read_text() == "owner-managed metadata need not be inspected\n"


def test_work_profile_does_not_require_or_inspect_personal_pi_package_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=False, deploy_plugins=False, profile="work")
    manifest = tmp_path / ".pi/agent/npm/node_modules/pi-agent-browser-native/package.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("dormant personal cache\n")

    findings = []
    drift._check_pi(tmp_path, findings, [], profile="work")

    assert findings == []
    assert manifest.read_text() == "dormant personal cache\n"


@pytest.mark.parametrize(
    "surface",
    [
        "defaultProvider",
        "defaultModel",
        "shellCommandPrefix",
        "packages",
        "provider",
        "extension",
        "shared-skill",
        "native-skill",
    ],
)
def test_work_drift_rejects_reintroduced_personal_surfaces(tmp_path, monkeypatch, surface, capsys):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")
    pi_home = tmp_path / ".pi/agent"
    if surface in {"defaultProvider", "defaultModel", "shellCommandPrefix", "packages"}:
        path = pi_home / "settings.json"
        settings = json.loads(path.read_text())
        settings[surface] = core._settings(core.AGENTS / "pi/settings.json")[surface]
        path.write_text(json.dumps(settings))
    elif surface == "provider":
        shutil.copyfile(core.AGENTS / "pi/models.json", pi_home / "models.json")
    elif surface == "extension":
        shutil.copyfile(
            core.AGENTS / "pi/extensions/inference-router.ts",
            pi_home / "extensions/inference-router.ts",
        )
    else:
        root = tmp_path / (".agents/skills" if surface == "shared-skill" else ".pi/agent/skills")
        shutil.copytree(core.AGENTS / "skills/paseo-management", root / "paseo-management")

    assert drift.drift(tmp_path, ("pi",), verify_plugins=False, profile="work") == 1
    assert "personal" in capsys.readouterr().out


def test_personal_to_work_migration_preserves_unknown_additions(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/local/bin/{name}")
    pi_home = tmp_path / ".pi/agent"
    pi_home.mkdir(parents=True)
    for name in ("settings.json", "models.json", "presets.json", "inference-router.json"):
        shutil.copyfile(core.AGENTS / "pi" / name, pi_home / name)
    shutil.copytree(core.AGENTS / "pi/extensions", pi_home / "extensions")
    (pi_home / "extensions/external.ts").write_text("// Owner-managed extension.\n")
    models_path = pi_home / "models.json"
    models = json.loads(models_path.read_text())
    models["providers"]["external"] = {"baseUrl": "https://example.test/v1"}
    models_path.write_text(json.dumps(models))
    for root in (".agents/skills", ".pi/agent/skills"):
        shutil.copytree(
            core.AGENTS / "skills/paseo-management", tmp_path / root / "paseo-management"
        )
    external_skill = pi_home / "skills/external/SKILL.md"
    external_skill.parent.mkdir(parents=True)
    external_skill.write_text("---\nname: external\ndescription: Owner-managed skill.\n---\n")

    sync.sync_pi(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")

    assert drift.drift(tmp_path, ("pi",), verify_plugins=False, profile="work") == 0
    output = capsys.readouterr().out
    assert "EXTERNAL Pi extension: external.ts" in output
    assert "EXTERNAL Pi models.json entry: external" in output
    assert "EXTERNAL pi skill: external" in output
    assert not (tmp_path / ".agents/skills/paseo-management").exists()
    assert not (pi_home / "skills/paseo-management").exists()
    assert not (pi_home / "extensions/inference-router.ts").exists()
    assert "defaultProvider" not in json.loads((pi_home / "settings.json").read_text())


@pytest.mark.parametrize("profile", ["personal", "work"])
def test_sync_retires_archify_from_every_skill_root(tmp_path, profile):
    assert "archify" in core.RETIRED_SKILLS
    for root in (".claude/skills", ".agents/skills", ".pi/agent/skills"):
        skill = tmp_path / root / "archify/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: archify\ndescription: Retired installation.\n---\n")
    findings, external = [], []
    drift._check_skills(tmp_path / ".agents/skills", "pi", findings, external, profile=profile)
    drift._check_pi_native_skills(tmp_path / ".pi/agent/skills", findings, external, profile)
    assert any("retired pi skill still present: archify" in finding for finding in findings)
    assert not any("archify" in item for item in external)

    sync.sync_claude(tmp_path, deploy_skills=True, deploy_plugins=False, profile=profile)
    sync.sync_pi(tmp_path, deploy_skills=True, deploy_plugins=False, profile=profile)

    for root in (".claude/skills", ".agents/skills", ".pi/agent/skills"):
        assert not (tmp_path / root / "archify").exists()


def test_sync_reports_skill_repair_and_retirement_then_becomes_unchanged(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    assert cli.main(["sync", "pi", "--profile", "work"]) == 0
    capsys.readouterr()
    skill = tmp_path / ".agents/skills/testing/SKILL.md"
    original = skill.read_text()
    skill.write_text("stale skill")
    retired = tmp_path / ".pi/agent/skills/archify/SKILL.md"
    retired.parent.mkdir(parents=True)
    retired.write_text("retired skill")

    assert cli.main(["sync", "pi", "--profile", "work"]) == 0

    output = capsys.readouterr().out
    assert "updated ~/.agents/skills/testing" in output
    assert "updated ~/.pi/agent/skills/archify" in output
    assert "nothing to change" not in output
    assert ".tmp" not in output
    assert ".bak" not in output
    assert skill.read_text() == original
    assert not retired.parent.exists()
    assert cli.main(["sync", "pi", "--profile", "work"]) == 0
    assert "nothing to change" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--no-skills", "--rules-only"])
def test_deploy_rejects_sync_only_flags_before_running_commands(tmp_path, flag):
    result, commands = _run_deploy_recipe(tmp_path, ["pi", flag])
    assert result.returncode != 0
    assert flag in result.stderr
    assert "sync" in result.stderr
    assert commands == []


def test_deploy_forwards_common_arguments_to_both_commands(tmp_path):
    result, commands = _run_deploy_recipe(tmp_path, ["pi", "--profile", "work", "--no-plugins"])
    assert result.returncode == 0, result.stderr
    assert commands == [
        "sync pi --profile work --no-plugins",
        "drift pi --profile work --no-plugins",
    ]


def _run_deploy_recipe(tmp_path, arguments):
    shutil.copyfile(core.ROOT / "justfile", tmp_path / "justfile")
    launcher = tmp_path / "bin/workbench"
    launcher.parent.mkdir()
    launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DEPLOY_LOG"\n')
    launcher.chmod(0o755)
    log = tmp_path / "commands"
    result = subprocess.run(
        ["just", "--justfile", str(tmp_path / "justfile"), "deploy", *arguments],
        env={**os.environ, "DEPLOY_LOG": str(log)},
        capture_output=True,
        text=True,
        check=False,
    )
    return result, log.read_text().splitlines() if log.exists() else []


def test_claude_sync_applies_requested_model_and_effort_defaults(tmp_path):
    path = tmp_path / ".claude/settings.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"model": "sonnet", "effortLevel": "high", "custom": True}))

    sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False, profile="work")

    settings = json.loads(path.read_text())
    assert settings["model"] == "opus"
    assert settings["effortLevel"] == "medium"
    assert settings["custom"] is True


@pytest.mark.parametrize("command", ["sync", "drift"])
@pytest.mark.parametrize(
    ("environment", "arguments", "expected"),
    [
        (None, [], "personal"),
        ("work", [], "work"),
        ("personal", [], "personal"),
        ("work", ["--profile", "personal"], "personal"),
        ("personal", ["--profile", "work"], "work"),
    ],
)
def test_cli_profile_defaults_and_explicit_override(
    tmp_path, monkeypatch, command, environment, arguments, expected
):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    monkeypatch.delenv("DOTFILES_PROFILE", raising=False)
    if environment is not None:
        monkeypatch.setenv("DOTFILES_PROFILE", environment)
    profiles = []

    def deploy(home, **kwargs):
        profiles.append(kwargs["profile"])

    def inspect(home, vendors, **kwargs):
        profiles.append(kwargs["profile"])
        return 0

    monkeypatch.setattr(cli, "sync_pi", deploy)
    monkeypatch.setattr(cli.drift_module, "drift", inspect)
    assert cli.main([command, "pi", *arguments]) == 0
    assert profiles == [expected]


@pytest.mark.parametrize("command", ["sync", "drift"])
def test_invalid_environment_profile_fails_before_access(tmp_path, monkeypatch, command):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path / "unused"))
    monkeypatch.setenv("DOTFILES_PROFILE", "typo")
    assert cli.main([command, "pi"]) == 2
    assert not (tmp_path / "unused").exists()


def test_work_profile_rejects_codex_target(monkeypatch):
    assert cli.main(["sync", "codex", "--profile", "work"]) == 2
    assert cli.main(["drift", "codex", "--profile", "work"]) == 2
    monkeypatch.setenv("DOTFILES_PROFILE", "work")
    assert cli.main(["sync", "codex"]) == 2
    assert cli.main(["drift", "codex"]) == 2


def test_drift_failure_reaches_process_exit_status(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "workbench.cli",
            "drift",
            "codex",
            "--no-plugins",
            "--profile",
            "personal",
        ],
        env={**os.environ, "WORKBENCH_HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert "managed drift item(s)" in result.stdout
    assert result.returncode == 1


def test_lint_failure_and_success_reach_cli_status(tmp_path, monkeypatch):
    agents = tmp_path / "agents"
    (agents / "skills").mkdir(parents=True)
    (agents / "codex").mkdir()
    (agents / "codex/default.rules").write_text("")
    (agents / "shared").mkdir()
    index = tmp_path / "playbook/README.md"
    index.parent.mkdir(parents=True)
    index.write_text("# Playbook\n")
    bad_link = tmp_path / "README.md"
    bad_link.write_text("[missing](missing.md)\n")
    monkeypatch.setattr(lint, "ROOT", tmp_path)
    monkeypatch.setattr(lint, "AGENTS", agents)
    with contextlib.redirect_stdout(io.StringIO()) as output:
        status = cli.main(["lint"])
    assert "broken local link" in output.getvalue()
    assert status == 1
    bad_link.write_text("# Healthy\n")
    assert cli.main(["lint"]) == 0


@pytest.mark.parametrize("link_kind", ["root", "directory", "file", "dangling"])
def test_session_hardening_rejects_symlinks_without_touching_targets(tmp_path, link_kind):
    agent = tmp_path / "agent"
    agent.mkdir()
    sessions = agent / "sessions"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o755)
    target = outside / "example.jsonl"
    target.write_text("synthetic transcript\n")
    target.chmod(0o644)
    if link_kind == "root":
        sessions.symlink_to(outside, target_is_directory=True)
    else:
        sessions.mkdir()
        link = sessions / "link"
        destination = {"directory": outside, "file": target, "dangling": outside / "missing"}
        link.symlink_to(destination[link_kind])
    with pytest.raises(core.WorkbenchError, match="session"):
        sync._harden_pi_session_permissions(agent)
    assert outside.stat().st_mode & 0o777 == 0o755
    assert target.stat().st_mode & 0o777 == 0o644
    assert target.read_text() == "synthetic transcript\n"


def test_drift_rejects_dangling_session_root(tmp_path):
    agent = tmp_path / ".pi/agent"
    agent.mkdir(parents=True)
    (agent / "sessions").symlink_to(tmp_path / "missing")
    findings = []
    drift._check_pi(tmp_path, findings, [])
    assert any("session path is a symlink" in finding for finding in findings)


def test_claude_sync_preserves_external_hooks_and_plugins_idempotently(tmp_path):
    settings_path = tmp_path / ".claude/settings.json"
    settings_path.parent.mkdir()
    owner_hook = {"type": "command", "command": "echo owner"}
    old_guard = {
        "type": "command",
        "command": "bash $HOME/.local/share/workbench/hooks/obsolete.sh",
    }
    settings_path.write_text(
        json.dumps(
            {
                "enabledPlugins": {"example@owner": True, "disabled@owner": False},
                "hooks": {
                    "SessionStart": [{"hooks": [owner_hook]}],
                    "PreToolUse": [{"matcher": "Bash", "hooks": [old_guard, owner_hook]}],
                },
            }
        )
    )
    sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False)
    first = settings_path.read_text()
    actual = json.loads(first)
    assert actual["enabledPlugins"]["example@owner"] is True
    assert actual["enabledPlugins"]["disabled@owner"] is False
    assert actual["hooks"]["SessionStart"] == [{"hooks": [owner_hook]}]
    assert actual["hooks"]["PreToolUse"][0] == {"matcher": "Bash", "hooks": [owner_hook]}
    assert "obsolete.sh" not in first
    assert "guard-destructive-shell.sh" in first
    sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False)
    assert settings_path.read_text() == first
    findings = []
    drift._check_claude(tmp_path, tmp_path / core.DATA_REL, findings, [])
    assert findings == []
    actual["hooks"]["PreToolUse"] = [actual["hooks"]["PreToolUse"][0]]
    settings_path.write_text(json.dumps(actual))
    drift._check_claude(tmp_path, tmp_path / core.DATA_REL, findings, [])
    assert any("Claude settings.hooks" in finding for finding in findings)


def test_desktop_mcp_reconciles_target_removal_and_preserves_external(tmp_path, monkeypatch):
    registry = {
        "moved": {"targets": ["codex"], "command": "new-target"},
        "inherited": {"targets": ["claude"], "command": "inherited"},
        "desktop": {"targets": ["desktop"], "type": "http", "url": "https://example.com/mcp"},
        "_retired_disabled": "retired",
    }
    monkeypatch.setattr(mcp, "_registry", lambda: registry)
    path = tmp_path / "Library/Application Support/Claude/claude_desktop_config.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "moved": {"command": "old"},
                    "retired": {"command": "retired"},
                    "external": {"command": "owner"},
                }
            }
        )
    )
    findings, external = [], []
    drift._check_claude(tmp_path, tmp_path / core.DATA_REL, findings, external)
    assert any("Desktop MCP" in finding and "moved" in finding for finding in findings)
    assert any("Desktop MCP" in finding and "retired" in finding for finding in findings)
    assert any("Desktop MCP" in item and "external" in item for item in external)
    sync._sync_claude_desktop(tmp_path)
    servers = json.loads(path.read_text())["mcpServers"]
    assert set(servers) == {"external", "inherited", "desktop"}
    assert servers["external"] == {"command": "owner"}
    assert servers["desktop"]["command"] == "npx"
    assert servers["desktop"]["args"] == ["-y", "mcp-remote@0.2.5", "https://example.com/mcp"]
    first = path.read_text()
    sync._sync_claude_desktop(tmp_path)
    assert path.read_text() == first


def test_claude_drift_detects_keys_removed_by_reconciliation(tmp_path):
    sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False)
    path = tmp_path / ".claude/settings.json"
    settings = json.loads(path.read_text())
    settings["permissions"]["defaultMode"] = "bypassPermissions"
    settings["hooks"]["Notification"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "bash $HOME/.local/share/workbench/hooks/retired.sh",
                }
            ]
        }
    ]
    path.write_text(json.dumps(settings))
    findings = []
    drift._check_claude(tmp_path, tmp_path / core.DATA_REL, findings, [])
    assert "DRIFT Claude settings.hooks" in findings
    assert "DRIFT Claude settings.permissions" in findings


def test_claude_invalid_hooks_fail_without_overwriting_settings(tmp_path):
    path = tmp_path / ".claude/settings.json"
    path.parent.mkdir()
    original = '{"hooks":{"PreToolUse":[{"hooks":[{"type":"command","command":null}]}]}}'
    path.write_text(original)
    with pytest.raises(core.WorkbenchError, match="invalid hook"):
        sync.sync_claude(tmp_path, deploy_skills=False, deploy_plugins=False)
    assert path.read_text() == original
