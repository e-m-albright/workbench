"""Keep the retired runtime out of the active development toolchain."""

import json
import re
from pathlib import Path


def test_development_toolchain_uses_node_and_pnpm():
    root = Path(__file__).resolve().parents[1]
    package = json.loads((root / "package.json").read_text())
    assert package["packageManager"].startswith("pnpm@")
    assert package["engines"]["node"] == ">=24.20.0 <25"
    active = [
        root / "justfile",
        root / ".github/workflows/ci.yml",
        *root.glob("tests/pi-*.test.ts"),
    ]
    for path in active:
        assert not re.search(r"\bbun(?:x|:test)?\b", path.read_text(), re.IGNORECASE), path
    assert not list(root.glob("bun.lock*"))
