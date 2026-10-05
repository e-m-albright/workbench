"""The same Claude renderer serves native and ordinary launches."""

import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("authority", ["restricted", "unrestricted"])
def test_claude_footer_shows_authority_and_remaining_quota(tmp_path, authority):
    script = Path(__file__).resolve().parents[1] / "agents/claude/statusline.sh"
    payload = {
        "workspace": {"current_dir": str(tmp_path)},
        "model": {"display_name": "example-model"},
        "context_window": {"used_percentage": 10},
        "rate_limits": {"five_hour": {"used_percentage": 20}},
    }
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        env={
            "PATH": os.environ["PATH"],
            "HOME": str(tmp_path),
            "NO_COLOR": "1",
            "WORKBENCH_AGENT_AUTHORITY": authority,
            "WORKBENCH_AGENT_LOCATION": "hosted",
        },
    )
    lines = result.stdout.splitlines()
    assert len(lines) == 2
    expected = "repo" if authority == "restricted" else "host"
    assert f"cloud > {expected}" in lines[0]
    assert "ctx 10%" in lines[1]
    assert "5h 80% left" in lines[1]
    assert "example-model" in lines[1]


def test_claude_footer_reports_efficiency_and_preserves_false_states(tmp_path):
    script = Path(__file__).resolve().parents[1] / "agents/claude/statusline.sh"
    payload = {
        "workspace": {"current_dir": str(tmp_path)},
        "model": {"display_name": "example-model"},
        "context_window": {
            "used_percentage": 8.4,
            "context_window_size": 1_000_000,
            "total_input_tokens": 155_000,
            "total_output_tokens": 1_200,
        },
        "cost": {"total_cost_usd": 1.2345},
        "prompt_cache": {"warm": True, "hit_ratio": 0.91},
        "effort": {"level": "high"},
        "fast_mode": True,
        "thinking": {"enabled": False},
        "rate_limits": {"spend_limit": {"used_percentage": 62.8}},
    }
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": os.environ["PATH"], "HOME": str(tmp_path), "NO_COLOR": "1"},
    )
    usage = result.stdout.splitlines()[1]
    assert "ctx 8% 156k/1.0M" in usage
    assert "spend 63% used" in usage
    assert "~$1.23" in usage
    assert "cache 91%" in usage
    assert "example-model high fast think off" in usage


def test_claude_footer_omits_noise_but_reports_cold_cache(tmp_path):
    script = Path(__file__).resolve().parents[1] / "agents/claude/statusline.sh"
    payload = {
        "workspace": {"current_dir": str(tmp_path)},
        "cost": {"total_cost_usd": 0.009},
        "prompt_cache": {"warm": False, "hit_ratio": 0},
    }
    result = subprocess.run(
        ["/bin/bash", str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": os.environ["PATH"], "HOME": str(tmp_path), "NO_COLOR": "1"},
    )
    usage = result.stdout.splitlines()[1]
    assert "cache cold" in usage
    assert "$" not in usage
