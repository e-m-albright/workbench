---
name: workspace-health-audit
description: "Manage and recover multi-agent workspaces: worktrees, branches, stashes, PRs, duplicate changes, and interrupted sessions. Use after parallel work, crashes, merge waves, or for worktree creation and cleanup."
---

# Workspace Health Audit

Detect integration failures that arise when multiple agents (or humans) work in parallel: orphaned artifacts, stale state, duplicate definitions, and pattern divergence from merge conflicts resolved mechanically rather than thoughtfully.

## Choose the mode

- **Audit integrated workspace state:** use this file; for the deeper checks (§5–§11: duplicate definitions, pattern adoption, compilation, dead code, misplaced/stale artifacts), read [audit-checklists.md](references/audit-checklists.md).
- **Create, list, or clean worktrees:** read [worktrees.md](references/worktrees.md).
- **Recover after a crash or lost terminal:** read [session-recovery.md](references/session-recovery.md).

Never delete a branch, worktree, or stash merely because it looks stale; prove the work is merged or ask.

Use after a wave of parallel agent work lands on main, when the user suspects agents stomped each other's changes, as a periodic hygiene check, or to confirm a clean baseline before a new phase of work.

## Audit Checklist

Run each section that applies to the repo. Report findings in a summary table at the end with severity (HIGH / MEDIUM / LOW / CLEAN) per section.

### 1. Stash Triage

For each `git stash list` entry: `git stash show stash@{N} --stat` to identify touched files, check whether the work already landed on main, then verdict: DROP (superseded), RECOVER (lost work), or ASK (ambiguous). Goal: empty stash.

### 2. Worktree Inventory

```bash
git worktree list
# Also check the vendor worktree dir, e.g. .claude/worktrees/ under Claude Code
# (Codex has no equivalent), plus any project convention like .worktrees/.
```

For each non-main worktree:
1. Check if its HEAD is reachable from main (`git merge-base --is-ancestor`).
2. Check for uncommitted changes (`git -C <path> status --short`).
3. If merged and clean: candidate for removal.
4. If it has unmerged work: flag for review.

Goal: single integration worktree + only-active feature worktrees.

### 3. Branch Hygiene

```bash
git branch -a --sort=-committerdate
git remote prune origin --dry-run
```

**Permanent branches:** read the repo's CONTRIBUTING / AGENTS / README to identify them (`main`, `dev`, deploy/automation branches). Any other branch is a candidate for cleanup.

Categorize every non-permanent branch:
- **Merged:** `git log --oneline main..origin/<branch>` is empty → safe to delete.
- **Superseded:** work landed via different commits → delete with note.
- **Unmerged with value:** unique content not on main → flag for cherry-pick or merge.
- **Stale:** last commit > 14 days old and unmerged → flag for review or deletion.
- **Workflow output:** auto-generated branches from CI cron jobs (see §3a).

#### 3a. Workflow-generated branch recognition

Automated workflows often push branches without opening PRs. Common prefixes: `worktree-*` (agent worktree leftovers), `auto-ratchet/*`, `audit/*` (delete once actioned); `dependabot/*` / `renovate/*` (leave for the bot).

**Bulk-delete pattern** — only branches that are fully merged AND have no open PR. A pushed-for-backup branch with unmerged commits must never be auto-deleted, even if its name matches a cleanup prefix:

```bash
pr_heads=$(mktemp)
gh pr list --state open --json headRefName --jq '.[].headRefName' > "$pr_heads"
git branch -r --merged origin/main | grep -E 'origin/(worktree-|auto-ratchet/|audit/)' \
  | sed 's|^ *origin/||' | grep -vFf "$pr_heads" \
  | xargs -n1 -I{} git push origin --delete {}
```

Branches the prefix matched but `--merged` excluded are unmerged: list them (`git branch -r --no-merged origin/main`) and review by hand — `git cherry main <branch>` distinguishes genuinely-unique commits from rebased duplicates.

Report bulk deletions as a single summary line. Severity: HIGH if workflow branches outnumber human branches by 3:1 or more — something automated is misconfigured.

### 4. Pull Request Triage

```bash
gh pr list --state open --json number,title,headRefName,baseRefName,state,isDraft,createdAt,updatedAt,mergeable,reviewDecision,statusCheckRollup,author
gh pr list --state closed --json number,title,headRefName,closedAt,mergedAt --limit 20   # accidental closures
```

For each open PR, categorize:
- **Ready to merge:** checks pass, approved, not draft → merge or flag.
- **Stale:** no activity > 7 days. If `gh pr diff` shows the work already landed on main, close with comment; otherwise flag.
- **Superseded:** branch already merged directly → close with "landed via direct merge" comment.
- **Draft / WIP:** note as in-progress.
- **Blocked:** failing checks or requested changes → diagnose the blocker.
- **Orphaned:** PR branch deleted or force-pushed away → close.

Goal: zero open PRs that should be closed; zero closed PRs with lost work.

### 5–11. Deeper checks

Read [audit-checklists.md](references/audit-checklists.md) for: duplicate definitions (§5, highest-value), pattern adoption (§6), compilation health (§7), dead code (§8), misplaced artifacts (§9), stale artifacts (§10), tracked-but-gitignored (§11).

## Output Format

```
## Workspace Health Audit — {date}

| Section | Status | Details |
|---------|--------|---------|
| Stash | CLEAN / n items | ... |
| Worktrees | CLEAN / n orphaned | ... |
| Branches | CLEAN / n stale | ... |
| Pull requests | CLEAN / n actionable | ... |
| §5–§11 (if run) | CLEAN / n findings | ... |

### Findings
#### [Section]: [Finding title] — severity, details, recommended action

### Actions Taken
(cleanup performed during the audit)

### Deferred for Next Wave
(issues needing discussion or design decisions)
```

## Important Notes

- This skill is **read-mostly**. Only take destructive actions (dropping stashes, removing worktrees, deleting branches) when the user explicitly authorizes cleanup, not just audit.
- When in doubt about whether work is superseded, flag for review rather than deleting.
- The duplicate-definition check ([audit-checklists.md](references/audit-checklists.md) §5) is the highest-value section — parallel agents creating conflicting types is the most dangerous failure mode because it compiles fine but produces runtime bugs.
