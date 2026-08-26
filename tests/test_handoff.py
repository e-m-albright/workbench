from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "agents/skills/handoff/scripts/handoff.py"


def run_handoff(state_home: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "XDG_STATE_HOME": str(state_home)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_save_creates_private_markdown_artifact(tmp_path: Path) -> None:
    result = run_handoff(
        tmp_path,
        "save",
        "--project",
        "dotfiles",
        "--repo",
        "/home/dev/dotfiles",
        stdin="## Context snapshot\n\n### Goal\n- Continue the change.\n",
    )

    assert result.returncode == 0, result.stderr
    artifact = Path(result.stdout.strip())
    assert artifact.parent == tmp_path / "workbench/handoffs/ready"
    assert artifact.stat().st_mode & 0o777 == 0o600
    assert artifact.parent.stat().st_mode & 0o777 == 0o700
    assert artifact.parent.parent.stat().st_mode & 0o777 == 0o700
    text = artifact.read_text()
    assert 'project: "dotfiles"' in text
    assert 'repository: "/home/dev/dotfiles"' in text
    assert "status: ready" in text
    assert "## Context snapshot" in text


def test_latest_then_consume_moves_artifact_without_destroying_it(tmp_path: Path) -> None:
    saved = run_handoff(
        tmp_path,
        "save",
        "--project",
        "dotfiles",
        stdin="## Context snapshot\n",
    )
    artifact = Path(saved.stdout.strip())

    latest = run_handoff(tmp_path, "latest", "--project", "dotfiles")
    assert latest.returncode == 0, latest.stderr
    assert Path(latest.stdout.strip()) == artifact

    consumed = run_handoff(tmp_path, "consume", str(artifact))
    assert consumed.returncode == 0, consumed.stderr
    destination = Path(consumed.stdout.strip())
    assert not artifact.exists()
    assert destination.parent == tmp_path / "workbench/handoffs/consumed"
    assert destination.exists()
    assert "status: consumed" in destination.read_text()
    assert "consumed_at:" in destination.read_text()


def test_consume_rejects_paths_outside_ready_queue(tmp_path: Path) -> None:
    unrelated = tmp_path / "unrelated.md"
    unrelated.write_text("keep me")

    result = run_handoff(tmp_path, "consume", str(unrelated))

    assert result.returncode != 0
    assert "ready handoff queue" in result.stderr
    assert unrelated.read_text() == "keep me"


def test_prune_only_removes_old_consumed_artifacts(tmp_path: Path) -> None:
    saved = run_handoff(
        tmp_path,
        "save",
        "--project",
        "dotfiles",
        stdin="## Context snapshot\n",
    )
    ready = Path(saved.stdout.strip())
    consumed = run_handoff(tmp_path, "consume", str(ready))
    archived = Path(consumed.stdout.strip())
    os.utime(archived, (1, 1))

    result = run_handoff(tmp_path, "prune", "--older-than-days", "7")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "1"
    assert not archived.exists()
