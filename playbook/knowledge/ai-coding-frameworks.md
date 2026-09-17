# AI Coding Frameworks — Why This Skeleton Is Shaped This Way

A retrospective on the design of this workbench. The original version of this file was a pre-build survey of community meta-frameworks (Superpowers, GSD, oh-my-claudecode); this replaces it with the rationale for what actually shipped.

## The shipped architecture

- **Native skills, on demand.** Discipline lives in `agents/skills/*/SKILL.md` files loaded when a task matches, not in always-on instructions. Iron laws worth keeping (TDD, root-cause debugging, verify-before-done) are kept; the ceremony around them is not. Skills stay vendor-neutral so the same files serve Pi, Claude Code, and Codex.
- **Native status fields.** Harness-provided status/config surfaces are used as-is rather than wrapped.
- **Bounded native delegation.** Skills may dispatch one-level, task-specific agents when isolated context materially helps. Workbench deploys no permanent specialist roster and permits no agent hierarchies or swarm coordination.
- **Deterministic sync/check reconciliation.** the `workbench` CLI (`src/workbench/`) deploys canonical files to each harness and verifies the deployed state matches. Drift is detected mechanically, not by convention.

## Deliberate non-goals

- **No orchestration framework.** The harness already dispatches subagents; a coordination layer on top adds surface without adding capability.
- **No plugin wrapper.** Skills are plain markdown deployed by sync. Packaging as a vendor plugin would fork the portable format for distribution we don't need.
- **No always-on instruction growth.** The global rules file is small and stable; new discipline becomes a skill (loaded when relevant), never another permanent paragraph in every context window.
- **No permanent analytics platform.** Workbench does not ship network telemetry or a durable usage dashboard. Pi's local discovery experiment is a narrow, seven-day, metadata-only exception with an explicit decision date and removal path.

## Rejected alternatives, and why (still true)

- **Universal ceremony (Superpowers-style mandatory gates).** Firing the full brainstorm→plan→review pipeline on every task burns tokens on ceremony a one-line fix doesn't need. We kept selective discipline: gate on complexity, not existence.
- **Standalone wrapper CLI (GSD-style).** Owning the execution environment buys programmatic context management at the cost of maintaining a second harness that trails vendor releases. Native skills plus fresh subagent contexts cover the context-rot problem well enough here.
- **Permanent agent rosters (OMC-style).** Installed specialists duplicate portable skills and add vendor-specific deployment machinery. Use explicit bounded delegation instead.
- **Hard numeric code-shape rules as always-on directives** (max file/function lines, helper counts). These belong in deterministic project gates (linters, ratchets), not in prose an agent may or may not weigh.

Patterns from that survey that did survive, in evolved form: cross-model review became the `adversarial-assessor` skill; the "6-8 skills that matter" instinct became routing (a few entry-point skills like `code-health` that load lens references on demand) rather than a cap on skill count; context-budget awareness became progressive disclosure inside skills instead of a token ceiling rule.

## The shape in one sentence

Plain markdown discipline, loaded selectively, deployed deterministically, verified mechanically — and nothing that requires maintaining our own framework to keep working.

See also: `ai-tools.md` (tool landscape), `engineering-gates.md` (ratchet mechanics), `docs/decisions/tombstones.md` (rejected designs with fuller rationale).
