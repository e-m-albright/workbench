#!/usr/bin/env python3
"""Manage private, temporary Markdown handoffs shared across agent harnesses."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path


def state_root() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return base / "workbench/handoffs"


def queue(name: str) -> Path:
    root = state_root()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    path = root / name
    path.mkdir(exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def now() -> datetime:
    return datetime.now(UTC)


def timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:48] or "project"


def atomic_write(path: Path, content: str) -> None:
    descriptor, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw_temp)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            handle.write(content)
        temp.replace(path)
        path.chmod(0o600)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def save(args: argparse.Namespace) -> int:
    body = sys.stdin.read().strip()
    if not body:
        raise ValueError("handoff body must be provided on stdin")
    created = now()
    name = f"{created.strftime('%Y%m%dT%H%M%SZ')}-{slug(args.project)}-{uuid.uuid4().hex[:8]}.md"
    path = queue("ready") / name
    metadata = "\n".join(
        (
            "---",
            "handoff_version: 1",
            f"project: {json.dumps(args.project)}",
            f"repository: {json.dumps(args.repo or '')}",
            f"created_at: {timestamp(created)}",
            "status: ready",
            "---",
            "",
        )
    )
    atomic_write(path, f"{metadata}{body}\n")
    print(path)
    return 0


def project_of(path: Path) -> str | None:
    for line in path.read_text().splitlines()[:12]:
        if line.startswith("project: "):
            value = json.loads(line.removeprefix("project: "))
            return value if isinstance(value, str) else None
    return None


def latest(args: argparse.Namespace) -> int:
    candidates = [
        path
        for path in queue("ready").glob("*.md")
        if args.project is None or project_of(path) == args.project
    ]
    if not candidates:
        raise ValueError("no ready handoff found")
    print(max(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name)))
    return 0


def consume(args: argparse.Namespace) -> int:
    ready = queue("ready").resolve()
    source = Path(args.path).expanduser().resolve()
    if source.parent != ready or not source.is_file():
        raise ValueError("path is not a file in the ready handoff queue")

    consumed_at = timestamp(now())
    content = source.read_text()
    if "status: ready\n" not in content:
        raise ValueError("handoff is not ready")
    content = content.replace(
        "status: ready\n",
        f"status: consumed\nconsumed_at: {consumed_at}\n",
        1,
    )
    destination = queue("consumed") / source.name
    atomic_write(destination, content)
    source.unlink()
    print(destination)
    return 0


def prune(args: argparse.Namespace) -> int:
    cutoff = now() - timedelta(days=args.older_than_days)
    removed = 0
    for path in queue("consumed").glob("*.md"):
        modified = datetime.fromtimestamp(path.stat().st_mtime, UTC)
        if modified < cutoff:
            path.unlink()
            removed += 1
    print(removed)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    save_parser = commands.add_parser("save", help="save stdin as a ready handoff")
    save_parser.add_argument("--project", required=True)
    save_parser.add_argument("--repo")
    save_parser.set_defaults(handler=save)

    latest_parser = commands.add_parser("latest", help="print the newest ready handoff path")
    latest_parser.add_argument("--project")
    latest_parser.set_defaults(handler=latest)

    consume_parser = commands.add_parser(
        "consume", help="move one ready handoff to the consumed archive"
    )
    consume_parser.add_argument("path")
    consume_parser.set_defaults(handler=consume)

    prune_parser = commands.add_parser("prune", help="delete old consumed handoffs")
    prune_parser.add_argument("--older-than-days", type=int, default=7)
    prune_parser.set_defaults(handler=prune)
    return root


def main() -> int:
    args = parser().parse_args()
    if getattr(args, "older_than_days", 0) < 0:
        parser().error("--older-than-days must be non-negative")
    try:
        return int(args.handler(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"handoff: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
