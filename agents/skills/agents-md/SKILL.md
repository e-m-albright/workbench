---
name: agents-md
description: Create or upgrade a project's AGENTS.md as the canonical agent instruction file. Use for "set up AGENTS.md", "onboard this repo for agents", or "create CLAUDE.md" (redirect to the native shared convention).
---

# AGENTS.md Setup

The convention: one hand-written `AGENTS.md` is canonical. Claude Code reads it natively. Keep a `GEMINI.md` symlink only when Gemini compatibility is needed. If the user asks for a `CLAUDE.md`, build `AGENTS.md` instead and explain that a real `CLAUDE.md` forks instructions per vendor while a symlink is now redundant.

## 1. Inventory what exists

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` — files or symlinks? Merge any unique instructions from a real `CLAUDE.md` into `AGENTS.md`, then remove `CLAUDE.md`. Preserve a `GEMINI.md` symlink only when that harness is in use. Never leave competing instruction files.
- `README.md`, `CONTRIBUTING.md`, `docs/` — what's already recorded there stays there. AGENTS.md points at it or omits it; it never duplicates it.
- Generated candidates (e.g. `/init` output): treat as raw material to prune hard, not as a finished file.

## 2. Interview the repo, not the user

Answer as much as possible from the repo itself; ask the user only what the repo can't tell you (the *why*, non-obvious constraints, forbidden areas).

- **Stack and tooling**: manifest files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`), lockfiles (which package manager), `justfile`/`Makefile`/npm scripts.
- **Entry points**: where execution starts, the one or two directories where real work happens.
- **Test command**: the exact invocation that runs the relevant tests, verified by running it.
- **Conventions**: formatter/linter config, CI workflow expectations, commit style from `git log`.

## 3. Write the smallest useful file

Structure:

- **`## Project Context`** — the what/why in a few sentences: what this repo is, who it serves, the one or two architectural facts an agent must know before editing.
- **Constraints** — project-specific rules that aren't discoverable from code: invariants ("never edit generated files under X"), required workflows, deploy realities.
- **Process** — the verified test/build/lint commands and anything the agent must run before claiming done.

Rules of thumb:

- Every line must change agent behavior. "Write clean code" doesn't; "run `just check` before committing" does.
- Prefer pointers over prose: link to README sections and docs rather than restating them.
- Global process/voice rules already live in the user's global instructions — don't repeat them per-project.
- A large domain glossary graduates to `DOMAIN.md`, referenced from AGENTS.md, so the always-loaded file stays lean.

### Review invariants

Treat project instructions as review guidance only when they capture a consequential, non-obvious invariant that reviewers would otherwise explain repeatedly. Formatting and other mechanical checks belong in deterministic tooling.

- State the invariant and the safe alternative, not only a prohibition.
- Keep repository-wide invariants at the root and put service or directory-specific guidance in the nearest nested `AGENTS.md`.
- Describe durable outcomes rather than current function names that will rot.
- Before retaining a new rule, test one violating change, one valid exception, and one unrelated change. The rule should catch the first without creating noise on the others.
- Remove or narrow rules that do not change review behavior or repeatedly produce false positives.

Source: OpenAI, [Custom Code Review rules for Codex](https://developers.openai.com/blog/custom-code-review-rules-for-codex).

## 4. Remove compatibility duplication

If `CLAUDE.md` exists, confirm that any unique content has been merged into `AGENTS.md`, then remove it. Claude Code now reads repository `AGENTS.md` directly.

If Gemini compatibility is required, expose the canonical file without duplicating content:

```bash
ln -sf AGENTS.md GEMINI.md
```

Verify the resulting files with `ls -la` and check that `.gitignore` does not exclude `AGENTS.md`.

## 5. Upgrading an existing AGENTS.md

Same discipline, subtractive first: delete stale commands (verify each by running it), remove anything README now covers, fold in what changed. An AGENTS.md that has only grown since creation is usually overdue for pruning.
