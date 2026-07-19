# Managed Surfaces

The exhaustive map of what `workbench sync` deploys and `workbench drift`
verifies, per vendor. The README keeps only the summary; this document is the
reference.

| Surface | Claude Code / Desktop | Codex |
| --- | --- | --- |
| Global instructions | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` |
| Vendor configuration | `~/.claude/settings.json`, `~/.claude.json` | `~/.codex/config.toml` |
| Desktop configuration | Claude Desktop MCPs and managed preferences | ChatGPT connector plugins through the Codex plugin CLI |
| Command policy | Claude permissions and sandbox settings | `~/.codex/rules/default.rules` |
| Hooks | Claude settings plus shared runtime scripts | `~/.codex/hooks.json` plus shared runtime scripts |
| Specialist agents | `~/.claude/agents/*.md` | `~/.codex/agents/*.toml` |
| Skills | Claude global skill directory | `~/.agents/skills` |
| Plugins | IDs from `agents/claude/plugins.json` | IDs from `agents/codex/plugins.json` |
| MCP servers | Shared registry plus preserved external servers | Shared registry plus preserved external servers |

Plugin IDs are version-controlled and installation is reproducible. OAuth
consent and account sessions remain interactive vendor state; Workbench cannot
and should not commit them.

## Drift semantics

`workbench drift` distinguishes two states:

- `DRIFT` — a Workbench-managed value is missing or differs; the command exits
  non-zero.
- `EXTERNAL` — a valid unmanaged addition remains in the live vendor config. It
  is reported for visibility but does not fail the command.

`sync` preserves unmanaged vendor settings, writes only Workbench-owned values,
and keeps one `.bak` file before replacing live configuration.
