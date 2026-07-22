# Pi agent - capability overview and build candidates

Snapshot of what the pi harness can do, what third parties have built on it, and the candidate enhancements we've considered. Status: **reference only - nothing here is committed work.** Captured 2026-07-21 after reviewing the community "PI Web UI / Control Deck" (@firstpick/pi-package-webui, v0.4.8 DEV).

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): branded welcome, custom footer (git-status), consult (second opinion), discovery telemetry, permission policy, presets, and safe-git.

## What the community PI Web UI adds (reviewed 2026-07-21)

| Capability | Our status |
|---|---|
| Session stats (tokens, cache, cost, ctx, model+effort, git) | **Have it** - our footer covers all of these |
| Generation speed (tok/s) | **Done** 2026-07-21 (footer, per-turn output/elapsed) |
| Auto-compact indicator | **Done** 2026-07-22 - shows `(auto)` before the first compaction and `compact×N` from actual session entries afterward |
| Fast-mode status | **Done** 2026-07-21 when the active model/session exposes it; red `fast ON`, dim `fast off` |
| Codex subscription windows | **Done** 2026-07-22 - remaining percentage and local reset date for each app-server rate-limit window; refreshed after responses and every five minutes |
| Branded startup mark | **Done** 2026-07-21 - six-line `PI` wordmark blending Workbench ruby through orange into Dotfiles topaz |
| Multi-session browser tabs | Gap - TUI is one session per terminal; tmux covers most of this |
| Remote access (open-to-network + PIN) | Gap - the standout feature; phone access to running agents |
| Agent-done desktop notifications | Gap - useful for long autonomous runs |
| GUI conveniences (model/thinking dropdowns, themes, repo explorer, server actions) | Low value for a terminal-native workflow |

Verdict at review time: **don't migrate.** Trust surface of a dev-version single-author package with a network-listening mode, against a workflow that is terminal-native and already hardened (permission-policy, safe-git). Revisit if multi-session or phone access becomes a real need.

## Managed Workbench target

Pi is a first-class `workbench sync pi` / `workbench drift pi` target. Workbench
deploys its global rules, settings, model providers, presets, permission policy,
extensions, and shared skills. Shared skills live once under `~/.agents/skills`,
which Pi discovers alongside Pi-only external skills under its native directory;
this prevents duplicate-skill startup warnings. Drift checks the Pi CLI, every
managed file, and reports unknown skills/extensions/providers/presets as external
without deleting them. Authentication, trust decisions, sessions, model cache,
and discovery logs remain private live state.

## Prompt navigation

Pi 0.81.1 already ships the safe core of the requested prompt navigator. Workbench
sets `/tree` to its `user-only` filter and keeps double-Escape bound to opening it.
From the transcript: double-Escape, then Up/Down to preview prior prompts, Escape
to return without changing context. Enter intentionally rewinds to the selected
prompt and starts a branch, so it is not a read-only scroll action. Pi's public
extension API does not expose the terminal scrollback viewport, so a Claude-style
preview that tracks manual terminal scrolling would require unsupported TUI
internals and is intentionally not built.

## Build candidates (idea parking lot, prioritized by leverage)

1. **Tighten what we have** - footer legend terseness pass once the annotations bed in; tune ctx severity thresholds with real usage.
2. **Completion notifications** - explicitly deferred because notifications interrupt flow; revisit only if long unattended runs become common.
3. **Multi-session awareness** - an extension or CLI that lists live pi sessions (pid, cwd, model, ctx%, cost) across terminals, read-only. Cheaper than tabs, fits tmux.
4. **Remote access, if ever needed** - prefer Tailscale + SSH/tmux over adopting the community web UI's PIN model; audit first if the package is ever installed.
5. **Speed-based model comparison** - with tok/s now logged in the footer, a future extension could record per-model speed/cost history to inform auto vs explicit model choice.

## Discovery telemetry experiment (started 2026-07-21)

A disposable, local-only experiment to identify where model navigation wastes time before building LSP or repository-index infrastructure.

- Extension: `agents/pi/extensions/discovery-telemetry.ts`
- Config: `agents/pi/settings.json#discoveryTelemetry`
- Raw state: `~/.local/state/workbench/pi-discovery/YYYY-MM-DD.jsonl`
- Commands: `/discovery status|on|off|report|clear`
- Retention: 7 days; 5 MB/day cap; trusted projects only
- Never persisted: prompts, responses, source contents, patches, search terms, complete commands, environment, URLs, credentials
- Current experiment metrics: first-mutation latency + prior tool/search/read counts; unique-path fanout; repeated reads only when path/range/mtime are unchanged; edit-before-read; routing-doc reads; classified tool failures; zero-result searches; per-turn tool mix, duration, and context growth; verification after mutation
- Footer status: `discovery ● on` (accent) / `discovery ○ off` (dim), inline with the repo line when width allows

**Removal is intentionally complete and mechanical:** delete the canonical extension, remove the `discoveryTelemetry` settings block, run `workbench sync pi`, and delete `~/.local/state/workbench/pi-discovery/`. No shared agent code depends on it.

Review after one week. Keep only if it identifies a concrete change (narrow LSP operations, better project maps, affected-test selection, or documentation fixes); otherwise remove it and clear the logs.

## Permission guardrails

Pi has no native OS sandbox. Workbench therefore deploys two explicit guardrail
layers: an effect-aware path/command policy and safe-git approval gates. Read and
write path rules are separate, so installed dependency documentation and harmless
filenames such as `token-efficiency.md` remain readable while credential files
stay blocked and dependency trees remain write-protected. Read-only GitHub API
and public `curl` output are allowed; mutations, downloads, uploads, remote script
execution, destructive Git, and shell filesystem mutation remain blocked.

These are harness guardrails, not syscall containment. Use Codex or Claude Code
when a task requires high-autonomy execution against untrusted content.

## Notes

- Context size is provider-specific. Pi 0.81.1 currently advertises GPT-5.6 Sol as 272K through the `openai-codex` subscription route and 1.1M through OpenRouter. The footer uses the active provider's model metadata; it must not relabel the subscription route as 1.1M without endpoint evidence.
- The extension API does not expose the auto-compaction toggle, but completed compactions appear as session entries and are counted in the footer. Codex subscription windows come from the authenticated local Codex app-server; no credentials or conversation content are read. Pi still has no direct thinking-level getter, so the footer reads `thinking_level_change` session entries.
- Footer convention: keep every data point the default footer had; additions must earn their width.
