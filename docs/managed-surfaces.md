# Managed Surfaces

The exhaustive map of what `workbench sync` deploys and `workbench drift`
verifies, per harness. The README keeps only the summary; this document is the
reference.

| Surface | Pi | Claude Code / Desktop | Codex |
| --- | --- | --- | --- |
| CLI presence | `pi` on `PATH` | Checked when managing plugins | Checked when managing plugins |
| Global instructions | `~/.pi/agent/AGENTS.md` | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` |
| Harness configuration | `~/.pi/agent/{settings,models,presets}.json` | `~/.claude/settings.json`, `~/.claude.json` | `~/.codex/config.toml` |
| Desktop configuration | None | Claude Desktop MCPs and managed preferences | ChatGPT connector plugins through the Codex plugin CLI |
| Command policy | `~/.pi/agent/permission-policy.json` plus permission-policy and safe-git extensions | Claude permissions and sandbox settings | `~/.codex/rules/default.rules` |
| Extensions / hooks | `~/.pi/agent/extensions/*.ts` | Claude settings plus shared runtime scripts | `~/.codex/hooks.json` plus shared runtime scripts |
| Specialist agents | Not native; intentionally not deployed | `~/.claude/agents/*.md` | `~/.codex/agents/*.toml` |
| Skills | Shared skills in `~/.agents/skills`; Pi-only external skills may remain in `~/.pi/agent/skills` | Claude global skill directory | `~/.agents/skills` |
| Plugins / packages | `packages` in managed Pi settings | IDs from `agents/claude/plugins.json` | IDs from `agents/codex/plugins.json` |
| MCP servers | None by design | Shared registry plus preserved external servers | Shared registry plus preserved external servers |
| Generated/private state | Contents preserved and unmanaged; session filesystem permissions enforced private | Preserved vendor state | Preserved vendor state |

Pi settings, models, and presets preserve unknown top-level entries while
Workbench replaces its managed entries. Pi and Codex share one deployed copy of
portable skills under `~/.agents/skills`, which both harnesses discover. This
avoids Pi's duplicate-skill warning; Pi-only external skills remain under
`~/.pi/agent/skills`. Unknown Pi extensions, skills, model providers, and presets
are reported as `EXTERNAL`, not deleted. Pi extensions
are deployed as real files rather than repository symlinks so moving a checkout
cannot silently disable the harness.

Plugin IDs are version-controlled and installation is reproducible. OAuth
consent and account sessions remain interactive vendor state; credentials,
session transcripts, trust decisions, and OAuth grants never belong in
Workbench. Sync sets Pi session directories to `0700` and transcript files to
`0600` without reading or changing their contents.

## Drift semantics

`workbench drift` distinguishes two states:

- `DRIFT` - a Workbench-managed value is missing or differs; the command exits
  non-zero.
- `EXTERNAL` - a valid unmanaged addition remains in the live harness config. It
  is reported for visibility but does not fail the command.

`sync` preserves unmanaged configuration, writes only Workbench-owned values,
and keeps one `.bak` file before replacing live configuration.
