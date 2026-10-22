"""Contracts for the standalone, installed native boundary (no live services)."""

import importlib.util
import json
import shlex
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"


def harness_manifest(home, vendor, *, links=(), files=(), read=()):
    hard = home / ".config/workbench/hard-deny-paths"
    hard.parent.mkdir(parents=True, exist_ok=True)
    hard.write_text("~/never-agent-readable/**\n")
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


def test_git_identity_respects_repository_values_without_following_local_includes(tmp_path):
    launcher = load_launcher()
    home, repo = tmp_path / "home", tmp_path / "repo"
    home.mkdir()
    repo.mkdir()
    (home / ".gitconfig").write_text("[user]\nname = Example Owner\nemail = owner@example.test\n")
    subprocess.run(["/usr/bin/git", "init", "--quiet", str(repo)], check=True)
    subprocess.run(
        ["/usr/bin/git", "-C", str(repo), "config", "user.email", "project@example.test"],
        check=True,
    )
    identity = launcher.git_identity(home, repo)
    assert identity["GIT_AUTHOR_EMAIL"] == "project@example.test"
    assert identity["GIT_COMMITTER_NAME"] == "Example Owner"
    injected = tmp_path / "included"
    injected.write_text("[user]\nemail = hidden@example.test\n")
    subprocess.run(
        ["/usr/bin/git", "-C", str(repo), "config", "include.path", str(injected)], check=True
    )
    assert launcher.git_identity(home, repo)["GIT_AUTHOR_EMAIL"] == "project@example.test"


def test_scratch_mapping_is_safe_and_uses_real_host_directories(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    state = home / "state"
    home.mkdir()
    plan = {
        "env": {"HOME": str(state)},
        "scratch_links": [
            {"path": "Desktop", "target": str(home / "Desktop")},
            {"path": "Downloads", "target": str(home / "Downloads")},
        ],
    }
    launcher.initialize_home(plan, home)
    assert (state / "Desktop").readlink() == home / "Desktop"
    assert (state / "Downloads").readlink() == home / "Downloads"
    (state / "Desktop").unlink()
    (state / "Desktop").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError, match="scratch link"):
        launcher.initialize_home(plan, home)


@pytest.mark.parametrize("location", ["checkout", "Desktop", "Downloads", "code/public"])
def test_launch_rejects_writable_supervisor_installations(tmp_path, location):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "checkout"
    (repo / ".git").mkdir(parents=True)
    harness_manifest(home, "shell")
    (home / ".config/workbench/private-paths").write_text("")
    node = home / location / "node-install/bin/node"
    config = {"node": str(node), "agents": {}}
    with pytest.raises(ValueError, match="supervisor installation"):
        launcher.build_plan(repo, home, config, "shell", "hosted", [])


def test_project_sandbox_denials_validate_and_never_admit_allow_lists(tmp_path):
    launcher = load_launcher()
    root, home = tmp_path / "repo", tmp_path / "home"
    config = root / ".claude/settings.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "sandbox": {
                    "filesystem": {
                        "denyRead": ["./private/**", "~/Documents/hidden", "/tmp/hidden"],
                        "denyWrite": ["./release"],
                        "allowRead": ["/"],
                        "allowWrite": ["/"],
                    }
                }
            }
        )
    )
    read, write = launcher.project_denials(root, home)
    assert read == [str(root / "private/**"), str(home / "Documents/hidden"), "/tmp/hidden"]
    assert write == [str(root / "release")]
    for malformed in (
        [],
        {"sandbox": []},
        {"sandbox": {"filesystem": []}},
        {"sandbox": {"filesystem": {"denyRead": "~/secret"}}},
        {"sandbox": {"filesystem": {"denyRead": [""]}}},
    ):
        config.write_text(json.dumps(malformed))
        with pytest.raises(ValueError, match="project policy"):
            launcher.project_denials(root, home)


def test_project_policy_does_not_follow_planted_links(tmp_path):
    launcher = load_launcher()
    root = tmp_path / "repo"
    (root / ".claude").mkdir(parents=True)
    (root / ".claude/settings.json").symlink_to(tmp_path / "private-file")
    with pytest.raises(ValueError, match="project policy"):
        launcher.project_denials(root, tmp_path)


def test_codex_login_sync_uses_the_newest_host_refresh(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    source = home / ".codex/auth.json"
    destination = home / ".local/share/workbench/model-auth/codex/auth.json"
    source.parent.mkdir(parents=True)
    destination.parent.mkdir(parents=True)
    source.write_text(json.dumps({"last_refresh": "2026-10-05T00:10:32Z", "token": "current"}))
    destination.write_text(json.dumps({"last_refresh": "2026-09-14T23:59:54Z", "token": "expired"}))
    source.chmod(0o600)
    destination.chmod(0o600)

    assert launcher.sync_codex_auth(home, destination) is True
    assert json.loads(destination.read_text()) == json.loads(source.read_text())
    assert destination.stat().st_mode & 0o077 == 0

    source.write_text(json.dumps({"last_refresh": "2026-09-01T00:00:00Z", "token": "stale"}))
    assert launcher.sync_codex_auth(home, destination) is False
    assert json.loads(destination.read_text())["token"] == "current"


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
    assert '(allow mach-lookup (global-name "com.apple.trustd.agent"))' in hardened[4]
    # Playwright's multiprocess Chromium hands ports to its children by this name.
    assert '(global-name-prefix "org.chromium.Chromium.MachPortRendezvousServer.")' in hardened[4]
    assert "/[Cc][Oo][Nn][Ff][Ii][Dd][Ee][Nn][Tt][Ii][Aa][Ll]" in hardened[4]
    assert '(regex "/[.][Ee][Nn][Vv]($|/|[.])")' in hardened[4]
    assert "subpath" not in hardened[4]
    with pytest.raises(ValueError):
        launcher.harden("echo unexpected-runtime-output")
    with pytest.raises(ValueError):
        launcher.harden(shlex.join(original).replace("deny default", "allow default"))
    browser = launcher.harden(shlex.join(original), browser_port=49152)[4]
    assert '(remote ip "localhost:49152")' in browser
    with pytest.raises(ValueError, match="port"):
        launcher.harden(shlex.join(original), browser_port=-1)


def test_plan_isolates_project_state_and_does_not_forward_host_secrets(tmp_path, monkeypatch):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/example"
    (repo / ".git").mkdir(parents=True)
    node = tmp_path / "tools/node"
    config = {
        "node": str(node),
        "browser": str(tmp_path / "browser/chrome-headless-shell"),
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
    with pytest.raises(ValueError, match="private-paths"):
        launcher.build_plan(repo, home, config, "codex", "hosted", ["--version"])
    private = home / ".config/workbench/private-paths"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text("# synthetic policy\n~/code/*/private-data/**\n")
    plan = launcher.build_plan(
        repo, home, config, "codex", "hosted", ["--version"], browser_port=49152
    )
    assert plan["env"]["HOME"] != str(home)
    sockets = str(Path(plan["env"]["TMPDIR"]) / "browser")
    assert plan["env"]["PI_AGENT_BROWSER_SOCKET_DIR"] == sockets
    assert plan["env"]["AGENT_BROWSER_SOCKET_DIR"] == sockets
    assert plan["policy"]["network"]["allowUnixSockets"] == [sockets]
    assert "AWS_SECRET_ACCESS_KEY" not in plan["env"]
    assert "NODE_OPTIONS" not in plan["env"]
    assert "HTTPS_PROXY" not in plan["env"]
    # rustls cannot discover public roots through the intentionally denied Keychain.
    assert plan["env"]["SSL_CERT_FILE"] == "/etc/ssl/cert.pem"
    assert plan["env"]["AGENT_BROWSER_EXECUTABLE_PATH"] == config["browser"]
    assert "--single-process" in plan["env"]["AGENT_BROWSER_ARGS"]
    assert "--remote-debugging-port=49152" in plan["env"]["AGENT_BROWSER_ARGS"]
    assert plan["browser_port"] == 49152
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
    assert plan["policy"]["network"]["allowLocalBinding"] is False
    assert str(home / "code/*/private-data/**") in plan["policy"]["filesystem"]["denyWrite"]
    assert plan["command"][:5] == [
        "/Library/Developer/CommandLineTools/usr/bin/python3",
        "-I",
        "-S",
        str(SCRIPT),
        "--browser-session",
    ]
    assert plan["command"][5] == config["agents"]["codex"]["command"][0]
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

    for retired in ("restricted", "daily", "unrestricted"):
        with pytest.raises(ValueError, match="authority"):
            launcher.build_plan(repo, home, config, "codex", "hosted", [], authority=retired)

    fs = plan["policy"]["filesystem"]
    for relative in ("code/public", "Desktop", "Downloads"):
        assert str(home / relative) in fs["allowRead"]
        assert str(home / relative) in fs["allowWrite"]
    assert str(home / "code") not in fs["allowRead"]
    assert str(home) not in fs["allowWrite"]
    assert str(home / "never-agent-readable/**") in fs["denyRead"]
    assert str(home / "code/*/private-data/**") in fs["denyRead"]
    assert str(home / ".local/share/workbench/shell") in fs["denyWrite"]
    assert "/Library/Application Support/ClaudeCode" in fs["allowRead"]
    assert "/usr/local/bin" in fs["allowRead"]
    assert "/usr/local/bin" in plan["env"]["PATH"].split(":")
    assert 'default_permissions="cloud > managed"' in plan["command"]


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
    assert plan["resume_hint"] is None
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
        assert plan["env"]["WORKBENCH_PI_MODE"] == "hosted-managed"
    else:
        assert plan["env"]["CLAUDE_SECURESTORAGE_CONFIG_DIR"] == str(store)
        writable = plan["policy"]["filesystem"]["allowWrite"]
        assert str(store / ".credentials.json.tmp.*") in writable
        assert str(store) not in writable
        assert not any("*" in path for path in plan["policy"]["filesystem"]["allowRead"])


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
def test_managed_home_loads_shared_harness_without_host_state(tmp_path, vendor, config_name):
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


def test_harness_link_migrates_a_prior_managed_file(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    state = home / "state"
    managed = state / ".pi/agent/AGENTS.md"
    managed.parent.mkdir(parents=True)
    managed.write_text("old generated copy")
    source = home / ".pi/agent/AGENTS.md"
    source.parent.mkdir(parents=True)
    source.write_text("current shared instructions")
    plan = {
        "env": {"HOME": str(state)},
        "auth_link": None,
        "harness": {
            "links": [{"path": ".pi/agent/AGENTS.md", "target": str(source)}],
            "files": [],
        },
    }

    launcher.initialize_home(plan, home)

    assert managed.is_symlink()
    assert managed.readlink() == source
    assert managed.read_text() == "current shared instructions"

    managed.unlink()
    managed.symlink_to(home / "unrelated")
    with pytest.raises(ValueError, match="harness link"):
        launcher.initialize_home(plan, home)


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


def test_native_claude_launcher_follows_auto_update_inside_admitted_versions(tmp_path):
    launcher = load_launcher()
    home = (tmp_path / "home").resolve()
    repo = home / "code/project"
    (repo / ".git").mkdir(parents=True)
    harness_manifest(home, "claude")
    (home / ".config/workbench/private-paths").write_text("")
    versions = home / ".local/share/claude/versions"
    versions.mkdir(parents=True)
    stable = home / ".local/bin/claude"
    stable.parent.mkdir(parents=True)
    config = {
        "node": "/usr/bin/node",
        "agents": {"claude": {"command": [str(stable)], "read": [str(versions)]}},
    }
    for version in ("2.1.304", "2.1.305"):
        (versions / version).write_text("synthetic native binary")
        stable.unlink(missing_ok=True)
        stable.symlink_to(versions / version)
        plan = launcher.build_plan(repo, home, config, "claude", "hosted", [])
        assert plan["command"][0] == str(versions / version)
    fs = plan["policy"]["filesystem"]
    assert str(versions) in fs["allowRead"]
    assert not any(str(versions).startswith(path) for path in fs["allowWrite"])
    assert plan["env"]["DISABLE_AUTOUPDATER"] == "1"

    outside = home / "elsewhere/claude"
    outside.parent.mkdir()
    outside.write_text("synthetic")
    stable.unlink()
    stable.symlink_to(outside)
    with pytest.raises(ValueError, match="outside its admitted installation"):
        launcher.build_plan(repo, home, config, "claude", "hosted", [])


def test_launch_rejects_writable_launcher_link_to_readonly_installation(tmp_path):
    launcher = load_launcher()
    home = (tmp_path / "home").resolve()
    repo = home / "code/project"
    (repo / ".git").mkdir(parents=True)
    harness_manifest(home, "claude")
    (home / ".config/workbench/private-paths").write_text("")
    versions = home / ".local/share/claude/versions"
    versions.mkdir(parents=True)
    (versions / "1").write_text("synthetic binary")
    stable = repo / "claude"
    stable.symlink_to(versions / "1")
    config = {
        "node": "/usr/bin/node",
        "agents": {"claude": {"command": [str(stable)], "read": [str(versions)]}},
    }
    with pytest.raises(ValueError, match="agent installation"):
        launcher.build_plan(repo, home, config, "claude", "hosted", [])


def test_launch_rejects_agent_installation_inside_a_write_grant(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/project"
    (repo / ".git").mkdir(parents=True)
    harness_manifest(home, "claude")
    (home / ".config/workbench/private-paths").write_text("")
    versions = home / "Downloads/claude/versions"
    config = {
        "node": "/usr/bin/node",
        "agents": {"claude": {"command": [str(versions / "1")], "read": [str(versions)]}},
    }
    with pytest.raises(ValueError, match="agent installation"):
        launcher.build_plan(repo, home, config, "claude", "hosted", [])


def test_repository_credentials_issue_only_the_checkouts_assignment(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/example"
    repo.mkdir(parents=True)
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        assert kwargs["env"]["HOME"] == str(home)
        if command[0] == "/usr/bin/security":
            stdout = "synthetic-github-token\n"
        elif "export-credentials" in command:
            stdout = json.dumps(
                {
                    "Version": 1,
                    "AccessKeyId": "AKIASYNTHETIC",
                    "SecretAccessKey": "synthetic-secret",
                    "SessionToken": "synthetic-session",
                }
            )
        else:
            stdout = "us-west-2\n"
        return subprocess.CompletedProcess(command, 0, stdout, "")

    assert launcher.repository_grants(home, repo) == {}
    config = home / ".config/workbench/repository-grants.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"~/code/other": {"github": "elsewhere"}}))
    assert launcher.repository_grants(home, repo) == {}

    config.write_text(json.dumps({"~/code/example": {"github": "example-token", "aws": "sandbox"}}))
    issued = launcher.repository_credentials(home, launcher.repository_grants(home, repo), run)
    assert issued["GH_TOKEN"] == "synthetic-github-token"
    assert issued["GIT_CONFIG_KEY_0"] == "credential.https://github.com.helper"
    assert issued["AWS_PROFILE"] == "sandbox"
    assert issued["AWS_REGION"] == "us-west-2"
    assert not any(key.startswith("AWS_") and "KEY" in key for key in issued)
    helper = issued["GIT_CONFIG_VALUE_0"].removeprefix("!")
    answer = subprocess.run(
        # Git appends the action to a shell helper's command string.
        ["/bin/sh", "-c", f"{helper} get"],
        env={"GH_TOKEN": "synthetic-github-token", "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert answer.stdout == "username=x-access-token\npassword=synthetic-github-token\n"

    agent_home = home / ".local/share/workbench/agent-state/example/home"
    launcher.refresh_aws(home, agent_home, "sandbox", run)
    assert calls[-1][1:5] == ["configure", "export-credentials", "--profile", "sandbox"]
    written = agent_home / ".aws/credentials"
    assert written.read_text() == (
        "[sandbox]\naws_access_key_id = AKIASYNTHETIC\n"
        "aws_secret_access_key = synthetic-secret\naws_session_token = synthetic-session\n"
    )
    assert written.stat().st_mode & 0o777 == 0o600
    victim = home / "victim"
    victim.write_text("must remain untouched")
    written.unlink()
    written.symlink_to(victim)
    launcher.refresh_aws(home, agent_home, "sandbox", run)
    assert victim.read_text() == "must remain untouched"
    assert not written.is_symlink()

    def expired(command, **kwargs):
        return subprocess.CompletedProcess(command, 255, "", "token expired")

    with pytest.raises(ValueError, match="aws sso login --profile sandbox"):
        launcher.refresh_aws(home, agent_home, "sandbox", expired)
    launcher.refresh_aws(home, agent_home, "sandbox", expired, launching=False)
    stale = written.read_text()
    assert "AKIASYNTHETIC" not in stale
    process = stale.split("credential_process = ", 1)[1].strip()
    # The AWS CLI and SDKs split credential_process with shell rules and report its stderr.
    reported = subprocess.run(shlex.split(process), capture_output=True, text=True, check=False)
    assert reported.returncode == 1
    assert "run `aws sso login --profile sandbox`" in reported.stderr
    launcher.refresh_aws(home, agent_home, "sandbox", run, launching=False)
    assert "aws_access_key_id = AKIASYNTHETIC" in written.read_text()
    for invalid in (
        {"docker": "yes"},
        {"env": "yes"},
        {"ports": "5432"},
        {"paths": "~/code/sibling"},
        {"unknown": True},
    ):
        config.write_text(json.dumps({str(repo): invalid}))
        with pytest.raises(ValueError, match="each checkout maps"):
            launcher.repository_grants(home, repo)
    config.write_text(json.dumps({str(repo): {"ports": [5432, "8000"]}}))
    with pytest.raises(ValueError, match="1 to 65535"):
        launcher.repository_grants(home, repo)
    for path in ("~", "~/code/missing", "relative"):
        config.write_text(json.dumps({str(repo): {"paths": [path]}}))
        with pytest.raises(ValueError, match="extra path"):
            launcher.repository_grants(home, repo)
    (config.parent / "repo-credentials.json").write_text("{}")
    with pytest.raises(ValueError, match="Merge"):
        launcher.repository_grants(home, repo)
    config.unlink()
    with pytest.raises(ValueError, match="Merge"):
        launcher.repository_grants(home, repo)


def test_loopback_ports_admit_serving_but_only_listed_destinations():
    launcher = load_launcher()
    profile = "(version 1)\n(deny default)\n(allow process-exec)"
    command = shlex.join(
        ["env", "A=1", "/usr/bin/sandbox-exec", "-p", profile, "/bin/bash", "-c", "true"]
    )
    closed = launcher.harden(command)[4]
    assert "network-bind" not in closed and "network-outbound" not in closed
    opened = launcher.harden(command, ports=[5432, 15173])[4]
    assert '(allow network-bind (local ip "*:*"))' in opened
    assert '(allow network-outbound (remote ip "localhost:5432"))' in opened
    assert '(allow network-outbound (remote ip "localhost:15173"))' in opened
    assert '"localhost:*"' not in opened
    with pytest.raises(ValueError):
        launcher.harden(command, ports=[True])


def test_environment_file_grant_opens_only_the_granted_checkout():
    launcher = load_launcher()
    profile = "(version 1)\n(deny default)\n(allow process-exec)"
    command = shlex.join(
        ["env", "A=1", "/usr/bin/sandbox-exec", "-p", profile, "/bin/bash", "-c", "true"]
    )
    opened = launcher.harden(command, env_root="/Users/example/code/app")[4]
    rule = opened.split('(require-not (subpath "/Users/example/code/app"))', 1)
    assert len(rule) == 2 and rule[0].rstrip().endswith("(require-all")
    assert '(regex "/[.][Ee][Nn][Vv]($|/|[.])")' in rule[1]
    # The confidential-directory invariant has no exemption.
    assert '(regex "/[Cc][Oo][Nn][Ff][Ii][Dd][Ee][Nn][Tt][Ii][Aa][Ll]($|/)"))' in opened
    assert opened.count("(") == opened.count(")")
    for invalid in ("relative/app", '/code/a"pp', "/code/a\\pp", "/code/a\npp"):
        with pytest.raises(ValueError, match="literal absolute"):
            launcher.harden(command, env_root=invalid)


def test_owner_grants_extend_one_checkout_with_docker_ports_and_paths(tmp_path, monkeypatch):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/work/example"
    sibling = home / "code/work/sibling"
    (repo / ".git").mkdir(parents=True)
    sibling.mkdir()
    engine = home / ".orbstack/run/docker.sock"
    engine.parent.mkdir(parents=True)
    engine.touch()
    bundle = tmp_path / "Applications/Engine.app/Contents"
    (bundle / "MacOS/xbin").mkdir(parents=True)
    (bundle / "MacOS/xbin/docker").touch()
    (bundle / "MacOS/xbin/docker-compose").touch()
    client = tmp_path / "bin/docker"
    client.parent.mkdir()
    client.symlink_to(bundle / "MacOS/xbin/docker")
    monkeypatch.setattr(
        launcher, "DOCKER_SOCKETS", ("/nonexistent/docker.sock", "~/.orbstack/run/docker.sock")
    )
    monkeypatch.setattr(launcher, "DOCKER_CLIENTS", (str(client),))
    harness_manifest(home, "claude")
    (home / ".config/workbench/private-paths").write_text("")
    tools = {
        "node": str(tmp_path / "tools/node"),
        "agents": {"claude": {"command": ["claude"], "read": []}},
    }
    plan = launcher.build_plan(repo, home, tools, "claude", "hosted", [])
    assert plan["ports"] == [] and plan["docker_config"] is None
    assert plan["env_root"] == ""
    assert "DOCKER_HOST" not in plan["env"]
    assert str(sibling) not in plan["policy"]["filesystem"]["allowWrite"]

    grants = home / ".config/workbench/repository-grants.json"
    grants.write_text(
        json.dumps(
            {
                "~/code/work/example": {
                    "docker": True,
                    "env": True,
                    "ports": [5432],
                    "paths": ["~/code/work/sibling"],
                }
            }
        )
    )
    plan = launcher.build_plan(repo, home, tools, "claude", "hosted", [])
    filesystem = plan["policy"]["filesystem"]
    assert plan["ports"] == [5432]
    assert plan["env_root"] == str(repo.resolve())
    assert plan["env"]["DOCKER_HOST"] == f"unix://{engine.resolve()}"
    assert str(engine.resolve()) in plan["policy"]["network"]["allowUnixSockets"]
    assert str(bundle.resolve()) in filesystem["allowRead"]
    assert str(bundle.resolve()) not in filesystem["allowWrite"]
    assert plan["docker_config"] == {
        "cliPluginsExtraDirs": [str((bundle / "MacOS/xbin").resolve())]
    }
    assert str(sibling.resolve()) in filesystem["allowWrite"]

    launcher.initialize_home(plan, home)
    written = Path(plan["env"]["HOME"]) / ".docker/config.json"
    assert json.loads(written.read_text()) == plan["docker_config"]

    engine.unlink()
    with pytest.raises(ValueError, match="no engine socket"):
        launcher.build_plan(repo, home, tools, "claude", "hosted", [])
