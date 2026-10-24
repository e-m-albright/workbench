"""A sync preview uses the real reconciliation without changing live state."""

import json
from pathlib import Path

import pytest

from workbench import cli, core, drift, sync
from workbench.preview import preview_sync


def snapshot(root: Path):
    return {
        str(path.relative_to(root)): (
            path.read_bytes() if path.is_file() else None,
            path.lstat().st_mode,
        )
        for path in root.rglob("*")
    }


def test_preview_empty_home_writes_nothing_and_lists_planned_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    before = snapshot(tmp_path)
    assert cli.main(["sync", "all", "--profile", "work", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert snapshot(tmp_path) == before
    assert "CREATE ~/.claude/settings.json" in output
    assert "CREATE ~/.agents/skills/" in output
    assert "native/harness/manifest.json" in output
    assert "no changes made" in output


def test_preview_matches_real_sync_paths_and_preserves_external_values(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    path = tmp_path / ".claude/settings.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"env": {"PRIVATE": "never-print-this"}, "model": "old"}))
    before = snapshot(tmp_path)
    assert cli.main(["sync", "claude", "--no-plugins", "--dry-run"]) == 0
    preview = capsys.readouterr().out
    assert "never-print-this" not in preview
    assert snapshot(tmp_path) == before
    assert cli.main(["sync", "claude", "--no-plugins"]) == 0
    applied = capsys.readouterr().out
    for line in applied.splitlines():
        if line.startswith("updated "):
            assert line.removeprefix("updated ") in preview
    assert json.loads(path.read_text())["env"] == {"PRIVATE": "never-print-this"}
    before = snapshot(tmp_path)
    assert cli.main(["sync", "claude", "--no-plugins", "--dry-run"]) == 0
    assert "nothing to change" in capsys.readouterr().out
    assert snapshot(tmp_path) == before


def test_preview_reports_removals_modes_and_plugins_without_vendor_mutations(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    monkeypatch.setattr(sync.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(sync, "_list_plugins", lambda *_: {})
    monkeypatch.setattr(sync.subprocess, "run", lambda *a, **k: pytest.fail("vendor mutation"))
    sync.sync_claude(tmp_path, deploy_skills=True, deploy_plugins=False)
    retired = tmp_path / ".claude/skills/archify/SKILL.md"
    retired.parent.mkdir()
    retired.write_text("retired")
    private = tmp_path / ".claude.json"
    private.chmod(0o644)
    before = snapshot(tmp_path)
    assert cli.main(["sync", "claude", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "REMOVE ~/.claude/skills/archify" in output
    assert "MODE ~/.claude.json" in output
    assert "PLUGIN claude" in output
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("vendor", ["claude", "pi"])
def test_drift_checks_required_denials_and_projection_without_repair(
    tmp_path, monkeypatch, capsys, vendor
):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/bin/{name}")
    deploy = sync.sync_claude if vendor == "claude" else sync.sync_pi
    deploy(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")
    assert drift.drift(tmp_path, (vendor,), verify_plugins=False, profile="work") == 0
    capsys.readouterr()
    policy = tmp_path / ".config/workbench/hard-deny-paths"
    policy.write_text("# required entries removed\n")
    projection = tmp_path / f".local/share/workbench/native/harness/{vendor}/.{vendor}"
    if vendor == "pi":
        projection /= "agent"
    settings = projection / "settings.json"
    settings.write_text("{}\n")
    before = snapshot(tmp_path)
    assert drift.drift(tmp_path, (vendor,), verify_plugins=False, profile="work") == 1
    output = capsys.readouterr().out
    assert "required exclusions" in output
    assert "projection" in output
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("vendor", ["claude", "codex", "pi"])
def test_preview_projection_bytes_match_real_sync(tmp_path, vendor):
    deploy = {"claude": sync.sync_claude, "codex": sync.sync_codex, "pi": sync.sync_pi}[vendor]
    with preview_sync() as plan:
        deploy(tmp_path, deploy_skills=True, deploy_plugins=False)
    assert list(tmp_path.iterdir()) == []
    deploy(tmp_path, deploy_skills=True, deploy_plugins=False)
    for path, content in plan.files.items():
        assert path.read_text() == content, str(path.relative_to(tmp_path))


def test_preview_does_not_harden_or_read_transcript_contents(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    transcript = tmp_path / ".pi/agent/sessions/example/session.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text("private conversation")
    transcript.chmod(0o644)
    before = snapshot(tmp_path)
    original = Path.read_text

    def read(path, *args, **kwargs):
        assert path != transcript
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    with preview_sync() as plan:
        sync.sync_pi(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")
    assert plan.operations[transcript] == "MODE"
    assert snapshot(tmp_path) == before
    assert cli.main(["sync", "pi", "--no-plugins", "--profile", "work"]) == 0
    assert transcript.stat().st_mode & 0o777 == 0o600
    assert "updated ~/.pi/agent/sessions/example/session.jsonl" in capsys.readouterr().out


@pytest.mark.parametrize(
    "surface", ["private-paths", "manifest", "shell", "missing-projection", "symlink"]
)
def test_drift_checks_each_projection_and_policy_gap_independently(
    tmp_path, monkeypatch, capsys, surface
):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/bin/{name}")
    sync.sync_claude(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")
    data = tmp_path / core.DATA_REL / "native/harness"
    if surface == "private-paths":
        (tmp_path / ".config/workbench/private-paths").write_text("# missing entries\n")
    elif surface in {"manifest", "shell"}:
        path = data / "manifest.json"
        value = json.loads(path.read_text())
        value["shell" if surface == "shell" else "claude"]["read"].append(
            str(tmp_path / "unapproved")
        )
        path.write_text(json.dumps(value))
    elif surface == "symlink":
        policy = tmp_path / ".config/workbench/private-paths"
        target = tmp_path / "untrusted-policy"
        target.write_text(policy.read_text())
        policy.unlink()
        policy.symlink_to(target)
    else:
        (data / "claude/.claude/settings.json").unlink()
    before = snapshot(tmp_path)
    assert drift.drift(tmp_path, ("claude",), verify_plugins=False, profile="work") == 1
    assert "DRIFT" in capsys.readouterr().out
    assert snapshot(tmp_path) == before


def test_drift_flags_retired_pi_state(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(drift.shutil, "which", lambda name: f"/usr/bin/{name}")
    sync.sync_pi(tmp_path, deploy_skills=True, deploy_plugins=False, profile="work")
    retired = tmp_path / core.RETIRED_PI_STATE_PATHS[0]
    retired.mkdir(parents=True)
    assert drift.drift(tmp_path, ("pi",), verify_plugins=False, profile="work") == 1
    assert "retired Pi state" in capsys.readouterr().out
