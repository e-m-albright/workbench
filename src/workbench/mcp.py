"""Shared MCP registry: active servers per target, tombstones, and merging."""

from __future__ import annotations

import re
from collections.abc import Mapping

from workbench.core import AGENTS, WorkbenchError, load_json


def _registry() -> dict[str, object]:
    raw = load_json(AGENTS / "shared/mcp-servers.json", {})
    if not isinstance(raw, dict):
        raise WorkbenchError("MCP registry must be a JSON object")
    return raw


def retired_mcp_names(registry: Mapping[str, object] | None = None) -> set[str]:
    names: set[str] = set()
    for key in registry if registry is not None else _registry():
        match = re.fullmatch(r"_(.+)_disabled", key)
        if match:
            names.add(match.group(1))
    return names


def active_mcp(
    target: str, registry: Mapping[str, object] | None = None
) -> dict[str, dict[str, object]]:
    if registry is None:
        registry = _registry()
    servers: dict[str, dict[str, object]] = {}
    for name, value in registry.items():
        if name.startswith("$") or not isinstance(value, dict):
            continue
        targets = value.get("targets", [])
        if isinstance(targets, list) and target in targets:
            servers[name] = {key: item for key, item in value.items() if key != "targets"}
    return servers


def merge_mcp(existing: Mapping[str, object], target: str) -> dict[str, object]:
    registry = _registry()
    retired = retired_mcp_names(registry)
    desired = active_mcp(target, registry)
    managed = {
        name
        for name, value in registry.items()
        if not name.startswith("$") and isinstance(value, dict)
    }
    kept = {
        name: value
        for name, value in existing.items()
        if name not in retired and (name not in managed or name in desired)
    }
    return {**kept, **desired}


def _desktop_mcp() -> dict[str, dict[str, object]]:
    raw = {**active_mcp("claude"), **active_mcp("desktop")}
    result: dict[str, dict[str, object]] = {}
    for name, config in raw.items():
        if config.get("type") == "http" and isinstance(config.get("url"), str):
            args: list[str] = ["-y", "mcp-remote", str(config["url"])]
            headers = config.get("headers", {})
            if isinstance(headers, dict):
                args.extend(f"--header={key}:{value}" for key, value in headers.items())
            result[name] = {"command": "npx", "args": args}
        else:
            result[name] = config
    return result
