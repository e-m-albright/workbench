---
name: testing
description: Design and implement tests, including vertical-slice TDD, test tiers, placement, markers, and affectedness. Use for "add tests", "what should I test", regression coverage, or red-green-refactor work.
---

# Testing Process

For ordinary coverage and test selection, use this file. When the user explicitly asks for test-driven development or the change benefits from a vertical red-green-refactor loop, read [tdd.md](references/tdd.md) and load its supporting references only as needed.

## Detect conventions first

Before writing any test, read the project's existing tests: framework, runner command, fixture patterns, naming, placement. Match them. A test that follows house conventions is worth more than a "better" test that introduces a second style.

For pytest projects, [python-pytest.md](references/python-pytest.md) has the marker convention, cost tiers, and directory layout.

## What to write

- **Cheapest test that exercises the real contract.** Prefer the lowest-cost tier (unit over integration over end-to-end) that still hits the actual behavior — not a mock of it.
- **Regression coverage at the right seam.** Every bug fix gets a test that failed before the fix, placed at the seam where the bug lived, not wherever is easiest to mock.

## What to run

- Run the tests affected by the change: map changed paths to their owning scope (package, service, module) and run that scope's tests.
- Widen to the full suite when core/shared code changed — a core change can break any consumer.

## Principles

- **Test behavior, not implementation.** Tests should survive refactors.
- **Prefer real dependencies over mocks.** A mock that passes while prod breaks is worse than no test.
- **Every bug fix gets a regression test.** No fix without proof it failed before.
- **Don't test framework code.** Trust your dependencies; test your logic.
- **Fast tests run often; slow tests run deliberately.** Hooks run free tests. CI runs cheap tests. Humans trigger the rest.

_Promoted from `.ai/rules/process/testing.mdc` (was an always-on rule; now an on-demand skill)._
