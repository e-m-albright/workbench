"""Claude conversation storage follows the project across managed/native launches."""

import importlib.util
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"


def launcher():
    spec = importlib.util.spec_from_file_location("claude_sessions", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def plan(tmp_path):
    home = tmp_path / "home"
    cwd = home / "code/project/subdir"
    cwd.mkdir(parents=True)
    (cwd.parent / ".git").mkdir()
    policy = home / ".config/workbench"
    policy.mkdir(parents=True)
    (policy / "private-paths").write_text("")
    (policy / "hard-deny-paths").write_text("~/private/**\n")
    manifest = home / ".local/share/workbench/native/harness/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"claude": {"files": [], "links": [], "read": []}}))
    tools = {
        "node": "/usr/bin/node",
        "agents": {"claude": {"command": ["/usr/bin/agent"], "read": []}},
    }
    return home, cwd, launcher().build_plan(cwd, home, tools, "claude", "hosted", [])


def test_only_selected_claude_namespace_is_shared(plan):
    home, cwd, value = plan
    key = re.sub(r"[^a-zA-Z0-9]", "-", str(cwd))
    target = home / ".claude/projects" / key
    assert value["claude_sessions"]["target"] == str(target)
    for operation in ("allowRead", "allowWrite"):
        grants = value["policy"]["filesystem"][operation]
        assert str(target) in grants
        assert str(home / ".claude") not in grants
        assert str(home / ".claude/projects") not in grants
    assert value["resume_hint"] is None


def test_existing_managed_and_native_conversations_merge_without_reading_content(plan):
    home, _, value = plan
    source = Path(value["claude_sessions"]["path"])
    target = Path(value["claude_sessions"]["target"])
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "managed.jsonl").write_text("synthetic-managed")
    (target / "native.jsonl").write_text("synthetic-native")
    (source / "sessions-index.json").write_text("managed-cache")
    (target / "sessions-index.json").write_text("native-cache")
    module = launcher()
    module.initialize_home(value, home)
    assert source.is_symlink() and source.readlink() == target
    assert (target / "managed.jsonl").read_text() == "synthetic-managed"
    assert (source / "native.jsonl").read_text() == "synthetic-native"
    assert not (target / "sessions-index.json").exists()
    assert len(list(target.glob(".workbench-index-*.bak"))) == 2
    module.initialize_home(value, home)
    assert len(list(target.glob("*.jsonl"))) == 2


def test_conflicting_transcripts_are_preserved(plan):
    home, _, value = plan
    source = Path(value["claude_sessions"]["path"])
    target = Path(value["claude_sessions"]["target"])
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "same.jsonl").write_text("managed")
    (target / "same.jsonl").write_text("native")
    with pytest.raises(ValueError, match="collision"):
        launcher().initialize_home(value, home)
    assert (source / "same.jsonl").read_text() == "managed"
    assert (target / "same.jsonl").read_text() == "native"


def test_writer_reopening_path_during_first_migration_preserves_both_copies(plan, monkeypatch):
    home, _, value = plan
    source = Path(value["claude_sessions"]["path"])
    target = Path(value["claude_sessions"]["target"])
    source.mkdir(parents=True)
    (source / "session.jsonl").write_text("old-record")
    module = launcher()
    unlink = os.unlink

    def reopen_after_unlink(name, **kwargs):
        unlink(name, **kwargs)
        if name == "session.jsonl":
            (source / name).write_text("new-record")

    monkeypatch.setattr(module.os, "unlink", reopen_after_unlink)
    with pytest.raises(ValueError, match="Stop managed Claude sessions"):
        module.initialize_home(value, home)
    assert (source / "session.jsonl").read_text() == "new-record"
    assert (target / "session.jsonl").read_text() == "old-record"


@pytest.mark.parametrize("location", ["source", "target", "host-parent", "entry"])
def test_session_migration_rejects_planted_links(plan, tmp_path, location):
    home, _, value = plan
    source = Path(value["claude_sessions"]["path"])
    target = Path(value["claude_sessions"]["target"])
    outside = tmp_path / "outside"
    outside.mkdir()
    if location == "host-parent":
        (home / ".claude").symlink_to(outside)
    else:
        source.parent.mkdir(parents=True)
        target.parent.mkdir(parents=True)
        if location == "entry":
            source.mkdir()
            (source / "private.jsonl").symlink_to(outside / "private")
        else:
            (source if location == "source" else target).symlink_to(outside)
    with pytest.raises(ValueError):
        launcher().initialize_home(value, home)
    assert list(outside.iterdir()) == []


def test_concurrent_startup_and_interrupted_file_move_recover(plan):
    home, _, value = plan
    source = Path(value["claude_sessions"]["path"])
    target = Path(value["claude_sessions"]["target"])
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    (source / "session.jsonl").write_text("synthetic")
    (target / "session.jsonl").hardlink_to(source / "session.jsonl")
    module = launcher()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: module.initialize_home(value, home), range(2)))
    assert source.is_symlink()
    assert (target / "session.jsonl").read_text() == "synthetic"


def test_unverified_long_namespace_keeps_isolation():
    module = launcher()
    assert module.claude_project_key(Path("/home/dev/my_project")) == "-home-dev-my-project"
    assert module.claude_project_key(Path("/" + "a" * 201)) is None
