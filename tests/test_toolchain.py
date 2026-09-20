"""Keep the retired runtime out of the active development toolchain."""

import json
import os
import re
import subprocess
from pathlib import Path

import yaml


def test_development_toolchain_uses_node_and_pnpm():
    root = Path(__file__).resolve().parents[1]
    package = json.loads((root / "package.json").read_text())
    assert package["packageManager"].startswith("pnpm@")
    assert package["engines"]["node"] == ">=24.20.0 <25"
    active = [
        root / "justfile",
        root / ".github/workflows/ci.yml",
        *root.glob("tests/pi-*.test.ts"),
    ]
    for path in active:
        assert not re.search(r"\bbun(?:x|:test)?\b", path.read_text(), re.IGNORECASE), path
    assert not list(root.glob("bun.lock*"))


def test_audit_runs_all_locked_dependency_surfaces(tmp_path):
    root = Path(__file__).resolve().parents[1]
    commands = tmp_path / "commands"
    binaries = tmp_path / "bin"
    binaries.mkdir()
    for name in ("uv", "pnpm", "npm"):
        binary = binaries / name
        binary.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> "$AUDIT_LOG"\n')
        binary.chmod(0o755)
    subprocess.run(
        ["just", "audit"],
        cwd=root,
        env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}", "AUDIT_LOG": str(commands)},
        check=True,
        capture_output=True,
    )
    assert commands.read_text().splitlines() == [
        "uv run --locked pip-audit",
        "pnpm audit",
        "npm --prefix agents/shared/sandbox audit --package-lock-only --ignore-scripts",
    ]


def test_ci_uses_the_shared_audit_recipe_with_pnpm_available():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["audit"]["steps"]
    assert any(step.get("uses", "").startswith("pnpm/action-setup@") for step in steps)
    assert [step["run"] for step in steps if "run" in step] == ["just audit"]
