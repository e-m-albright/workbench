# Feature Catalogue

Timestamped map of maintained agent-intelligence capabilities in this repository.

**Snapshot:** 2026-09-03. Refresh the map and scale snapshot on demand during an explicit capability-health review, not during routine implementation.

## Scale snapshot

Counts are physical lines in the named source trees, including comments and blank
lines. They measure maintenance surface without forcing shared files into an
arbitrary capability bucket or counting one file twice.

| Source tree | Files | Lines | What it owns |
|---|---:|---:|---|
| `src/workbench/` plus `bin/workbench` | 10 | 1,675 | Deployment, drift, lint, rendering, MCP, and Codex merge |
| `agents/pi/extensions/` | 17 | 4,046 | Pi runtime extensions and connector adapters |
| `agents/skills/` | 73 | 5,760 | Portable workflows, references, and small supporting scripts |
| `agents/templates/` | 4 | 471 | Reusable owner-facing document templates |
| `playbook/` | 47 | 9,587 | Engineering doctrine, stack guidance, and research |
| `health/` | 2 | 74 | Portable deterministic health patterns |
| `docs/` | 6 | 693 | Current operational state, experiments, and decisions |
| `tests/` | 18 | 2,234 | Python and Pi behavior tests plus shared test data |

## Registry

| Capability | Posture |
|---|---|
| Workbench CLI, sync, drift, lint, rendering, MCP, and Codex merge | Core deployment engine |
| Pi extensions and direct connector adapters | Core local runtime layer |
| Shared rules, safety hooks, permission policy, and launchers | Core trust boundary |
| Reusable skills and their references | Core portable workflow library |
| Temporary handoff workflow | Active; explicit private state |
| Reusable prompts | Small supporting surface |
| Owner document templates | Small supporting surface; Pandoc-backed render contract |
| Engineering playbook | Active reference; review for staleness |
| Project-health kit | Small adoption contract |
| Capability, experiment, and decision documentation | Active head-state and tombstones |

## Capability map

### Configuration deployment and drift

- Canonical shared rules, skills, prompts, hooks, status lines, permission policy, MCP declarations, plugins, profiles, presets, and Pi extensions.
- Native deployment into Pi, Claude Code, and Codex.
- Staged tree replacement, bounded merges that preserve unmanaged state, one-file backups, retired-surface cleanup, and live drift reporting.
- CLI rendering, contextual help, linting, managed-surface validation, and privacy checks.

**Assessment:** Keep. This is Workbench's core reason to exist. Continue using vendor-native configuration and bounded merge logic. Reject additional abstraction when a direct file deployment is sufficient.

### Safety and permission boundary

- Shared destructive-shell and sensitive-file guards.
- Pi command classification, protected-path handling, connector trust rules, and remote MCP denial.
- Claude permissions and Codex safety-rule merging.
- Public/private boundary: public rules may point to optional machine-local private context, but never publish its contents.

**Assessment:** Keep and treat as high consequence. Tests should follow every newly allowed mutation path. Prefer denying an unsupported operation over broad pattern exceptions.

### Pi runtime extensions

- Activity naming, welcome, footer and quota display, presets, privacy-first local/frontier inference routing, consult, worker delegation, and Git safety.
- Confirmed GitHub workflow dispatch.
- Read-only Google, Calendar, Strava, and bounded Apple Notes integration surfaces.
- Agent Browser integration through the pinned native package rather than a competing browser layer.

**Assessment:** Keep selectively. Each extension must provide a capability Pi does not natively supply or enforce a local trust boundary. Review extensions when upstream Pi gains equivalent behavior; remove the local implementation rather than maintaining two paths.

### Reusable skills

- Planning and plan execution.
- Capability health, repository health, code health, and explicit whole-project health reviews.
- Testing and test-suite health, systematic debugging, code review, security review, and dependency audits.
- Frontend design, prototyping, project files, repository ontology, release, GitHub workflow, and workspace recovery.
- Agent instruction and skill authoring.
- Adversarial assessment, Paseo operations, Pi guidance, handoffs, and reflection.

**Assessment:** Keep, with aggressive deduplication. Skills should remain triggers and workflows that point to canonical doctrine. The health family separates portfolio value, repository operations, and implementation quality; `project-health-review` composes them without duplicating their rubrics. The deprecated `improvement-hunt` and `context-session-breakdown` aliases were removed after their migration window closed. Merge overlapping skills when they prescribe the same sequence or output contract; do not duplicate project-specific workflow instances here.

### Owner document templates

- A Notes-style call-script template renders canonical Markdown into a standalone
  HTML reading view for live conversations and rehearsal.
- Pandoc is an explicit optional dependency; `just check-documents` verifies the
  maintained example and runs in CI.

**Assessment:** Keep small. Add a template only for a recurring document job with
a distinct retrieval or interaction need; do not grow this into a general document
application or maintain duplicate Markdown and HTML prose.

### Engineering playbook and health kit

- Engineering philosophy, stack guidance, prompting, agent design, browser tooling, AI interface-design tooling, evaluation, open-model inference, infrastructure, security, and technology research.
- Small portable health-gate patterns and adoption guidance.

**Assessment:** Keep as a reference library, not an always-loaded instruction surface. This is the largest maintained body of prose. Review for stale versions, repeated doctrine, and guidance that no active repository uses.

### Handoffs and prompts

- Private temporary Markdown handoff lifecycle under local state.
- Small reusable prompt library for tasks that do not warrant a skill.

**Assessment:** Keep. Handoffs must remain temporary and explicit; durable knowledge belongs in repository documentation. Promote a prompt to a skill only when it needs a reliable trigger and workflow contract.

## Review triggers

- Remove a local Pi extension when upstream behavior becomes equivalent.
- Merge skills when their trigger, workflow, and output contract substantially overlap.
- Run capability health when the catalogue drifts, upstream behavior may replace a local capability, or the skill portfolio develops overlapping contracts.
- Run repository health when documentation, automation, dependencies, test feedback, or recurring chores accumulate maintenance drag.
- Reserve `project-health-review` for an explicit comprehensive pass; use the narrower health skill for ordinary grooming.
- Retire playbook guidance that is stale, duplicated, or unused by active repositories.
- Keep exact private project inventories in machine-local context only.
- Add a new deployment adapter only for a first-class supported harness with stable native configuration.
