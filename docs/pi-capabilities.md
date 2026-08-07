# Pi agent - capability overview and build candidates

Snapshot of what the Pi harness can do and the candidate enhancements under review. [`pi-build-philosophy.md`](pi-build-philosophy.md) owns adoption and rejection rationale; this page owns current operational state. Captured 2026-07-21 and updated as the managed harness changes.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, transcript reader, branded welcome, custom footer (git-status), consult (second opinion), permission policy, presets (including read-only plan mode), safe-git, worker (one worktree-isolated delegate), owned read-only Google and Strava connectors, and a confirmed Apple Notes bridge whose writes are restricted to `Agents`. The pinned package wraps the existing Agent Browser CLI.

## Delta over vanilla Pi

Everything the managed harness adds to a stock `pi` install, in one place:

| Addition | Kind | What it provides |
|---|---|---|
| Workbench deploy + drift | Infrastructure | One public source of truth for settings, providers, presets, policy, extensions, and shared skills; `workbench sync pi` / `workbench drift pi` |
| Custom footer (`git-status.ts`) | Extension | Git state, model, thinking, context %, tokens, cost, tok/s, compaction count, Codex subscription quota windows |
| Activity title (`activity-title.ts`) | Extension | Terminal-tab spinner, repository, deterministic first-prompt session name, active tool |
| Transcript reader (`transcript-reader.ts`) | Extension | `/reader` or Ctrl+Shift+R opens a read-only prompt/work/answer navigator at the newest completed answer; work is summarized and expandable while the standard Pi transcript remains available |
| Welcome mark (`welcome.ts`) | Extension | Branded confirmation that managed configuration loaded |
| Permission policy (`permission-policy.ts` + JSON) | Guardrail | Deny rules for risky shell effects, protected read/write paths, remote-MCP default-deny, self-modification protection |
| Safe git (`safe-git.ts`) | Guardrail | Approval gates on destructive git and mutating `gh` |
| Presets (`presets.ts` + JSON) | Extension | `plan` (read-only, plan contract), `sources` (connector reads only, no shell/edit — the prompt-injection containment mode), `read`, `safe-auto`, `dev` |
| Consult (`consult.ts`) | Extension | `/consult` second opinion via Claude, Codex, or Fable |
| Worker (`worker.ts`) | Extension | `/worker` — one worktree-isolated child Pi; parent-owned review and merge |
| Google read-only (`google-readonly.ts`) | Extension | Owned Gmail/Calendar tools; loopback OAuth, read-only scopes, 0600 tokens |
| Strava read-only (`strava-readonly.ts`) | Extension | Owned activity/stats tools; loopback OAuth, `activity:read_all`, 0600 tokens |
| Apple Notes (`apple-notes.ts` + shared CLI) | Extension | Reads unshared, unlocked notes; confirmed create/append only in unshared `Agents`; Claude Code and Codex can use the same macOS-only CLI through shell |
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
without deleting them. Authentication, trust decisions, sessions, and model cache remain private live state.

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
context; Enter intentionally rewinds and branches.

For reading rather than branching, `/reader` or Ctrl+Shift+R opens the managed
Transcript Reader. It groups the active branch into prompt, compact work, and final
answer sections, opens at the newest completed answer, and moves between turns with
`[` / `]`. `p`, `a`, and `g` jump to the prompt, current answer, and newest answer;
`w` expands progress notes. It uses only the public session and custom-component APIs,
never changes the active branch or editor, and leaves the standard Pi transcript as
the full-detail fallback. Paseo owns its mobile rendering, so this TUI extension does
not add the same controls to the Paseo App Store client.

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
