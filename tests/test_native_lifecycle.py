"""A guardian must establish signal containment before cleanup can target all peers."""

import importlib.util
import json
import os
import signal
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"
spec = importlib.util.spec_from_file_location("native_lifecycle", SCRIPT)
assert spec and spec.loader
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def arguments(*, guarded=True):
    profile = "(version 1)\n(deny default)\n"
    if guarded:
        profile += launcher.SESSION_SIGNAL_GUARD
    return [
        "env",
        "EXAMPLE=a=b",
        "/usr/bin/sandbox-exec",
        "-p",
        profile,
        "/bin/bash",
        "-c",
        "exit 37",
    ]


def test_session_refuses_missing_signal_guard_before_cleanup(monkeypatch):
    monkeypatch.setattr(launcher.os, "kill", lambda *_: pytest.fail("unsafe cleanup"))
    monkeypatch.setattr(launcher, "apply_profile", lambda *_: pytest.fail("unsafe profile"))
    with pytest.raises(ValueError, match="signal isolation guard"):
        launcher.apply_session(arguments(guarded=False))


def test_session_refuses_regular_file_status_channel(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher.os, "kill", lambda *_: pytest.fail("unsafe cleanup"))
    monkeypatch.setattr(launcher, "apply_profile", lambda *_: pytest.fail("unsafe profile"))
    with (
        (tmp_path / "ordinary-file").open("wb") as stream,
        pytest.raises(ValueError, match="private supervisor status pipe"),
    ):
        launcher.apply_session(arguments(), stream.fileno())


def test_failed_sandbox_application_never_spawns_or_signals(monkeypatch):
    def fail(_profile):
        raise ValueError("application failed")

    monkeypatch.setattr(launcher, "apply_profile", fail)
    monkeypatch.setattr(launcher.os, "kill", lambda *_: pytest.fail("unsafe cleanup"))
    monkeypatch.setattr(
        launcher.subprocess, "Popen", lambda *_a, **_kw: pytest.fail("unsafe spawn")
    )
    reader, writer = os.pipe()
    try:
        with pytest.raises(ValueError, match="application failed"):
            launcher.apply_session(arguments(), writer)
    finally:
        os.close(reader)
        os.close(writer)


def test_closed_status_pipe_still_cleans_after_vendor_failure(monkeypatch):
    monkeypatch.setattr(launcher, "apply_profile", lambda _profile: None)
    monkeypatch.setattr(signal, "signal", lambda *_: None)

    def failed_spawn(*_args, **_kwargs):
        raise FileNotFoundError("synthetic missing vendor")

    def cleaned(pid, sig):
        assert pid == -1 and sig == signal.SIGKILL
        raise SystemExit("synthetic guardian cleanup")

    monkeypatch.setattr(launcher.subprocess, "Popen", failed_spawn)
    monkeypatch.setattr(launcher.os, "kill", cleaned)
    reader, writer = os.pipe()
    os.close(reader)
    try:
        with pytest.raises(SystemExit, match="synthetic guardian cleanup"):
            launcher.apply_session(arguments(), writer)
    finally:
        os.close(writer)


@pytest.mark.parametrize("vendor_status, expected", [(37, b"37\n"), (-15, b"143\n")])
def test_session_privately_reports_exit_then_cleans_same_sandbox(
    monkeypatch, vendor_status, expected
):
    calls = []
    monkeypatch.setattr(launcher, "apply_profile", lambda profile: calls.append("applied"))
    monkeypatch.setattr(signal, "signal", lambda *_: None)

    def spawn(command, **kwargs):
        assert calls == ["applied"]
        assert command == ["/bin/bash", "-c", "exit 37"]
        assert kwargs["env"]["EXAMPLE"] == "a=b"
        assert kwargs["close_fds"] is True
        calls.append("spawned")
        return SimpleNamespace(wait=lambda: vendor_status)

    def killed(pid, sig):
        assert pid == -1 and sig == signal.SIGKILL
        calls.append("cleaned")
        raise SystemExit("synthetic guardian exit")

    monkeypatch.setattr(launcher.subprocess, "Popen", spawn)
    monkeypatch.setattr(launcher.os, "kill", killed)
    reader, writer = os.pipe()
    try:
        with pytest.raises(SystemExit, match="synthetic guardian exit"):
            launcher.apply_session(arguments(), writer)
        assert os.read(reader, 100) == expected
        assert calls == ["applied", "spawned", "cleaned"]
    finally:
        os.close(reader)


def test_supervisor_requires_private_exit_report_and_guardian_sigkill():
    source = SCRIPT.with_suffix(".mjs").read_text()
    function = (
        "function completion(process) {"
        + source.split("function completion(process) {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    cases = [
        (["3", "7\n"], None, "SIGKILL", 37),
        (["0\n"], None, "SIGKILL", 0),
        ([], 0, None, 1),
        (["0\n"], None, "SIGTERM", 1),
        (["garbage\n"], None, "SIGKILL", 1),
        (["37"], None, "SIGKILL", 1),
        (["999\n"], None, "SIGKILL", 1),
        (["0\n37\n"], None, "SIGKILL", 1),
    ]
    probe = (
        'import { EventEmitter } from "node:events";\n'
        + function
        + "const results = [];\n"
        + f"for (const [chunks, code, signal] of {json.dumps(cases)}) {{\n"
        + "  const child = new EventEmitter();\n"
        + "  child.stdio = [null, null, null, new EventEmitter()];\n"
        + "  const result = completion(child);\n"
        + '  for (const chunk of chunks) child.stdio[3].emit("data", Buffer.from(chunk));\n'
        + '  child.emit("close", code, signal);\n'
        + "  results.push(await result);\n"
        + "}\nconsole.log(JSON.stringify(results));\n"
    )
    result = subprocess.run(
        ["node", "--input-type=module"],
        input=probe,
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout) == [case[3] for case in cases]
