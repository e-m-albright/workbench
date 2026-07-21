# Pi agent - capability overview and build candidates

Snapshot of what the pi harness can do, what third parties have built on it, and the candidate enhancements we've considered. Status: **reference only - nothing here is committed work.** Captured 2026-07-21 after reviewing the community "PI Web UI / Control Deck" (@firstpick/pi-package-webui, v0.4.8 DEV).

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`workbench/agents/pi/extensions/`): custom footer (git-status), consult (second opinion), permission-policy, presets, safe-git.

## What the community PI Web UI adds (reviewed 2026-07-21)

| Capability | Our status |
|---|---|
| Session stats (tokens, cache, cost, ctx, model+effort, git) | **Have it** - our footer covers all of these |
| Generation speed (tok/s) | **Done** 2026-07-21 (footer, per-turn output/elapsed) |
| Auto-compact indicator | **Done** 2026-07-21 (static "(auto)"; extension API can't read the toggle) |
| Multi-session browser tabs | Gap - TUI is one session per terminal; tmux covers most of this |
| Remote access (open-to-network + PIN) | Gap - the standout feature; phone access to running agents |
| Agent-done desktop notifications | Gap - useful for long autonomous runs |
| GUI conveniences (model/thinking dropdowns, themes, repo explorer, server actions) | Low value for a terminal-native workflow |

Verdict at review time: **don't migrate.** Trust surface of a dev-version single-author package with a network-listening mode, against a workflow that is terminal-native and already hardened (permission-policy, safe-git). Revisit if multi-session or phone access becomes a real need.

## Build candidates (idea parking lot, prioritized by leverage)

1. **Tighten what we have** - footer legend terseness pass once the annotations bed in; tune ctx severity thresholds with real usage.
2. **Desktop notification on `agent_settled`** - small extension, no new surface; covers the main notification win without the web UI.
3. **Multi-session awareness** - an extension or CLI that lists live pi sessions (pid, cwd, model, ctx%, cost) across terminals, read-only. Cheaper than tabs, fits tmux.
4. **Remote access, if ever needed** - prefer tailscale + SSH/tmux over adopting the community web UI's PIN model; audit first if the package is ever installed.
5. **Speed-based model comparison** - with tok/s now logged in the footer, a future extension could record per-model speed/cost history to inform auto vs explicit model choice.

## Notes

- The extension API does not expose: auto-compaction state, rate-limit windows (except Codex response headers), or a direct thinking-level getter (we read `thinking_level_change` session entries instead).
- Footer convention: keep every data point the default footer had; additions must earn their width.
