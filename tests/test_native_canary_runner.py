"""The native canary entrypoint never reuses a real home or enrolls logins."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workbench.core import ROOT, WorkbenchError


def runner():
    spec = importlib.util.spec_from_file_location(
        "native_canary_runner", ROOT / "scripts/native_canary.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_refuses_unsupported_host_before_preparing(monkeypatch):
    module = runner()
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.native, "prepare", lambda *_: pytest.fail("unexpected preparation"))
    with pytest.raises(WorkbenchError, match="require macOS"):
        module.run([])


def test_runner_refuses_missing_tools(monkeypatch):
    module = runner()
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    with pytest.raises(WorkbenchError, match="require node"):
        module.run([])


def test_runner_prepares_fresh_home_and_propagates_test_failure(monkeypatch):
    module = runner()
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/bin/{name}")
    prepared = []

    def prepare(home):
        assert home.is_relative_to("/private/tmp")
        assert list(home.iterdir()) == []
        assert home.stat().st_mode & 0o777 == 0o700
        prepared.append(home)
        tools = home / ".local/share/workbench/native/tools.json"
        tools.parent.mkdir(parents=True)
        tools.write_text(json.dumps({"browser": "/host/browser", "agents": {"pi": {}}}))

    def execute(command, *, cwd, env, check):
        assert cwd == ROOT
        assert env["WORKBENCH_NATIVE_CANARY_HOME"] == str(prepared[0])
        assert env["TMPDIR"] == str(prepared[0])
        tools = json.loads((prepared[0] / ".local/share/workbench/native/tools.json").read_text())
        assert tools == {"browser": None, "agents": {"pi": {}}}
        assert command[-2:] == ["-k", "denials"]
        assert Path(command[command.index("--basetemp") + 1]).is_relative_to(prepared[0])
        assert not check
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(module.native, "prepare", prepare)
    monkeypatch.setattr(module.subprocess, "run", execute)
    assert module.run(["-k", "denials"]) == 1
    assert not prepared[0].exists()


def test_runner_cannot_target_existing_home_or_override_pytest_scratch():
    with pytest.raises(SystemExit):
        runner().run(["--basetemp", "/tmp/existing"])
