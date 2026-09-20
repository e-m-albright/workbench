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


def test_documented_pi_and_browser_versions_match_managed_pins():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text()
    pi_versions = set(re.findall(r"@earendil-works/pi-coding-agent@(\d+\.\d+\.\d+)", workflow))
    assert len(pi_versions) == 1
    pi_version = pi_versions.pop()
    for path in (
        root / "docs/pi-capabilities.md",
        root / "agents/skills/pi-guide/references/tutorial.md",
    ):
        assert f"Pi {pi_version}" in path.read_text(), path

    settings = json.loads((root / "agents/pi/settings.json").read_text())
    browser_pin = next(
        package
        for package in settings["packages"]
        if package.startswith("npm:pi-agent-browser-native@")
    )
    browser_version = browser_pin.rsplit("@", 1)[1]
    for path in (root / "docs/pi-capabilities.md", root / "docs/pi-build-philosophy.md"):
        assert f"pi-agent-browser-native` {browser_version}" in path.read_text(), path


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
        "uv run --locked pip-audit --cache-dir tmp/pip-audit-cache",
        "pnpm audit",
        "npm --prefix agents/shared/sandbox audit --package-lock-only --ignore-scripts",
    ]


def test_ci_uses_the_shared_audit_recipe_with_pnpm_available():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["audit"]["steps"]
    assert any(step.get("uses", "").startswith("pnpm/action-setup@") for step in steps)
    assert [step["run"] for step in steps if "run" in step] == ["just audit"]
