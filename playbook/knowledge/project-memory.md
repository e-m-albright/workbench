# Project Memory and Decisions

Keep current instructions, durable decisions, and temporary working state in
separate places with explicit owners. A new session should find the current
contract without reconstructing a conversation.

## Current instructions

`AGENTS.md` owns project purpose, architecture, conventions, and operating rules.
Keep it concise enough to load on every task. Claude Code reads it natively;
retain a `GEMINI.md` symlink only where Gemini compatibility is needed.

Keep a small domain glossary in `AGENTS.md`. Move it to `DOMAIN.md` when it needs
independent structure or multiple bounded contexts, and link it from `AGENTS.md`.
Domain vocabulary describes concepts; agent instructions prescribe behavior.

## Durable decisions

Use the project's existing `docs/` structure. A short guide can own a settled
decision; use an architecture decision record when alternatives, consequences,
or a superseding decision deserve a durable record. The
[planning ADR template](../../agents/skills/planning/references/adr-format.md)
provides a starting point.

Record the problem, constraints, decision, evidence, consequences, and conditions
that would justify revisiting it. Distinguish an accepted decision from an
unverified assumption. Attribution should explain who supplied a constraint or
accepted a tradeoff, without creating a separate approval hierarchy.

When a decision changes, update the current guide and mark the older record as
superseded. Link the replacement and explain the changed premise. Git preserves
editing history; a separate chronological decision index is useful only when
readers need it.

Rejected tools and approaches belong in the project's decision records rather
than an active watchlist. In Workbench, code-enforced retirements keep their
reasons beside the off-switch; other retirements live in
[tombstones](../../docs/decisions/tombstones.md).

## Temporary state

Use [Working Files and Agent Artifacts](agent-output.md) for scratch files, plans,
research, and generated reading views. Use the
[handoff skill](../../agents/skills/handoff/SKILL.md) for cross-session continuity.
Neither is a substitute for maintained project documentation.

Promote settled knowledge into its owning document, then remove obsolete scratch
material. Keep private transcripts, credentials, and personal operating state
outside public repositories. Preserve a useful conclusion and its supporting
evidence rather than copying the conversation that produced it.
