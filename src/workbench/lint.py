"""Validate canonical repository sources: skills, links, JSON, TOML, shell."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

from workbench.core import AGENTS, ROOT, WorkbenchError, _frontmatter_field, load_json


def _markdown_link_errors(root: Path) -> list[str]:
    errors: list[str] = []
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for path in sorted(root.rglob("*.md")):
        # Skip dot-directories (.venv, .git): vendored docs are not repository sources.
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        fenced = False
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            for match in link_pattern.finditer(line):
                raw = match.group(1).split("#", 1)[0].strip().strip("<>")
                if not raw or "://" in raw or raw.startswith(("mailto:", "/")):
                    continue
                if not (path.parent / raw).resolve().exists():
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
    try:
        tomllib.loads((AGENTS / "codex/statusline.toml").read_text())
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"invalid Codex statusline TOML: {exc}")

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

    names: set[str] = set()
    for skill in sorted((AGENTS / "skills").glob("*/SKILL.md")):
        content = skill.read_text()
        name = _frontmatter_field(content, "name")
        if not name:
            errors.append(f"missing skill name: {skill.relative_to(ROOT)}")
            continue
        if name != skill.parent.name:
            errors.append(f"skill name/path mismatch: {skill.parent.name} != {name}")
        if name in names:
            errors.append(f"duplicate skill name: {name}")
        names.add(name)
        raw_description = _frontmatter_field(content, "description")
        if not raw_description:
            errors.append(f"missing skill description: {skill.relative_to(ROOT)}")
            continue
        if ": " in raw_description and not (
            raw_description.startswith('"') and raw_description.endswith('"')
        ):
            errors.append(f"skill description with colon must be quoted: {name}")
        length = len(raw_description.strip('"'))
        description_chars += length
        if length > 280:
            errors.append(f"skill description exceeds 280 chars: {name} ({length})")

    if description_chars > 5_000:
        errors.append(f"skill descriptions exceed 5000-char context budget: {description_chars}")

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
