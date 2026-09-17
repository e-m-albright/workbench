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
        ("pi", "pi"),
        ("pih", "pi"),
        ("pihr", "pi"),
        ("co", "codex"),
        ("cc", "claude"),
        ("ccr", "claude"),
        ("cca", "claude"),
    ],
)
def test_restricted_aliases_enter_installed_native_boundary(launch_home, alias, vendor):
    result = invoke(launch_home, alias)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[:2] == [vendor, "hosted"]


def test_restricted_codex_effort_does_not_require_host_profiles(launch_home):
    result = invoke(launch_home, 'co --quick "hello world"')
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert "--profile" not in args
    assert 'model_reasoning_effort="low"' in args
    assert args[-1] == "hello world"


@pytest.mark.parametrize("alias", ["pil", "pihu", "cou", "ccu"])
def test_unrestricted_aliases_require_explicit_interactive_confirmation(launch_home, alias):
    result = invoke(launch_home, alias)
    assert result.returncode != 0
    assert "requires an interactive terminal" in result.stderr
    assert not result.stdout


def test_local_pi_has_one_command_even_after_reloading_an_old_shell(launch_home):
    script = ROOT / "agents/shared/shell/agent-launchers.zsh"
    result = subprocess.run(
        [
            "/bin/zsh",
            "-f",
            "-c",
            f'pilr() {{ :; }}; pilu() {{ :; }}; source "{script}"; '
            "(( $+functions[pil] && ! $+functions[pilr] && ! $+functions[pilu] ))",
        ],
        env={"HOME": str(launch_home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_private_commit_macro_is_text_only_and_explicitly_local(launch_home):
    wrapper = launch_home / ".local/share/workbench/shell/agent-sandbox.zsh"
    wrapper.write_text("printf '%s\\n' \"$@\"\n")
    result = invoke(launch_home, "_wb_local_commit_message --no-session")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "pi",
        "local",
        "unrestricted",
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


@pytest.mark.parametrize("overrides", [[], ["--sandbox", "read-only"], ["--profile", "quick"]])
def test_codex_host_footer_does_not_widen_inner_permissions(tmp_path, overrides):
    stub = tmp_path / "codex"
    stub.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    stub.chmod(0o700)
    result = subprocess.run(
        [
            "/bin/zsh",
            "-f",
            str(ROOT / "agents/shared/shell/agent-sandbox.zsh"),
            "codex",
            "hosted",
            "unrestricted",
            *overrides,
        ],
        env={"HOME": str(tmp_path), "PATH": f"{tmp_path}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert not result.stderr
    assert ":root" not in result.stdout
    if overrides:
        assert result.stdout.splitlines() == overrides
    else:
        assert 'default_permissions="hosted > unrestricted"' in result.stdout
        assert 'extends=":workspace"' in result.stdout
