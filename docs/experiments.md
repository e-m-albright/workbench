# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Active

None.

## Proposed, not active

- **Cursor-style repository automation:** schedules, repository events, tightly scoped tools, explicit no-op outcomes, and a small deduplication ledger are credible patterns for recurring repository maintenance. Do not build a scheduler into Pi. Start a trial only when one concrete workflow recurs often enough to name its trigger, permissions, output destination, cost ceiling, and deterministic verification. Prefer GitHub Actions or the private automation layer as the runtime.

## Completed

- **Pi native fullscreen versus Transcript Reader (closed 2026-08-26):** adopted native fullscreen and retired the custom reader at the owner's request. Fullscreen supplies search, scrolling, selection, links, and user-prompt jumps with no extension code. It does not reproduce final-answer landmarks or compact work summaries; those differences were not valuable enough to justify the custom surface.
- **Cross-harness mobile viewer (closed 2026-08-26):** standardized on Paseo over Tailscale for Pi, Claude Code, and Codex. The owner does not need phone terminal access, so Zellij web, tmux, Mosh, and the Mission Control session manager have no remaining job. Reconsider only if Paseo fails a concrete workflow that an existing cross-harness client cannot satisfy.
