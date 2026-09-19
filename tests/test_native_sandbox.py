"""Contracts for the standalone, installed native boundary (no live services)."""

import importlib.util
import json
import shlex
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"


def harness_manifest(home, vendor, *, links=(), files=(), read=()):
    path = home / ".local/share/workbench/native/harness/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({vendor: {"links": list(links), "files": list(files), "read": list(read)}})
    )


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
    harness_manifest(home, "codex")
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
        ".npm-global/lib/node_modules/agent-browser",
        ".npm-global/lib/node_modules/pnpm",
    ):
        assert str(home / relative) in plan["policy"]["filesystem"]["allowRead"]
        assert str(home / relative) not in plan["policy"]["filesystem"]["allowWrite"]
    assert str(home / ".npm-global/bin") in plan["env"]["PATH"].split(":")
    zoneinfo = "/private/var/db/timezone/zoneinfo"
    assert zoneinfo in plan["policy"]["filesystem"]["allowRead"]
    assert plan["env"]["PYTHONTZPATH"] == zoneinfo
    assert str(home / ".bun/bin") not in plan["env"]["PATH"].split(":")
    assert str(home / ".bun/bin") not in plan["policy"]["filesystem"]["allowRead"]
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
    harness_manifest(home, vendor)
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
        agent_dir = Path(plan["env"]["HOME"]) / ".pi/agent"
        assert plan["env"]["PI_CODING_AGENT_DIR"] == str(agent_dir)
        launcher.initialize_home(plan, home)
        assert (agent_dir / "auth.json").readlink() == store / "auth.json"
        (agent_dir / "trust.json").write_text("{}")
        assert not (store / "trust.json").exists()
        assert "--session-dir" in plan["command"]
        assert str(store / "auth.json.lock") in plan["policy"]["filesystem"]["allowWrite"]
        assert str(store) not in plan["policy"]["filesystem"]["allowWrite"]
        for flag in ("--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes"):
            assert flag not in plan["command"]
        assert plan["env"]["WORKBENCH_PI_MODE"] == "hosted-restricted"
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


@pytest.mark.parametrize(
    "vendor,config_name",
    [
        ("pi", ".pi/agent/settings.json"),
        ("codex", ".codex/config.toml"),
        ("claude", ".claude/settings.json"),
    ],
)
def test_restricted_home_loads_shared_harness_without_host_state(tmp_path, vendor, config_name):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/project"
    (repo / ".git").mkdir(parents=True)
    private = home / ".config/workbench/private-paths"
    private.parent.mkdir(parents=True)
    private.write_text("")
    skill = home / ".agents/skills/review/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("shared review instructions")
    source = home / ".local/share/workbench/native/harness" / vendor / "settings"
    source.parent.mkdir(parents=True)
    source.write_text('model = "configured-model"')
    harness_manifest(
        home,
        vendor,
        links=[{"path": ".agents/skills", "target": str(skill.parent.parent)}],
        files=[{"path": config_name, "source": str(source)}],
        read=[str(skill.parent.parent)],
    )
    tools = {"node": "/usr/bin/node", "agents": {vendor: {"command": ["agent"], "read": []}}}
    plan = launcher.build_plan(repo, home, tools, vendor, "hosted", [])
    launcher.initialize_home(plan, home)
    isolated = Path(plan["env"]["HOME"])
    assert (isolated / ".agents/skills/review/SKILL.md").read_text() == skill.read_text()
    assert (isolated / config_name).read_text() == source.read_text()
    assert not (isolated / config_name).is_symlink()
    assert str(skill.parent.parent) in plan["policy"]["filesystem"]["allowRead"]
    assert str(skill.parent.parent) in plan["policy"]["filesystem"]["denyWrite"]
    assert str(home / ".codex") not in plan["policy"]["filesystem"]["allowRead"]
    # Refresh defaults without sharing any settings writes back to the host.
    (isolated / config_name).write_text("local mutation")
    launcher.initialize_home(plan, home)
    assert (isolated / config_name).read_text() == source.read_text()


@pytest.mark.parametrize("attack", ["symlink", "hardlink", "parent"])
def test_harness_initialization_cannot_overwrite_host_files(tmp_path, attack):
    launcher = load_launcher()
    home = tmp_path / "home"
    state = home / "state"
    state.mkdir(parents=True)
    source = home / "safe-settings"
    source.write_text("safe")
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "settings.json"
    victim.write_text("must remain untouched")
    directory = state / ".pi/agent"
    directory.mkdir(parents=True)
    target = directory / "settings.json"
    if attack == "symlink":
        target.symlink_to(victim)
    elif attack == "hardlink":
        target.hardlink_to(victim)
    else:
        directory.rmdir()
        directory.symlink_to(outside)
    plan = {
        "env": {"HOME": str(state)},
        "auth_link": None,
        "harness": {
            "links": [],
            "files": [{"path": ".pi/agent/settings.json", "source": str(source)}],
        },
    }
    if attack == "parent":
        with pytest.raises(ValueError, match="symlink"):
            launcher.initialize_home(plan, home)
    else:
        launcher.initialize_home(plan, home)
        assert target.read_text() == "safe"
    assert victim.read_text() == "must remain untouched"
