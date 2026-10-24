"""In-memory sync preview at the existing filesystem mutation seams.

This is deliberately not a filesystem emulator: only managed text, copied skill
roots, removals, and modes are projected. Vendor installations are listed, never
run; their resulting assets require a subsequent sync to verify.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Preview:
    files: dict[Path, str] = field(default_factory=dict)
    trees: dict[Path, Path] = field(default_factory=dict)
    removed: set[Path] = field(default_factory=set)
    operations: dict[Path, str] = field(default_factory=dict)
    plugins: list[str] = field(default_factory=list)

    def source(self, path: Path) -> Path:
        for destination, source in self.trees.items():
            if path.is_relative_to(destination):
                return source / path.relative_to(destination)
        return path

    def exists(self, path: Path) -> bool:
        if path in self.files or path in self.trees:
            return True
        if any(path == removed or path.is_relative_to(removed) for removed in self.removed):
            return False
        if any(child.is_relative_to(path) for child in (*self.files, *self.trees)):
            return True
        return self.source(path).exists()

    def text(self, path: Path) -> str:
        return self.files[path] if path in self.files else self.source(path).read_text()

    def write(self, path: Path, content: str, *, mode: int | None = None) -> None:
        exists = self.exists(path)
        if not exists or self.text(path) != content:
            self.operations.setdefault(path, "UPDATE" if exists else "CREATE")
            self.files[path] = content
        elif mode is not None and path.exists() and path.stat().st_mode & 0o777 != mode & 0o777:
            self.operations.setdefault(path, "MODE")

    def remove(self, path: Path, *, report: bool = True) -> None:
        if self.exists(path) or path.is_symlink():
            self.removed.add(path)
            if report:
                self.operations[path] = "REMOVE"


_active: ContextVar[Preview | None] = ContextVar("sync_preview", default=None)


def current() -> Preview | None:
    return _active.get()


@contextmanager
def preview_sync() -> Iterator[Preview]:
    preview = Preview()
    token = _active.set(preview)
    try:
        yield preview
    finally:
        _active.reset(token)


def exists(path: Path) -> bool:
    preview = current()
    return preview.exists(path) if preview else path.exists()


def glob(root: Path, pattern: str) -> list[Path]:
    paths = set(root.glob(pattern))
    plan = current()
    if plan is not None:
        paths.update(path for path in plan.files if path.parent == root and path.match(pattern))
        paths = {path for path in paths if plan.exists(path)}
    return sorted(paths)


def resolve(path: Path, *, strict: bool = False) -> Path:
    plan = current()
    if plan is not None and path in plan.files:
        return path.absolute()
    return path.resolve(strict=strict)


def read_text(path: Path) -> str:
    preview = current()
    return preview.text(path) if preview else path.read_text()
