---
name: github-workflow
description: "Run GitHub workflows with gh: prepare PRs, summarize changes, monitor CI, recover hook failures, and drive a PR green. Use for PR creation, checks, Actions, issues, secrets, or pre-push failures."
---

# GitHub & Workflow

## Choose the mode

- **Open or update a PR:** follow this file, then read [pr-summary.md](references/pr-summary.md) for the description structure.
- **Drive CI to green:** read [greenlight-cycle.md](references/greenlight-cycle.md).
- **Recover a failed commit or push hook:** read [hook-failure-triage.md](references/hook-failure-triage.md) before retrying.

Load one mode at a time. Ordinary `gh` operations do not need the specialized references.

## Pull Requests

- Use `gh pr create` for PRs. Keep titles concise and descriptions audit-friendly (intent, risk, verification).
- Don't skip required CI checks or approval gates — if the org uses a compliance platform (e.g. Drata), its audits may depend on them.
- Avoid force-pushing to `main`/`master` without explicit instruction; it rewrites shared history others may have built on.

## Issues & Incidents

- Reference the org's issue tracker (GitHub Issues, or e.g. Linear if the org uses it) by ID when closing or linking work.
- If the org uses an incident tracker (e.g. Rootly), confirm before auto-closing issues that may be tied to an active incident.

## Code Review

- Use `gh pr checkout <number>` to review PRs locally.
- When suggesting changes in review, prefer concrete diffs over vague descriptions.

## CI & Actions

- Use `gh run list` / `gh run watch` to monitor workflow status from the terminal.
- Understand the full trigger matrix before modifying GitHub Actions workflows — a change can fire (or silently stop firing) jobs you didn't intend.

## Secrets & Config

- Use GitHub Actions secrets (or the org's secrets manager, e.g. Doppler, if it uses one) for sensitive values — hardcoding them in workflow files leaks them into history and logs.
- For org-level secrets, check existing patterns before proposing new secret names.

_Promoted from `.ai/rules/process/github-workflow.mdc` (was an always-on rule; now an on-demand skill)._
