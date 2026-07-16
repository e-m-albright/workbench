---
name: agents-md
description: Create or upgrade a project's AGENTS.md as the canonical agent instruction file, with CLAUDE.md/GEMINI.md symlinked to it. Use for "set up AGENTS.md", "onboard this repo for agents", or "create CLAUDE.md" (redirect to this convention).
---

# AGENTS.md Setup

The convention: one hand-written `AGENTS.md` is canonical; `CLAUDE.md` and `GEMINI.md` are symlinks to it so every harness loads the same instructions. If the user asks for a CLAUDE.md, build this instead and explain why — a real CLAUDE.md file forks instructions per vendor.

## 1. Inventory what exists

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` — files or already symlinks? A pre-existing CLAUDE.md with real content becomes the seed for AGENTS.md, then gets replaced by a symlink. Never leave two competing instruction files.
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

## 4. Set up the symlinks

```sh
ln -sf AGENTS.md CLAUDE.md
ln -sf AGENTS.md GEMINI.md
```

If a real CLAUDE.md existed, confirm its content is merged into AGENTS.md before replacing it. Verify with `ls -la` that both are symlinks, and check `.gitignore` doesn't exclude them.

## 5. Upgrading an existing AGENTS.md

Same discipline, subtractive first: delete stale commands (verify each by running it), remove anything README now covers, fold in what changed. An AGENTS.md that has only grown since creation is usually overdue for pruning.
