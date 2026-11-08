"""Audit the locked native runtime and verify its upstream security fixes."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from workbench.core import AGENTS


def audit() -> None:
    """Require a clean upstream audit and both executable regression probes."""
    source = AGENTS / "shared/sandbox"
    with tempfile.TemporaryDirectory(prefix="workbench-dependency-audit-") as directory:
        runtime = Path(directory)
        for name in ("package.json", "package-lock.json"):
            shutil.copyfile(source / name, runtime / name)
        subprocess.run(
            ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=runtime,
            check=True,
        )
        for probe in ("verify-forge.cjs", "verify-zod.cjs"):
            subprocess.run(["node", str(source / probe), str(runtime)], check=True)
        subprocess.run(
            ["npm", "audit", "--package-lock-only", "--ignore-scripts"],
            cwd=runtime,
            check=True,
        )
        print("OK sandbox dependency audit; upstream fixes and security regressions verified")


if __name__ == "__main__":
    audit()
