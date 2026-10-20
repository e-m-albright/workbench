# Pi agent - capability overview and build candidates

Snapshot of the managed Pi 0.86.1 harness, reviewed against repository configuration on 2026-10-20. [Pi design decisions](decisions.md) owns adoption and rejection rationale; this page owns current operational state.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, verified local clipboard copy, structured workspace file operations, confirmed ingress discard, branded welcome, custom footer, consult, permission policy, the `dev` preset, explicit local/frontier routing, one worktree-isolated worker, confirmed GitHub workflow dispatch, and the read-only Strava connector. The pinned package wraps the existing Agent Browser CLI. The Google connector is retired; Apple Notes is intentionally outside the coding-agent boundary.

## Delta over vanilla Pi

Everything the managed harness adds to a stock `pi` install, in one place:

Managed `p` and native `pi` share deployed extensions. Their usable operations
differ because only `p` adds the Workbench outer boundary; see the launch matrix below.

| Addition | Kind | What it provides |
|---|---|---|
| Workbench deploy + drift | Infrastructure | One public source of truth for settings, providers, presets, policy, extensions, and shared skills; `workbench sync pi` / `workbench drift pi` |
| Custom footer (`footer.ts`) | Extension | Git state refreshed every 15 seconds and after tools or user shell commands; model, thinking, context %, tokens, cost, tok/s, compaction count, Codex subscription quota windows |
| Activity title (`activity-title.ts`) | Extension | Local working row with elapsed time, terminal-tab spinner, repository, deterministic first-prompt session name, active tool, and immediate `/rename` during active work |
| Welcome mark (`welcome.ts`) | Extension | Branded confirmation that shared configuration loaded, including the authoritative installed Pi version; authority is shown separately |
| Permission policy (`permission-policy.ts` + JSON) | Guardrail | Deny rules for risky shell effects, machine-local private paths, remote-MCP default-deny, managed harness edits, and actionable safe alternatives on rejection |
| Workspace files (`workspace-files.ts`) | Tool | Workspace-bounded rename, copy, and directory creation without shell mutation; no deletion or overwrite |
| Ingress discard (`ingress.ts`) | Tool | Confirmed move of one consumed `~/code/ingress` file to Trash; agent handoffs remain lifecycle-managed |
| Clipboard (`clipboard.ts`) | Tool | Copies approved plain text through the terminal's one-way OSC 52 channel without reading the clipboard or creating temporary files |
| Safe git (`safe-git.ts`) | Guardrail | Approval gates on destructive git and mutating `gh` |
| Presets (`presets.ts` + JSON) | Extension | One default `dev` tool and execution profile; model location and access scope belong to the launch mode rather than a preset |
| Pi shortcut + native sandbox | Host guardrail | `p` shows `cloud > managed`; full `pi` retains native behavior |
| Consult (`consult.ts`) | Extension | Native hosted `/consult` provides a second opinion via Claude, Codex, or Fable; managed sessions direct the owner to native Pi, and local sessions refuse cloud consult |
| Worker (`worker.ts`) | Extension | Starts one child Pi in a sibling Git worktree, reports progress, and supports review and discard; managed children inherit the parent boundary and require an admitted sibling path |
| Strava read-only (`strava-readonly.ts`) | Extension | Owned activity/stats tools; loopback OAuth, `activity:read_all`, 0600 tokens |
| Apple Contacts (`apple-contacts` CLI, owned by a machine-local private layer) | Shared CLI | Fixed-field search/read/create/update through macOS Contacts; writes require `--confirm-write`, preserve notes outside a bounded managed block, and never delete; private projection policy stays with its private owner |
| `pi-agent-browser-native` 0.6.15 | Pinned package | Structured Agent Browser wrapper with optional machine-local public search |
| `just typecheck-pi` | Dev gate | Typechecks extensions against the installed Pi API |
| pi-guide skill | Skill | Versioned tutorial for native Pi plus this harness |

The community Pi Web UI comparison that previously lived here concluded
**don't migrate**; the decision and its revisit conditions live in
[Pi design decisions](decisions.md) (Explicitly absent).

## Managed Workbench target

Pi is a first-class `workbench sync pi` / `workbench drift pi` target. Workbench
deploys its global rules, settings, model providers, presets, permission policy,
extensions, and shared skills. Shared skills live once under `~/.agents/skills`,
which Pi discovers alongside Pi-only external skills under its native directory;
this prevents duplicate-skill startup warnings. Drift checks the Pi CLI, every
managed file, and reports unknown skills/extensions/providers/presets as external
without deleting them. Authentication, trust decisions, sessions, and model cache remain private live state.

Personal hosted sessions default to `openai-codex/gpt-6.1-sol` with medium thinking.
The work profile leaves provider and model selection to the host's policy and
rejects known personal settings, providers, extensions, and excluded skills.
Shared skill deployment uses tracked sources; the Archify archive download path is retired.

## Prompt navigation

Managed settings use Pi 0.86.1's native fullscreen mode. It intentionally looks like the ordinary transcript until viewport behavior matters, then provides owned-viewport scrolling, search, text selection, links, and previous/next jumps keyed to OSC 133 prompt-start markers. It does not provide a final-answer jump or restructure turns into prompt/work/answer sections. Those additions did not justify retaining the custom Transcript Reader.

Workbench also sets `/tree` to its `user-only` filter and keeps double-Escape bound
to opening it. Up/Down previews prior prompts and Escape returns without changing
context; Enter intentionally rewinds and branches.

## Bounded orchestration

A managed worker preflights an ordinary checkout and sibling placement beneath
`~/code/public`, `~/Desktop`, or `~/Downloads` before creating Git state. It launches a direct
child Pi binary, which inherits the parent's outer policy. This does not make
linked worktrees valid entrypoints for `p`; the managed entrypoint still requires
an ordinary checkout. Worktrees outside those shared roots fail with native-continuation guidance. Worker workflow
availability is not a claim that every Git operation succeeds under the boundary.
`/consult` directs managed sessions to native Pi because another vendor's login
is not admitted. Native hosted Pi can consult; local sessions refuse cloud consult.

The model-callable `worker` tool is the Pi harness's answer to one independent parallel implementation thread. It creates a separate Git worktree, starts one child Pi in the background with the parent's selected provider, model, and thinking level, and returns control to the parent after setup. A lightweight footer status reports elapsed time without polling or extra model calls; completion produces one notification. `worker review` or `/worker-status` reads the live diff or finished report against the captured starting commit, including staged and untracked output. The child is instructed not to commit, push, install dependencies, or merge, and adoption remains with the parent. In the `dev` preset the model may delegate without user approval, continue disjoint parent work, review and adopt useful changes, verify them in the parent checkout, and discard the worktree. `/worker <task>`, `/worker-status`, and `/worker-done` remain manual controls.

Discarding changed output requires an explicit `adopted` or `rejected` disposition.
Commits not reachable from the parent remain preserved; deliberate rejection of
those commits requires the manual `/worker-done --force` command. Failed Git
inspection preserves the worktree. Worker entrypoints reject recursive delegation.

This does not provide workflow fleets, background schedules, or autonomous merging. A worker must start from committed state and must not receive a task that depends on uncommitted parent files. In native hosted sessions, `/consult` covers read-only independent judgment.

The shared handoff skill uses a private global queue outside the managed grants.
A managed session cannot save there; return continuation text in the conversation
and save it from an authorized native session. Native history is separate from
managed history. Resume from the same checkout path; moving it changes its state
identity. Do not import private transcripts into hosted inference automatically.

## Connector access

General agents have no Gmail, Google Calendar, or Google Drive capability. The Google connector implementation is retired; Google connector credentials, local Drive trees, browser destinations, and shared Google API/content endpoints remain enforced exclusions in managed sessions. Native Pi retains soft connector guards,
which do not contain arbitrary code running with host authority. A future email labeler must be a separate brokered capability rather than an exception inside the coding harness. Apple Notes remains unavailable.

Pi has no MCP client installed. `pi-mcp-adapter` was removed once active source
access moved to owned connectors, and Granola's remaining project-scoped MCP
route was removed when the product was retired. The permission policy's
remote-MCP default-deny remains as dormant defense should an MCP tool ever
reappear.

Strava is served by the sibling `strava-readonly.ts` extension: a personal API
app (free; callback domain `localhost`), then `/strava-auth`. Tools:
`strava_list_activities`, `strava_get_activity`, `strava_athlete_stats` —
read-only, `read,activity:read_all` scopes, rotating refresh tokens persisted at
0600. The MCP route stays retired (Strava's discovery metadata is incompatible
with local MCP proxies; Claude's hosted connector works because Anthropic's
client handles it).

## Native Agent Browser

Workbench pins `pi-agent-browser-native` 0.6.15 around the existing Agent Browser
CLI. It adds structured tool results, bounded context spills, secret redaction,
stale-reference guards, session recovery, artifact metadata, and the
optional `agent_browser_web_search` companion when a search provider is configured
on the machine. Workbench distributes no search credential or Exa connector.
Use available native search to discover public sources, `agent_browser read <url>` to read a known
source with the lightest available reader, and a full browser only for rendered state,
JavaScript-only content, authentication, interaction, screenshots, or diagnostics.
Managed sessions use a fresh contained browser; personal profiles are denied.
The installed Agent Browser proxy path may launch this browser even for `read`;
do not describe that path as browserless. Native authenticated profiles remain
an explicit host workflow. The wrapper's required CLI baseline belongs in its package contract;
transient machine install state belongs in live drift or doctor output, not this
document.

## Build candidates

Adoption rationale, research tracks, and the idea parking lot live in
[Pi design decisions](decisions.md); active time-boxed trials live
in [`experiments.md`](../../experiments.md). This page records only current
operational state.

## Launch modes and permission guardrails

| Command | Inference | Workbench outer boundary |
|---|---|---|
| `p` | Hosted | `cloud > managed`; selected ordinary checkout, `~/code/public`, `~/Desktop`, and `~/Downloads`, with exclusions |
| `co` | Hosted Codex | Same managed policy |
| `cc`, `ccr` | Hosted Claude | Same managed policy; `ccr` requests native plan mode |
| `pi`, `codex`, `claude` | Native vendor selection | No added Workbench boundary when started from the host |
| `pi --route private --provider omlx` | Local | Native Pi; no added Workbench boundary |

Full vendor commands retain shared configuration, skills, extensions, and soft
permission guards. They do not disable their vendor's own approval or sandbox
features. Native binaries launched by a managed parent inherit its outer policy;
a command name or environment change cannot escape it.

The shortcut authority is always `managed`. The old `--restricted`, `--daily`,
and `--unrestricted` flags fail with guidance to choose the shortcut or native
command. Reloading the launcher removes old functions including `pih`, `pihr`,
`pihu`, `pil`, `cou`, and `ccu`. Pi's native `-r` still resumes a session. Arguments
after `--` are forwarded literally. Local inference uses native Pi because the
managed policy does not admit the host inference service. The internal `frontier`
and `private` routes select providers; they do not grant operating-system access.
Managed Pi rejects explicit private/local route requests before model input;
it never silently converts that request into hosted inference. Pi's `dev` preset
selects tools, not authority. The isolated HOME maps `~/Desktop` and `~/Downloads`
to the real host scratch directories with the same private exclusions.

The managed harness derives instructions, skills, extensions, prompt templates,
themes, presets, and model preferences from the native configuration. Host code
assets are read-only; conversations and mutable settings use an isolated home
per repository. The selected provider login is shared across those isolated
homes. A valid `worker.timeoutMs` preference survives projection. Connector
credentials and host conversations are not imported. Installed plugin and
extension trees are trusted code assets, not sanitized file collections.
`workbench native status pi` reports paths and login metadata; after native
sign-in, `workbench native authorize pi --replace` backs up and replaces only
Pi's managed login. Presence does not prove authentication.

Machine-local exclusions, confidential directories, and real environment files
remain denied inside every admitted directory. The
[launch design catalogue](../launch-design.md) compares all layers; the
[security reference](../../security/isolation.md) owns exact access, accepted
risks, and dated verification evidence. The
[managed-surfaces reference](../../configuration.md) owns deployment paths.

Editor and Paseo callbacks may execute tools with their own host permissions.
The terminal boundary does not contain those callbacks or desktop agents.
Prepare the runtime, sync, reload the shell, and start a fresh process after
configuration changes; existing processes retain launch-time permissions.
Resuming a conversation carries its old content, so confidential local history
must not move to hosted inference without the owner's release.

### What the guards prove

The operating-system policy enforces the managed boundary. Pi's permission
extension and Git guard provide readable denials and approval prompts, but do
not isolate arbitrary native code. Positive controls must show that a program
started before a failed operation counts as a denial. Synthetic tests verify
specific routes, not every kernel exploit, terminal callback, or future feature.

Admitted files and provider logins remain readable to the agent; public network
access permits disclosure. Live edits may affect later host execution. The
boundary shares the Mac kernel and is not VM-equivalent isolation. Local
inference does not imply network or filesystem isolation. Terminal clipboard
callbacks need separate host-terminal configuration. Ghostty is configured to
deny programmatic reads and allow writes without prompts; existing windows require
**Command+Shift+Comma** to reload. Terminal programs can replace clipboard contents,
an owner-accepted tradeoff. Manual paste remains user-controlled.
Pre-existing admitted hardlinks can expose excluded bytes under another name;
keep private aliases outside admitted paths.

Architectural choices and candidate replacements belong in
[Pi design decisions](decisions.md).

## Notes

- Context size is provider-specific. The earlier Pi 0.84.3 snapshot advertised GPT-5.6 Sol as 272K through the `openai-codex` subscription route and 1.1M through OpenRouter; those are historical observations, not current limits. The footer uses the active provider's model metadata.
- The extension API does not expose the auto-compaction toggle, but completed compactions appear as session entries and are counted in the footer. Codex subscription windows come from the authenticated local Codex app-server; no credentials or conversation content are read. Pi still has no direct thinking-level getter, so the footer reads `thinking_level_change` session entries.
- Footer convention: keep every data point the default footer had; additions must earn their width.
