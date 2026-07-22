# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Pi discovery telemetry

- **Started:** 2026-07-21
- **Review:** after seven days of ordinary Pi use, no later than 2026-07-28
- **Question:** does local metadata identify a concrete navigation or verification bottleneck?
- **Keep only if:** the report changes a harness, documentation, navigation, or test-selection decision.
- **Remove:** delete `agents/pi/extensions/discovery-telemetry.ts`, remove `discoveryTelemetry` from Pi settings, run `workbench sync pi`, and clear `~/.local/state/workbench/pi-discovery/`.

## Visible request ledger

- **Started:** 2026-07-22
- **Review:** 2026-08-05 or after ten qualifying multipart prompts
- **Question:** does showing and closing a numbered request ledger prevent dropped threads without adding distracting ceremony?
- **Keep only if:** it catches at least one omission or materially improves orientation on long prompts.
- **Remove:** revert the visible-ledger sentence in `agents/shared/rules.md`; retain the underlying requirement to reconcile multipart prompts internally.
- **Non-goal:** no task database, autonomous decomposition framework, or durable third action surface.

## Proposed, not active

- **Pi phone Web UI over Tailscale:** tracked in the private Work queue. Trial an audited existing package before building a client. Any trial needs its own dated entry here when it begins.
