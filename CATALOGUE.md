# Feature Catalogue

Canonical map of maintained agent-intelligence capabilities in this repository. Update the affected row when a capability is added, removed, materially expanded, split, or consolidated.

## Counting method

Counts are physical lines in tracked files in the current working tree, including comments and blank lines. Implementation includes Python, TypeScript, shell, agent rules, prompts, and executable skill instructions. Tests are separate. Config/data includes vendor JSON/TOML, permission declarations, and project automation. The playbook, health kit, and decision documents are counted as maintained guidance rather than executable source. Attribution is file-based; shared files stay in a shared platform bucket.

## Registry

| Capability | Implementation/guidance | Tests | Config/data | Total | Posture |
|---|---:|---:|---:|---:|---|
| Workbench CLI, sync, drift, lint, rendering, MCP, and Codex merge | 1,566 | 889 | 265 | 2,720 | Core deployment engine |
| Pi extensions and direct connector adapters | 3,213 | 317 | 171 | 3,701 | Core local runtime layer |
| Shared rules, safety hooks, permission policy, and launchers | 439 | 213 | 223 | 875 | Core trust boundary |
| Reusable skills and their references | 4,720 | 0 | 0 | 4,720 | Core portable workflow library; contract checks live in the shared deployment-engine tests |
| Temporary handoff workflow | 276 | 99 | 0 | 375 | Active; explicit private state |
| Reusable prompts | 83 | 0 | 0 | 83 | Small supporting surface |
| Engineering playbook | 7,512 | 0 | 0 | 7,512 | Active reference; review for staleness |
| Project-health kit | 65 | 0 | 0 | 65 | Small adoption contract |
| Capability, experiment, and decision documentation | 650 | 0 | 0 | 650 | Active head-state and tombstones |

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

- Activity naming, welcome, footer and quota display, presets, consult, worker delegation, and Git safety.
- Confirmed GitHub workflow dispatch.
- Read-only Google, Calendar, Strava, and bounded Apple Notes integration surfaces.
- Agent Browser integration through the pinned native package rather than a competing browser layer.

**Assessment:** Keep selectively. Each extension must provide a capability Pi does not natively supply or enforce a local trust boundary. Review extensions when upstream Pi gains equivalent behavior; remove the local implementation rather than maintaining two paths.

### Reusable skills

- Planning and plan execution.
- Testing, systematic debugging, code review, security review, code health, and improvement hunts.
- Frontend design, prototyping, project files, repository ontology, release, GitHub workflow, and workspace recovery.
- Agent instruction and skill authoring.
- Adversarial assessment, Paseo operations, Pi guidance, handoffs, and reflection.

**Assessment:** Keep, with aggressive deduplication. Skills should remain triggers and workflows that point to canonical doctrine. Merge overlapping skills when they prescribe the same sequence or rubric; do not duplicate project-specific workflow instances here.

### Engineering playbook and health kit

- Engineering philosophy, stack guidance, prompting, agent design, browser tooling, evaluation, infrastructure, security, and technology research.
- Small portable health-gate patterns and adoption guidance.

**Assessment:** Keep as a reference library, not an always-loaded instruction surface. This is the largest maintained body of prose. Review for stale versions, repeated doctrine, and guidance that no active repository uses.

### Handoffs and prompts

- Private temporary Markdown handoff lifecycle under local state.
- Small reusable prompt library for tasks that do not warrant a skill.

**Assessment:** Keep. Handoffs must remain temporary and explicit; durable knowledge belongs in repository documentation. Promote a prompt to a skill only when it needs a reliable trigger and workflow contract.

## Review triggers

- Remove a local Pi extension when upstream behavior becomes equivalent.
- Merge skills when their trigger, workflow, and output contract substantially overlap.
- Retire playbook guidance that is stale, duplicated, or unused by active repositories.
- Keep exact private project inventories in machine-local context only.
- Add a new deployment adapter only for a first-class supported harness with stable native configuration.
