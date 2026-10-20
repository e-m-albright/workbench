# Feature Catalogue

Timestamped map of maintained agent-intelligence capabilities in this repository.

**Snapshot:** 2026-10-20. Refresh the map and counts on demand during an explicit capability-health review, not during routine implementation.

The [terminal launch design catalogue](docs/agents/launch-design.md) records the
managed/native launch split and the owner-approved
[six-model review corrections](docs/decisions/managed-launch-review.md).

## Scale snapshot

Run `just catalogue` to reproduce the scale table from the current tracked working tree. During an uncommitted review, `just catalogue --include-untracked` also includes new files that Git does not ignore. Deleted files and submodule directories are excluded. Counts are physical lines, including comments, blank lines, and a final unterminated line. Symlinks count as one line without following their targets.

The script assigns each text file to the first applicable group:

- **Generated/vendor:** files named `uv.lock`, `pnpm-lock.yaml`, or `package-lock.json`, and files beneath the root `vendor/` directory.
- **Code - tests:** every remaining text file beneath `tests/`, including helpers and declarative fixtures.
- **Code - source:** remaining `.py`, `.ts`, `.js`, `.mjs`, `.c`, `.sh`, `.zsh`, `.css`, and `.html` files, plus files beneath `bin/`. Files ending in `.config.ts` are configuration and stay in Text.
- **Text:** all remaining text, including documentation, instructions, configuration, prompts, and human-maintained examples.

Text must be UTF-8 without NUL bytes; other files are binary assets, reported by file count and bytes. Attribution is file-based; these repository totals deliberately avoid speculative per-capability splitting.

| Group | Files | Lines |
|---|---:|---:|
| Code - source | 46 | 9,873 |
| Code - tests | 38 | 8,203 |
| Text | 199 | 20,750 |
| Generated/vendor | 3 | 2,016 |
| **Source tree text total** | **286** | **40,842** |

Binary assets: 2 files, 223,107 bytes. Workbench contains 31 tracked local skills.
Archify and its external archive download pipeline are retired; reasons and
cleanup enforcement live in `RETIRED_SKILLS` in `src/workbench/core.py`.
Archify and Whiteboard remain [watch candidates for AI-led code understanding](playbook/engineering/review.md#change-comprehension-and-visualization).

## Registry

| Capability | Posture |
|---|---|
| Workbench CLI, sync, drift, lint, rendering, MCP, and Codex merge | Core deployment engine |
| Pi extensions and direct connector adapters | Shared harness; operations depend on inference and launch authority |
| Shared rules, safety hooks, permission policy, and launchers | Core trust boundary |
| Reusable skills and their references | Core portable workflow library; 31 local skills after repeated consolidation passes |
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
- Personal Pi and Codex defaults use `gpt-6.1-sol` with medium reasoning; Claude uses `opus` with medium effort. Work Pi leaves provider and model selection to host policy.
- Managed Claude links only its matching native project transcript namespace; settings and provider login handling remain separate.
- CLI rendering, contextual help, linting, managed-surface validation, and privacy checks.

**Assessment:** Keep. This is Workbench's core reason to exist. Continue using vendor-native configuration and bounded merge logic. Reject additional abstraction when a direct file deployment is sufficient.

### Safety and permission boundary

- Shared destructive-shell and sensitive-file guards.
- A native macOS boundary around `p`, `cc`, `co`, and their children; full vendor commands started from the host retain native authority.
- Pi command classification, protected-path handling, connector trust rules, and remote MCP denial.
- Claude permissions and Codex safety-rule merging.
- Public/private boundary: public rules may point to optional machine-local private context, but never publish its contents.

**Assessment:** Keep and treat as high consequence. Tests should follow every newly allowed mutation path. Prefer denying an unsupported operation over broad pattern exceptions.

### Pi runtime extensions

- Activity naming, welcome, footer and quota display, one development preset, explicit local/frontier inference routing, and Git safety in the shared harness.
- One worktree worker in native sessions or admitted sibling locations in managed sessions, retaining the parent's model selection and boundary. Review precedes explicit adoption/rejection; unique commits remain preserved and recursive worker entrypoints are blocked.
- Consult in native hosted sessions; managed sessions direct the owner to native Pi and local inference refuses cloud consult.
- Confirmed GitHub workflow dispatch and confirmed ingress discard.
- Read-only Strava tools for local inference. The Google connector is retired; Google data and Apple Notes remain outside the coding-agent boundary.
- Agent Browser integration through the pinned native package rather than a competing browser layer.

**Assessment:** Keep selectively. Each extension must provide a capability Pi does not natively supply or enforce a local trust boundary. Review extensions when upstream Pi gains equivalent behavior; remove the local implementation rather than maintaining two paths.

### Reusable skills

- Planning and plan execution.
- Capability health, repository health, code health, and explicit whole-project health reviews.
- Testing and test-suite health, systematic debugging, code review, security review, and dependency audits.
- Frontend design, prototyping, project files, repository ontology, release, GitHub workflow, workspace recovery, and document and presentation design.
- Agent instruction, skill authoring, and public-tool discovery through `tool-radar`.
- Adversarial assessment, Paseo operations, Pi guidance, handoffs, and reflection.

**Assessment:** Keep, with aggressive deduplication. Skills should remain triggers and workflows that point to canonical doctrine. The health family separates portfolio value, repository operations, and implementation quality; `project-health-review` composes them without duplicating their rubrics. Prior consolidation removed duplicate skills and expired aliases. Merge overlapping skills when they prescribe the same sequence or output contract; do not duplicate project-specific workflow instances here.

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
