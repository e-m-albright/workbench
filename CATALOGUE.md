# Feature Catalogue

Timestamped map of maintained agent-intelligence capabilities in this repository.

**Snapshot:** 2026-09-07. Refresh the map and counts on demand during an explicit capability-health review, not during routine implementation.

## Scale snapshot

Counts are physical lines in tracked text blobs, including comments and blank lines. Tracked symlinks count as their one-line Git blob rather than duplicating their target. Every tracked file belongs to exactly one group:

- **Code - source:** executable implementation and styling maintained here.
- **Code - tests:** executable verification, including test helpers and fixtures.
- **Text:** documentation, instructions, configuration, prompts, and human-maintained examples.
- **Generated/vendor:** generated dependency state or third-party code retained in the repository.

Binary assets are reported by file count and bytes, not fake line counts. Attribution is file-based; these repository totals deliberately avoid speculative per-capability splitting.

| Group | Files | Lines |
|---|---:|---:|
| Code - source | 35 | 6,560 |
| Code - tests | 18 | 2,231 |
| Text | 164 | 18,086 |
| Generated/vendor | 78 | 115,388 |
| **Tracked text total** | **295** | **142,265** |

Binary assets: 3 tracked files, 227,224 bytes. The generated/vendor group is 114,767 lines of the pinned upstream Archify distribution plus the 621-line dependency lockfile. Archify is one skill, not 77 skills; Workbench currently contains 32 skills total.

## Registry

| Capability | Posture |
|---|---|
| Workbench CLI, sync, drift, lint, rendering, MCP, and Codex merge | Core deployment engine |
| Pi extensions and direct connector adapters | Core local runtime layer |
| Shared rules, safety hooks, permission policy, and launchers | Core trust boundary |
| Reusable skills and their references | Core portable workflow library; 32 skills after repeated consolidation passes |
| Archify diagram generation | Active trial; one vendored upstream skill with a disproportionate 114,767-line footprint |
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
- Frontend design, prototyping, project files, repository ontology, release, GitHub workflow, workspace recovery, and document and presentation design.
- Agent instruction, skill authoring, and public-tool discovery through `tool-radar`.
- Adversarial assessment, Paseo operations, Pi guidance, handoffs, reflection, and validated system-diagram generation through the vendored `archify` skill.

**Assessment:** Keep, with aggressive deduplication. Skills should remain triggers and workflows that point to canonical doctrine. The health family separates portfolio value, repository operations, and implementation quality; `project-health-review` composes them without duplicating their rubrics. Prior consolidation removed duplicate skills and expired aliases, so the current count is 32 rather than the 152 files under `agents/skills/`. Merge overlapping skills when they prescribe the same sequence or output contract; do not duplicate project-specific workflow instances here.

Archify is the exception to the usual small-skill shape. Workbench copied a complete upstream distribution from `tt-a1i/archify` and disabled its self-updater so local behavior stays reviewed, pinned, offline, and deterministic. This is vendoring, not a Workbench-owned fork, but it shifts upstream code and generated examples into this repository's maintenance surface. Before promoting the trial, evaluate replacing the copied runtime with a pinned upstream package or checkout while retaining only a small local skill wrapper and provenance lock. Do not count generated HTML examples as authored source.

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
- Decide whether Archify earns a vendored offline runtime after real use; otherwise retain a thin skill wrapper around a pinned upstream installation.
- Run capability health when the catalogue drifts, upstream behavior may replace a local capability, or the skill portfolio develops overlapping contracts.
- Run repository health when documentation, automation, dependencies, test feedback, or recurring chores accumulate maintenance drag.
- Reserve `project-health-review` for an explicit comprehensive pass; use the narrower health skill for ordinary grooming.
- Retire playbook guidance that is stale, duplicated, or unused by active repositories.
- Keep exact private project inventories in machine-local context only.
- Add a new deployment adapter only for a first-class supported harness with stable native configuration.
