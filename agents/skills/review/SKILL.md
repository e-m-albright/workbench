---
name: review
description: Read-only pre-merge review of a diff, branch, or PR — findings-first bug hunt plus a graded health report card. Use for "review this", "is this safe to ship", "what could break", or grading a change. Reports only; applies fixes only when the user asks afterward.
allowed-tools: Read Grep Glob Bash(git:*) Bash(gh:*) Bash(rg:*) Bash(wc:*) Agent
metadata:
  source: Merged from premerge-review (fix-first bug hunt) and code-quality-audit (graded health rubric). Criteria live in references/bug-hunt-criteria.md and references/health-rubric.md.
---

# Review

Two complementary lenses on the same change, run together before it merges:

1. **Bug hunt** — find defects about to land (correctness, security, data integrity, ops), each classified so the caller knows what is mechanical and what is a judgment call.
2. **Health report card** — grade module health against the universal engineering rubric (letter grades + domain observations).

This skill is read-only: it produces the findings and the report card. It never edits code. When the user asks to address the findings afterward, that is a separate, explicit step.

## When to Use

- Reviewing your own branch before opening a PR, or a teammate's PR before approving
- "Is this safe to ship?" / "what could break here?" / "review this diff" / "grade this PR"
- A final pass after TDD or feature work, before PR/merge closeout
- Periodic health check on a module or directory (run the rubric threads, skip the diff-scoped ones)

**When NOT to use:**
- **`systematic-debugging`** — when something is *already* broken and you need the root cause. This skill reviews changes that (as far as anyone knows) work.
- **`security-review`** — when you want a dedicated, exhaustive security pass. This skill covers high-frequency security misses inline; the security skill (or the `security-auditor` subagent, where isolated agents exist) owns the deep audit.
- **`code-health`** — for structural grading and cleanup of existing code outside a pending change; this skill is scoped to a diff/branch/PR about to merge.

## Workflow

### 1. Establish scope

Determine exactly what you're reviewing and read it in full plus enough surrounding code to judge correctness — never review hunks blind:

- A PR number/URL → `gh pr diff <n>` (and `gh pr view <n>` for intent)
- The current branch → `git fetch origin && git diff origin/main...HEAD`
- Staged/working changes → `git diff` / `git diff --staged`
- A module/directory health check → read every file in scope, not just samples

If no scope is given, default to the unstaged changes (`git diff`).

### 2. Understand intent before judging

What is this change *trying* to do? Read the PR description / commit messages / linked issue. A correct implementation of the wrong thing is the most expensive bug.

### 3. Detect the surface(s)

By file extension and layout, so the right rubric criteria apply (see [Health rubric](references/health-rubric.md)):
- `*.py` / pyproject.toml → Python
- `*.rs` / Cargo.toml → Rust
- `*.ts`, `*.tsx`, `*.svelte`, `*.vue` → Web
- `*.go` / go.mod → Go
- Mixed → audit each surface separately, combine into one report

Read the repository's `AGENTS.md` and project-local engineering philosophy if
present. Then inspect language, framework, and directory-specific instructions
that the repository actually owns. If the project has a code-health manifesto
or equivalent, prefer it because projects own their philosophy.

### 4. Walk the audit lenses

Default to one focused sequential pass through the lenses below — most changes
do not need parallel machinery. Fan the lenses out as isolated read-only
subagent threads only when the scope is genuinely large (many files, mixed
surfaces) *and* the active harness and project policy permit delegation. Each
lens gets the scope, surface, and criteria.

| # | Thread | Lens | Criteria |
|---|--------|------|----------|
| **T1** | **Correctness** | bug hunt | [bug-hunt-criteria.md](references/bug-hunt-criteria.md) → Correctness |
| **T2** | **Security** | bug hunt | [bug-hunt-criteria.md](references/bug-hunt-criteria.md) → Security |
| **T3** | **Data Integrity** | bug hunt | [bug-hunt-criteria.md](references/bug-hunt-criteria.md) → Data Integrity |
| **T4** | **Operational Readiness** | bug hunt | [bug-hunt-criteria.md](references/bug-hunt-criteria.md) → Operational |
| **T5** | **Health — universal** | report card | [health-rubric.md](references/health-rubric.md) → U1–U11 |
| **T6** | **Health — surface + structure** | report card | [health-rubric.md](references/health-rubric.md) → surface criteria + anti-pattern scan |

Each thread returns its findings (bug-hunt) or its graded criteria (report card) with `file:line` evidence. Don't let a thread manufacture issues to look thorough — empty is a valid result.

### 5. Synthesize

Collect all threads. De-duplicate overlapping findings (a missing null guard may surface in both T1 and T5 — report it once, in the bug hunt, and let it cost the rubric grade). Reconcile severities. Compute the report-card grades and weighted overall.

### 6. Classify the bug-hunt findings

Every T1–T4 finding gets classified before reporting. Nothing is applied —
the classification tells the caller what a follow-up "apply the fixes" request
would touch without discussion versus what needs a decision:

| Classification | Meaning |
|---------------|---------|
| **QUICK FIX** | A senior engineer would apply without discussion. Mechanical, unambiguous: unused imports/variables, dead code, import ordering, naming inconsistencies with surrounding code, missing error context in logs, obvious null guards at boundaries, deprecated API with a drop-in replacement. |
| **JUDGMENT** | Reasonable engineers could disagree. Trade-offs, architecture, security-sensitive changes, API surface, dependencies, test strategy. |

**Default to JUDGMENT when uncertain.** For the full table and worked examples, see [bug-hunt-criteria.md](references/bug-hunt-criteria.md).

### 7. Report

Report in the format below. Do not edit any file. If the user then asks to
address the findings, apply QUICK FIX items directly and confirm each
JUDGMENT item before touching it.

## Output Format

```markdown
# Review: [scope]

## Summary
[1-2 sentences: what the change does + overall read. Verdict: safe to merge / fix top items first / not yet.]

## Findings (bug hunt)
### [SEVERITY] Finding title
**Category**: Correctness | Security | Data Integrity | Ops | Performance
**Classification**: QUICK FIX | JUDGMENT
**Location**: file:line
**Recommendation**: [specific action]
**Why**: [brief rationale]

## Health Report Card
**Surface:** [Python | Rust | Web | Go | Mixed]  **Overall Grade:** [A–F, weighted]

| # | Criterion | Grade | Justification (file:line) |
|---|-----------|-------|---------------------------|
| U1 | Type Safety | B+ | ... |
| ... | ... | ... | ... |

### Domain Observations
- **Strength / Opportunity / Concern:** [title] — [1-3 sentences, file:line]

## Top 3 Action Items
1. **[Priority]** [action + file:line] — [why it matters]
2. ...
3. ...
```

Severity: **Critical** (must fix before merge), **Warning** (should fix), **Note** (consider).

Below a **B** overall should not merge without addressing the top action items. If there are no findings, say so plainly — don't manufacture issues.

## Composition

This skill is the shared rubric for both first-class vendors. Invoke it directly
for one focused pass or use its independent threads as native subagent tasks
when isolation and parallelism materially help.
