"""Exact temporary forge backport shared by native preparation and dependency audit."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from workbench.core import AGENTS, WorkbenchError

# Remove with the first fixed upstream release; see docs/security/dependencies.md.
ADVISORY = "https://github.com/advisories/GHSA-86w9-cpqp-85rv"
ORIGINAL_SHA256 = "fd4740238145ec26470eb3f06a627c72039538ce1307dbdce40521f94dfd0a50"
PATCHED_SHA256 = "c9b1e3799e230528b6d6815c1f6cd3c6058b9d45975264b55d995abb976589af"
OLD = "            obj.value.length !== 2) {"
NEW = """            obj.value.length !== 2 ||
            obj.value[0].value.length !==
              (('parameters' in capture) ? 2 : 1)) {"""


def _forge_file(runtime: Path) -> Path:
    package = runtime / "node_modules/node-forge"
    if json.loads((package / "package.json").read_text()).get("version") != "1.4.0":
        raise WorkbenchError("Unexpected node-forge version; review and retire the backport")
    return package / "lib/rsa.js"


def verify_forge(runtime: Path) -> None:
    if hashlib.sha256(_forge_file(runtime).read_bytes()).hexdigest() != PATCHED_SHA256:
        raise WorkbenchError("node-forge backport checksum mismatch")


def patch_forge(runtime: Path) -> None:
    path = _forge_file(runtime)
    source = path.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest == PATCHED_SHA256:
        return
    if digest != ORIGINAL_SHA256 or source.count(OLD.encode()) != 1:
        raise WorkbenchError("Unexpected node-forge source checksum; refusing to patch")
    patched = source.replace(OLD.encode(), NEW.encode())
    if hashlib.sha256(patched).hexdigest() != PATCHED_SHA256:
        raise WorkbenchError("node-forge backport result checksum mismatch")
    path.write_bytes(patched)
    verify_forge(runtime)


def check_audit(report: object, returncode: int, runtime: Path) -> None:
    """Accept only the exact repaired finding and its propagated parent finding."""
    verify_forge(runtime)
    if not isinstance(report, dict) or report.get("error") or report.get("auditReportVersion") != 2:
        raise WorkbenchError("Invalid npm audit response")
    findings = report.get("vulnerabilities")
    if not isinstance(findings, dict) or returncode != (1 if findings else 0):
        raise WorkbenchError("npm audit failed or returned an inconsistent result")
    if report.get("metadata", {}).get("vulnerabilities", {}).get("total") != len(findings):
        raise WorkbenchError("npm audit finding count mismatch")
    expected = {
        "node-forge": ["node_modules/node-forge"],
        "@anthropic-ai/sandbox-runtime": ["node_modules/@anthropic-ai/sandbox-runtime"],
    }
    for name, finding in findings.items():
        if not isinstance(finding, dict) or name not in expected:
            raise WorkbenchError(f"Unpatched dependency finding: {name}")
        if finding.get("name") != name or finding.get("nodes") != expected[name]:
            raise WorkbenchError(f"Unexpected dependency finding location: {name}")
        # npm currently offers only a downgrade that removes newer sandbox fixes.
        downgrade = {
            "name": "@anthropic-ai/sandbox-runtime",
            "version": "0.0.50",
            "isSemVerMajor": True,
        }
        if finding.get("fixAvailable") is not False and finding.get("fixAvailable") != downgrade:
            raise WorkbenchError("npm offers a different fix; review and retire the backport")
        via = finding.get("via")
        if name == "node-forge":
            allowed = (
                isinstance(via, list)
                and len(via) == 1
                and isinstance(via[0], dict)
                and via[0].get("name") == name
                and via[0].get("url") == ADVISORY
            )
        else:
            allowed = via == ["node-forge"] and "node-forge" in findings
        if not allowed:
            raise WorkbenchError(f"Unpatched dependency advisory: {name}")


def audit() -> None:
    """Audit a fresh locked installation, prove the defect, then verify its repair."""
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
        probe = ["node", str(source / "verify-forge.cjs"), str(runtime)]
        subprocess.run([*probe, "--unpatched"], check=True)
        patch_forge(runtime)
        subprocess.run(probe, check=True)
        result = subprocess.run(
            ["npm", "audit", "--json", "--package-lock-only", "--ignore-scripts"],
            cwd=runtime,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            check_audit(json.loads(result.stdout), result.returncode, runtime)
        except (ValueError, WorkbenchError):
            print(result.stdout or result.stderr)
            raise
        print(
            f"OK sandbox dependency audit; {ADVISORY.rsplit('/', 1)[1]} locally patched and tested"
        )


if __name__ == "__main__":
    audit()
