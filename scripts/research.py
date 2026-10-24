"""Prepare and structurally check an offline public technology research run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

LIMIT = 2_000_000
SOURCE_ID = re.compile(r"S[0-9]{2,}")
CITATION = re.compile(r"\[(S[0-9]{2,})\]")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def no_symlinks(path: Path) -> None:
    require(
        not any(part.is_symlink() for part in (path.absolute(), *path.absolute().parents)),
        f"symlink path is not allowed: {path}",
    )


def text(path: Path) -> str:
    no_symlinks(path)
    require(path.is_file(), f"expected regular file: {path}")
    require(path.stat().st_size <= LIMIT, f"file exceeds {LIMIT} bytes: {path}")
    return path.read_text(encoding="utf-8")


def dated(value: object) -> date:
    require(isinstance(value, str), f"expected ISO date, got {value!r}")
    require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value))), f"invalid date: {value!r}")
    return date.fromisoformat(str(value))


def snapshot(path: Path, root: Path) -> dict:
    content = text(path)
    headings = re.findall(r"^#{1,6} (.+)$", content, re.MULTILINE)
    urls = sorted(set(re.findall(r"https?://[^\s<>\)\]\"']+", content)))
    return {
        "path": path.relative_to(root).as_posix(),
        "title": headings[0] if headings else path.stem,
        "headings": headings,
        "urls": urls,
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
    }


def dump(path: Path, value: object) -> None:
    # Exclusive creation makes an accidental repeated preparation fail without overwriting.
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def prepare(root: Path, output: Path, as_of: str, since: str) -> None:
    require(dated(since) <= dated(as_of), "since date must not exceed as-of date")
    no_symlinks(output)
    require(not output.exists(), f"output already exists: {output}")
    playbook = root / "playbook"
    no_symlinks(playbook)
    require(playbook.is_dir(), f"missing playbook: {playbook}")
    topics = []
    for directory, directories, files in os.walk(playbook, followlinks=False):
        directories[:] = sorted(d for d in directories if not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix == ".md" and path != playbook / "watchlist.md" and not path.is_symlink():
                topics.append(snapshot(path, root))
    require(topics, "no topic pages found")
    inventory = {
        "schema_version": 1,
        "as_of": as_of,
        "since": since,
        "topics": sorted(topics, key=lambda topic: topic["path"]),
        "watchlist": snapshot(playbook / "watchlist.md", root),
    }
    output.mkdir(parents=True)
    dump(output / "inventory.json", inventory)
    dump(
        output / "coverage.json",
        [
            {"topic": topic["path"], "status": "pending", "note": "", "sources": []}
            for topic in inventory["topics"]
        ],
    )
    dump(output / "evidence.json", {"schema_version": 1, "sources": []})
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(
            f"---\ntitle: Technology research\n---\n\n"
            f"Research window: {since} through {as_of}.\n\n"
            "## What changes the next decision\n\n"
            "## What changed in the research window\n\n"
            "## New categories and counterarguments\n\n"
            "## Experiments and explicit deferrals\n\n"
            "## Sources and evidence limits\n"
        )
    print(f"Prepared {len(topics)} topics in {output}")


def document(output: Path, name: str):
    try:
        return json.loads(text(output / name))
    except json.JSONDecodeError as error:
        raise ValueError(f"{name}: invalid JSON: {error.msg}") from error


def source_records(ledger: object, as_of: date) -> tuple[set[str], list[str]]:
    require(
        isinstance(ledger, dict) and ledger.get("schema_version") == 1, "invalid evidence schema"
    )
    require(isinstance(ledger.get("sources"), list), "evidence.sources must be a list")
    ids, urls, warnings = set(), set(), []
    for source in ledger["sources"]:
        require(isinstance(source, dict), "source must be an object")
        for field in ("id", "title", "url", "kind", "claim", "limitation"):
            require(
                isinstance(source.get(field), str) and source[field].strip(),
                f"source requires nonempty {field}",
            )
        identifier = source["id"]
        require(SOURCE_ID.fullmatch(identifier), f"invalid source id: {identifier}")
        require(identifier not in ids, f"duplicate source id: {identifier}")
        ids.add(identifier)
        url = source["url"]
        parsed = urlsplit(url)
        require(
            parsed.scheme in {"http", "https"}
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and not re.search(r"[\s\x00-\x1f]", url),
            f"invalid source URL: {identifier}",
        )
        require(url not in urls, f"duplicate source URL: {identifier}")
        urls.add(url)
        require(
            source["kind"] in {"primary", "independent", "community"}, f"invalid kind: {identifier}"
        )
        retrieved = dated(source.get("retrieved"))
        require(retrieved <= as_of, f"retrieval date after as-of date: {identifier}")
        require("published" in source, f"published date or null required: {identifier}")
        if source["published"] is None:
            warnings.append(f"{identifier}: undated source; chronology is unproven")
        else:
            require(
                dated(source["published"]) <= retrieved,
                f"publication date after retrieval: {identifier}",
            )
    return ids, warnings


def check(output: Path) -> list[str]:
    inventory = document(output, "inventory.json")
    require(
        isinstance(inventory, dict) and inventory.get("schema_version") == 1,
        "invalid inventory schema",
    )
    as_of = dated(inventory.get("as_of"))
    require(dated(inventory.get("since")) <= as_of, "invalid inventory date range")
    require(isinstance(inventory.get("topics"), list) and inventory["topics"], "missing topics")
    topics = set()
    for topic in inventory["topics"]:
        require(isinstance(topic, dict), "invalid inventory topic")
        key = topic.get("path")
        require(isinstance(key, str), "topic path must be a string")
        path = PurePosixPath(key)
        require(
            bool(path.parts)
            and not path.is_absolute()
            and ".." not in path.parts
            and path.parts[0] == "playbook"
            and path.suffix == ".md",
            f"invalid inventory topic path: {key}",
        )
        require(key not in topics, f"duplicate inventory topic: {key}")
        require(re.fullmatch(r"[a-f0-9]{64}", str(topic.get("sha256"))), f"invalid hash: {key}")
        topics.add(key)
    coverage = document(output, "coverage.json")
    require(isinstance(coverage, list), "coverage must be a list")
    # Validate coverage before sources so a new run immediately exposes its pending work.
    covered = set()
    for row in coverage:
        require(isinstance(row, dict), "coverage row must be an object")
        key = row.get("topic")
        require(isinstance(key, str) and key in topics, f"unknown coverage topic: {key}")
        require(key not in covered, f"duplicate coverage topic: {key}")
        covered.add(key)
        status = row.get("status")
        require(
            status in ("researched", "reviewed", "deferred"), f"pending or invalid status: {key}"
        )
        require(
            isinstance(row.get("note"), str) and row["note"].strip(),
            f"missing coverage note: {key}",
        )
        require(
            isinstance(row.get("sources"), list)
            and all(isinstance(item, str) for item in row["sources"]),
            f"invalid coverage sources: {key}",
        )
        require(status != "researched" or row["sources"], f"researched topic needs sources: {key}")
    require(covered == topics, f"missing coverage topics: {sorted(topics - covered)}")
    ids, warnings = source_records(document(output, "evidence.json"), as_of)
    for row in coverage:
        require(not (set(row["sources"]) - ids), f"unknown source in coverage: {row['topic']}")
    report = text(output / "report.md")
    require(report.strip(), "empty report")
    cited = set(CITATION.findall(report))
    require(not (cited - ids), f"unknown report citations: {sorted(cited - ids)}")
    require(not (ids - cited), f"uncited evidence records: {sorted(ids - cited)}")
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("prepare", help="freeze local topics; make no network requests")
    start.add_argument("--output", required=True, type=Path)
    start.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    start.add_argument("--since", help="default: seven days before --date")
    validate = commands.add_parser("check", help="check structure, not factual accuracy")
    validate.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            since = args.since or (dated(args.date) - timedelta(days=7)).isoformat()
            prepare(Path(__file__).resolve().parents[1], args.output, args.date, since)
        else:
            for warning in check(args.directory):
                print(f"Warning: {warning}")
            print(
                "Structure valid. Facts, source independence, and search completeness "
                "are NOT verified."
            )
    except (ValueError, OSError) as error:
        parser.exit(1, f"research: {error}\n")


if __name__ == "__main__":
    main()
