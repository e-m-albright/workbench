# Execution Discipline

How the planning criteria carry through into implementation. Separate from "should we build it" because the failure modes are different — over-engineering and scope sprawl rather than misalignment.

## Standing license to refactor (when crossed in flight)

You have standing authorization to unify, remove duplication, and build better abstractions when you cross them in the course of other work. You do not need to ask permission for every refactor.

A refactor is **acceptable** if it:

- Aligns the implementation with the stated design or charter.
- Removes a real duplication or abstraction smell encountered on the way.
- Improves extensibility for already-planned work.
- Ships with the tests/observability the surrounding code already has.

A refactor is **not** acceptable if it:

- Breaks a contract surface without versioning.
- Expands scope mid-execution without an explicit re-brainstorm.
- Touches code outside the change's blast radius for aesthetic reasons.
- "Improves" something with no link to a stated goal.

When in doubt between a small patch and a clean rewrite, lean toward the rewrite, but propose it explicitly first. Architectural decisions still surface explicitly in design docs before code lands; the refactor license expands what is *allowed*, it does not remove the discipline of designing first.

## Don't overengineer before core works

If a feature feels like "such a waste of time right now," put it on the roadmap and move on. Pre-core polish and configurability is wasted effort — the core will change shape and invalidate the polish.

When implementing, ask "does the core experience work yet?" If not, defer nice-to-haves (theme picker, settings page, edge-case error states) to roadmap items. Focus on the critical path.

## Multi-pass cadence

Defer aggressively to downstream brainstorms. A closeout should surface gaps; it should not pre-resolve every gap. The operating mode is multiple discrete brainstorm-and-execute passes, not one giant pass.

Triage before asking. Not every gap surfaced needs an answer this turn. Carry it forward.

Defer a question to a later pass when:

- The answer is downstream of a decision that has not been made yet.
- The question is about an artifact that does not exist yet.
- Answering now would require fabricating context the user has not yet provided.

Do NOT defer when:

- The user has explicitly raised the question.
- Deferring would create a parallel-state smell (e.g., two design docs ship with conflicting vocabulary for the same concept). In that case the question is load-bearing for downstream coherence and must be answered.

Multi-pass is sequenced by exit criteria, not by calendar. "Multiple passes" does not mean "multiple weeks"; it means multiple discrete brainstorm-and-execute cycles.

## Operational simplicity while strapped

Pre-customer or resource-strapped projects should prefer script-level discipline over new infrastructure for safety properties. The safety net is harness-level discipline, not isolation infrastructure.

- Don't spin up a parallel env for safety properties when a one-line guard in a script does the job.
- Don't introduce IAM-locked credentials as a workflow step until external customers exist.
- Reuse existing surfaces (terminal UIs, existing CLIs) before building new ones.

Exceptions where infrastructure-level enforcement IS appropriate:

- External customers exist and a safety failure would be visible to them.
- The work is destructive by nature (database migrations, history rewrites, file deletions). Backups and review are mandatory regardless.
- The user explicitly asks for the architecturally rigorous path on a specific decision. Honour the instruction.
