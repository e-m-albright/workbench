# Workbench

## Project Context

Workbench is a public, personal development-intelligence repository. It
owns portable agent configuration, engineering guidance, project-health tools,
and context-free automation building blocks.

The adjacent repositories own different state:

- `dotfiles` owns fresh-Mac setup, packages, shell/editor configuration, drift
  reconciliation, and remote-host access.
- `notes` owns private knowledge, CRM data, daily pages, personal automation
  instances, and generated operational state.

## Constraints

- Optimize for the owner's workflow, not unknown users or machines.
- Never commit secrets, credentials, personal records, conversations, or agent
  memory.
- Claude Code and Codex are the only first-class coding-agent integrations.
- Keep rejected tools and approaches in `docs/decisions/tombstones.md`. When
  code enforces a retirement, the reason lives with the enforcement instead
  (`RETIRED_*` in `scripts/workbench.py`, `_*_disabled` in the MCP registry).
- Prefer native vendor configuration and small scripts. Do not create a platform
  where a file copy or documented command is sufficient.
- Deterministic health checks may gate changes. Stochastic assessments are
  advisory and must record evidence, rubric version, and model provenance.
- Reusable automation mechanics may live here; workflows coupled to private
  notes or venture context stay in `notes`.

## Process

- Plan non-trivial changes before implementation.
- Preserve unrelated user changes.
- Verify commands and file deployment before claiming completion.
- When removing a capability, record why and what would justify revisiting it.
