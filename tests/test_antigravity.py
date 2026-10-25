"""Antigravity rules, skills, and isolated launch configuration."""

from workbench import cli, core


def test_antigravity_sync_preview_drift_and_idempotence(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    assert cli.main(["sync", "antigravity", "--dry-run"]) == 0
    assert not list(tmp_path.iterdir())
    assert "CREATE ~/.gemini/AGENTS.md" in capsys.readouterr().out
    assert cli.main(["sync", "antigravity"]) == 0
    rules = tmp_path / ".gemini/AGENTS.md"
    assert rules.read_bytes() == (core.AGENTS / "shared/rules.md").read_bytes()
    skills = tmp_path / ".gemini/antigravity-cli/skills"
    assert (skills / "testing/SKILL.md").is_file()
    assert (tmp_path / core.DATA_REL / "native/harness/manifest.json").is_file()
    assert cli.main(["drift", "antigravity"]) == 0
    capsys.readouterr()
    assert cli.main(["sync", "antigravity"]) == 0
    assert "nothing to change" in capsys.readouterr().out
    rules.write_text("changed")
    assert cli.main(["drift", "antigravity"]) == 1
    assert "DRIFT antigravity rules" in capsys.readouterr().out


def test_antigravity_rules_only_and_no_skills_preserve_vendor_state(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    settings = tmp_path / ".gemini/antigravity-cli/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"custom":true}')
    assert cli.main(["sync", "antigravity", "--rules-only"]) == 0
    assert not (settings.parent / "skills").exists()
    assert cli.main(["sync", "antigravity", "--no-skills"]) == 0
    assert settings.read_text() == '{"custom":true}'
    assert not (settings.parent / "skills").exists()


def test_antigravity_excluded_from_work_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    assert cli.main(["sync", "antigravity", "--profile", "work"]) != 0
    assert cli.main(["drift", "antigravity", "--profile", "work"]) != 0
    assert not list(tmp_path.iterdir())
