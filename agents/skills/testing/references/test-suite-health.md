# Test-Suite Health

Audit whether an existing test suite gives fast, trustworthy evidence. This is
a read-only assessment unless the user separately asks to implement fixes.

## Workflow

1. Read the test configuration, task-runner commands, CI jobs, markers, fixtures,
   and a representative path from each test tier.
2. Run the project's documented fast suite. Use existing duration, retry, and
   coverage reporting when available; do not install audit machinery merely to
   create a score.
3. Inspect failures and high-value samples for:
   - flaky behavior: time, randomness, ordering, shared state, external services;
   - weak assertions that prove execution but not the contract;
   - mocks that duplicate implementation or permit production-incompatible
     behavior;
   - skipped, quarantined, or expected-failure tests without an active owner;
   - slow tests in the default tier and cheap tests omitted from normal feedback;
   - load-bearing behavior with no effective regression coverage;
   - tests coupled to implementation details that block safe refactoring;
   - inconsistent placement, naming, fixtures, and tier markers.
4. Separate observed evidence from inference. A slow-looking integration test is
   not a performance finding without timing evidence; an uncovered line is not
   automatically a meaningful test gap.
5. Rank fixes by confidence gained relative to execution and maintenance cost.
   Prefer deleting redundant tests, strengthening one contract test, or moving a
   test to the correct tier over adding broad duplicate coverage.
6. Recommend deterministic follow-ups only for stable signals: duration budgets,
   retry counts, skipped-test ceilings, mutation floors, or coverage on a
   load-bearing scope. Gate deltas rather than demanding an immediate rewrite.

## Report

- **Verdict:** confidence, feedback speed, and the largest weakness.
- **Findings:** impact, evidence, affected tier, and recommended change.
- **Coverage gaps:** only load-bearing contracts whose absence was verified.
- **Deletion candidates:** redundant, assertion-free, or obsolete tests.
- **Deterministic follow-ups:** stable project-owned checks worth adopting.
- **Checked, clean:** tiers and failure classes examined without findings.
