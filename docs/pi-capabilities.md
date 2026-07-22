# Pi agent - capability overview and build candidates

Snapshot of what the Pi harness can do and the candidate enhancements under review. [`pi-build-philosophy.md`](pi-build-philosophy.md) owns adoption and rejection rationale; this page owns current operational state. Captured 2026-07-21 and updated as the managed harness changes.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, branded welcome, custom footer (git-status), consult (second opinion), discovery telemetry, permission policy, presets, and safe-git. Pinned packages add the token-efficient MCP discovery proxy and a native wrapper around the existing Agent Browser CLI.

## What the community PI Web UI adds (reviewed 2026-07-21)

| Capability | Our status |
|---|---|
| Session stats (tokens, cache, cost, ctx, model+effort, git) | **Have it** - our footer covers all of these |
| Generation speed (tok/s) | **Done** 2026-07-21 (footer, per-turn output/elapsed) |
| Auto-compact indicator | **Done** 2026-07-22 - shows `(auto)` before the first compaction and `compact×N` from actual session entries afterward |
| Terminal activity title + session name | **Done** 2026-07-22 - spinner, repository, deterministic first-prompt name, and active tool; explicit session names remain authoritative |
| Fast-mode status | Intentionally removed 2026-07-22 - the subscription route does not expose reliable state, priority service is expensive, and Evan prefers default-off over custom control machinery |
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

Pi 0.81.1 emits OSC 133 semantic zones around user and final assistant messages,
and Ghostty defines `jump_to_prompt` actions for navigating those zones. In the
current Ghostty session, however, Command-Up/Down behaved as top/bottom scrolling
rather than semantic navigation; effective-config inspection did not establish a
working binding. Compaction may remove old transcript content, but it does not
explain the observed key behavior. Treat terminal-native navigation as promising
but unverified until a controlled fresh-session probe passes.

Workbench also sets `/tree` to its `user-only` filter and keeps double-Escape bound
to opening it. Up/Down previews prior prompts and Escape returns without changing
context; Enter intentionally rewinds and branches. Pi's public extension API still
does not expose the terminal scrollback viewport, so a richer read-only navigator
needs either a verified terminal path or an upstream viewport API.

## Connector access

Workbench configures pinned `pi-mcp-adapter` 2.11.0 with lazy OAuth routes for
Gmail and Google Calendar. The servers are official `googleapis.com` endpoints;
the client adapter is a third-party community package, not official Pi or Google
support. OAuth stays explicit with `/mcp-auth <server>`, scopes are read-only, and
Workbench's permission policy blocks remote tool calls outside a read-only
allowlist. Tokens would remain in mode-0600 adapter state outside Workbench.
Google does not advertise dynamic client registration, so no token is granted
until a registered client and the residual extension trust are accepted.

Strava is not configured in Pi yet. Its protected-resource metadata points clients
to an issuer path whose prefix-form discovery URL returns HTML/404, while the
working RFC suffix-form metadata advertises dynamic registration. The current MCP
adapter therefore fails with `Unable to register client`. Do not retain a noisy
broken startup route; use Claude's already-connected Strava MCP until that
metadata/adapter incompatibility is fixed or a client is registered explicitly.

## Native Agent Browser

Workbench pins `pi-agent-browser-native` 0.2.71 around the existing Agent Browser
CLI. It adds structured tool results, bounded context spills, secret redaction,
stale-reference guards, session recovery, and artifact metadata. A live
`example.com` open/snapshot smoke passed. Its doctor still flags the machine's
Agent Browser 0.31.1 against the wrapper's 0.32.2 baseline; Dotfiles already
declares 0.32.2, but the global dependency update is blocked by the harness and
must be run manually. It does not justify using authenticated browser profiles by default;
temporary sessions stay the safe baseline. Optional search credentials remain
disabled.

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
