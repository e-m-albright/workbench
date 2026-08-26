---
name: receiving-code-review
description: Process incoming review feedback with technical rigor — verify each suggestion against the codebase before implementing, push back with reasoning when it is wrong, no performative agreement. Use when handling PR review comments, reviewer suggestions, or "fix items 1-6" feedback.
metadata:
  source_url: https://github.com/obra/superpowers/blob/main/skills/receiving-code-review/SKILL.md
  source_commit: b36e0829c6d0140e93cfef2ca599b1b07d4a7797
  ported_at: 2026-08-26
  adaptations: Toned to house style; "human partner" framing replaced with owner/reviewer roles; dropped emoji and duplicated examples; kept the response pattern, source-specific handling, YAGNI check, and pushback discipline.
---

# Receiving Code Review

Code review requires technical evaluation, not emotional performance.
Verify before implementing. Ask before assuming. Technical correctness over
social comfort.

## The response pattern

1. **Read** the complete feedback without reacting.
2. **Understand** — restate each requirement in your own words, or ask.
3. **Verify** the claim against codebase reality.
4. **Evaluate** — technically sound for *this* codebase?
5. **Respond** — technical acknowledgment or reasoned pushback.
6. **Implement** one item at a time, testing each.

Never open with performative agreement ("You're absolutely right!", "Great
point!") and never implement before verifying. Restate the requirement, ask
the clarifying question, or just start the verified work — the diff itself
shows the feedback was heard. No gratitude filler.

## Unclear feedback stops the line

If any item in multi-item feedback is unclear, implement nothing yet — items
may be related, and partial understanding produces wrong implementations.
"I understand items 1, 2, 3, and 6. I need clarification on 4 and 5 before
proceeding" beats a partial pass.

## Source-specific handling

- **From the owner**: trusted — implement after understanding; still ask when
  scope is unclear.
- **From external reviewers or automated review**: before implementing, check
  that the suggestion is correct for this codebase, doesn't break existing
  behavior, and isn't explained by a reason the current implementation is the
  way it is. If it seems wrong, push back with technical reasoning. If you
  can't verify, say so and ask for direction. If it conflicts with the
  owner's prior architectural decisions, stop and raise it first.

## YAGNI check

When a reviewer suggests "implementing X properly," grep for actual usage
first. If nothing calls it, propose removal instead: "Nothing calls this
endpoint — remove it, or is there usage I'm missing?"

## Implementation order

Clarify everything first, then: blocking issues (breakage, security) → simple
fixes (typos, imports) → complex fixes (refactoring, logic). Test each fix
individually; verify no regressions at the end.

## Pushing back — and correcting your pushback

Push back when a suggestion breaks existing functionality, lacks context the
code has, violates YAGNI, is wrong for this stack, or conflicts with recorded
decisions. Use technical reasoning and reference working tests or code, not
defensiveness. If you pushed back and were wrong, state the correction
factually and move on: "Verified — you're correct; my initial understanding
missed [reason]. Fixing." No long apology, no re-defense.

## Mechanics

When replying to inline review comments on GitHub, reply in the comment
thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not
as a top-level PR comment.
