"""Keep subject discovery and documentation references valid after relocation."""

import shutil

from workbench import core, lint


def test_subject_pages_need_no_individual_registration(tmp_path):
    playbook = tmp_path / "playbook"
    subject = playbook / "agents"
    subject.mkdir(parents=True)
    (playbook / "README.md").write_text("# Playbook\n")
    (subject / "README.md").write_text("# Agents\nAgent design and execution.\n")
    (subject / "new-topic.md").write_text("# New topic\n")

    assert lint._playbook_structure_errors(tmp_path) == []


def test_playbook_requires_subject_placement_and_scope(tmp_path):
    playbook = tmp_path / "playbook"
    (playbook / "agents").mkdir(parents=True)
    (playbook / "README.md").write_text("# Playbook\n")
    (playbook / "loose-topic.md").write_text("# Misplaced\n")

    errors = lint._playbook_structure_errors(tmp_path)

    assert len(errors) == 2
    assert any("subject overview missing: playbook/agents/README.md" in e for e in errors)
    assert any("place knowledge under a subject: playbook/loose-topic.md" in e for e in errors)


def test_markdown_links_validate_fragments_and_duplicate_headings(tmp_path):
    (tmp_path / "target.md").write_text(
        "# Target\n## Same heading\n## Same heading\n## Code `read` & write\n"
        '<a id="explicit"></a>\n'
    )
    (tmp_path / "source.md").write_text(
        "# Source\n[local](#source)\n[one](target.md#same-heading)\n"
        "[two](target.md#same-heading-1)\n[code](target.md#code-read--write)\n"
        "[explicit](target.md#explicit)\n[missing](target.md#absent)\n"
    )

    errors = lint._markdown_link_errors(tmp_path)

    assert len(errors) == 1
    assert "target.md#absent" in errors[0]


def test_markdown_examples_do_not_create_links_or_heading_targets(tmp_path):
    (tmp_path / "source.md").write_text(
        "# Source\n````md\n```python\n# Example\n```\n[example](missing.md)\n````\n"
        "~~~\n# Another example\n[example](missing.md)\n~~~\n[bad](#example)\n"
    )

    errors = lint._markdown_link_errors(tmp_path)

    assert len(errors) == 1
    assert "#example" in errors[0]


def test_skill_links_must_survive_deployment_but_may_reach_siblings(tmp_path):
    skills = tmp_path / "agents/skills"
    first = skills / "first"
    second = skills / "second"
    first.mkdir(parents=True)
    second.mkdir()
    (tmp_path / "README.md").write_text("# Repository\n")
    (first / "SKILL.md").write_text(
        "[sibling](../second/SKILL.md)\n[repository](../../../README.md)\n"
    )
    (second / "SKILL.md").write_text("# Second\n")

    errors = lint._markdown_link_errors(tmp_path)

    assert len(errors) == 1
    assert "skill link leaves deployed tree" in errors[0]


def test_ignored_artifacts_do_not_become_documentation_sources(tmp_path):
    for name in ("tmp", "artifacts", "node_modules", ".cache"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "generated.md").write_text("[temporary](missing.md)\n")

    assert lint._markdown_link_errors(tmp_path) == []


def test_canonical_skills_resolve_after_copy_to_unrelated_directory(tmp_path):
    shutil.copytree(core.AGENTS / "skills", tmp_path / "installed/skills")

    assert lint._markdown_link_errors(tmp_path, repository_root=core.ROOT) == []


def test_public_repository_references_are_checked_against_source_offline(tmp_path):
    (tmp_path / "guide.md").write_text("# Guide\n")
    (tmp_path / "links.md").write_text(
        "[guide](https://github.com/e-m-albright/workbench/blob/main/guide.md#guide)\n"
        "[missing](https://github.com/e-m-albright/workbench/blob/main/guide.md#missing)\n"
        "[vendor](https://example.com/unavailable.md)\n"
    )

    errors = lint._markdown_link_errors(tmp_path, repository_root=tmp_path)

    assert len(errors) == 1
    assert "guide.md#missing" in errors[0]
