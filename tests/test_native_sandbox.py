"""Contracts for the standalone, installed native boundary (no live services)."""

import importlib.util
import json
import re
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
    assert '(global-name-prefix "org.chromium.Chromium.MachPortRendezvousServer.")' in hardened[4]
    assert "/[Cc][Oo][Nn][Ff][Ii][Dd][Ee][Nn][Tt][Ii][Aa][Ll]" in hardened[4]
    with pytest.raises(ValueError):
        launcher.harden("echo unexpected-runtime-output")
    with pytest.raises(ValueError):
        launcher.harden(shlex.join(original).replace("deny default", "allow default"))


@pytest.mark.parametrize(
    ("name", "denied"),
    [
        (".env", True),
        (".ENV", True),
        (".env.local", True),
        (".Env.Production", True),
        (".env.", True),
        (".env.exampl", True),
        (".env.examples", True),
        (".env/nested", True),
        (".env.example", False),
        (".ENV.Sample", False),
        (".env.template", False),
        (".envrc", False),
        ("app.env", False),
    ],
)
def test_environment_guard_denies_secrets_and_admits_templates(name, denied):
    # Seatbelt regex is POSIX-like; Python agrees on this lookahead-free subset.
    guard = load_launcher().GUARD
    assert "(?" not in guard
    pattern = re.search(r'\(regex "(/\[\.\]\[Ee\][^"]+)"\)', guard).group(1)
    assert bool(re.search(pattern, f"/repo/{name}")) is denied


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
    with pytest.raises(ValueError, match="private-paths"):
        launcher.build_plan(repo, home, config, "codex", "hosted", ["--version"])
    private = home / ".config/workbench/private-paths"
    private.parent.mkdir(parents=True, exist_ok=True)
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
    browsers = str(home / "Library/Caches/ms-playwright")
    assert browsers in plan["policy"]["filesystem"]["allowRead"]
    assert browsers not in plan["policy"]["filesystem"]["allowWrite"]
    assert plan["env"]["PLAYWRIGHT_BROWSERS_PATH"] == browsers
    assert plan["ports"] == []
    zoneinfo = "/private/var/db/timezone/zoneinfo"
    assert zoneinfo in plan["policy"]["filesystem"]["allowRead"]
    assert plan["env"]["PYTHONTZPATH"] == zoneinfo
    assert str(home / ".bun/bin") not in plan["env"]["PATH"].split(":")
    assert str(home / ".bun/bin") not in plan["policy"]["filesystem"]["allowRead"]
    assert plan["policy"]["filesystem"]["denyRead"][0] == "/"
    assert str(home / "code/*/private-data/**") in plan["policy"]["filesystem"]["denyWrite"]
    for grant in ("allowRead", "allowWrite"):
        assert str(home / "Desktop") in plan["policy"]["filesystem"][grant]
    assert "/usr/local/bin" in plan["env"]["PATH"].split(":")
    managed = "/Library/Application Support/ClaudeCode"
    assert managed in plan["policy"]["filesystem"]["allowRead"]
    assert managed not in plan["policy"]["filesystem"]["allowWrite"]
    assert plan["policy"]["network"]["allowUnixSockets"] == []
    assert plan["policy"]["network"]["allowLocalBinding"] is False
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

    unrestricted = launcher.build_plan(
        repo, home, config, "codex", "hosted", [], authority="unrestricted"
    )
    assert unrestricted["policy"]["filesystem"]["allowRead"] == ["/"]
    assert unrestricted["policy"]["filesystem"]["allowWrite"] == ["/"]
    invariant = str(home / "never-agent-readable/**")
    assert invariant in unrestricted["policy"]["filesystem"]["denyRead"]
    assert invariant in unrestricted["policy"]["filesystem"]["denyWrite"]
    assert unrestricted["env"]["WORKBENCH_AGENT_AUTHORITY"] == "unrestricted"
    assert unrestricted["policy"]["network"]["deniedResolvedAddresses"] == []
    assert "/var/run/docker.sock" in unrestricted["policy"]["network"]["allowUnixSockets"]
    assert unrestricted["policy"]["network"]["allowLocalBinding"] is True
    assert "mail.google.com" in unrestricted["policy"]["network"]["deniedDomains"]
    assert "drive.google.com" in unrestricted["policy"]["network"]["deniedDomains"]
    assert "*.googleapis.com" in unrestricted["policy"]["network"]["deniedDomains"]


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
        assert "`cc --resume <id>`" in plan["resume_hint"]
        unrestricted = launcher.build_plan(
            repo, home, config, vendor, "hosted", [], authority="unrestricted"
        )
        assert "`ccu --resume <id>`" in unrestricted["resume_hint"]
    if vendor != "claude":
        assert plan["resume_hint"] is None


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


def test_project_sandbox_deny_lists_tighten_both_authorities(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/example"
    (repo / ".git").mkdir(parents=True)
    (repo / ".claude").mkdir()
    (repo / ".claude/settings.json").write_text(
        json.dumps(
            {
                "sandbox": {
                    "filesystem": {
                        "denyWrite": ["guard.py", "./.githooks", "/opt/shared", "~/notes"],
                        "denyRead": ["data/**"],
                        "allowWrite": ["/"],
                    }
                }
            }
        )
    )
    (repo / ".claude/settings.local.json").write_text(
        json.dumps({"sandbox": {"filesystem": {"denyWrite": ["local-guard"]}}})
    )
    config = {
        "node": str(tmp_path / "tools/node"),
        "agents": {"codex": {"command": ["codex"], "read": []}},
    }
    harness_manifest(home, "codex")
    (home / ".config/workbench/private-paths").write_text("")
    for authority in ("restricted", "unrestricted"):
        policy = launcher.build_plan(
            repo, home, config, "codex", "hosted", [], authority=authority
        )["policy"]["filesystem"]
        for denied in ("guard.py", ".githooks", "local-guard"):
            assert str(repo / denied) in policy["denyWrite"]
        assert "/opt/shared" in policy["denyWrite"]
        assert str(home / "notes") in policy["denyWrite"]
        assert str(repo / "data/**") in policy["denyRead"]
        if authority == "restricted":
            assert "/" not in policy["allowWrite"]

    (repo / ".claude/settings.json").write_text("{broken")
    with pytest.raises(ValueError, match="project policy"):
        launcher.build_plan(repo, home, config, "codex", "hosted", [])


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
                    "Expiration": "2030-01-01T00:00:00+00:00",
                }
            )
        else:
            stdout = "us-west-2\n"
        return subprocess.CompletedProcess(command, 0, stdout, "")

    assert launcher.repository_credentials(home, repo, run) == {}
    config = home / ".config/workbench/repo-credentials.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"~/code/other": {"github": "elsewhere"}}))
    assert launcher.repository_credentials(home, repo, run) == {}
    assert calls == []

    config.write_text(json.dumps({"~/code/example": {"github": "example-token", "aws": "sandbox"}}))
    issued = launcher.repository_credentials(home, repo, run)
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

    def expired(command, **kwargs):
        return subprocess.CompletedProcess(command, 255, "", "token expired")

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
    with pytest.raises(ValueError, match="aws sso login --profile sandbox"):
        launcher.refresh_aws(home, agent_home, "sandbox", expired)
    config.write_text(json.dumps({str(repo): {"aws": "sandbox", "docker": "yes"}}))
    with pytest.raises(ValueError, match="'ports' to a list"):
        launcher.repository_credentials(home, repo, run)
    config.write_text(json.dumps({str(repo): {"ports": [5432, "8000"]}}))
    with pytest.raises(ValueError, match="1 to 65535"):
        launcher.repository_grants(home, repo)
    config.write_text(json.dumps({str(repo): {"ports": [5432]}}))
    assert launcher.repository_grants(home, repo) == {"ports": [5432]}
    assert launcher.repository_credentials(home, repo, run) == {}


def test_loopback_ports_admit_serving_but_only_listed_destinations():
    launcher = load_launcher()
    profile = "(version 1)\n(deny default)\n(allow process-exec)"
    command = shlex.join(
        ["env", "A=1", "/usr/bin/sandbox-exec", "-p", profile, "/bin/bash", "-c", "true"]
    )
    closed = launcher.harden(command)[4]
    assert "network-bind" not in closed and "network-outbound" not in closed
    opened = launcher.harden(command, [5432, 15173])[4]
    assert '(allow network-bind (local ip "*:*"))' in opened
    assert '(allow network-outbound (remote ip "localhost:5432"))' in opened
    assert '(allow network-outbound (remote ip "localhost:15173"))' in opened
    assert '"localhost:*"' not in opened
    with pytest.raises(ValueError):
        launcher.harden(command, [0])


def test_git_identity_comes_from_the_global_file_only(tmp_path):
    launcher = load_launcher()
    home = tmp_path / "home"
    repo = home / "code/example"
    repo.mkdir(parents=True)
    subprocess.run(["/usr/bin/git", "init", "--quiet", str(repo)], check=True)
    (repo / ".git/config").write_text("[user]\n\tname = Planted\n\temail = planted@example.com\n")
    assert launcher.git_identity(home, repo) == {}
    (home / ".gitconfig").write_text("[user]\n\tname = Octo Cat\n\temail = octocat@example.com\n")
    assert launcher.git_identity(home, repo) == {
        "GIT_AUTHOR_NAME": "Octo Cat",
        "GIT_COMMITTER_NAME": "Octo Cat",
        "GIT_AUTHOR_EMAIL": "octocat@example.com",
        "GIT_COMMITTER_EMAIL": "octocat@example.com",
    }
