# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Active

None.

## Proposed, not active

- **Cursor-style repository automation:** schedules, repository events, tightly scoped tools, explicit no-op outcomes, and a small deduplication ledger are credible patterns for recurring repository maintenance. Do not build a scheduler into Pi. Start a trial only when one concrete workflow recurs often enough to name its trigger, permissions, output destination, cost ceiling, and deterministic verification. Prefer GitHub Actions or the private automation layer as the runtime.
- **Provenance-aware sandboxed execution:** soft rules plus provenance tracking, a disposable credential-free workspace, default-deny egress, and parent-owned patch adoption are the credible response to indirect prompt injection. No trial is active. Revisit only when a recurring task requires execution against untrusted web, archive, package, or unfamiliar-repository content and the current explicit sandboxed-harness fallback proves materially restrictive or unreliable. Start with one bounded execution profile, not a universal classifier, taint engine, or network broker.

## Completed

- **Pi native fullscreen versus Transcript Reader (closed 2026-08-26):** adopted native fullscreen and retired the custom reader. The result and revisit trigger live in [`decisions/tombstones.md`](decisions/tombstones.md#retired-pi-harness-experiments).
- **Cross-harness mobile viewer (closed 2026-08-26):** standardized on Paseo over Tailscale. The retired Pi-specific and terminal variants live in [`decisions/tombstones.md`](decisions/tombstones.md#terminal-continuity-mobile-access-and-process-runners).
