"""Catalogue counts describe the working tree without following symlink targets."""

import subprocess
import sys
from pathlib import Path


def test_catalogue_counts_disjoint_surfaces_and_optional_untracked_files(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/catalogue.py"
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    files = {
        "src/example.py": b"first\n\nlast",
        "tests/fixture.json": b"{\n}\n",
        "README.md": "Hello\n世界\n".encode(),
        "vitest.config.ts": b"export default {};\n",
        "pnpm-lock.yaml": b"generated:\n  yes\n",
        "image.png": b"\x89PNG\0",
    }
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (tmp_path / "CLAUDE.md").symlink_to("missing-target.md")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    (tmp_path / "new.py").write_text("new\n")
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "ignored.py").write_text("ignored\n")

    def count(*args):
        return subprocess.check_output(
            [sys.executable, str(script), *args], cwd=tmp_path, text=True
        )

    tracked = count()
    assert "| Code - source | 1 | 3 |" in tracked
    assert "| Code - tests | 1 | 2 |" in tracked
    assert "| Text | 3 | 4 |" in tracked
    assert "| Generated/vendor | 1 | 2 |" in tracked
    assert "| **Tracked text total** | **6** | **11** |" in tracked
    assert "Binary assets: 1 files, 5 bytes." in tracked

    expanded = count("--include-untracked")
    assert "| Code - source | 2 | 4 |" in expanded
    assert "| Text | 4 | 5 |" in expanded
    assert "| **Tracked + untracked text total** | **8** | **13** |" in expanded
