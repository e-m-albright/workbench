# Adversarial Agent-Safety Audit

Use this prompt with a capable model that has no prior conversation context.
Give it read-only access to `~/code/public/workbench` and
`~/code/public/dotfiles`.

```text
Act as a skeptical macOS security engineer reviewing a personal coding-agent
configuration. This is a read-only audit: do not edit files, run destructive
tests, install software, or modify live agent settings.

Goal: determine whether this setup provides the smallest honest safety boundary
that prevents obvious catastrophic mistakes without making normal coding work
approval-heavy. The machine has no production databases. Database, cloud, and
infrastructure controls should normally belong to the projects that own them.

Threat model:
- accidental or misinterpreted commands from Claude Code or Codex
- recursive force-deletion, destructive disk commands, destructive Git, and
  writes to credential files
- bypass by flag ordering, shell wrappers, command composition, symlinks, MCP
  tools, non-shell file tools, or vendor modes that disable protections
- configuration drift and unsupported settings that create false confidence
- compromised tools, malicious dependencies, and deliberate hostile code are
  out of scope unless the current design falsely claims to cover them

Current local versions at the time of this prompt:
- Claude Code 2.1.177
- Codex CLI 0.144.4

Inspect at minimum:
- ~/code/public/workbench/README.md
- ~/code/public/workbench/agents/claude/permissions.json
- ~/code/public/workbench/agents/shared/hooks.json
- ~/code/public/workbench/agents/codex/default.rules
- ~/code/public/workbench/agents/codex/statusline.toml
- ~/code/public/workbench/agents/shared/hooks/
- ~/code/public/workbench/scripts/workbench.py
- ~/code/public/workbench/tests/test_workbench.py
- ~/code/public/dotfiles/install.sh

Also inspect the deployed ~/.claude and ~/.codex configuration read-only if it
is available. Compare canonical and live state.

Fact-check all vendor-specific claims against current official Claude Code and
OpenAI Codex documentation. Distinguish clearly among:
1. OS-enforced boundaries
2. vendor sandbox/permission enforcement
3. hook or command-pattern defense in depth
4. advisory prompt instructions

Answer these questions:
1. What is genuinely prevented, and by which enforcement layer?
2. What is merely discouraged or detected?
3. Which settings are unsupported, stale, silently ignored, or overridden by a
   command-line flag or vendor mode?
4. Can ordinary command variants bypass the deny rules or hooks? Demonstrate
   only with inert strings or parser-level tests, never real destructive paths.
5. Are any allow rules broader than their comments imply?
6. Do the hooks fail closed or fail open when jq, Bash, input fields, or hook
   registration behave unexpectedly?
7. Is anything duplicated across sandbox, permissions, hooks, and prose without
   adding meaningful defense?
8. What is the smallest coherent configuration you would ship on a personal
   Mac? Prefer deletion and native vendor controls over custom infrastructure.

Return:
- a one-paragraph verdict and confidence level
- a threat/control matrix with enforcement strength and bypasses
- findings ordered by severity with exact file and line references
- a KEEP / SIMPLIFY / REMOVE / ADD table
- a minimal recommended end-state configuration
- safe, non-destructive verification cases
- unresolved claims that require vendor confirmation

Do not reward complexity. Penalize controls that create a feeling of safety
without enforceable coverage. Do not propose daemons, scheduled audits,
snapshots, kernel extensions, MDM, or a general policy framework unless you can
show a concrete threat in this personal-laptop scope that native controls cannot
address.
```
