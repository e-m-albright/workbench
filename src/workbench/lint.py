"""Validate canonical repository sources: skills, links, JSON, TOML, shell."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import yaml

from workbench.core import AGENTS, ROOT, WorkbenchError, load_json

# Single source for the skill-description context budget; the test suite
# imports these rather than re-deriving the rule.
PER_SKILL_DESCRIPTION_LIMIT = 280
DESCRIPTION_BUDGET = 5_500


def _frontmatter_mapping(text: str, path: Path) -> dict[str, object]:
    if not text.startswith("---\n"):
        raise WorkbenchError(f"missing opening frontmatter delimiter: {path}")
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise WorkbenchError(f"missing closing frontmatter delimiter: {path}")
    try:
        raw = yaml.safe_load(text[4:closing])
    except yaml.YAMLError as exc:
        raise WorkbenchError(f"invalid YAML frontmatter: {path}: {exc}") from exc
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise WorkbenchError(f"frontmatter must be a string-keyed object: {path}")
    return raw


def _markdown_link_errors(root: Path) -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in sorted(root.rglob("*.md")):
        # Skip dot-directories (.venv, .git): vendored docs are not repository sources.
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        # Ceiling: fences toggle on any ``` prefix, so a ````-wrapped block
        # containing ``` examples inverts the state. Fine at current usage;
        # match fence lengths if that ever appears in repository docs.
        fenced = False
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            for match in link_pattern.finditer(line):
                raw = match.group(1).split("#", 1)[0].strip().strip("<>")
                if not raw or "://" in raw or raw.startswith("mailto:"):
                    continue
                # Root-absolute links resolve against the repository root; the
                # convention is relative links, but a typo'd /path should fail
                # rather than being skipped.
                base = root / raw.lstrip("/") if raw.startswith("/") else path.parent / raw
                if not base.resolve().exists():
                    relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
                    errors.append(f"broken local link: {relative}:{line_number}: {raw}")
    return errors


def lint() -> int:
    errors: list[str] = []
    description_chars = 0
    for path in sorted(AGENTS.rglob("*.json")):
        try:
            load_json(path)
        except WorkbenchError as exc:
            errors.append(str(exc))
    for toml_path in sorted(AGENTS.rglob("*.toml")):
        try:
            tomllib.loads(toml_path.read_text())
        except tomllib.TOMLDecodeError as exc:
            errors.append(f"invalid TOML: {toml_path.relative_to(ROOT)}: {exc}")

    for entry in sorted((AGENTS / "skills").iterdir()):
        if entry.is_dir() and not (entry / "SKILL.md").exists():
            errors.append(f"skill directory without SKILL.md: {entry.relative_to(ROOT)}")

    # A reference file carrying SKILL.md frontmatter keys is demoted-skill
    # debris: the skill body moved under references/ but kept its metadata.
    debris_keys = ("name", "description", "disable-model-invocation", "allowed-tools")
    for reference in sorted((AGENTS / "skills").glob("*/references/*.md")):
        text = reference.read_text()
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) != 3:
            continue
        for key in debris_keys:
            if re.search(rf"^{key}:", parts[1], re.MULTILINE):
                errors.append(
                    "demoted-skill frontmatter in reference file: "
                    f"{reference.relative_to(ROOT)} ({key}:)"
                )
                break

    rule_pattern = re.compile(
        r'prefix_rule\(pattern=\["[^"]+"(?:,\s*"[^"]+")*\], decision="[a-z_-]+"\)'
    )
    rules_path = AGENTS / "codex/default.rules"
    for number, line in enumerate(rules_path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not rule_pattern.fullmatch(stripped):
            errors.append(f"invalid Codex rule syntax: {rules_path.relative_to(ROOT)}:{number}")

    for subagent in sorted((AGENTS / "subagents").glob("*.md")):
        content = subagent.read_text()
        try:
            frontmatter = _frontmatter_mapping(content, subagent)
        except WorkbenchError as exc:
            errors.append(str(exc))
            continue
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        tools = frontmatter.get("tools")
        if not isinstance(name, str) or name != subagent.stem:
            errors.append(f"subagent name/path mismatch: {subagent.relative_to(ROOT)}")
        if not isinstance(description, str) or not description:
            errors.append(f"missing subagent description: {subagent.relative_to(ROOT)}")
        if tools is not None and not isinstance(tools, str):
            errors.append(
                f"subagent tools must be a comma-separated string: {subagent.relative_to(ROOT)}"
            )
        closing = content.find("\n---\n", 4)
        if closing < 0 or not content[closing + 5 :].strip():
            errors.append(f"missing subagent body: {subagent.relative_to(ROOT)}")

    names: set[str] = set()
    for skill in sorted((AGENTS / "skills").glob("*/SKILL.md")):
        content = skill.read_text()
        try:
            frontmatter = _frontmatter_mapping(content, skill)
        except WorkbenchError as exc:
            errors.append(str(exc))
            continue
        name_value = frontmatter.get("name")
        if not isinstance(name_value, str) or not name_value:
            errors.append(f"missing skill name: {skill.relative_to(ROOT)}")
            continue
        name = name_value
        if name != skill.parent.name:
            errors.append(f"skill name/path mismatch: {skill.parent.name} != {name}")
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        names.add(name)
        description_value = frontmatter.get("description")
        if not isinstance(description_value, str) or not description_value:
            errors.append(f"missing skill description: {skill.relative_to(ROOT)}")
            continue
        length = len(description_value)
        description_chars += length
        if length > PER_SKILL_DESCRIPTION_LIMIT:
            errors.append(
                f"skill description exceeds {PER_SKILL_DESCRIPTION_LIMIT} chars: {name} ({length})"
            )

    if description_chars > DESCRIPTION_BUDGET:
        errors.append(
            f"skill descriptions exceed {DESCRIPTION_BUDGET}-char context budget: "
            f"{description_chars}"
        )

    # bin/wf's STARTERS array is a hand-listed subset of skills; a renamed or
    # retired skill must fail here rather than silently breaking the launcher.
    wf_text = (ROOT / "bin/wf").read_text()
    starters_match = re.search(r"STARTERS=\(\n(.*?)\)", wf_text, re.DOTALL)
    if not starters_match:
        errors.append("bin/wf: STARTERS array not found")
    else:
        for starter in starters_match.group(1).split():
            if not (AGENTS / "skills" / starter / "SKILL.md").exists():
                errors.append(f"bin/wf starter without a skill: {starter}")

    for script in sorted(AGENTS.rglob("*.sh")):
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        if result.returncode:
            errors.append(result.stderr.strip())
    errors.extend(_markdown_link_errors(ROOT))
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        return 1
    print(f"OK {len(names)} skills, JSON, TOML, and shell syntax")
    return 0
