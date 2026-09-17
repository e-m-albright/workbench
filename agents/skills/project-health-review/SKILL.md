---
name: project-health-review
description: Combine capability, repository, and code health into one ranked plan. Use for an explicit full health review or whole-project audit.
allowed-tools: Read Grep Glob Bash(git:*) Bash(rg:*) Bash(ls:*) Bash(wc:*) Bash(just:*) Bash(fd:*) Agent WebSearch WebFetch
disable-model-invocation: true
---

# Project Health Review

Run an explicit, comprehensive review across the project's three health layers:

1. **Capability health** — does the project own the right capabilities?
2. **Repository health** — is the operating layer truthful, current, and
   efficient?
3. **Code health** — is the implementation structurally maintainable, reliable,
   secure, and performant under its composed review model?

This is the successor to the broad improvement hunt. It is user-invoked because
whole-project review is expensive and should not auto-trigger from an ordinary
request to improve one area. The review is read-only; implementation happens in
follow-up sessions selected from the report.

## Workflow

1. **Confirm scope and budget.** Identify the repository, excluded surfaces,
   available delegation, current date, and whether cross-repository comparison
   is explicitly in scope. Default to the current repository only.
2. **Orient once.** Read project instructions, purpose, feature map, task runner,
   top-level tree, health records, and decisions. Share this factual context
   across the passes without forcing them toward the same conclusions.
3. **Run the three passes.** Read and follow:
   - [Capability health](../capability-health/SKILL.md)
   - [Repository health](../repository-health/SKILL.md)
   - [Code health](../code-health/SKILL.md)

   Run independent read-only passes in parallel only when scope is large enough
   to repay coordination. Keep synthesis and final verification in the parent
   context.
4. **Compose specialist audits.** Follow the routing in the three skills for
   testing, dependency, security, correctness, and performance concerns. Do not
   recreate their rubrics in this orchestrator.
5. **Verify and deduplicate.** Confirm each finding against actual evidence.
   Assign it to one primary owner. Merge symptoms caused by the same underlying
   decision into one workstream.
6. **Rank the project, not each silo.** Compare capability value, repository
   drag, implementation health, risk, and effort together. A low-level cleanup
   must not outrank a capability cut that deletes the affected surface.
7. **Propose a sequence.** Delete or cut first, settle capability and boundary
   decisions next, repair the operating layer, then refactor what remains.

## Integrated report

1. **Executive verdict** — the shortest path to the best stable version of the
   project.
2. **Health by layer** — capability, repository, and code conclusions, including
   checked-clean areas and uncertainty.
3. **Ranked workstreams** — every recommended session, with primary owner,
   impact, effort, evidence, dependencies, and verification.
4. **Capability decisions** — keep, sharpen, cut, consolidate, replace, or add.
5. **Deletion and retirement candidates** — features, automation, dependencies,
   documentation, and code.
6. **Deterministic follow-ups** — stable signals worth encoding in project-owned
   gates.
7. **Research notes** — dated primary sources used for current external claims.
8. **Deferred findings** — verified but not currently worth acting on, so later
   reviews do not rediscover and rerank them without new evidence.

Thoroughness means every layer was genuinely examined, not that every possible
nit appears in the report. Preserve full verified evidence while using ranking,
workstreams, and deferred state to keep the result actionable.
