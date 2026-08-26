---
name: improvement-hunt
description: Exhaustive read-only whole-repo improvement hunt — parallel sweeps across every lens, ranked findings report. Use for "improvement hunt", "push this repo forward", or "find everything worth improving". For a single diff or PR, use `review` instead.
allowed-tools: Read Grep Glob Bash(git:*) Bash(rg:*) Bash(ls:*) Bash(wc:*) Bash(just:*) Bash(fd:*) Agent WebSearch WebFetch
---

# Improvement Hunt

Find every high-value improvement in this repository and deliver a ranked,
evidence-backed report. The ambition is not a punch list of nitpicks — it is
to map the shortest path from the repo's current state to the best stable
version of itself, in one or a few shots. Hunt accordingly: exhaustive
coverage, then ruthless ranking.

This skill is read-only. The deliverable is the report; fixes happen in
follow-up sessions the user chooses to run. (If the user pre-authorizes it,
small zero-risk fixes may land on a branch and be noted in the report.)

## Workflow

1. **Orient.** Read AGENTS.md/CLAUDE.md, the justfile/task runner, README,
   and the directory tree. Understand what the repo is *for* and what its
   stated philosophy is — findings are judged against the repo's own goals,
   not a generic ideal.
2. **Sweep in parallel.** Dispatch one subagent per lens group below, all in
   a single message so they run concurrently (Explore, code-reviewer,
   security-auditor, performance-engineer, or general-purpose as fits each
   lens). Give each agent the whole repo as scope and instruct it to be
   exhaustive within its lens: read the real code, follow every lead, and
   report everything it finds — filtering happens at the ranking stage, not
   inside the sweep. Research-lens agents must use current web sources.
3. **Verify.** Confirm each finding against actual code, docs, or a cited
   current source before it enters the report. Claims about "the better way"
   or "the frontier" need a 2026-dated citation, not training-data memory.
   Drop anything that doesn't survive verification.
4. **Rank and synthesize.** Merge, dedupe, and rank the full set by
   impact × effort. Report everything that survived — the ranking, not a
   count cap, is what keeps the report navigable. Group related findings
   into coherent workstreams where several fixes are naturally one session
   of work.

## Lenses

**Subtract (look here first)**
- Dead code, unused dependencies, features built but demonstrably unused
- Redundant abstractions, over-general config, competing implementations
- Docs describing behavior that no longer exists (documentation drift)

**Health & simplicity**
- Code health: unclear naming, shallow modules, tangled effects,
  copy-paste divergence, convention drift within the repo
- Maintenance burden: anything requiring manual ritual, memory, or periodic
  hand-fixing — automate, simplify, or delete
- Idempotency and bootstrap correctness for setup/install scripts

**Deepen**
- Features actually in use that are 80% done — what makes them excellent?
- DX friction: slow commands, confusing errors, missing recipes, weak output
- Test gaps on load-bearing logic; flaky or assertion-weak tests

**Research (web search; cite sources with dates)**
- Better ways to do things the repo currently does the hard way
- New capabilities worth adopting — what's frontier in AI tooling and agent
  capabilities that fits this repo's purpose (skills, MCP, automation,
  model capabilities)
- Best-in-breed tool check: is anything superseded by a clearly better,
  stable, well-maintained alternative? High bar — churn is a cost.

**Risk**
- Security: injection, unsafe shell expansion, curl-pipe-sh, secrets
  handling, overly broad permissions, untrusted input reaching eval/exec
- Supply chain: stale or abandoned deps, unpinned installs, typosquat exposure
- Privacy: personal data, private-project names, absolute home paths, or
  employment signals in tracked files (public repos: flag that git history
  may need a separate scrub)
- Silent failure modes: missing error handling on paths the user relies on

**Process**
- How work flows through this repo: commit/release/review rituals, CI or
  the absence of it, verification steps that exist only in the user's head
- Recurring chores that could become recipes, hooks, scheduled routines, or
  agent automations — and existing automation that misfires or gets ignored
- Feedback loops: how fast does the repo tell you something broke? Where
  would a cheap check catch a class of mistakes earlier?

**Cross-repo & agents**
- Consistency with sibling repos (dotfiles / workbench / notes):
  conventions, CLI patterns, or rules that drifted apart — which repo has
  it right, and does anything live in the wrong repo?
- Agent ergonomics: is AGENTS.md accurate and sufficient? Are skills,
  rules, or subagent definitions stale, missing, or contradicted by code?

## Report

For each finding: **title · lens · impact (high/med/low) · effort (S/M/L) ·
evidence (file:line or URL) · recommended action in one or two sentences.**

Structure:
1. **Workstreams, ranked** — coherent bundles of findings, each with a
   paragraph on the payoff and what one focused session would accomplish.
   Every workstream and standalone finding appears; ranking replaces
   truncation.
2. **Full findings table**, grouped by lens.
3. **Deletion candidates** as their own list — subtraction is the highest-
   leverage category and deserves its own visibility.
4. **Research notes** with dated citations.
5. **Clean bill** — what was checked and found healthy. Absence of findings
   is signal only if the reader knows the lens actually ran.

Calibrate to the repo's stated philosophy: small surface area beats new
machinery. A finding that adds infrastructure must clear a higher bar than
one that removes it.
