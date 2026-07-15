# Language packs

Reference configuration for project-local code-health ratchets. A Go or Rust repo
can adopt the relevant suppression patterns and file globs without copying Python
defaults.

The workbench does not install a ratchet into every repo. Copy the relevant pack
only when a project has earned a deterministic health baseline, then keep the
project's implementation and baseline in that project.

## Pack schema (`<language>.json`)

| Field | Purpose |
|---|---|
| `language` | the pack's name (recorded in baselines.json) |
| `markers` | files whose presence at the repo root selects this pack |
| `files_glob` | the pathspec the ratchet counts over (`:(glob)`-expanded) |
| `run_from` | dir the glob is relative to |
| `suppression_patterns` | family → extended-regex; the ratchet recounts these (test files excluded) |
| `tools` | reference only — the canonical fmt/lint/types/test/coverage/complexity/mutation/audit command per language (informs the human + the findings ledger, not the ratchet) |

## Adding a language

Drop a `<language>.json` here following the schema. Keep `suppression_patterns`
factored so a pattern's literal
form can't match its own grep (e.g. `except (Exception|BaseException)`, not the bare
alternation). Per-language taste (pick/avoid, idioms) lives in `playbook/stacks/`; this is
just the gate wiring.
