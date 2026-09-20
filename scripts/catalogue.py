"""Print Workbench's disjoint working-tree scale counts for catalogue reviews."""

from __future__ import annotations

import argparse
import os
import subprocess
from collections import Counter
from pathlib import Path

GROUPS = ("Code - source", "Code - tests", "Text", "Generated/vendor")
SOURCE_SUFFIXES = {".py", ".ts", ".js", ".mjs", ".c", ".sh", ".zsh", ".css", ".html"}
LOCKFILES = {"uv.lock", "pnpm-lock.yaml", "package-lock.json"}


def group(path: Path) -> str:
    if path.name in LOCKFILES or path.parts[0] == "vendor":
        return "Generated/vendor"
    if path.parts[0] == "tests":
        return "Code - tests"
    if not path.name.endswith(".config.ts") and (
        path.suffix in SOURCE_SUFFIXES or path.parts[0] == "bin"
    ):
        return "Code - source"
    return "Text"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untracked", action="store_true")
    args = parser.parse_args()
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    command = ["git", "ls-files", "--cached", "-z"]
    if args.include_untracked:
        command += ["--others", "--exclude-standard"]
    paths = subprocess.check_output(command, cwd=root).split(b"\0")
    files: Counter[str] = Counter()
    lines: Counter[str] = Counter()
    binary_files = binary_bytes = 0
    for raw in sorted(set(paths) - {b""}):
        relative = Path(os.fsdecode(raw))
        path = root / relative
        if path.is_symlink():
            count = 1  # Count the link blob, including dangling links; never open its target.
        else:
            if not path.is_file():
                continue  # Deleted tracked files and submodule directories have no local blob.
            content = path.read_bytes()
            try:
                content.decode("utf-8")
                binary = b"\0" in content
            except UnicodeDecodeError:
                binary = True
            if binary:
                binary_files += 1
                binary_bytes += len(content)
                continue
            count = content.count(b"\n") + int(bool(content) and not content.endswith(b"\n"))
        category = group(relative)
        files[category] += 1
        lines[category] += count

    print("| Group | Files | Lines |\n|---|---:|---:|")
    for category in GROUPS:
        print(f"| {category} | {files[category]:,} | {lines[category]:,} |")
    scope = "Tracked + untracked" if args.include_untracked else "Tracked"
    print(f"| **{scope} text total** | **{sum(files.values()):,}** | **{sum(lines.values()):,}** |")
    print(f"\nBinary assets: {binary_files:,} files, {binary_bytes:,} bytes.")


if __name__ == "__main__":
    main()
