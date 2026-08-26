# Workbench

## Project Context

Workbench is a public, personal development-intelligence repository. It
owns portable agent configuration, engineering guidance, and project-health
tools. Reusable automation mechanics may live here when one earns its place
(none do today); private workflow instances stay in their owning private layer.
`CATALOGUE.md` is the maintained feature map; update it when a capability is
added, removed, materially expanded, split, or consolidated.

The adjacent public host repository owns fresh-Mac setup, packages,
shell/editor configuration, drift reconciliation, and remote-host access.
Exact private repository names, paths, and routing belong only in the
machine-local context named by the shared agent rules.

## Constraints

- Optimize for the owner's workflow, not unknown users or machines.
- Never commit secrets, credentials, personal records, conversations, or agent
  memory.
- Pi, Claude Code, and Codex are the only first-class coding-agent integrations.
- Keep rejected tools and approaches in `docs/decisions/tombstones.md`. When
  code enforces a retirement, the reason lives with the enforcement instead
  (`RETIRED_*` in `src/workbench/core.py`, `_*_disabled` in the MCP registry).
- Prefer native vendor configuration and small scripts. Do not create a platform
  where a file copy or documented command is sufficient.
- Deterministic health checks may gate changes. Stochastic assessments from
  review skills are advisory and must record evidence, rubric version, and model provenance.
- Reusable automation mechanics may live here; workflows coupled to private
  personal or venture context stay in their private owner.

## Privacy (public repo)

This repo is public. Before committing, `git grep -niI` for private-project
names or personal absolute paths and ensure tracked files return nothing.

- Never reference a private project by name in tracked files — use generic
  phrasing ("a private project", "the private layer").
- No hardcoded `/Users/<name>/...` home paths — use `~` / `$HOME`.
- Test fixtures use neutral placeholders (`octocat/hello-world`), never real
  private repository names.
- Keep it neutral — no employment or status signals.
- Caveat: prior git *history* may still contain previously-scrubbed content;
  true removal needs a history rewrite (filter-repo/BFG) plus a force push.

## Process

- Plan non-trivial changes before implementation.
- Preserve unrelated user changes.
- Verify commands and file deployment before claiming completion.
- When removing a capability, record why and what would justify revisiting it.
