"""Native preparation resolves tools once, outside restricted sessions."""

import json
from types import SimpleNamespace

from workbench import native


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
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(value))
    destination.chmod(0o600)
    value["claudeAiOauth"]["accessToken"] = "synthetic-restored-login"
    assert native.authorize(home)["claude"] is True
    assert json.loads(destination.read_text()) == value
