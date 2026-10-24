"""Global deny patterns must not pin every directory against ordinary cleanup."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "agents/shared/shell/native-sandbox.mjs"
PLAN = {
    "mandatory_read": [
        "/**/confidential",
        "/**/vault/secret",
        "/synthetic-home/projects/*/sensitive/secret.json",
    ]
}


def policy_function():
    source = SCRIPT.read_text()
    return (
        "function mandatoryRules() {"
        + source.split("function mandatoryRules() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )


def node_json(probe):
    result = subprocess.run(
        ["node", "--input-type=module"],
        input=probe,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_mandatory_policy_pins_named_ancestors_without_recursive_root():
    probe = (
        'import path from "node:path";\n'
        + f"const plan = {json.dumps(PLAN)};\n"
        + "const denied = [], pinned = [];\n"
        + "const normalizePathForSandbox = value => value;\n"
        + "const removeTrailingGlobSuffix = value => value;\n"
        + 'const containsGlobChars = value => value.includes("*");\n'
        + "const denyGlobRegex = value => { denied.push(value); return value; };\n"
        + "const globToRegex = value => { pinned.push(value); return value; };\n"
        + policy_function()
        + "mandatoryRules(); console.log(JSON.stringify({denied, pinned}));\n"
    )
    result = node_json(probe)
    assert "/**/confidential" in result["denied"]
    assert "/**" not in result["pinned"]
    assert set(result["pinned"]) == {
        "/**/vault",
        "/synthetic-home/projects/*/sensitive",
        "/synthetic-home/projects/*",
    }


def test_installed_policy_denies_confidential_but_allows_ordinary_lock_unlink():
    runtime = (
        Path.home() / ".local/share/workbench/native/node_modules/@anthropic-ai/sandbox-runtime"
    )
    helpers = runtime / "dist/sandbox/sandbox-utils.js"
    if not helpers.is_file():
        pytest.skip("requires the prepared pinned sandbox runtime")
    pin = json.loads((SCRIPT.parents[1] / "sandbox/package.json").read_text())
    installed = json.loads((runtime / "package.json").read_text())
    assert installed["version"] == pin["dependencies"]["@anthropic-ai/sandbox-runtime"]
    probe = (
        'import path from "node:path";\n'
        + "import {containsGlobChars, normalizePathForSandbox, removeTrailingGlobSuffix} from "
        + json.dumps(helpers.as_uri())
        + ";\nimport {denyGlobRegex, globToRegex} from "
        + json.dumps((helpers.parent / "glob-pattern.js").as_uri())
        + ";\n"
        + f"const plan = {json.dumps(PLAN)};\n"
        + policy_function()
        + r"""
const rules = mandatoryRules();
const filters = [...rules.matchAll(/\((regex|literal|subpath) ("(?:[^"\\]|\\.)*")\)/g)]
  .map(([, kind, value]) => [kind, JSON.parse(value)]);
function deniesUnlink(value) {
  return filters.some(([kind, target]) => kind === "regex" ? new RegExp(target).test(value)
    : kind === "literal" ? value === target : value === target || value.startsWith(`${target}/`));
}
console.log(JSON.stringify({
  confidential: deniesUnlink("/synthetic-home/project/confidential/report.txt"),
  ordinaryLock: deniesUnlink("/synthetic-home/.pi/agent/auth.json.lock"),
  namedVault: deniesUnlink("/synthetic-home/private/vault"),
  boundedAncestor: deniesUnlink("/synthetic-home/projects/example/sensitive"),
}));
"""
    )
    assert node_json(probe) == {
        "confidential": True,
        "ordinaryLock": False,
        "namedVault": True,
        "boundedAncestor": True,
    }
