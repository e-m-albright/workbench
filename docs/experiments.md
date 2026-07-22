# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Pi discovery telemetry

- **Started:** 2026-07-21
- **Review:** after seven days of ordinary Pi use, no later than 2026-07-28
- **Question:** does local metadata identify a concrete navigation or verification bottleneck?
- **Keep only if:** the report changes a harness, documentation, navigation, or test-selection decision.
- **Remove:** delete `agents/pi/extensions/discovery-telemetry.ts`, remove `discoveryTelemetry` from Pi settings, run `workbench sync pi`, and clear `~/.local/state/workbench/pi-discovery/`.

## Proposed, not active

- **Pi phone Web UI over Tailscale:** tracked in the private Work queue. Trial an audited existing package before building a client. Any trial needs its own dated entry here when it begins.
