"""Research runs freeze the topic baseline and expose incomplete evidence offline."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "research", Path(__file__).resolve().parents[1] / "scripts/research.py"
)
assert SPEC and SPEC.loader
research = importlib.util.module_from_spec(SPEC)


def load_module():
    SPEC.loader.exec_module(research)
    return research


def seed(tmp_path):
    root = tmp_path / "repo"
    topic = root / "playbook/agents/models/example.md"
    topic.parent.mkdir(parents=True)
    topic.write_text("# Models\n\n## Decision\n[Source](https://example.org/news)\n")
    (root / "playbook/README.md").write_text("# Index\n")
    (root / "playbook/watchlist.md").write_text("# Watch\n[Watch](https://example.org/)\n")
    return root, tmp_path / "run"


def prepare(tmp_path):
    module = load_module()
    root, output = seed(tmp_path)
    module.prepare(root, output, "2026-10-23", "2026-02-23")
    return module, root, output


def save(path, value):
    path.write_text(json.dumps(value))


def finish(output):
    coverage = json.loads((output / "coverage.json").read_text())
    for row in coverage:
        row.update(status="researched", note="Compared release notes.", sources=["S01"])
    save(output / "coverage.json", coverage)
    save(
        output / "evidence.json",
        {
            "schema_version": 1,
            "sources": [
                {
                    "id": "S01",
                    "title": "Release notes",
                    "url": "https://example.org/news",
                    "kind": "primary",
                    "published": "2026-10-20",
                    "retrieved": "2026-10-23",
                    "claim": "An upstream feature was released.",
                    "limitation": "Not tested locally.",
                }
            ],
        },
    )
    (output / "report.md").write_text("# Research\n\nRelease notes document a feature. [S01]\n")


def test_inventory_and_final_evidence(tmp_path):
    module, root, output = prepare(tmp_path)
    inventory = json.loads((output / "inventory.json").read_text())
    assert inventory["since"] == "2026-02-23"
    assert inventory["as_of"] == "2026-10-23"
    assert len(inventory["topics"]) == 2
    topic = next(row for row in inventory["topics"] if row["title"] == "Models")
    assert topic["path"] == "playbook/agents/models/example.md"
    assert topic["title"] == "Models"
    assert topic["headings"] == ["Models", "Decision"]
    assert topic["urls"] == ["https://example.org/news"]
    assert len(topic["sha256"]) == 64
    assert inventory["watchlist"]["urls"] == ["https://example.org/"]
    (root / topic["path"]).write_text("Changed after the snapshot")
    assert json.loads((output / "inventory.json").read_text()) == inventory
    with pytest.raises(ValueError, match="pending"):
        module.check(output)
    finish(output)
    assert module.check(output) == []


def test_prepare_refuses_overwrite_and_invalid_ranges(tmp_path):
    module, root, output = prepare(tmp_path)
    with pytest.raises(ValueError, match="exists"):
        module.prepare(root, output, "2026-10-23", "2026-02-23")
    for as_of, since in [("bad", "2026-02-23"), ("2026-10-23", "2027-01-01")]:
        target = tmp_path / "invalid"
        with pytest.raises(ValueError):
            module.prepare(root, target, as_of, since)
        assert not target.exists()


def test_symlinks_are_not_followed(tmp_path):
    module = load_module()
    root, output = seed(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "hidden.md").write_text("# Not a topic")
    (root / "playbook/linked").symlink_to(outside, target_is_directory=True)
    (root / "playbook/linked.md").symlink_to(outside / "hidden.md")
    module.prepare(root, output, "2026-10-23", "2026-10-16")
    assert len(json.loads((output / "inventory.json").read_text())["topics"]) == 2
    link = tmp_path / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        module.prepare(root, link / "run", "2026-10-23", "2026-10-16")
    finish(output)
    (output / "evidence.json").unlink()
    (output / "evidence.json").symlink_to(outside / "hidden.md")
    with pytest.raises(ValueError, match="symlink"):
        module.check(output)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("url", "file:///etc/passwd", "URL"),
        ("url", "https://user:pass@example.org/", "URL"),
        ("published", "2026-10-24", "date"),
        ("retrieved", "2026-10-24", "date"),
        ("kind", "rumor", "kind"),
        ("claim", "", "claim"),
        ("limitation", "", "limitation"),
        ("id", "wrong", "id"),
    ],
)
def test_bad_source_fields(tmp_path, field, value, message):
    module, _, output = prepare(tmp_path)
    finish(output)
    ledger = json.loads((output / "evidence.json").read_text())
    ledger["sources"][0][field] = value
    save(output / "evidence.json", ledger)
    with pytest.raises(ValueError, match=message):
        module.check(output)


def test_duplicate_sources_and_unknown_citations(tmp_path):
    module, _, output = prepare(tmp_path)
    finish(output)
    ledger = json.loads((output / "evidence.json").read_text())
    ledger["sources"].append(dict(ledger["sources"][0], id="S02"))
    save(output / "evidence.json", ledger)
    with pytest.raises(ValueError, match="duplicate"):
        module.check(output)
    finish(output)
    (output / "report.md").write_text("Unknown evidence [S99].")
    with pytest.raises(ValueError, match="S99"):
        module.check(output)
    (output / "report.md").write_text("No citations.")
    with pytest.raises(ValueError, match="uncited"):
        module.check(output)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "unknown-source", "note"])
def test_coverage_must_account_for_every_topic(tmp_path, mutation):
    module, _, output = prepare(tmp_path)
    finish(output)
    coverage = json.loads((output / "coverage.json").read_text())
    if mutation == "missing":
        coverage = []
    elif mutation == "extra":
        coverage.append(dict(coverage[0], topic="playbook/unknown.md"))
    elif mutation == "duplicate":
        coverage.append(coverage[0])
    elif mutation == "unknown-source":
        coverage[0]["sources"] = ["S99"]
    else:
        coverage[0]["note"] = ""
    save(output / "coverage.json", coverage)
    with pytest.raises(ValueError):
        module.check(output)


@pytest.mark.parametrize("bad", ["{", "null", "[]", '{"schema_version": 99}'])
def test_invalid_inventory_fails_cleanly(tmp_path, bad):
    module, _, output = prepare(tmp_path)
    (output / "inventory.json").write_text(bad)
    with pytest.raises(ValueError):
        module.check(output)


def test_undated_source_warns_without_inventing_chronology(tmp_path):
    module, _, output = prepare(tmp_path)
    finish(output)
    ledger = json.loads((output / "evidence.json").read_text())
    ledger["sources"][0]["published"] = None
    save(output / "evidence.json", ledger)
    assert "chronology" in module.check(output)[0]


@pytest.mark.parametrize("key", ["", "../outside.md", "/outside.md", "playbook/../outside.md"])
def test_invalid_topic_paths(tmp_path, key):
    module, _, output = prepare(tmp_path)
    inventory = json.loads((output / "inventory.json").read_text())
    inventory["topics"][0]["path"] = key
    save(output / "inventory.json", inventory)
    with pytest.raises(ValueError, match="path"):
        module.check(output)


@pytest.mark.parametrize("artifact", ["evidence.json", "coverage.json", "report.md"])
def test_missing_run_artifacts(tmp_path, artifact):
    module, _, output = prepare(tmp_path)
    finish(output)
    (output / artifact).unlink()
    with pytest.raises(ValueError, match="regular file"):
        module.check(output)


def test_cli_default_week_and_clean_failure(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/research.py"
    output = tmp_path / "run"
    created = subprocess.run(
        [sys.executable, str(script), "prepare", "--output", str(output), "--date", "2026-10-23"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Prepared" in created.stdout
    assert json.loads((output / "inventory.json").read_text())["since"] == "2026-10-16"
    rejected = subprocess.run(
        [sys.executable, str(script), "check", str(output)], capture_output=True, text=True
    )
    assert rejected.returncode == 1
    assert "pending" in rejected.stderr
    assert "Traceback" not in rejected.stderr
