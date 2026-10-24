"""Run the real macOS boundary probes with a disposable, credential-free home."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from workbench import native
from workbench.core import ROOT, WorkbenchError


def run(args: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-k", default="", help="run only tests matching this expression")
    selection = parser.parse_args(args)
    if platform.system() != "Darwin":
        raise WorkbenchError("Native canaries require macOS; no tests were run")
    for command in ("node", "npm", "codex", "claude", "pi", "clang"):
        if not shutil.which(command):
            raise WorkbenchError(f"Native canaries require {command} on PATH; no tests were run")
    # Never accept an existing home or enroll provider logins. Preparation only
    # resolves installed tools and installs the locked sandbox dependency tree.
    with tempfile.TemporaryDirectory(prefix="workbench-canary-", dir="/private/tmp") as raw:
        home = Path(raw).resolve()
        home.chmod(0o700)
        native.prepare(home)
        # Browser startup has its own tests. These probes use CLI/RPC and must
        # not depend on a host browser profile or an optional UI executable.
        tools_path = home / ".local/share/workbench/native/tools.json"
        tools = json.loads(tools_path.read_text())
        tools["browser"] = None
        tools_path.write_text(json.dumps(tools))
        env = {
            **os.environ,
            "WORKBENCH_NATIVE_CANARY_HOME": str(home),
            "TMPDIR": str(home),
        }
        print("Running real native probes with synthetic state; no model requests", flush=True)
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_native_canary.py",
                "--basetemp",
                str(home / "pytest"),
                "-q",
                "-k",
                selection.k,
            ],
            cwd=ROOT,
            env=env,
            check=False,
        ).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except (WorkbenchError, OSError, subprocess.CalledProcessError) as error:
        print(f"Native canaries failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
