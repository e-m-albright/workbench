# AI Coding Frameworks — Why This Skeleton Is Shaped This Way

A retrospective on the design of this workbench. The original version of this file was a pre-build survey of community meta-frameworks (Superpowers, GSD, oh-my-claudecode); this replaces it with the rationale for what actually shipped.

## The shipped architecture

- **Native skills, on demand.** Discipline lives in `agents/skills/*/SKILL.md` files loaded when a task matches, not in always-on instructions. Iron laws worth keeping (TDD, root-cause debugging, verify-before-done) are kept; the ceremony around them is not. Skills stay vendor-neutral so the same files serve Claude Code and Codex.
- **Native status fields.** Harness-provided status/config surfaces are used as-is rather than wrapped.
- **One-level subagents.** Specialists (reviewer, security auditor, debugger) are dispatched one level deep for isolated context. No agent hierarchies, no swarm coordination.
- **Deterministic sync/check reconciliation.** the `workbench` CLI (`src/workbench/`) deploys canonical files to each harness and verifies the deployed state matches. Drift is detected mechanically, not by convention.

## Deliberate non-goals

- **No orchestration framework.** The harness already dispatches subagents; a coordination layer on top adds surface without adding capability.
- **No plugin wrapper.** Skills are plain markdown deployed by sync. Packaging as a vendor plugin would fork the portable format for distribution we don't need.
- **No always-on instruction growth.** The global rules file is small and stable; new discipline becomes a skill (loaded when relevant), never another permanent paragraph in every context window.
- **No telemetry.** No cost tracking, session analytics, or usage dashboards. The reconciliation check is the only self-measurement.

## Rejected alternatives, and why (still true)

- **Universal ceremony (Superpowers-style mandatory gates).** Firing the full brainstorm→plan→review pipeline on every task burns tokens on ceremony a one-line fix doesn't need. We kept selective discipline: gate on complexity, not existence.
- **Standalone wrapper CLI (GSD-style).** Owning the execution environment buys programmatic context management at the cost of maintaining a second harness that trails vendor releases. Native skills plus fresh subagent contexts cover the context-rot problem well enough here.
- **Large agent rosters (OMC-style).** Dozens of specialized agents create "Oh-My-Zsh syndrome": easy to install everything, hard to know what's running. A small set of subagents with obvious triggers is legible.
- **Hard numeric code-shape rules as always-on directives** (max file/function lines, helper counts). These belong in deterministic project gates (linters, ratchets), not in prose an agent may or may not weigh.

Patterns from that survey that did survive, in evolved form: cross-model review became the `adversarial-assessor` skill; the "6-8 skills that matter" instinct became routing (a few entry-point skills like `code-health` that load lens references on demand) rather than a cap on skill count; context-budget awareness became progressive disclosure inside skills instead of a token ceiling rule.

## The shape in one sentence

Plain markdown discipline, loaded selectively, deployed deterministically, verified mechanically — and nothing that requires maintaining our own framework to keep working.

See also: `ai-tools.md` (tool landscape), `engineering-gates.md` (ratchet mechanics), `docs/decisions/tombstones.md` (rejected designs with fuller rationale).
