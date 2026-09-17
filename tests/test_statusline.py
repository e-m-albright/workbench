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
    assert f"hosted > {authority}" in lines[0]
    assert "ctx 10%" in lines[1]
    assert "5h 80% left" in lines[1]
    assert "example-model" in lines[1]
