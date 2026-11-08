"""Locked upstream fixes and security probes must pass without audit exceptions."""

import json
import subprocess

import pytest

from workbench import native_dependencies as deps
from workbench.core import AGENTS


def test_runtime_pins_fixed_upstream_forge():
    manifest = json.loads((AGENTS / "shared/sandbox/package.json").read_text())
    assert manifest["overrides"]["@anthropic-ai/sandbox-runtime"]["node-forge"] == "1.4.3"


def test_audit_uses_a_fresh_install_both_probes_and_unfiltered_npm_audit(monkeypatch):
    calls = []

    def run(command, **kwargs):
        assert kwargs["check"] is True
        calls.append(command)

    monkeypatch.setattr(deps.subprocess, "run", run)
    deps.audit()
    assert calls[0] == ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
    assert calls[1][0] == "node" and calls[1][1].endswith("verify-forge.cjs")
    assert calls[2][0] == "node" and calls[2][1].endswith("verify-zod.cjs")
    assert calls[3] == ["npm", "audit", "--package-lock-only", "--ignore-scripts"]
    assert all("--unpatched" not in command for command in calls)


@pytest.mark.parametrize("stage", ["ci", "verify-forge.cjs", "verify-zod.cjs", "audit"])
def test_any_install_probe_or_audit_failure_fails_the_gate(monkeypatch, stage):
    def run(command, **kwargs):
        assert kwargs["check"] is True
        if command[1] == stage or command[1].endswith("/" + stage):
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(deps.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        deps.audit()
