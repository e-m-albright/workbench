# AI Tooling

This document describes the durable ownership model for the owner's active AI
development tools. It deliberately avoids model rankings, pricing, benchmarks,
and product-status snapshots because those age too quickly to serve as
configuration guidance.

## First-class coding agents

Claude Code and Codex are the only first-class coding-agent targets.

- Workbench owns portable rules, skills, prompts, subagent definitions, hooks,
  permissions policy, MCP declarations, and deployment translation.
- Dotfiles owns installing vendor applications and CLIs on a fresh Mac, plus
  invoking Workbench reconciliation.
- Each project owns its context, language conventions, commands, and tests in
  `AGENTS.md` and native project files.

The source stays vendor-neutral where the concepts are shared. Deployment is
vendor-native where formats differ: Claude subagents are Markdown, while Codex
subagents are TOML. Do not force identical output formats merely to make the
source tree look symmetric.

## Desktop applications and connectors

Claude Desktop and ChatGPT/Codex Desktop are supported companions to their CLI
tools. Installed connector configuration is declarative where a stable vendor
CLI exists. Authentication remains account-bound and interactive; credentials,
session tokens, and OAuth grants never belong in dotfiles or Workbench.

The expected connector split is:

- ChatGPT/Codex: official plugins for Gmail, Google Calendar, and Granola.
- Claude Code/Desktop: managed MCP declarations where no equivalent managed
  plugin is part of the selected workflow.
- External local MCPs remain explicit and are reported by `workbench check`
  rather than silently deleted.

## Editor and terminal

Editors and terminals are user-interface choices owned by dotfiles. They do not
become first-class agent configuration targets merely because they can host an
agent extension. Project instructions remain portable through `AGENTS.md` and
the two managed vendor entry points.

## Evaluation boundary

Candidates belong in [`../tools-to-evaluate.md`](../tools-to-evaluate.md).
Rejected or retired integrations belong in
[`../../docs/decisions/tombstones.md`](../../docs/decisions/tombstones.md).
Promote a tool into this document only after it becomes part of the recurring
workflow and has a reproducible install, update, and removal path.

Evaluate additions on:

1. distinct recurring value rather than feature overlap
2. predictable context and token cost
3. stable, declarative installation
4. safe authentication and secret handling
5. observability and deterministic health checks
6. clean removal without leaving generated residue

One-off experiments do not justify another deployment target. When an
integration is removed, delete its active configuration and record the reason
and revisit trigger in the tombstone log.
