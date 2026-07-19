"""Codex-native rendering and merging: TOML config, command rules, subagents."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping
from pathlib import Path

from workbench.core import AGENTS, CODEX_APPENDIX, WorkbenchError, _frontmatter_field
from workbench.mcp import merge_mcp


def expected_codex_rules_md() -> str:
    """Canonical ~/.codex/AGENTS.md content, shared by sync and drift."""
    return (AGENTS / "shared/rules.md").read_text().rstrip() + CODEX_APPENDIX


def _subagent_fields(path: Path) -> tuple[str, str, str, list[str] | None]:
    content = path.read_text()
    parts = content.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise WorkbenchError(f"invalid subagent frontmatter: {path}")
    frontmatter, body = parts[1], parts[2].strip()
    name = _frontmatter_field(frontmatter, "name")
    description = _frontmatter_field(frontmatter, "description")
    if not name or not description or not body:
        raise WorkbenchError(f"incomplete subagent: {path}")
    raw_tools = _frontmatter_field(frontmatter, "tools")
    tools = (
        [tool.strip() for tool in raw_tools.split(",") if tool.strip()]
        if raw_tools is not None
        else None
    )
    return name, description, body, tools


# Claude write-capable tools whose absence from a `tools:` restriction marks
# a subagent as read-only for Codex rendering purposes.
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def _render_codex_subagent(path: Path) -> str:
    name, description, instructions, tools = _subagent_fields(path)
    lines = [
        f"name = {json.dumps(name)}",
        f"description = {json.dumps(description)}",
    ]
    # Codex agent TOML has no per-tool allowlist equivalent to Claude's
    # `tools:` frontmatter, but its subagent schema does accept `sandbox_mode`
    # with "read-only" | "workspace-write" (verified against the codex
    # 0.144.4 binary: the subagent frontmatter parser enumerates
    # model_reasoning_effort, sandbox_mode, developer_instructions). Render
    # read-only sandboxing when the source restricts tools to a
    # non-writing set.
    if tools is not None and not (_WRITE_TOOLS & set(tools)):
        lines.append('sandbox_mode = "read-only"')
    lines.append(f"developer_instructions = {json.dumps(instructions)}")
    lines.append("")
    return "\n".join(lines)


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return (
            "{"
            + ", ".join(f"{json.dumps(str(k))} = {_toml_value(v)}" for k, v in value.items())
            + "}"
        )
    raise WorkbenchError(f"unsupported TOML value type: {type(value).__name__}")


def _render_mcp(servers: Mapping[str, object]) -> str:
    lines: list[str] = []
    for name, raw in sorted(servers.items()):
        lines.append(f"[mcp_servers.{name}]")
        if isinstance(raw, dict):
            lines.extend(f"{key} = {_toml_value(value)}" for key, value in raw.items())
        lines.append("")
    return "\n".join(lines)


def _drop_tables(text: str, prefixes: tuple[str, ...]) -> str:
    # Ceiling: line-based, not TOML-aware. A multi-line string whose body
    # contains a line that looks like a table header will be mis-parsed;
    # the round-trip tomllib guard in merge_codex_config catches the
    # corruption and aborts instead of writing it. Upgrade path: rewrite on
    # top of a real TOML parser/emitter (e.g. tomlkit) that preserves
    # comments and formatting.
    result: list[str] = []
    dropping = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("["):
            dropping = any(stripped.startswith(prefix) for prefix in prefixes)
        if not dropping:
            result.append(line)
    return "".join(result).rstrip()


def merge_codex_config(text: str) -> str:
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise WorkbenchError(f"invalid Codex TOML: {exc}") from exc

    existing = parsed.get("mcp_servers", {})
    if not isinstance(existing, dict):
        existing = {}
    servers = merge_mcp(existing, "codex")
    cleaned = _drop_tables(text, ("[mcp_servers", "[tui"))
    status = tomllib.loads((AGENTS / "codex/statusline.toml").read_text())
    existing_tui = parsed.get("tui", {})
    if not isinstance(existing_tui, dict):
        existing_tui = {}
    tui_values = {**existing_tui, **status}
    tui = "[tui]\n" + "\n".join(
        f"{key} = {_toml_value(value)}" for key, value in tui_values.items()
    )
    fallback = 'project_doc_fallback_filenames = ["CODEX.md"]'
    if "project_doc_fallback_filenames" not in parsed:
        cleaned = f"{fallback}\n\n{cleaned}" if cleaned else fallback
    defaults: list[str] = []
    if "sandbox_mode" not in parsed:
        defaults.append('sandbox_mode = "workspace-write"')
    if "approval_policy" not in parsed:
        defaults.append('approval_policy = "on-request"')
    if defaults:
        cleaned = "\n".join(defaults) + (f"\n\n{cleaned}" if cleaned else "")
    blocks = [part for part in (cleaned, _render_mcp(servers).rstrip(), tui) if part]
    merged = "\n\n".join(blocks) + "\n"
    try:
        tomllib.loads(merged)
    except tomllib.TOMLDecodeError as exc:
        raise WorkbenchError(f"generated invalid Codex TOML: {exc}") from exc
    return merged


def merge_codex_rules(canonical: str, live: str) -> str:
    """Preserve local approvals without retaining known policy bypasses.

    Codex appends interactively approved rules wherever the cursor lands, so
    unknown prefix_rule lines are harvested from the whole live file — not
    just the locally-approved section — deduped against the canonical rules,
    and re-homed under the marker.
    """
    canonical_lines = set(canonical.splitlines())
    marker = "# --- Locally approved additions ---"
    unsafe_fragments = (
        '"--no-verify"',
        '["git", "reset", "--hard"]',
        '["git", "push", "--force"]',
        '["git", "push", "-f"]',
        '["rm", "-rf"]',
        '["rm", "-fr"]',
    )
    additions: list[str] = []
    for line in live.splitlines():
        if (
            line.startswith("prefix_rule(")
            and line not in canonical_lines
            and line not in additions
            and not any(fragment in line for fragment in unsafe_fragments)
        ):
            additions.append(line)
    result = canonical.rstrip()
    if additions:
        result += f"\n\n{marker}\n" + "\n".join(additions)
    return result + "\n"
