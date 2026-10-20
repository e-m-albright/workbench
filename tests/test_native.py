"""Native preparation resolves tools once, outside restricted sessions."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from workbench import core, native


def test_prepare_copies_a_protected_runtime_without_copying_credentials(tmp_path, monkeypatch):
    home = tmp_path / "home"
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("node", "npm", "codex", "claude", "pi"):
        (tools / name).write_text("synthetic binary")
    monkeypatch.setattr(native.shutil, "which", lambda name: str(tools / name))
    calls = []
    monkeypatch.setattr(
        native.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    monkeypatch.setattr(native, "patch_forge", lambda runtime: None)
    native.prepare(home)
    runtime = home / ".local/share/workbench"
    assert (runtime / "shell/native-sandbox.py").is_file()
    assert (runtime / "shell/native-sandbox.mjs").is_file()
    manifest = json.loads((runtime / "native/harness/manifest.json").read_text())
    assert set(manifest) == {"pi", "claude", "codex", "shell"}
    assert all(manifest[vendor]["files"] for vendor in ("pi", "claude", "codex"))
    assert (runtime / "native/tools.json").is_file()
    assert not (home / ".codex").exists()
    assert not (home / ".pi").exists()
    private_paths = (home / ".config/workbench/private-paths").read_text().splitlines()
    assert core.MEETING_RECORDINGS_PRIVATE_PATH in private_paths
    assert core.LEGACY_VAULT_PRIVATE_PATH not in private_paths
    hard_deny = (home / ".config/workbench/hard-deny-paths").read_text().splitlines()
    assert "/**/confidential" in hard_deny
    assert "~/Library/CloudStorage/GoogleDrive*" in hard_deny
    assert calls[0][0][0][1:3] == ["ci", "--ignore-scripts"]


def test_authorize_copies_only_model_credentials_and_preserves_refreshes(tmp_path, monkeypatch):
    home = tmp_path / "home"
    for relative, value in (
        (".codex/auth.json", {"auth_mode": "chatgpt", "tokens": {"access_token": "fake"}}),
        (
            ".pi/agent/auth.json",
            {
                "openai-codex": {"type": "oauth", "access": "fake"},
                "google": {"type": "api_key", "key": "!do-not-run"},
            },
        ),
    ):
        path = home / relative
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(value))
        path.chmod(0o600)
    keychain = {
        "claudeAiOauth": {"accessToken": "fake-model"},
        "mcpOAuth": {"private-connector": "must-not-copy"},
    }
    monkeypatch.setattr(
        native.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(keychain)),
    )
    assert native.authorize(home) == {"codex": True, "pi": True, "claude": True}
    store = home / ".local/share/workbench/model-auth"
    assert json.loads((store / "claude/.credentials.json").read_text()) == {
        "claudeAiOauth": keychain["claudeAiOauth"]
    }
    assert set(json.loads((store / "pi/auth.json").read_text())) == {"openai-codex"}
    credential = store / "codex/auth.json"
    credential.write_text('{"refreshed": true}')
    native.authorize(home)
    assert json.loads(credential.read_text()) == {"refreshed": True}
    assert credential.stat().st_mode & 0o077 == 0


def test_authorize_does_not_treat_empty_claude_tokens_as_a_login(tmp_path, monkeypatch):
    home = tmp_path / "home"
    value = {"claudeAiOauth": {"accessToken": "", "refreshToken": "", "scopes": ["user:inference"]}}
    monkeypatch.setattr(
        native.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stdout=json.dumps(value)),
    )
    assert native.authorize(home)["claude"] is False
    destination = home / ".local/share/workbench/model-auth/claude/.credentials.json"
    assert not destination.exists()
    destination.parent.mkdir(parents=True, mode=0o700)
    destination.write_text(json.dumps(value))
    destination.chmod(0o600)
    value["claudeAiOauth"]["accessToken"] = "synthetic-restored-login"
    assert native.authorize(home)["claude"] is False
    assert json.loads(destination.read_text()) != value
    assert native.authorize(home, vendor="claude", replace=True)["claude"] is True
    assert json.loads(destination.read_text()) == value


def test_concurrent_prepare_cannot_publish_readiness_during_failed_install(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setattr(native, "_binary", lambda name: tmp_path / name)
    monkeypatch.setattr(native.shutil, "which", lambda name: None)
    monkeypatch.setattr(native.subprocess, "run", lambda *args, **kwargs: None)

    def patch(runtime):
        # A second preparer must be rejected before it can publish a manifest
        # while the first still owns a mutable, possibly unpatched installation.
        monkeypatch.setattr(native, "patch_forge", lambda runtime: None)
        with pytest.raises(core.WorkbenchError, match="already being prepared"):
            native.prepare(home)
        raise subprocess.CalledProcessError(1, "interrupted installation")

    monkeypatch.setattr(native, "patch_forge", patch)
    with pytest.raises(subprocess.CalledProcessError):
        native.prepare(home)
    assert not (home / ".local/share/workbench/native/tools.json").exists()
    # Failure releases the lock, so a subsequent preparation can repair it.
    native.prepare(home)
    assert (home / ".local/share/workbench/native/tools.json").is_file()


@pytest.mark.parametrize("failure", ["install", "patch", "probe"])
def test_failed_reprepare_invalidates_previous_readiness(tmp_path, monkeypatch, failure):

    home = tmp_path / "home"
    runtime = home / ".local/share/workbench/native"
    runtime.mkdir(parents=True)
    manifest = runtime / "tools.json"
    manifest.write_text('{"previously": "ready"}')
    monkeypatch.setattr(native, "_binary", lambda name: tmp_path / name)
    monkeypatch.setattr(native.shutil, "which", lambda name: None)

    def run(command, **kwargs):
        if (failure == "install" and command[1] == "ci") or (
            failure == "probe" and command[1].endswith("verify-forge.cjs")
        ):
            raise subprocess.CalledProcessError(1, command)

    def patch(runtime):
        if failure == "patch":
            raise subprocess.CalledProcessError(1, "patch")

    monkeypatch.setattr(native.subprocess, "run", run)
    monkeypatch.setattr(native, "patch_forge", patch)
    with pytest.raises(subprocess.CalledProcessError):
        native.prepare(home)
    assert not manifest.exists()


def test_reenroll_is_explicit_vendor_scoped_and_backs_up_existing_login(tmp_path, monkeypatch):
    home = tmp_path / "home"
    source = home / ".codex/auth.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"tokens":{"access_token":"new-synthetic"}}')
    source.chmod(0o600)
    destination = home / ".local/share/workbench/model-auth/codex/auth.json"
    destination.parent.mkdir(parents=True, mode=0o700)
    destination.write_text('{"tokens":{"access_token":"old-synthetic"}}')
    destination.chmod(0o600)
    monkeypatch.setattr(native.subprocess, "run", lambda *a, **kw: pytest.fail("other vendor read"))
    old, new = destination.read_bytes(), source.read_bytes()
    assert native.authorize(home, vendor="codex") == {"codex": True}
    assert destination.read_bytes() == old
    assert native.authorize(home, vendor="codex", replace=True) == {"codex": True}
    assert json.loads(destination.read_bytes()) == json.loads(new)
    assert source.read_bytes() == new
    backups = list((home / ".local/state/workbench/backups").glob("model-login-*/codex/auth.json"))
    assert len(backups) == 1 and backups[0].read_bytes() == old
    assert backups[0].stat().st_mode & 0o077 == 0
    assert backups[0].parent.stat().st_mode & 0o077 == 0


def test_reenroll_invalid_source_preserves_existing_login(tmp_path):
    home = tmp_path / "home"
    source = home / ".codex/auth.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"unexpected":"not-a-login"}')
    source.chmod(0o600)
    destination = home / ".local/share/workbench/model-auth/codex/auth.json"
    destination.parent.mkdir(parents=True, mode=0o700)
    destination.write_text('{"tokens":{"access_token":"existing-synthetic"}}')
    destination.chmod(0o600)
    old = destination.read_bytes()
    with pytest.raises(core.WorkbenchError, match="No reusable"):
        native.authorize(home, vendor="codex", replace=True)
    assert destination.read_bytes() == old
    assert not (home / ".local/state/workbench/backups").exists()


@pytest.mark.parametrize(
    "relative",
    [
        "Desktop/node",
        "Downloads/node",
        "code/public/tool/bin/node",
        ".local/share/workbench/agent-state/node",
    ],
)
def test_bootstrap_refuses_managed_writable_locations(tmp_path, monkeypatch, relative):
    home = tmp_path / "home"
    unsafe = home / relative
    unsafe.parent.mkdir(parents=True)
    unsafe.write_text("synthetic")
    monkeypatch.setattr(native, "_binary", lambda name: unsafe)
    with pytest.raises(core.WorkbenchError, match="bootstrap"):
        native.prepare(home)
    assert not (home / ".local/share/workbench/native/tools.json").exists()


def test_status_reports_presence_without_reading_credentials_or_history(tmp_path, monkeypatch):
    home = tmp_path / "home"
    token = home / ".local/share/workbench/model-auth/codex/auth.json"
    token.parent.mkdir(parents=True)
    token.write_text("sensitive malformed text must never be read")
    token.chmod(0o600)
    monkeypatch.setattr(native, "_credential_json", lambda *a: pytest.fail("credential read"))
    status = native.status(home, vendor="codex", cwd=tmp_path)
    assert status["agents"]["codex"]["login"] == "present; authentication unverified"
    assert status["agents"]["codex"]["executable_ready"] is False
    assert "sensitive" not in json.dumps(status)
    assert status["state_path"].endswith("/home")


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "public-mode"])
def test_reenroll_rejects_unsafe_source_without_replacing_login(tmp_path, kind):
    home = tmp_path / "home"
    source = home / ".codex/auth.json"
    source.parent.mkdir(parents=True)
    original = tmp_path / "source-login"
    original.write_text('{"tokens":{"access_token":"synthetic"}}')
    original.chmod(0o600)
    if kind == "symlink":
        source.symlink_to(original)
    elif kind == "hardlink":
        source.hardlink_to(original)
    else:
        source.write_bytes(original.read_bytes())
        source.chmod(0o644)
    with pytest.raises((core.WorkbenchError, OSError)):
        native.authorize(home, vendor="codex", replace=True)
    assert not (home / ".local/share/workbench/model-auth/codex/auth.json").exists()


def test_native_cli_enrollment_is_separate_and_never_claims_verified_login(
    tmp_path, monkeypatch, capsys
):
    from workbench import cli

    calls = []
    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    monkeypatch.setattr(native, "prepare", lambda: pytest.fail("dependency install"))
    monkeypatch.setattr(
        native, "authorize", lambda home, **kwargs: calls.append((home, kwargs)) or {"codex": True}
    )
    assert cli.main(["native", "authorize", "codex", "--replace"]) == 0
    assert calls == [(tmp_path, {"vendor": "codex", "replace": True})]
    assert "enrolled; authentication unverified" in capsys.readouterr().out


def test_status_cli_reports_synthetic_state_without_launching_tools(tmp_path, monkeypatch, capsys):
    from workbench import cli

    monkeypatch.setenv("WORKBENCH_HOME", str(tmp_path))
    monkeypatch.setattr(native, "status", lambda home, **kwargs: {"login": "absent"})
    assert cli.main(["native", "status", "codex"]) == 0
    assert json.loads(capsys.readouterr().out) == {"login": "absent"}


def test_bootstrap_refuses_loader_installation_symlink_into_scratch(tmp_path, monkeypatch):
    home = tmp_path / "home"
    scratch = home / "Downloads"
    scratch.mkdir(parents=True)
    share = home / ".local/share"
    share.mkdir(parents=True)
    (share / "workbench").symlink_to(scratch, target_is_directory=True)
    monkeypatch.setattr(native, "_binary", lambda name: tmp_path / "tools" / name)
    with pytest.raises(core.WorkbenchError, match="bootstrap"):
        native.prepare(home)
    assert list(scratch.iterdir()) == []


def test_explicit_reenroll_recovers_corrupt_managed_login_and_backs_it_up(tmp_path):
    home = tmp_path / "home"
    source = home / ".codex/auth.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"tokens":{"access_token":"synthetic-valid"}}')
    source.chmod(0o600)
    destination = home / ".local/share/workbench/model-auth/codex/auth.json"
    destination.parent.mkdir(parents=True, mode=0o700)
    destination.write_text("interrupted previous write")
    destination.chmod(0o600)
    assert native.authorize(home, vendor="codex", replace=True) == {"codex": True}
    backups = list((home / ".local/state/workbench/backups").glob("model-login-*/codex/auth.json"))
    assert backups[0].read_text() == "interrupted previous write"
    assert json.loads(destination.read_text()) == json.loads(source.read_text())


def native_claude(home, version="2.1.304", root=None):
    versions = (root or home / ".local/share") / "claude/versions"
    versions.mkdir(parents=True, exist_ok=True)
    (versions / version).write_text("synthetic native binary")
    (versions / version).chmod(0o755)
    launcher = home / ".local/bin/claude"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.unlink(missing_ok=True)
    launcher.symlink_to(versions / version)
    return launcher, versions


def prepare_offline(monkeypatch, tools):
    monkeypatch.setattr(
        native.shutil,
        "which",
        lambda name: str(tools / name) if (tools / name).exists() else None,
    )
    monkeypatch.setattr(native.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(native, "patch_forge", lambda runtime: None)


def test_prepare_prefers_native_claude_and_survives_auto_update(tmp_path, monkeypatch):
    home = (tmp_path / "home").resolve()
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("node", "npm", "claude"):
        (tools / name).write_text("synthetic npm copy")
    launcher, versions = native_claude(home)
    prepare_offline(monkeypatch, tools)
    native.prepare(home)
    manifest = json.loads((home / ".local/share/workbench/native/tools.json").read_text())
    # The stable launcher, not the versioned file or the PATH copy, is recorded.
    assert manifest["agents"]["claude"] == {"command": [str(launcher)], "read": [str(versions)]}
    native_claude(home, "2.1.305")
    (versions / "2.1.304").unlink()
    assert native.status(home, vendor="claude", cwd=tmp_path)["agents"]["claude"][
        "executable_ready"
    ]


def test_prepare_uses_path_claude_when_no_native_install(tmp_path, monkeypatch):
    home = tmp_path / "home"
    tools = tmp_path / "tools"
    (tools / "lib/claude-code").mkdir(parents=True)
    (tools / "lib/claude-code/package.json").write_text("{}")
    (tools / "lib/claude-code/cli.js").write_text("synthetic npm copy")
    for name in ("node", "npm"):
        (tools / name).write_text("synthetic")
    (tools / "claude").symlink_to(tools / "lib/claude-code/cli.js")
    prepare_offline(monkeypatch, tools)
    native.prepare(home)
    manifest = json.loads((home / ".local/share/workbench/native/tools.json").read_text())
    package = (tools / "lib/claude-code").resolve()
    assert manifest["agents"]["claude"] == {
        "command": [str(package / "cli.js")],
        "read": [str(package)],
    }


def test_prepare_refuses_native_claude_versions_in_writable_scratch(tmp_path, monkeypatch):
    home = tmp_path / "home"
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("node", "npm"):
        (tools / name).write_text("synthetic")
    native_claude(home, root=home / "Downloads")
    prepare_offline(monkeypatch, tools)
    with pytest.raises(core.WorkbenchError, match="bootstrap"):
        native.prepare(home)
    assert not (home / ".local/share/workbench/native/tools.json").exists()


def test_prepare_reports_a_broken_native_claude_launcher(tmp_path, monkeypatch):
    home = tmp_path / "home"
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("node", "npm"):
        (tools / name).write_text("synthetic")
    _, versions = native_claude(home)
    (versions / "2.1.304").unlink()
    prepare_offline(monkeypatch, tools)
    with pytest.raises(core.WorkbenchError, match="reinstall Claude Code"):
        native.prepare(home)
