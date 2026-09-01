# Pi agent - capability overview and build candidates

Snapshot of what the Pi harness can do and the candidate enhancements under review. [`pi-build-philosophy.md`](pi-build-philosophy.md) owns adoption and rejection rationale; this page owns current operational state. Captured 2026-07-21 and updated as the managed harness changes.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, branded welcome, custom footer, consult, permission policy, presets, safe-git, privacy-first inference routing, one worktree-isolated worker, confirmed GitHub workflow dispatch, read-only Google and Strava connectors, and an Apple Notes bridge whose writes require confirmation and remain restricted to `Agents`. The pinned package wraps the existing Agent Browser CLI; machine-local Apple bridge CLIs remain outside this repository.

## Delta over vanilla Pi

Everything the managed harness adds to a stock `pi` install, in one place:

| Addition | Kind | What it provides |
|---|---|---|
| Workbench deploy + drift | Infrastructure | One public source of truth for settings, providers, presets, policy, extensions, and shared skills; `workbench sync pi` / `workbench drift pi` |
| Custom footer (`footer.ts`) | Extension | Git state, model, thinking, context %, tokens, cost, tok/s, compaction count, Codex subscription quota windows |
| Activity title (`activity-title.ts`) | Extension | Local working row with elapsed time, terminal-tab spinner, repository, deterministic first-prompt session name, active tool |
| Welcome mark (`welcome.ts`) | Extension | Branded confirmation that managed configuration loaded, including the authoritative installed Pi version |
| Permission policy (`permission-policy.ts` + JSON) | Guardrail | Deny rules for risky shell effects, protected read/write paths, remote-MCP default-deny, self-modification protection |
| Safe git (`safe-git.ts`) | Guardrail | Approval gates on destructive git and mutating `gh` |
| Presets (`presets.ts` + JSON) | Extension | `plan` (read-only, plan contract), `sources` (connector reads only, no shell/edit — the prompt-injection containment mode), `read`, `safe-auto`, `dev` |
| Consult (`consult.ts`) | Extension | `/consult` second opinion via Claude, Codex, or Fable |
| Worker (`worker.ts`) | Extension | Model-callable `worker` tool plus `/worker`: autonomously delegate, review, and discard one worktree-isolated child Pi; parent-owned adoption and verification |
| Google read-only (`google-readonly.ts`) | Extension | Owned Gmail/Calendar tools; loopback OAuth, read-only scopes, 0600 tokens |
| Strava read-only (`strava-readonly.ts`) | Extension | Owned activity/stats tools; loopback OAuth, `activity:read_all`, 0600 tokens |
| Apple Notes (`apple-notes.ts` + notes-layer CLI) | Extension | Reads unshared, unlocked notes; confirmed create/append only in unshared `Agents`; Claude Code and Codex can use the same macOS-only CLI through shell |
| Apple Contacts (`apple-contacts` CLI, owned by a machine-local private layer) | Shared CLI | Fixed-field search/read/create/update through macOS Contacts; writes require `--confirm-write`, preserve notes outside a bounded managed block, and never delete; private projection policy stays with its private owner |
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

Managed settings use Pi 0.84.3's native fullscreen mode. It intentionally looks like the ordinary transcript until viewport behavior matters, then provides owned-viewport scrolling, search, text selection, links, and previous/next jumps keyed to OSC 133 prompt-start markers. It does not provide a final-answer jump or restructure turns into prompt/work/answer sections. Those additions did not justify retaining the custom Transcript Reader.

Workbench also sets `/tree` to its `user-only` filter and keeps double-Escape bound
to opening it. Up/Down previews prior prompts and Escape returns without changing
context; Enter intentionally rewinds and branches.

## Bounded orchestration

The model-callable `worker` tool is the Pi harness's answer to one independent parallel implementation thread. It creates a separate Git worktree, runs one child Pi, forbids commit, push, dependency installation, and merge, and leaves adoption to the parent. In the `dev` preset the model may delegate without user approval, review and adopt useful changes, verify them in the parent checkout, and discard the worktree. `/worker <task>`, `/worker-status`, and `/worker-done` remain manual controls.

This does not provide workflow fleets, background schedules, or autonomous merging. `/consult` covers read-only independent judgment, while Claude Code remains the explicit route for exceptional coordinated finder/verifier fleets.

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
stale-reference guards, session recovery, and artifact metadata. The wrapper's
required CLI baseline belongs in its package contract; transient machine install
state belongs in live drift or doctor output, not this document. Authenticated
browser profiles remain opt-in, and temporary sessions stay the safe baseline.

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
calls are allowed, while shell network retrieval, mutations, downloads, uploads,
remote script execution, destructive Git, and shell filesystem mutation remain
blocked.

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
- `just typecheck-pi` typechecks every extension against the installed Pi API.
- Pi has no active MCP client or remote-tool allowlist. Gmail, Calendar, Strava,
  and Apple Notes access is provided by the bounded owned connectors above.
- On every session start, the permission-policy extension sets the active transcript
  to owner-only mode (`0600`). This preserves ordinary session history and resume
  behavior while removing group and other mode bits.

Known limits are recorded as named residual risks in
[`pi-build-philosophy.md`](pi-build-philosophy.md): GET-based exfiltration,
adapter token custody, and alias expansion after inspection.

These are harness guardrails, not syscall containment. Use Codex or Claude Code
when a task requires high-autonomy execution against untrusted content.

## Notes

- Context size is provider-specific. Pi (verified on 0.84.3) currently advertises GPT-5.6 Sol as 272K through the `openai-codex` subscription route and 1.1M through OpenRouter. The footer uses the active provider's model metadata; it must not relabel the subscription route as 1.1M without endpoint evidence.
- The extension API does not expose the auto-compaction toggle, but completed compactions appear as session entries and are counted in the footer. Codex subscription windows come from the authenticated local Codex app-server; no credentials or conversation content are read. Pi still has no direct thinking-level getter, so the footer reads `thinking_level_change` session entries.
- Footer convention: keep every data point the default footer had; additions must earn their width.
