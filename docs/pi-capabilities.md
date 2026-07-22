# Pi agent - capability overview and build candidates

Snapshot of what the Pi harness can do and the candidate enhancements under review. [`pi-build-philosophy.md`](pi-build-philosophy.md) owns adoption and rejection rationale; this page owns current operational state. Captured 2026-07-21 and updated as the managed harness changes.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, branded welcome, custom footer (git-status), consult (second opinion), discovery telemetry, permission policy, presets (including read-only plan mode), safe-git, worker (one worktree-isolated delegate), and google-readonly (owned Gmail/Calendar read-only tools). Pinned packages add the currently-idle MCP discovery proxy and a native wrapper around the existing Agent Browser CLI.

## Delta over vanilla Pi

Everything the managed harness adds to a stock `pi` install, in one place:

| Addition | Kind | What it provides |
|---|---|---|
| Workbench deploy + drift | Infrastructure | One public source of truth for settings, providers, presets, policy, extensions, and shared skills; `workbench sync pi` / `workbench drift pi` |
| Custom footer (`git-status.ts`) | Extension | Git state, model, thinking, context %, tokens, cost, tok/s, compaction count, Codex subscription quota windows |
| Activity title (`activity-title.ts`) | Extension | Terminal-tab spinner, repository, deterministic first-prompt session name, active tool |
| Welcome mark (`welcome.ts`) | Extension | Branded confirmation that managed configuration loaded |
| Permission policy (`permission-policy.ts` + JSON) | Guardrail | Deny rules for risky shell effects, protected read/write paths, remote-MCP default-deny, self-modification protection |
| Safe git (`safe-git.ts`) | Guardrail | Approval gates on destructive git and mutating `gh` |
| Presets (`presets.ts` + JSON) | Extension | `plan` (read-only, plan contract), `read`, `safe-auto`, `dev` |
| Consult (`consult.ts`) | Extension | `/consult` second opinion via Claude, Codex, or Fable |
| Worker (`worker.ts`) | Extension | `/worker` — one worktree-isolated child Pi; parent-owned review and merge |
| Google read-only (`google-readonly.ts`) | Extension | Owned Gmail/Calendar tools; loopback OAuth, read-only scopes, 0600 tokens |
| Strava read-only (`strava-readonly.ts`) | Extension | Owned activity/stats tools; loopback OAuth, `activity:read_all`, 0600 tokens |
| Discovery telemetry (`discovery-telemetry.ts`) | Experiment | Local navigation/verification friction metrics; review 2026-07-28 |
| `pi-agent-browser-native` 0.2.71 | Pinned package | Structured wrapper over the Agent Browser CLI (0.32.2) |
| `just typecheck-pi` | Dev gate | Typechecks extensions against the installed Pi API |
| pi-guide skill | Skill | Versioned tutorial for native Pi plus this harness |

The community Pi Web UI comparison that previously lived here concluded
**don't migrate**; the decision and its revisit conditions live in
[`pi-build-philosophy.md`](pi-build-philosophy.md) (Explicitly absent).

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

Gmail and Google Calendar are served by the Workbench-owned `google-readonly.ts`
extension: direct REST calls to `googleapis.com`, loopback OAuth with PKCE,
read-only scopes. All connector credentials live in one agent-neutral root,
`~/Library/Application Support/notes-app/` — `google/client-secret.json` (the
OAuth client shared with the notes Gmail labeler), `google/readonly-token.json`,
`strava/client.json`, and `strava/token.json`, each mode 0600 under 0700
directories. The whole root is on the permission policy's protected read and
write lists. `/google-auth` mints the grant once; `/google-status` reports
state.
Tools: `gmail_search_threads`, `gmail_get_thread`, `calendar_list_calendars`,
`calendar_list_events` — read-only by construction, with a standing guideline
that message and event content is untrusted data, never instructions.

Pi has no MCP client installed. `pi-mcp-adapter` was removed once every source
moved to owned connectors; the notes project's Granola tools spawn a pinned
`mcp-remote` directly. The permission policy's remote-MCP default-deny remains
as dormant defense should an MCP tool ever reappear.

Strava is served by the sibling `strava-readonly.ts` extension: a personal API
app (free; callback domain `localhost`), then `/strava-auth`. Tools:
`strava_list_activities`, `strava_get_activity`, `strava_athlete_stats` —
read-only, `read,activity:read_all` scopes, rotating refresh tokens persisted at
0600. The MCP route stays retired (Strava's discovery metadata is incompatible
with local MCP proxies; Claude's hosted connector works because Anthropic's
client handles it).

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

## Build candidates

Adoption rationale, research tracks, and the idea parking lot live in
[`pi-build-philosophy.md`](pi-build-philosophy.md); active time-boxed trials live
in [`experiments.md`](experiments.md). This page records only current
operational state.

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

Hardened 2026-07-21 after an adversarial review of the guardrail regexes:

- `curl` short upload/exfil flags (`-d`, `-H`, `-b`, `-o`, `-T`, `-X`) and the
  long `--form`/`--header`/`--cookie`/`--json` forms are denied alongside the
  previously blocked long data flags. `-F` remains open because case-insensitive
  matching would also block the ubiquitous `-f`; form uploads still trip the
  protected-path mention check when they reference secrets.
- Interpreter escapes via `--eval`/`--exec` and heredocs (`python3 <<EOF`) are
  denied, not just `-c`/`-e`.
- Protected-path matching now strips substitution punctuation (`$(cat X)`),
  expands `$HOME`, and resolves symlinks before glob matching.
- `~/.pi/agent/**` is write-protected, so a session cannot silently edit its own
  policy, extensions, or settings; changes flow through the repo and
  `workbench sync pi`.
- Safe-git prompts only on mutating `gh` subcommands; reads pass silently so a
  session-wide approval never covers unseen mutations.
- `just typecheck-pi` typechecks every extension against the installed Pi API,
  and `workbench sync pi` merges `mcp.json` per server, so ad hoc connected
  servers survive a sync and appear in drift as external entries.
- The MCP allowlist still carries both prefixed and unprefixed tool-name variants
  for Gmail/Calendar; prune to the observed names after the first authorized
  connection.

Known limits are recorded as named residual risks in
[`pi-build-philosophy.md`](pi-build-philosophy.md): GET-based exfiltration,
adapter token custody, and alias expansion after inspection.

These are harness guardrails, not syscall containment. Use Codex or Claude Code
when a task requires high-autonomy execution against untrusted content.

## Notes

- Context size is provider-specific. Pi 0.81.1 currently advertises GPT-5.6 Sol as 272K through the `openai-codex` subscription route and 1.1M through OpenRouter. The footer uses the active provider's model metadata; it must not relabel the subscription route as 1.1M without endpoint evidence.
- The extension API does not expose the auto-compaction toggle, but completed compactions appear as session entries and are counted in the footer. Codex subscription windows come from the authenticated local Codex app-server; no credentials or conversation content are read. Pi still has no direct thinking-level getter, so the footer reads `thinking_level_change` session entries.
- Footer convention: keep every data point the default footer had; additions must earn their width.
