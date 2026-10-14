"""Public aliases select the installed boundary without executing checkout code."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def launch_home(tmp_path):
    home = tmp_path / "home"
    shell = home / ".local/share/workbench/shell"
    shell.mkdir(parents=True)
    (shell / "native-sandbox.py").write_text("import json,sys\nprint(json.dumps(sys.argv[1:]))\n")
    return home


def invoke(home, command):
    script = ROOT / "agents/shared/shell/agent-launchers.zsh"
    return subprocess.run(
        ["/bin/zsh", "-f", "-c", f'source "{script}"; {command}'],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "alias,vendor",
    [
        ("p", "pi"),
        ("co", "codex"),
        ("cc", "claude"),
    ],
)
def test_shortcuts_enter_installed_managed_boundary(launch_home, alias, vendor):
    result = invoke(launch_home, alias)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[:2] == [vendor, "hosted"]
    assert json.loads(result.stdout)[2] == "managed"


@pytest.mark.parametrize(
    "alias", ["co", "p", "cc", "ccr", 'cca --feedback "Keep the parser simple"']
)
def test_shortcuts_keep_an_installed_boundary(launch_home, alias):
    result = invoke(launch_home, alias)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[2] == "managed"


def test_pi_keeps_native_resume_flag(launch_home):
    result = invoke(launch_home, 'p -r -- "--restricted"')
    args = json.loads(result.stdout)
    assert args[2] == "managed"
    assert args[-3:] == ["-r", "--", "--restricted"]


def test_managed_codex_effort_does_not_require_host_profiles(launch_home):
    result = invoke(launch_home, 'co --quick "hello world"')
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert "--profile" not in args
    assert 'model_reasoning_effort="low"' in args
    assert args[-1] == "hello world"


def test_codex_short_flags_are_not_claimed_for_restriction(launch_home):
    result = invoke(launch_home, 'co -r "hello world"')
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert args[:3] == ["codex", "hosted", "managed"]
    assert "-r" in args
    assert args[-1] == "hello world"


@pytest.mark.parametrize("alias", ["co", "cc", "p"])
def test_wrapper_flags_after_separator_are_forwarded_literally(launch_home, alias):
    result = invoke(launch_home, f'{alias} -- --unrestricted --quick "hello world"')
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert args[2] == "managed"
    assert args[-4:] == ["--", "--unrestricted", "--quick", "hello world"]


@pytest.mark.parametrize("alias", ["co", "cc", "p"])
@pytest.mark.parametrize("flag", ["--restricted", "--unrestricted", "--daily"])
def test_retired_modes_fail_with_migration_guidance(launch_home, alias, flag):
    result = invoke(launch_home, f"{alias} {flag}")
    assert result.returncode != 0
    assert "retired" in result.stderr
    assert not result.stdout


def test_full_commands_are_not_wrapped_after_reloading_old_shell(launch_home):
    script = ROOT / "agents/shared/shell/agent-launchers.zsh"
    result = subprocess.run(
        [
            "/bin/zsh",
            "-f",
            "-c",
            f'pi() {{ :; }}; pil() {{ :; }}; cou() {{ :; }}; source "{script}"; '
            "(( $+functions[p] && ! $+functions[pi] && ! $+functions[pil] "
            "&& ! $+functions[cou] && ! $+functions[codex] && ! $+functions[claude] ))",
        ],
        env={"HOME": str(launch_home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_private_commit_macro_is_text_only_and_explicitly_local(launch_home):
    binary = launch_home / "pi"
    binary.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    binary.chmod(0o700)
    result = invoke(launch_home, 'PATH="$HOME:$PATH" _wb_local_commit_message --no-session')
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "--route",
        "private",
        "--provider",
        "omlx",
        "--no-session",
        "--no-tools",
    ]


def test_native_cli_forwards_arguments_without_a_lima_command(monkeypatch):
    from typer.testing import CliRunner

    from workbench import cli

    calls = []
    monkeypatch.setattr(cli.native_module, "run_agent", lambda *args: calls.append(args) or 0)
    runner = CliRunner()
    result = runner.invoke(
        cli.app, ["native", "run", "codex", "--", "--model", "example", "hello world"]
    )
    assert result.exit_code == 0, result.output
    assert calls == [("codex", "hosted", ["--model", "example", "hello world"])]
    assert runner.invoke(cli.app, ["lima", "--help"]).exit_code != 0


@pytest.mark.parametrize("authority", ["restricted", "daily", "unrestricted"])
def test_standalone_launcher_rejects_retired_authorities(tmp_path, authority):
    stub = tmp_path / ".local/share/workbench/shell/native-sandbox.py"
    stub.parent.mkdir(parents=True)
    stub.write_text('import sys\nprint("\\n".join(sys.argv[1:]))\n')
    result = subprocess.run(
        [
            "/bin/zsh",
            "-f",
            str(ROOT / "agents/shared/shell/agent-sandbox.zsh"),
            "codex",
            "hosted",
            authority,
        ],
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not result.stdout


@pytest.mark.parametrize("command", ["ccc", "ccc --quick", "cc --chrome", "cc --quick --chrome"])
def test_chrome_shortcuts_fail_before_launch_with_native_guidance(launch_home, command):
    result = invoke(launch_home, command)
    assert result.returncode == 2
    assert not result.stdout
    assert "claude --chrome" in result.stderr
    assert "host terminal" in result.stderr


def test_chrome_after_separator_is_literal(launch_home):
    result = invoke(launch_home, "cc -- --chrome")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[-2:] == ["--", "--chrome"]


@pytest.mark.parametrize(
    "arguments", ["", "123", "https://github.com/octocat/hello-world/pull/123"]
)
def test_feedback_fetch_requires_explicit_native_continuation(launch_home, arguments):
    result = invoke(launch_home, f"cca {arguments}")
    assert result.returncode == 2
    assert not result.stdout
    assert "GitHub credentials" in result.stderr
    assert "native claude" in result.stderr
    assert "--feedback" in result.stderr


@pytest.mark.parametrize("flag", ["-c", "-p", "-cp", "-pc"])
def test_feedback_writes_rejected_before_agent_launch(launch_home, flag):
    result = invoke(launch_home, f'cca {flag} --feedback "Synthetic feedback"')
    assert result.returncode == 2
    assert not result.stdout
    assert "host terminal" in result.stderr
    assert "GitHub credentials" in result.stderr


def test_feedback_can_be_supplied_without_remote_authentication(launch_home):
    result = invoke(launch_home, 'cca --feedback "Use a bounded parser; keep quoted text intact."')
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert args[:3] == ["claude", "hosted", "managed"]
    assert "--worktree" not in args
    assert "Use a bounded parser; keep quoted text intact." in args[-1]
    assert "Do not fetch" in args[-1]
    assert "gh api" not in args[-1]


def test_feedback_separator_keeps_flag_like_text_literal(launch_home):
    result = invoke(launch_home, 'cca -- "-c" "-p" "literal review text"')
    assert result.returncode == 0, result.stderr
    assert "-c -p literal review text" in json.loads(result.stdout)[-1]


def test_feedback_missing_value_is_actionable(launch_home):
    result = invoke(launch_home, "cca --feedback")
    assert result.returncode == 2
    assert not result.stdout
    assert "requires review text" in result.stderr
