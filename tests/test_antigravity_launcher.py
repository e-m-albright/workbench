"""Antigravity enters the same boundary without host account or connector state."""

import json

import pytest
from test_native_sandbox import harness_manifest, load_launcher

from workbench import native, native_config


def test_prepare_resolves_native_agy_without_shell_function(tmp_path, monkeypatch):
    binary = tmp_path / "install/antigravity"
    binary.parent.mkdir()
    binary.write_text("synthetic binary")
    launcher = tmp_path / "agy"
    launcher.symlink_to(binary)
    monkeypatch.setattr(
        native.shutil, "which", lambda name: str(launcher) if name == "agy" else None
    )
    agent, executable = native._agent(tmp_path, "antigravity", tmp_path / "node")
    assert agent["command"] == [str(binary)]
    assert executable == binary


def test_projection_shares_only_rules_and_skills(tmp_path):
    rules = tmp_path / ".gemini/AGENTS.md"
    rules.parent.mkdir()
    rules.write_text("shared instructions")
    skills = tmp_path / ".gemini/antigravity-cli/skills"
    skills.mkdir(parents=True)
    settings = skills.parent / "settings.json"
    settings.write_text(json.dumps({"mcpServers": {"private": {}}, "secret": "must-not-copy"}))
    projection = native_config.render_harness(tmp_path, "antigravity")
    assert {item["path"] for item in projection.manifest["links"]} == {
        ".gemini/AGENTS.md",
        ".gemini/antigravity-cli/skills",
    }
    assert not any("must-not-copy" in content for content in projection.contents.values())
    assert str(settings) not in projection.manifest["read"]


@pytest.mark.parametrize(
    "args", [["--help"], ["--remote-control"], ["remote-control", "start"], ["mic-serve"]]
)
def test_antigravity_boundary_and_terminal_only_policy(tmp_path, args):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "checkout"
    (repo / ".git").mkdir(parents=True)
    harness_manifest(home, "antigravity")
    (home / ".config/workbench/private-paths").write_text("")
    binary = "/opt/homebrew/Caskroom/antigravity-cli/test/antigravity"
    tools = {
        "node": "/opt/homebrew/bin/node",
        "agents": {"antigravity": {"command": [binary], "read": [str(tmp_path / "installed")]}},
    }
    if args != ["--help"]:
        with pytest.raises(ValueError, match="terminals only"):
            launcher.build_plan(repo, home, tools, "antigravity", "hosted", args)
        return
    plan = launcher.build_plan(repo, home, tools, "antigravity", "hosted", args)
    assert plan["command"] == [binary, "--help"]
    assert plan["env"]["HOME"] != str(home)
    assert plan["auth_link"] is None
    grants = plan["policy"]["filesystem"]["allowRead"]
    assert str(home / ".gemini") not in grants
    assert str(home / "Library/Keychains") not in grants
    assert "*.googleapis.com" in plan["policy"]["network"]["deniedDomains"]
    launcher.initialize_home(plan, home)


def test_status_reports_isolated_login_without_reading_tokens(tmp_path):
    result = native.status(tmp_path, vendor="antigravity")
    assert result["agents"]["antigravity"]["login_path"] is None
    assert (
        result["agents"]["antigravity"]["login"]
        == "isolated vendor login; authentication unverified"
    )
