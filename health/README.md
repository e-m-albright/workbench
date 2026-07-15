# Project Health

Workbench separates objective regression prevention from judgment.

## Deterministic Floor

Each project owns its native formatter, linter, type checker, tests, security
checks, and architectural constraints. CI runs the same `just check` developers
run locally.

Persist only thresholds that are meaningful for that project:

- coverage and mutation score floors
- maximum function complexity
- dependency cycles and forbidden imports
- duplication and dead-code ceilings
- vulnerability counts
- explicit suppressions such as ignored types, lint disables, skipped tests,
  and uncovered branches

Gate the delta rather than demanding an immediate cleanup of existing debt.
When a metric improves, lower its ceiling. Raising one requires a committed
reason. Do not ratchet total LOC or combine unlike metrics into a synthetic
score.

## Advisory Review

AI review covers qualities static tools cannot reliably measure: conceptual
integrity, module depth, naming, locality, accidental abstraction, and test
quality. A persisted assessment records its rubric version, model, evidence,
confidence, and open findings. It informs human review but does not block CI on
its raw score.

When the same advisory finding recurs and can be expressed objectively, convert
it into a test, linter rule, dependency constraint, or deterministic budget.

## Adoption

1. Use the repository's existing task runner and language-native tools.
2. Add one `check` command that runs the fast deterministic floor.
3. Record only current debt that a tool can count reproducibly.
4. Run an advisory review when design judgment is useful.
5. Delete health machinery that no longer catches real regressions.

The workbench provides patterns and review rubrics. It does not require every
project to install a shared framework.

For projects that adopt the bundled suppression ratchet, copy
`baseline.example.json` to `docs/health/<scope>/baselines.json`, narrow its
`files_glob`, and keep only patterns the project can count reliably. Store
advisory findings beside it in `findings.md` and dated `report-<date>.md` files.
