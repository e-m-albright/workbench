---
name: cleanup
description: "Review, integrate, and clean main-repository Git workspaces. Use for /cleanup, \"clean up our workspaces\", or \"return repos to main only\". SKIP code and disk cleanup."
---

# Cleanup

Return the selected repositories to their integration branches without losing useful work. This is the executing counterpart to [workspace-health-audit](../workspace-health-audit/SKILL.md), not a second audit implementation.

## Scope and authority

With no repository arguments, resolve the owner's main repositories from the machine-local routing index named by the shared rules. Keep that inventory private. Explicit repository arguments narrow the scope; ask if no routing index or unambiguous scope exists. Read each repository's instructions before acting.

Treat an explicit request to run this workflow as approval to review and integrate worthwhile routine changes, close demonstrably superseded proposals, and remove verified preserved branches, clean worktrees, and redundant stashes within that scope. An audit-only request remains read-only. Respect repository shipping policy and tool boundaries; invocation does not authorize security or credential changes, production operations beyond the repository's shipping policy, force pushes, or discarding ambiguous unique work.

Aim for one clean integration checkout, only the integration branch locally and remotely, no stashes, and no open PRs. Preserve documented permanent branches and active work; report exceptions rather than manufacturing a main-only result.

## 1. Inventory

Follow workspace-health-audit's stash, worktree, branch, and PR checklists. Include the shared index, tracked and untracked changes, live remote refs, and the configured integration branch. Fetch before classifying branches. Record reviewed commit IDs so later mutations can detect concurrent changes.

State the scope and approach briefly, then proceed. Delegate independent repository reviews when useful, with one writer per repository and explicit mutation limits.

## 2. Review what is worth keeping

Use [review](../review/SKILL.md) for unique changes and [dependency-upgrades](../dependency-upgrades/SKILL.md) for dependency proposals. Compare against current integration content and history, not merely commit ancestry or PR age.

- **Already integrated or superseded:** identify the landed replacement, close the PR with that evidence, then clean its preserved refs.
- **Useful and current:** integrate the smallest coherent change, run repository gates, and ship through its chosen path. Resolve required checks and review comments before merging an existing PR.
- **Mixed useful and obsolete work:** preserve useful material in the current implementation, verify it, and document what was deliberately omitted. Keep a verified recovery bundle before deleting a uniquely committed source branch.
- **Uncertain, substantial, or authority-sensitive:** leave intact and ask one concrete decision question. Cleanup alone does not justify expanding access or reviving a competing implementation.

Distinguish published output or presentation from the generator that produced it. A merged article or reader does not prove that an experimental runtime merged. Trace the exact implementation before calling an older proposal either missing or superseded.

Review dirty files instead of sweeping them into a commit. Ship only understood, relevant changes with the repository's documented data or recovery workflow where applicable. Leave live or unidentified edits with their owner. Remove prototype files only when the user identified them for removal or their disposal is otherwise explicitly authorized; an untracked directory is not evidence that it is disposable.

## 3. Ship without disturbing other work

Recheck status, index, branch tip, and remote tip immediately before staging, integrating, or updating a checkout. If another session changed them, reassess rather than using the earlier inventory.

Use an isolated checkout when the integration checkout is dirty or owned by another session. Fast-forward a clean checkout with autostash disabled, for example `git -c merge.autostash=false pull --ff-only`; do not let configured autostash hide concurrent work. Avoid creating stashes. Recover any temporary stash created by this run before final verification, preserving both upstream and local changes if restoration conflicts.

Summarize impact and verification before committing; confirm the staged paths match that summary. Verify the shipped commit and its CI. A queued, running, cancelled, or timed-out check is not a pass.

## 4. Remove preserved leftovers

Follow workspace-health-audit's authorized-cleanup procedure: refresh inventory, verify preservation and the exact live remote tips, check PR state, then use normal repository hooks and non-forcing removal for merged worktrees and branches.

For reviewed unique branches or stashes whose useful content was selectively integrated, preserve and verify a recovery bundle or equivalent before removal. A backup is not permission to discard ambiguous or active work. Report retained backup paths without publishing private contents.

If a tool guard blocks an operation, stop that operation and hand off its exact safest command. Do not switch tools, bypass hooks, or change authorization. A missing GitHub workflow scope may require the owner to merge the reviewed PR through GitHub's website; do not request a broader token merely to finish cleanup. Inspect uncertain outcomes before retrying.

## 5. Verify and close

Recheck all selected repositories: working tree, shared index, local branches, live remote heads, worktrees, stashes, open PRs, and shipped CI. Report a concise per-repository result with integrations, removals, and any leftovers with their reasons. Include every actionable PR title and URL when a decision remains.

Distinguish completed cleanup from blocked or pending work. Use the shared owner-command format for handoffs, keeping each terminal command on one copyable line. After the owner reports completion, inspect the resulting state and drop completed instructions rather than repeating them.
