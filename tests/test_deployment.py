"""Exercise deployment contracts through their command and filesystem boundaries."""

import contextlib
import io
import json
import os
import subprocess
import sys

import pytest

from workbench import cli, core, drift, lint, mcp, sync


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
        "footer.ts",
        "permission-policy.ts",
        "presets.ts",
        "safe-git.ts",
        "welcome.ts",
        "worker.ts",
        "workspace-files.ts",
    }
    assert not (tmp_path / ".agents/skills/paseo-management").exists()
    assert not (tmp_path / ".agents/skills/archify").exists()
    assert drift.drift(tmp_path, ("claude", "pi"), verify_plugins=False, profile="work") == 0


def test_work_profile_rejects_codex_target():
    assert cli.main(["sync", "codex", "--profile", "work"]) == 2
    assert cli.main(["drift", "codex", "--profile", "work"]) == 2


def test_drift_failure_reaches_process_exit_status(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "workbench.cli", "drift", "codex", "--no-plugins"],
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
    (agents / "shared/external-skills.json").write_text('{"$comment":"test", "skills":[]}')
    index = tmp_path / "playbook/knowledge/README.md"
    index.parent.mkdir(parents=True)
    index.write_text("# Knowledge\n")
    bad_link = tmp_path / "README.md"
    bad_link.write_text("[missing](missing.md)\n")
    monkeypatch.setattr(lint, "ROOT", tmp_path)
    monkeypatch.setattr(lint, "AGENTS", agents)
    monkeypatch.setattr(lint, "OVERLAYS", agents / "external-skills")
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
