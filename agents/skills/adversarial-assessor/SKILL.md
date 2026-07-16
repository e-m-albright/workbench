---
name: adversarial-assessor
description: Route work through an independent skeptical model. Use for adversarial review, blind-spot discovery, sycophancy resistance, or requests for a different model to challenge a consequential decision or implementation.
metadata:
  type: reference
---

# Adversarial Assessor

> **Why this exists.** Sycophancy is trained in by RLHF and cannot be prompted away — the research is blunt (even frontier models stay sycophantic ~29% of the time; "none eliminate it"). The durable counter is not asking the same model to be harsher; it is **routing the work past a different model, in a fresh context, with no stake in it.** That independent critic finds what the insider has normalized. In this repo it already earned its keep: a Fable-5 pass found a real `rm -rf` guard bypass the default agent had walked past.

## What it does

Runs a **skeptical principal-engineer assessment** of a scope (a repo, a subsystem, a diff) using an independent model — the script defaults to the vendor's strongest alias, overridable via `ASSESSOR_MODEL` or `--model`; pick one *different* from the model doing the work. Read-only. Output is four ranked sections (code health · risk/correctness · feature completeness · add/alter/cut with FOR/AGAINST/verdict), plus "3 things first" and the single biggest risk.

## How to run it

```
agents/skills/adversarial-assessor/scripts/assess.sh [focus text...]
agents/skills/adversarial-assessor/scripts/assess.sh --scope src/payments  the payments subsystem
ASSESSOR_MODEL=<model-id> agents/skills/adversarial-assessor/scripts/assess.sh   # override the assessor
```

Run `scripts/assess.sh` as a black box — do not read the source or reimplement it; it exists to be called directly rather than ingested into your context window.

It writes a timestamped report (header names the resolved model) to `docs/health/assessments/` and prints the path. It calls a **paid model** under a budget cap, so it is opt-in and scoped, not a gate. Needs the `claude` CLI on PATH.

## The discipline (this is the load-bearing part)

1. **Findings are claims to verify, not gospel.** Apply the same skepticism to the assessor that it applies to the code. Before acting on any finding, check it against the actual source — confirm the bug reproduces, the bypass works, the coupling is real. In this repo's first run, the guard bypass was real and got fixed test-first; other findings were fair-but-deferred or wrong. Sort them yourself.
2. **Use a *different* model than the one being assessed.** The point is independence. Assessing a model's work with the same model defeats it; set `ASSESSOR_MODEL` to a different model (or another vendor's CLI).
3. **Rank by leverage and irreversibility.** A verified safety/security/data bug outranks a style nit, always. Fix the irreversible-risk findings first.
4. **Record what you did with each finding** — fixed / deferred-with-reason / dismissed-as-wrong — in `docs/decisions/`, so the next pass converges instead of re-litigating.

## When NOT to reach for it

- A routine pre-merge diff review → `/review` (same-model is fine for mechanical correctness).
- You already know the area is healthy enough → don't burn the spend to be told so. This is for when you suspect your own (or the agent's) confidence is unearned.
- Generating *new* ideas collaboratively → use the ideation mode in `planning`. This skill attacks existing work; it does not brainstorm.

## See also
- `docs/decisions/` — where finding dispositions and durable decisions live; prior assessment reports sit under `docs/health/assessments/`.
