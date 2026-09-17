# Audit Checklists §5–§11

Deeper checks for the workspace health audit. Run each section that applies to the repo; report into the same summary table as §1–§4 in [SKILL.md](../SKILL.md).

## 5. Duplicate Definitions (highest-value check)

Search for the same symbol defined in multiple locations. Focus on types parallel agents commonly duplicate:

**Python enums and models:**
```bash
grep -rn "class \w\+\(.*\(Enum\|BaseModel\)" . --include="*.py" | grep -v __pycache__
```
Group by class name. Flag any name appearing more than once — especially if the base types differ (StrEnum vs IntEnum, Pydantic v1 vs v2).

**Rust types:**
```bash
grep -rn "pub enum \|pub struct " . --include="*.rs"
```
Group by name. Flag duplicates that aren't in `tests/` or behind `#[cfg(test)]`.

**TypeScript types:**
```bash
grep -rnE "(export )?(interface|type) \w+" . --include="*.ts"
```

**Import consistency:**
For each duplicate found, trace all importers and verify they import from the canonical location.

## 6. Pattern Adoption Consistency

Check that patterns established by one workstream were adopted by all peers. Examples:

- **Factory pattern:** if a module establishes a `make_*` / `build_*` / `lazy_*` factory pattern, every peer should use it. Flag old `_build_*()` or one-off helpers.
- **Shared infrastructure:** check that shared modules are declared in their crate's `lib.rs` / package `index.ts` and have at least one importer. Flag orphaned modules.
- **Re-export / backward compat:** after a god-module split, check that parent modules re-export extracted symbols or that all callers updated their imports.

## 7. Compilation & Type Health

Run compilation checks as a final signal:

```bash
# Rust
cargo check 2>&1 | tail -20

# Python (if pyright/mypy configured)
pyright --outputjson 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(f'errors={d[\"summary\"][\"errorCount\"]} warnings={d[\"summary\"][\"warningCount\"]}')"

# TypeScript
tsc --noEmit
```

## 8. Dead Code Scan (lightweight)

Check for files that exist on disk but aren't imported or declared anywhere:

- **Rust:** For each `.rs` file in `src/`, verify it's either `mod`-declared in `lib.rs`/`main.rs` or is `lib.rs`/`main.rs`/`build.rs` itself.
- **Python:** For each `.py` file, verify it's either imported somewhere or is `__init__.py`/`conftest.py`/`__main__.py`.
- **Web (SvelteKit / Next.js):** Route files (`+page.svelte`, `page.tsx`, etc.) are discovered by the framework's filesystem router, **not** by imports. They will always appear as zero-importer files to static analysis tools. Never flag or delete route files based on import analysis. To verify a route is dead, check the running app — not the import graph.

## 9. Misplaced Artifacts

Scan tracked directories for files that look like working artifacts rather than permanent fixtures.

**Date-prefixed files in permanent directories:**
```bash
rg --files docs .agents/artifacts 2>/dev/null | rg '(^|/)20[0-9]{2}-[0-9]{2}-[0-9]{2}-'
```
Date-prefixed files (`YYYY-MM-DD-*`) are a strong signal of session-specific working artifacts. They belong in an ignored `.agents/artifacts/` directory, not tracked directories. Exception: files in `docs/specs/` or `docs/strategy/` may legitimately use date prefixes for versioned baselines.

**Bootstrap/handoff language in tracked files:**
```bash
grep -rl "continue from\|bootstrap\|handoff\|next session\|context transfer" docs/ --include="*.md" 2>/dev/null
```
Files containing session-continuation language are working artifacts.

**Stray markdown in project root:**
```bash
ls *.md 2>/dev/null | grep -v "README\|LICENSE\|CHANGELOG\|AGENTS\|CONTRIBUTING\|SECURITY"
```
Unexpected `.md` files in the root are often agent output that missed its target.

For each finding outside an explicitly-permitted directory: flag with severity MEDIUM, recommend moving to the appropriate ephemeral location.

## 10. Stale Artifacts

Scan ephemeral artifact directories for forgotten files:

```bash
rg --files .agents/artifacts -g '*.md' 2>/dev/null
```

For each file:
1. Check if the content was incorporated elsewhere (search for key phrases in git log or current codebase).
2. **Verdict:** DELETE (incorporated or abandoned), KEEP (still active), or ASK (ambiguous).

Goal: `.agents/artifacts/` contains only active working files, not a graveyard. Severity: LOW (these are local-only files, no git impact).

## 11. Tracked-but-Should-Be-Gitignored

```bash
git ls-files .agents/artifacts/ 2>/dev/null
```

If any files appear under a directory the project considers ephemeral, something is wrong with `.gitignore` or a file was force-added. Severity: HIGH.
