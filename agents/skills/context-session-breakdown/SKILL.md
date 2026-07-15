---
name: context-session-breakdown
description: Produce a compact session handoff or full workflow closeout. Use for "summarize context", "session breakdown", "fresh chat prompt", preserving current state, or extracting reusable lessons before ending work.
metadata:
  source: Local; inspired by Mitsupi-style context breakdown utilities, adapted as a portable repo-owned skill instead of a Pi package dependency.
---

# Context Session Breakdown

Create a short, accurate session snapshot that another agent or a future chat can act on without reading the whole transcript.

Use this when the user wants continuity, not a full retrospective. Keep it factual. Do not invent unstated decisions.

## Quick triage

Choose the output depth:

- **Tiny**: 5-8 bullets when the user asks "where are we?" or needs a quick status.
- **Standard**: the template below for handoff, fresh-chat bootstrap, or mid-session checkpoint.
- **Full closeout**: read [closeout-learning.md](references/closeout-learning.md) when the work is ending and the user wants learnings, a coverage audit, and a clean bootstrap prompt.
- **Crash recovery**: use `workspace-health-audit` when reconstructing lost sessions, branches, worktrees, or orphaned work.

## Gather evidence

Prefer evidence over memory:

1. Check `git status --short` for changed files unless the user only wants a conversational recap.
2. Check recent command/test outputs already visible in the session.
3. Read changed files only when needed to disambiguate actual state.
4. Separate confirmed facts from hypotheses and proposed next steps.

Avoid noisy inventories. The goal is a usable snapshot, not a full repo audit.

## Standard output template

```md
## Context snapshot

### Goal
- <one sentence: what the user is trying to accomplish>

### Current state
- <what is implemented / decided / verified>
- <important changed files or artifacts>

### Decisions
- <durable decision + rationale, if any>

### Verification
- <commands run and result, or "Not run yet">

### Open threads
- <unresolved decision / blocker / follow-up>

### Next best action
- <single recommended next step>
```

## Fresh-chat bootstrap variant

When the user asks for a prompt to continue in a new chat, add:

```md
## Bootstrap prompt

You are working in <repo/path>. The current goal is <goal>.

Known state:
- <state bullets>

Changed files / artifacts:
- <paths>

Verification so far:
- <commands + results>

Continue by:
1. <next step>
2. <verification step>

Constraints/preferences:
- <user preferences relevant to the next agent>
```

## Rules

- Name deferrals explicitly: "Deferred to follow-up", "Blocked on decision", or "Intentionally rejected".
- If a user asked explicit questions, include direct answers as well as the snapshot.
- Prefer precise terms: "provenance", "evidence", "verification artifact", "handoff", "snapshot".
- Keep the snapshot shorter than the work itself. If it exceeds ~40 bullets, summarize harder.
