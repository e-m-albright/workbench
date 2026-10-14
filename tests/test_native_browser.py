"""Fresh browser identity must be established before any managed model input."""

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"
spec = importlib.util.spec_from_file_location("browser_sandbox", SOURCE)
assert spec and spec.loader
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)
UUID = "12345678-1234-1234-1234-123456789abc"
ENDPOINT = f"ws://127.0.0.1:43210/devtools/browser/{UUID}"


@pytest.fixture
def browser_env(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_AGENT_AUTHORITY", "managed")
    monkeypatch.setenv("WORKBENCH_BROWSER_PORT", "43210")
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("AGENT_BROWSER_PROFILE", str(tmp_path / "browser-profile"))
    calls = []
    monkeypatch.setattr(os, "execvpe", lambda *args: calls.append(args))
    return tmp_path / "browser-profile", calls


def fake_browser(monkeypatch, profile, *, content=None, reported=ENDPOINT, returncode=0):
    def run(command, **kwargs):
        assert kwargs["capture_output"]
        assert kwargs["timeout"] <= 30
        if "open" in command and content is not None:
            (profile / "DevToolsActivePort").write_text(content)
        return subprocess.CompletedProcess(command, returncode, reported + "\n", "synthetic")

    monkeypatch.setattr(subprocess, "run", run)


def test_browser_pins_verified_uuid_before_vendor_exec(browser_env, monkeypatch):
    profile, calls = browser_env
    fake_browser(monkeypatch, profile, content=f"43210\n/devtools/browser/{UUID}")
    sandbox.browser_session(["vendor", "--mode", "rpc"])
    assert (profile.parent / "browser").stat().st_mode & 0o777 == 0o700
    assert calls[0][:2] == ("vendor", ["vendor", "--mode", "rpc"])
    assert calls[0][2]["AGENT_BROWSER_CDP"] == ENDPOINT


@pytest.mark.parametrize(
    "content,reported",
    [
        (None, ENDPOINT),
        (f"43211\n/devtools/browser/{UUID}", ENDPOINT),
        ("43210\n/devtools/browser/fabricated", ENDPOINT),
        (f"43210\n/devtools/browser/{UUID}\nextra", ENDPOINT),
        ("x" * 4096, ENDPOINT),
        (f"43210\n/devtools/browser/{UUID}", ENDPOINT.replace(UUID, "other")),
    ],
)
def test_missing_or_mismatched_endpoint_never_launches_vendor(
    browser_env, monkeypatch, content, reported
):
    profile, calls = browser_env
    fake_browser(monkeypatch, profile, content=content, reported=reported)
    with pytest.raises((ValueError, OSError), match=r"browser|Browser|DevToolsActivePort"):
        sandbox.browser_session(["vendor"])
    assert calls == []


@pytest.mark.parametrize("failure", ["status", "missing_binary", "timeout"])
def test_browser_failure_never_launches_vendor(browser_env, monkeypatch, failure):
    profile, calls = browser_env
    fake_browser(monkeypatch, profile, returncode=1)
    if failure != "status":

        def fail(*_args, **_kwargs):
            if failure == "missing_binary":
                raise FileNotFoundError("browser missing")
            raise subprocess.TimeoutExpired("agent-browser", 30)

        monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises((ValueError, OSError)):
        sandbox.browser_session(["vendor"])
    assert calls == []


def test_existing_profile_is_never_deleted_or_reused(browser_env):
    profile, calls = browser_env
    profile.mkdir()
    sentinel = profile / "sentinel"
    sentinel.write_text("synthetic preserve")
    with pytest.raises((ValueError, OSError)):
        sandbox.browser_session(["vendor"])
    assert sentinel.read_text() == "synthetic preserve"
    assert calls == []


def test_endpoint_symlink_is_not_followed(browser_env, monkeypatch):
    profile, calls = browser_env
    outside = profile.parent / "outside"
    outside.write_text(f"43210\n/devtools/browser/{UUID}")

    def run(command, **_kwargs):
        (profile / "DevToolsActivePort").symlink_to(outside)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises((ValueError, OSError)):
        sandbox.browser_session(["vendor"])
    assert calls == []


@pytest.mark.parametrize(
    "missing",
    ["WORKBENCH_AGENT_AUTHORITY", "WORKBENCH_BROWSER_PORT", "TMPDIR", "AGENT_BROWSER_PROFILE"],
)
def test_missing_launch_context_fails_before_browser_or_files(browser_env, monkeypatch, missing):
    profile, calls = browser_env
    monkeypatch.delenv(missing)
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: pytest.fail("browser started"))
    with pytest.raises(ValueError):
        sandbox.browser_session(["vendor"])
    assert not profile.exists()
    assert calls == []


@pytest.mark.parametrize("kind", ["fifo", "hardlink"])
def test_endpoint_must_be_an_unshared_regular_file(browser_env, monkeypatch, kind):
    profile, calls = browser_env

    def run(command, **_kwargs):
        endpoint = profile / "DevToolsActivePort"
        if kind == "fifo":
            os.mkfifo(endpoint)
        else:
            original = profile / "other"
            original.write_text(f"43210\n/devtools/browser/{UUID}")
            endpoint.hardlink_to(original)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(ValueError, match="Invalid browser endpoint"):
        sandbox.browser_session(["vendor"])
    assert calls == []


@pytest.mark.parametrize("port", ["0", "1023", "65536", "43210extra"])
def test_invalid_port_fails_before_browser_or_profile_creation(browser_env, monkeypatch, port):
    profile, calls = browser_env
    monkeypatch.setenv("WORKBENCH_BROWSER_PORT", port)
    with pytest.raises(ValueError, match="prepared managed launch"):
        sandbox.browser_session(["vendor"])
    assert not profile.exists()
    assert calls == []


def test_profile_outside_session_scratch_is_never_touched(browser_env, monkeypatch):
    profile, calls = browser_env
    foreign = profile.parent / "foreign-profile"
    monkeypatch.setenv("AGENT_BROWSER_PROFILE", str(foreign))
    with pytest.raises(ValueError, match="prepared managed launch"):
        sandbox.browser_session(["vendor"])
    assert not foreign.exists()
    assert calls == []
