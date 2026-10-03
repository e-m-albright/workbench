"""Security backports must fail closed and leave unrelated audit findings visible."""

import hashlib

import pytest

from workbench import native_dependencies as deps
from workbench.core import WorkbenchError


def forge_tree(tmp_path, monkeypatch):
    package = tmp_path / "node_modules/node-forge"
    (package / "lib").mkdir(parents=True)
    (package / "package.json").write_text('{"version":"1.4.0"}')
    original = ("before\n" + deps.OLD + "\nafter\n").encode()
    patched = original.replace(deps.OLD.encode(), deps.NEW.encode())
    monkeypatch.setattr(deps, "ORIGINAL_SHA256", hashlib.sha256(original).hexdigest())
    monkeypatch.setattr(deps, "PATCHED_SHA256", hashlib.sha256(patched).hexdigest())
    path = package / "lib/rsa.js"
    path.write_bytes(original)
    return path, patched


def test_backport_requires_exact_source_and_is_idempotent(tmp_path, monkeypatch):
    path, patched = forge_tree(tmp_path, monkeypatch)
    deps.patch_forge(tmp_path)
    assert path.read_bytes() == patched
    deps.patch_forge(tmp_path)
    deps.verify_forge(tmp_path)
    path.write_bytes(patched + b"changed")
    with pytest.raises(WorkbenchError, match="checksum"):
        deps.patch_forge(tmp_path)


def test_unpatched_or_changed_version_is_rejected(tmp_path, monkeypatch):
    path, _ = forge_tree(tmp_path, monkeypatch)
    with pytest.raises(WorkbenchError, match="checksum"):
        deps.verify_forge(tmp_path)
    path.parent.parent.joinpath("package.json").write_text('{"version":"1.4.1"}')
    with pytest.raises(WorkbenchError, match="version"):
        deps.patch_forge(tmp_path)


def report():
    return {
        "auditReportVersion": 2,
        "vulnerabilities": {
            "node-forge": {
                "name": "node-forge",
                "fixAvailable": False,
                "nodes": ["node_modules/node-forge"],
                "via": [{"name": "node-forge", "url": deps.ADVISORY}],
            },
            "@anthropic-ai/sandbox-runtime": {
                "name": "@anthropic-ai/sandbox-runtime",
                "fixAvailable": False,
                "nodes": ["node_modules/@anthropic-ai/sandbox-runtime"],
                "via": ["node-forge"],
            },
        },
        "metadata": {"vulnerabilities": {"total": 2}},
    }


def test_audit_accepts_only_verified_backport(tmp_path, monkeypatch):
    forge_tree(tmp_path, monkeypatch)
    with pytest.raises(WorkbenchError):
        deps.check_audit(report(), 1, tmp_path)
    deps.patch_forge(tmp_path)
    deps.check_audit(report(), 1, tmp_path)


@pytest.mark.parametrize("change", ["advisory", "location", "package", "error", "status", "empty"])
def test_audit_rejects_other_findings_and_invalid_responses(tmp_path, monkeypatch, change):
    forge_tree(tmp_path, monkeypatch)
    deps.patch_forge(tmp_path)
    data = report()
    status = 1
    if change == "advisory":
        data["vulnerabilities"]["node-forge"]["via"].append({"url": "another-advisory"})
    elif change == "location":
        data["vulnerabilities"]["node-forge"]["nodes"].append("node_modules/other/node-forge")
    elif change == "package":
        data["vulnerabilities"]["other"] = {"via": ["node-forge"]}
    elif change == "error":
        data["error"] = {"code": "ENETWORK"}
    elif change == "status":
        status = 2
    else:
        data = {}
    with pytest.raises(WorkbenchError):
        deps.check_audit(data, status, tmp_path)


def test_audit_accepts_known_unsafe_downgrade_but_demands_review_of_new_fix(tmp_path, monkeypatch):
    forge_tree(tmp_path, monkeypatch)
    deps.patch_forge(tmp_path)
    data = report()
    fix = {"name": "@anthropic-ai/sandbox-runtime", "version": "0.0.50", "isSemVerMajor": True}
    data["vulnerabilities"]["node-forge"]["fixAvailable"] = fix
    deps.check_audit(data, 1, tmp_path)
    fix["version"] = "0.0.79"
    with pytest.raises(WorkbenchError, match="retire"):
        deps.check_audit(data, 1, tmp_path)
    data["vulnerabilities"]["node-forge"]["fixAvailable"] = True
    with pytest.raises(WorkbenchError, match="retire"):
        deps.check_audit(data, 1, tmp_path)
