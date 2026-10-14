"""Managed Codex refresh retains narrow trust decisions, never permissions."""

import importlib.util
import json
import os
import tomllib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.py"


def launcher():
    spec = importlib.util.spec_from_file_location("native_trust", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def state(tmp_path):
    home = tmp_path / "home"
    agent = home / "managed"
    (agent / ".codex").mkdir(parents=True)
    source = home / "projection"
    source.mkdir()
    hooks = {"hooks": {"PreToolUse": [{"hooks": [{"command": "guard"}]}]}}
    (source / "hooks.json").write_text(json.dumps(hooks))
    (agent / ".codex/hooks.json").write_text(json.dumps(hooks))
    (source / "config.toml").write_text('sandbox_mode = "danger-full-access"\n')
    root = tmp_path / "checkout"
    key = f"{agent}/.codex/hooks.json:pre_tool_use:0:0"
    plan = {
        "root": str(root),
        "env": {"HOME": str(agent)},
        "harness": {
            "links": [],
            "files": [
                {"path": ".codex/hooks.json", "source": str(source / "hooks.json")},
                {"path": ".codex/config.toml", "source": str(source / "config.toml")},
            ],
        },
    }
    return home, agent, source, root, key, plan


def trust(key, *, enabled=False):
    return (
        f"[hooks.state.{json.dumps(key)}]\n"
        f'enabled = {str(enabled).lower()}\ntrusted_hash = "{"a" * 64}"\n'
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_refresh_retains_only_this_project_and_unchanged_hooks(state, reverse):
    home, agent, source, root, key, plan = state
    prior = (
        'approval_policy = "never"\nmodel = "unwanted"\n'
        f'[projects.{json.dumps(str(root))}]\ntrust_level = "trusted"\n'
        '[projects."/unrelated"]\ntrust_level = "trusted"\n'
        + trust(key)
        + trust(key.replace(":0:0", ":9:9"))
        + trust("/unrelated/hooks.json:pre_tool_use:0:0")
    )
    (agent / ".codex/config.toml").write_text(prior)
    # An explicit managed decision overrides an unchanged imported host record.
    (source / "config.toml").write_text('model = "current"\n' + trust(key, enabled=True))
    if reverse:
        plan["harness"]["files"].reverse()
    launcher().initialize_home(plan, home)
    result = tomllib.loads((agent / ".codex/config.toml").read_text())
    assert result == {
        "model": "current",
        "projects": {str(root): {"trust_level": "trusted"}},
        "hooks": {"state": {key: {"enabled": False, "trusted_hash": "a" * 64}}},
    }


def test_hook_change_drops_old_hook_trust_but_preserves_project_decision(state):
    home, agent, source, root, key, plan = state
    (agent / ".codex/config.toml").write_text(
        f'[projects.{json.dumps(str(root))}]\ntrust_level = "untrusted"\n' + trust(key)
    )
    (source / "hooks.json").write_text('{"hooks": {"PreToolUse": []}}')
    launcher().initialize_home(plan, home)
    result = tomllib.loads((agent / ".codex/config.toml").read_text())
    assert result["projects"] == {str(root): {"trust_level": "untrusted"}}
    assert "hooks" not in result


@pytest.mark.parametrize(
    "fragment",
    [
        'trust_level = "trusted"\nsandbox_mode = "danger-full-access"\n',
        'trust_level = "trusted"\ntrust_level = "untrusted"\n',
        'trust_level = "anything"\n',
        "trust_level = true\n",
        'trust_level = "trusted"\n[projects."another"]\nvalue = """unterminated\n',
    ],
)
def test_unsupported_prior_trust_fails_closed(state, fragment):
    home, agent, _, root, _, plan = state
    (agent / ".codex/config.toml").write_text(f"[projects.{json.dumps(str(root))}]\n" + fragment)
    launcher().initialize_home(plan, home)
    result = tomllib.loads((agent / ".codex/config.toml").read_text())
    assert "projects" not in result


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_linked_prior_config_is_replaced_without_retaining_its_contents(state, kind):
    home, agent, source, root, _, plan = state
    outside = source / "do-not-import"
    content = f'[projects.{json.dumps(str(root))}]\ntrust_level = "trusted"\n'
    outside.write_text(content)
    destination = agent / ".codex/config.toml"
    if kind == "symlink":
        destination.symlink_to(outside)
    else:
        os.link(outside, destination)
    launcher().initialize_home(plan, home)
    assert "projects" not in tomllib.loads(destination.read_text())
    assert outside.read_text() == content
    assert not destination.is_symlink()


@pytest.mark.parametrize(
    "record",
    [
        'enabled = "true"\ntrusted_hash = "' + "a" * 64 + '"\n',
        'enabled = true\ntrusted_hash = "not-a-hash"\n',
        'enabled = true\ntrusted_hash = "' + "a" * 64 + '"\ncommand = "extra"\n',
    ],
)
def test_malformed_hook_decisions_are_not_imported(state, record):
    home, agent, _, _, key, plan = state
    (agent / ".codex/config.toml").write_text(f"[hooks.state.{json.dumps(key)}]\n" + record)
    launcher().initialize_home(plan, home)
    assert "hooks" not in tomllib.loads((agent / ".codex/config.toml").read_text())


def test_duplicate_project_tables_do_not_select_one_decision(state):
    home, agent, _, root, _, plan = state
    table = f'[projects.{json.dumps(str(root))}]\ntrust_level = "trusted"\n'
    (agent / ".codex/config.toml").write_text(table * 2)
    launcher().initialize_home(plan, home)
    assert "projects" not in tomllib.loads((agent / ".codex/config.toml").read_text())
