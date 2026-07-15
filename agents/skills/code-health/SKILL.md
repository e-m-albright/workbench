---
name: code-health
description: Diagnose and improve code structure through lenses for pruning, domain alignment, module depth, effect isolation, refactoring, clarity, and style. Use for code-health audits, cleanup, simplification, or a named lens.
---

# Code Health

Reach for this when the goal is "make this healthier" but the right move is not obvious, or when the user names one of the lenses below. Load only the relevant reference; the lens names remain stable even though they no longer consume separate always-loaded skill entries.

## The completeness model: form vs. function

Read this first, because it sets honest expectations. Code quality has four source-measurable pillars (CISQ/ISO 5055): **Reliability, Performance, Security, Maintainability.** Refactoring is *behavior-preserving by definition*, so the refactor lenses below address essentially **only Maintainability** — they make code well-formed, not correct, secure, or fast. A refactor-only pass can even *introduce* security regressions.

So the portfolio is two tiers, and a real "health pass" needs both:

- **Tier A — form (behavior-preserving refactor lenses):** make it well-structured, idiomatic, legible, minimal.
- **Tier B — function / safety / speed (non-behavior-preserving):** find defects, vulnerabilities, and bottlenecks. Use `review` and `systematic-debugging`; when isolated specialist context is useful, delegate to the `security-auditor` or `performance-engineer` subagent. **Robustness comes from Tier B plus real test coverage, never from Tier A alone.**

State this to the user when they ask for "unimpeachable" code: the book guarantees form; correctness and safety rest on Tier B and tests.

## Tier A routing — pick by symptom

| Symptom / request | Lens | Axis |
|---|---|---|
| "this area's design feels wrong", coupled, shallow modules, conversational | **[deepen](references/deepen.md)** | taste · divergent |
| whole-repo, measured, ratchet down, reduce LOC, converge over passes | **converge** | measured · convergent |
| "clean up this function", extract, flatten conditionals, a known transform | **[tidy](references/tidy.md)** | mechanical · convergent |
| "hard to follow", naming, comments, newcomer/agent comprehension | **[clarify](references/clarify.md)** | taste · readability |
| "make this elegant/beautiful/artful", best code possible, the wince test | **[style](references/style.md)** | taste · aesthetic |
| names don't match the business, leaked API names, wrong boundaries | **[align](references/align.md)** | conceptual · divergent |
| over-engineered, dead code, YAGNI, "make it smaller" | **[prune](references/prune.md)** | minimalist · convergent |
| "can only test end-to-end", tame side effects, illegal states | **[purify](references/purify.md)** | testability · structural |

For a **single area**, route to one lens. For a **full pass**, sequence them (next section).

## The convergent sequence (full pass)

Lenses have a natural order that minimizes rework:

1. **prune** — delete first; never restructure code you could remove. Smaller surface for everything after.
2. **align** + **deepen** — get the concepts and boundaries right (diverge: find the real design).
3. **purify** — isolate effects so what remains is testable.
4. **tidy** — execute the mechanical transforms safely.
5. **clarify** — readability and navigation pass.
6. **style** — the capstone elegance pass, once the code is correct, clear, and structured. Aesthetic only; never a substitute for the structural lenses above it.
7. **converge** — measure, ratchet the gains into CI contracts, and re-grade. This is what makes the pass *stick* and *converge* rather than re-rot.
8. **Tier B** — `review`, `systematic-debugging`, and optional security or performance subagents for the pillars refactoring cannot reach.

Don't run all seven blindly — let the Tier-A routing table and the scorecard pick where effort actually pays (churn × complexity hotspots).

## Keeping lenses from fighting

The lenses genuinely contradict (dedup↔decouple, deepen↔prune, DDD-richness↔YAGNI). Two shared rules, enforced by every lens:

- **Rejected-decision log.** Before proposing, read the ADR log (`docs/adr/`) for decisions already declined; never re-litigate them. When a lens rejects a move for a load-bearing reason, write it back. This is the memory that stops successive passes and sibling lenses from undoing each other.
- **Arbitration, not accretion.** When two lenses recommend opposite edits on the same code, surface the tradeoff and decide *once*, recording it — don't let whichever ran last win.

## Scheduling policy (what's safe unattended)

Generative, structural refactoring on a weekly cron, auto-merged, is an anti-pattern — empirically it produces cosmetic churn with no measured health gain and a review backlog. So:

- **Safe unattended (weekly):** the `scorecard`/audit **detection** run that opens an issue or draft PR (never auto-merge); **ratchet enforcement** in CI (block regressions); deterministic codemods from the tidy lens.
- **Interactive / human-gated:** deepen, align, prune, purify, the engine's structural moves, and all of Tier B. These are judgment- and conflict-heavy; they need a human and the arbitration rules above.

The review prompts under `health/reviews/` are available on demand. Automation is optional; deterministic project gates remain the default guardrail.

## See also
- The measured engine and its references (metrics, ratchet, de-slop catalog, ontology, deepening vocab): [converge](../converge/SKILL.md).
- Shared guidance: [playbook/engineering-philosophy.md](../../../playbook/engineering-philosophy.md) (12 principles), [playbook/knowledge/engineering-gates.md](../../../playbook/knowledge/engineering-gates.md) (ratchet mechanics), and [health/README.md](../../../health/README.md) (the adoption boundary).
