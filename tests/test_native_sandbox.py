"""Contracts for the standalone, installed native boundary (no live services)."""

import importlib.util
import shlex
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"


def load_launcher():
    spec = importlib.util.spec_from_file_location("native_sandbox", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_admission_requires_a_real_repository_and_rejects_home(tmp_path):
    launcher = load_launcher()
    with pytest.raises(ValueError, match="repository"):
        launcher.workspace_root(tmp_path / "missing", tmp_path)
    (tmp_path / ".git").mkdir()
    with pytest.raises(ValueError, match="home"):
        launcher.workspace_root(tmp_path, tmp_path)
    repo = tmp_path / "example"
    (repo / ".git").mkdir(parents=True)
    (repo / "src").mkdir()
    assert launcher.workspace_root(repo / "src", tmp_path) == repo
    wildcard = tmp_path / "example*"
    (wildcard / ".git").mkdir(parents=True)
    with pytest.raises(ValueError, match="literal"):
        launcher.workspace_root(wildcard, tmp_path)


def test_hardening_preserves_arguments_and_denies_host_process_inspection():
    launcher = load_launcher()
    command = "printf '%s' 'quoted; $(touch nope)'"
    profile = "(version 1)\n(deny default)\n(allow process-exec)"
    original = [
        "env",
        "HTTP_PROXY=http://localhost:1234",
        "/usr/bin/sandbox-exec",
        "-p",
        profile,
        "/bin/bash",
        "-c",
        command,
    ]
    hardened = launcher.harden(shlex.join(original))
    assert hardened[-1] == command
    assert "(deny process-info*)" in hardened[4]
    assert "kern.proc" in hardened[4]
    assert "com.apple.securityd.xpc" in hardened[4]
    with pytest.raises(ValueError):
        launcher.harden("echo unexpected-runtime-output")
    with pytest.raises(ValueError):
        launcher.harden(shlex.join(original).replace("deny default", "allow default"))


def test_plan_isolates_project_state_and_does_not_forward_host_secrets(tmp_path, monkeypatch):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/example"
    (repo / ".git").mkdir(parents=True)
    node = tmp_path / "tools/node"
    config = {
        "node": str(node),
        "agents": {
            "codex": {
                "command": [str(tmp_path / "tools/codex")],
                "read": [str(tmp_path / "tools")],
            }
        },
    }
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "synthetic-secret")
    monkeypatch.setenv("NODE_OPTIONS", "--require /untrusted/startup.js")
    monkeypatch.setenv("HTTPS_PROXY", "http://untrusted-proxy")
    with pytest.raises(ValueError, match="private-data"):
        launcher.build_plan(repo, home, config, "codex", "hosted", ["--version"])
    private = home / ".config/workbench/private-paths"
    private.parent.mkdir(parents=True)
    private.write_text("# synthetic policy\n~/code/*/private-data/**\n")
    plan = launcher.build_plan(repo, home, config, "codex", "hosted", ["--version"])
    assert plan["env"]["HOME"] != str(home)
    assert "AWS_SECRET_ACCESS_KEY" not in plan["env"]
    assert "NODE_OPTIONS" not in plan["env"]
    assert "HTTPS_PROXY" not in plan["env"]
    assert str(repo) in plan["policy"]["filesystem"]["allowRead"]
    assert str(home) not in plan["policy"]["filesystem"]["allowRead"]
    for relative in (
        ".local/share/uv/python",
        ".npm-global/global",
        ".npm-global/lib/node_modules/pnpm",
        ".bun/bin",
    ):
        assert str(home / relative) in plan["policy"]["filesystem"]["allowRead"]
        assert str(home / relative) not in plan["policy"]["filesystem"]["allowWrite"]
    assert str(home / ".npm-global/bin") in plan["env"]["PATH"].split(":")
    assert plan["policy"]["filesystem"]["denyRead"][0] == "/"
    assert str(home / "code/*/private-data/**") in plan["policy"]["filesystem"]["denyWrite"]
    assert plan["command"][0] == config["agents"]["codex"]["command"][0]
    assert "--version" in plan["command"]
    assert plan["command"][-1] == "--version"
    other = home / "code/other"
    (other / ".git").mkdir(parents=True)
    second = launcher.build_plan(other, home, config, "codex", "hosted", [])
    assert plan["env"]["HOME"] != second["env"]["HOME"]
    with pytest.raises(ValueError, match="local"):
        launcher.build_plan(repo, home, config, "codex", "local", [])
    with pytest.raises(ValueError, match="terminal"):
        launcher.build_plan(repo, home, config, "codex", "hosted", ["app-server"])


@pytest.mark.parametrize("vendor", ["codex", "pi", "claude"])
def test_shared_model_login_with_separate_project_sessions(tmp_path, vendor):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/project"
    (repo / ".git").mkdir(parents=True)
    policy = home / ".config/workbench/private-paths"
    policy.parent.mkdir(parents=True)
    policy.write_text("")
    config = {
        "node": "/usr/bin/node",
        "agents": {vendor: {"command": ["/usr/bin/agent"], "read": []}},
    }
    plan = launcher.build_plan(repo, home, config, vendor, "hosted", [])
    store = home / ".local/share/workbench/model-auth" / vendor
    filename = ".credentials.json" if vendor == "claude" else "auth.json"
    assert str(store / filename) in plan["policy"]["filesystem"]["allowRead"]
    assert str(home / ".codex") not in plan["policy"]["filesystem"]["allowRead"]
    if vendor == "codex":
        assert 'cli_auth_credentials_store="file"' in plan["command"]
        assert plan["env"]["CODEX_HOME"] == str(Path(plan["env"]["HOME"]) / ".codex")
        assert "features.apps=false" in plan["command"]
        launcher.initialize_home(plan, home)
        link = Path(plan["env"]["HOME"]) / ".codex/auth.json"
        assert link.is_symlink() and link.readlink() == store / filename
        launcher.initialize_home(plan, home)
        link.unlink()
        link.symlink_to(home / "unrelated")
        with pytest.raises(ValueError, match="login link"):
            launcher.initialize_home(plan, home)
    elif vendor == "pi":
        assert plan["env"]["PI_CODING_AGENT_DIR"] == str(store)
        assert "--session-dir" in plan["command"]
        assert str(store / "auth.json.lock") in plan["policy"]["filesystem"]["allowWrite"]
        assert str(store) not in plan["policy"]["filesystem"]["allowWrite"]
        assert "--no-extensions" in plan["command"]
    else:
        assert plan["env"]["CLAUDE_SECURESTORAGE_CONFIG_DIR"] == str(store)


def test_home_initialization_refuses_agent_planted_parent_symlinks(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    state = home / ".local/share/workbench/agent-state/example/home"
    state.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (state / ".codex").symlink_to(outside)
    plan = {
        "env": {"HOME": str(state)},
        "auth_link": {
            "path": str(state / ".codex/auth.json"),
            "target": str(home / "model-auth/auth.json"),
        },
    }
    with pytest.raises(ValueError, match="symlink"):
        launcher.initialize_home(plan, home)
    assert not list(outside.iterdir())
