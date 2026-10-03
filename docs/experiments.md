# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Active

None.

## Proposed, not active

- **Cursor-style repository automation:** schedules, repository events, tightly scoped tools, explicit no-op outcomes, and a small deduplication ledger are credible patterns for recurring repository maintenance. Do not build a scheduler into Pi. Start a trial only when one concrete workflow recurs often enough to name its trigger, permissions, output destination, cost ceiling, and deterministic verification. Prefer GitHub Actions or the private automation layer as the runtime.
- **Provenance-aware sandboxed execution:** soft rules plus provenance tracking, a disposable credential-free workspace, default-deny egress, and parent-owned patch adoption are the credible response to indirect prompt injection. A future trial must isolate the filesystem and process space, account for DNS, redirects, proxies, loopback, metadata services, and alternate address forms, and keep reusable credentials outside the sandbox. Any authorized request should pass through a trusted broker that injects task-scoped authority, records the destination and operation, and can reduce permissions after setup. No trial is active. Revisit only when a recurring task requires execution against untrusted web, archive, package, or unfamiliar-repository content and the current explicit sandboxed-harness fallback proves materially restrictive or unreliable. Start with one bounded execution profile; do not build a universal classifier, taint engine, or general network broker before the workload exists.
- **Direct assistant versus owned business API:** compare a supervised read-only connector or skill with one application-owned reconciliation slice when a real workflow needs two sources and a proposed write. Measure setup time, source attribution, authorization gaps, review effort, recovery from ambiguous writes, and reuse across assistant clients. The owned slice should expose only normalized read, discrepancy, proposal, approval, and commit operations; keep canonical rules, process versions, audit, and idempotency in the service. Run this in the owning application with synthetic or narrowly scoped data. Review after one complete workflow and remove the experimental connector and endpoints if they do not reduce errors or repeated work. The [boundary rationale](../playbook/agents/integrations.md#direct-agent-integrations-and-application-owned-boundaries) is documented separately; no trial is active.

## Completed

- **Pi native fullscreen versus Transcript Reader (closed 2026-08-26):** adopted native fullscreen and retired the custom reader. The result and revisit trigger live in [`decisions/tombstones.md`](decisions/tombstones.md#retired-pi-harness-experiments).
- **Cross-harness mobile viewer (closed 2026-08-26):** standardized on Paseo over Tailscale. The retired Pi-specific and terminal variants live in [`decisions/tombstones.md`](decisions/tombstones.md#terminal-continuity-mobile-access-and-process-runners).

## Workbench Watch Items (2026-08)

Sync-simplifying upgrades the improvement hunt confirmed are not ready yet;
re-check occasionally.

- **`uv audit`** ([astral.sh/blog/uv-audit](https://astral.sh/blog/uv-audit), 2026-06-08) -- uv-native pip-audit replacement; would delete the pip-audit dev-dependency tree. Explicitly preview/unstable as of June 2026 — adopt when stabilized.
- **Exa hosted MCP** ([docs.exa.ai/reference/exa-mcp](https://docs.exa.ai/reference/exa-mcp)) -- remote Streamable HTTP endpoint at `mcp.exa.ai/mcp` could replace the stdio server and the stamp-time key-baking workaround; evaluate the auth tradeoff (OAuth vs key-in-URL) before switching.
- **Pi Packages** ([extensions docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)) -- npm/git distribution for Pi extensions/skills/themes. The real-file deployment remains the deliberate choice for owned, drift-checked config; revisit if extension count grows.
