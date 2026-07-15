# Workbench

Workbench is the version-controlled intelligence layer for its owner's development
environment. It carries agent behavior, engineering judgment, project-health
tools, and reusable automation building blocks between repositories.

It is personal and opinionated. It supports one workflow rather than unknown
users or arbitrary machines. It must remain safe to publish: credentials,
personal records, conversations, generated memory, and private automation state
belong outside this repository.

## Scope

- `agents/` - canonical configuration for Claude Code and Codex, shared skills,
  prompts, subagents, MCP definitions, hooks, and permissions.
- `playbook/` - engineering principles and researched technology preferences.
- `health/` - deterministic project checks, ratchets, and advisory AI review
  rubrics.
- `automations/` - reusable, context-free automation adapters and experiments.
- `docs/decisions/` - durable rejected-tool and architectural decisions.

The host layer remains in `~/code/public/dotfiles`. Private context and
instantiated personal automations remain in the `notes` repository.

## Supported Agents

Claude Code and Codex are first-class. Other harnesses remain evaluation
candidates until their recurring value justifies integration work.

## Commands

```text
workbench sync [claude|codex|all]   reconcile managed agent configuration
workbench check [claude|codex|all]  report managed drift and external additions
workbench lint                       validate skills, JSON, TOML, and shell syntax
```

`sync` preserves unmanaged vendor settings, translates shared subagents into
each vendor's native format, installs declared plugins, and keeps one backup
before changing a live config file. Pass `--no-skills` or `--no-plugins` for a
configuration-only reconciliation.

Plugin IDs are version-controlled in `agents/<vendor>/plugins.json`. Installing
a plugin is reproducible; OAuth grants and account sessions remain interactive
vendor state and are never stored in this repository.
Dotfiles links `bin/workbench` into `~/.local/bin` during fresh-Mac setup.

## Safety Boundary

Workbench keeps ordinary agent work inside the active repository. Vendor
sandboxes provide the filesystem boundary; concise permission rules and two
PreToolUse hooks deny sensitive-file edits, recursive force-deletion,
destructive Git operations, and disk erasure. Database and infrastructure
policy belongs to the projects that own those resources.

For an independent fact-check, give another model the read-only
[`adversarial audit prompt`](docs/security/adversarial-audit-prompt.md).

Completion and approval notifications use each vendor's native notification
channel. Workbench does not install a notification script or background service.

## Design Rules

1. Prefer declarative files and small scripts over a framework.
2. Add executable behavior only for a repeated workflow.
3. Keep deterministic checks separate from stochastic assessments.
4. Treat generated agent state as private and disposable.
5. Preserve rejected decisions as tombstones instead of repeatedly evaluating
   the same tools.
