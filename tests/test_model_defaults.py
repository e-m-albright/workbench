"""Ordinary launches use the owner's model and effort defaults."""

import tomllib

import pytest

from workbench.codex import merge_codex_config, merge_codex_rules
from workbench.core import AGENTS, CLAUDE_DEFAULTS, CODEX_DEFAULTS
from workbench.sync import merge_claude_settings


@pytest.mark.parametrize("profile", ["personal", "work"])
def test_claude_defaults_use_latest_opus_and_medium_without_changing_other_preferences(
    tmp_path, profile
):
    existing = {
        "model": "old-model",
        "effortLevel": "high",
        "theme": "dark",
        "autoCompactEnabled": False,
    }
    merged = merge_claude_settings(existing, tmp_path, profile)
    assert {key: merged[key] for key in CLAUDE_DEFAULTS} == CLAUDE_DEFAULTS
    assert merged["theme"] == "dark"
    assert merged["autoCompactEnabled"] is False
    assert merge_claude_settings(merged, tmp_path, profile) == merged


@pytest.mark.parametrize(
    "existing",
    ["", 'model = "old-model"\nmodel_reasoning_effort = "high"\n'],
)
def test_codex_sync_updates_default_model_and_effort(existing):
    result = tomllib.loads(merge_codex_config(existing))
    assert {key: result[key] for key in CODEX_DEFAULTS} == CODEX_DEFAULTS
    assert merge_codex_config(merge_codex_config(existing)) == merge_codex_config(existing)


def test_codex_default_update_preserves_explicit_profiles_and_other_preferences():
    existing = (
        'model = "old-model"\nmodel_reasoning_effort = "high"\n'
        'personality = "pragmatic"\n'
        '[profiles.focus]\nmodel = "chosen-model"\nmodel_reasoning_effort = "high"\n'
    )
    result = tomllib.loads(merge_codex_config(existing))
    assert result["model"] == CODEX_DEFAULTS["model"]
    assert result["personality"] == "pragmatic"
    assert result["profiles"]["focus"] == {
        "model": "chosen-model",
        "model_reasoning_effort": "high",
    }


def test_retired_universal_approvals_do_not_return_as_local_additions():
    canonical = (AGENTS / "codex/default.rules").read_text()
    old = "\n".join(
        f'prefix_rule(pattern={pattern}, decision="allow")'
        for pattern in ('["uv", "run"]', '["just", "check"]', '["git", "push", "origin"]')
    )
    retained = 'prefix_rule(pattern=["custom", "inspect"], decision="allow")'
    result = merge_codex_rules(canonical, old + "\n" + retained)
    assert retained in result
    assert 'prefix_rule(pattern=["uv", "run"], decision="allow")' not in result
    assert 'prefix_rule(pattern=["just", "check"], decision="allow")' not in result
    assert 'prefix_rule(pattern=["git", "push", "origin"], decision="allow")' not in result
