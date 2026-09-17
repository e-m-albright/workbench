# Pi agent - capability overview and build candidates

Snapshot of what the Pi harness can do and the candidate enhancements under review. [`pi-build-philosophy.md`](pi-build-philosophy.md) owns adoption and rejection rationale; this page owns current operational state. Captured 2026-07-21 and updated as the managed harness changes.

## What pi exposes (official, today)

- **TUI** (the daily driver): custom footer (`ctx.ui.setFooter`), extension statuses (`setStatus`), widgets above/below the editor, full editor replacement, overlays/dialogs, custom commands, keybindings.
- **Extension events:** session lifecycle, `turn_start/end`, `agent_start/end/settled`, `tool_execution_end`, `after_provider_response` (headers accessible - our quota parsing uses this), `user_bash`, model/thinking changes.
- **Non-TUI modes:** `print`, `json`, and **RPC** - a headless pi driven by another process. RPC is the hook any web UI or external dashboard would use.
- **Our current extensions** (`agents/pi/extensions/`): activity title and deterministic session naming, verified local clipboard copy, structured workspace file operations, confirmed ingress discard, branded welcome, custom footer, consult, permission policy, the `dev` preset, explicit local/frontier routing, one worktree-isolated worker, confirmed GitHub workflow dispatch, and read-only Google and Strava connectors. The pinned package wraps the existing Agent Browser CLI. Apple Notes is intentionally outside the coding-agent boundary.

## Delta over vanilla Pi

Everything the managed harness adds to a stock `pi` install, in one place:

These host extensions are available in explicitly unrestricted workflows.
Restricted `pi` deliberately does not load them; see the launch matrix below.

| Addition | Kind | What it provides |
|---|---|---|
| Workbench deploy + drift | Infrastructure | One public source of truth for settings, providers, presets, policy, extensions, and shared skills; `workbench sync pi` / `workbench drift pi` |
| Custom footer (`footer.ts`) | Extension | Git state refreshed every 15 seconds and after tools or user shell commands; model, thinking, context %, tokens, cost, tok/s, compaction count, Codex subscription quota windows |
| Activity title (`activity-title.ts`) | Extension | Local working row with elapsed time, terminal-tab spinner, repository, deterministic first-prompt session name, active tool, and immediate `/rename` during active work |
| Welcome mark (`welcome.ts`) | Extension | Branded confirmation that managed configuration loaded, including the authoritative installed Pi version |
| Permission policy (`permission-policy.ts` + JSON) | Guardrail | Deny rules for risky shell effects, machine-local private paths, remote-MCP default-deny, unrestricted harness edits, and actionable safe alternatives on rejection |
| Workspace files (`workspace-files.ts`) | Tool | Workspace-bounded rename, copy, and directory creation without shell mutation; no deletion or overwrite |
| Ingress discard (`ingress.ts`) | Tool | Confirmed move of one consumed `~/code/ingress` file to Trash; agent handoffs remain lifecycle-managed |
| Clipboard (`clipboard.ts`) | Tool | Copies approved plain text directly to the local macOS clipboard and verifies the exact value without temporary files or shell interpolation |
| Safe git (`safe-git.ts`) | Guardrail | Approval gates on destructive git and mutating `gh` |
| Presets (`presets.ts` + JSON) | Extension | One default `dev` tool and execution profile; model location and access scope belong to the launch mode rather than a preset |
| Pi launchers + native sandbox | Host guardrail | Cloud terminal sessions are restricted; local Pi is explicitly unrestricted, with no inference-service tunnel (see the mode table below) |
| Consult (`consult.ts`) | Extension | Hosted-only `/consult` second opinion via Claude, Codex, or Fable; local modes refuse this cloud subprocess |
| Worker (`worker.ts`) | Extension | Model-callable `worker` tool plus `/worker`: start one worktree-isolated child Pi in the background, show elapsed progress and completion status, review live or finished work, and discard after parent-owned adoption and verification |
| Google read-only (`google-readonly.ts`) | Extension | Owned Gmail/Calendar tools; loopback OAuth, read-only scopes, 0600 tokens |
| Strava read-only (`strava-readonly.ts`) | Extension | Owned activity/stats tools; loopback OAuth, `activity:read_all`, 0600 tokens |
| Apple Contacts (`apple-contacts` CLI, owned by a machine-local private layer) | Shared CLI | Fixed-field search/read/create/update through macOS Contacts; writes require `--confirm-write`, preserve notes outside a bounded managed block, and never delete; private projection policy stays with its private owner |
| `pi-agent-browser-native` 0.2.71 | Pinned package | Structured Agent Browser wrapper plus Exa-backed public web search |
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

The model-callable `worker` tool is the Pi harness's answer to one independent parallel implementation thread. It creates a separate Git worktree, starts one child Pi in the background, and returns control to the parent after setup. A lightweight footer status reports elapsed time without polling or extra model calls; completion produces one notification. `worker review` or `/worker-status` reads the live diff or finished report on demand. The child cannot commit, push, install dependencies, or merge, and adoption remains with the parent. In the `dev` preset the model may delegate without user approval, continue disjoint parent work, review and adopt useful changes, verify them in the parent checkout, and discard the worktree. `/worker <task>`, `/worker-status`, and `/worker-done` remain manual controls.

This does not provide workflow fleets, background schedules, or autonomous merging. A worker must start from committed state and must not receive a task that depends on uncommitted parent files. `/consult` covers read-only independent judgment, while Claude Code remains the explicit route for exceptional coordinated finder/verifier fleets.

## Connector access

Gmail and Google Calendar use the Workbench-owned `google-readonly.ts` extension: direct REST calls to `googleapis.com`, loopback OAuth with PKCE, and read-only scopes. Their provider and access requirements are enforced by Pi's connector policy; unrestricted filesystem access is not a blanket connector grant. Source content enters the selected model's context, so confidential-source work must follow its owner's release policy.

OAuth client configuration and refresh tokens remain machine-local, with 0600 files inside 0700 directories. `/google-auth` creates an explicitly approved grant; `/google-status` reports state. The tool policy protects raw credentials. A connector in the same process must still read its own tokens, so these rules do not isolate trusted extensions from arbitrary code in that process. Apple Notes remains unavailable. Connector content is untrusted evidence, never instructions.

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

Workbench pins `pi-agent-browser-native` 0.2.71 around the existing Agent Browser
CLI. It adds structured tool results, bounded context spills, secret redaction,
stale-reference guards, session recovery, artifact metadata, and the
`agent_browser_web_search` companion backed by a machine-local Exa credential.
Use search to discover public sources, `agent_browser read <url>` to read a known
source without launching Chrome, and a full browser only for rendered state,
JavaScript-only content, authentication, interaction, screenshots, or diagnostics.
Authenticated browser profiles remain opt-in, and temporary sessions stay the
safe baseline. The wrapper's required CLI baseline belongs in its package contract;
transient machine install state belongs in live drift or doctor output, not this
document.

## Build candidates

Adoption rationale, research tracks, and the idea parking lot live in
[`pi-build-philosophy.md`](pi-build-philosophy.md); active time-boxed trials live
in [`experiments.md`](experiments.md). This page records only current
operational state.

## Launch modes and permission guardrails

| Command | Inference | Workbench access |
|---|---|---|
| `pi`, `pih`, `pihr` | Hosted | Native restricted terminal |
| `pihu` | Hosted | Unrestricted host, with interactive confirmation |
| `pil`, `pilu` | Local | Unrestricted host, with interactive confirmation |
| `pilr` | None | Refuses; restricted local mode is retired |
| `cc`, `ccr` | Claude Code's selected provider | Native restricted terminal |
| `ccu` | Claude Code's selected provider | Unrestricted host, with interactive confirmation |
| `co` | Codex's selected provider | Native restricted terminal |
| `cou` | Codex's selected provider | Unrestricted host, with interactive confirmation |

Restricted Pi is intentionally plain Pi: no host extensions, skills, prompt
templates, themes, connector tools, or host settings are loaded. The managed
extension features described elsewhere on this page belong to host workflows,
not the default restricted `pi` command. Its selected provider login persists
across repositories while conversation storage remains per repository.

The installed native launcher wraps the entire process and its children in a
default-deny macOS policy. It admits the selected ordinary Git checkout, necessary
tools, isolated state, and the selected provider's login paths. Machine-local
private exclusions and environment files remain denied even inside that
checkout. Existing vault exclusions are not lifted. Linked worktrees are
unsupported. The [security reference](restricted-agents.md) owns the exact
permissions, authentication risks, accepted limits, and verification procedure.

Hosted and local inference are not equivalent authority choices. Local Pi is
explicitly unrestricted because exposing the whole local inference service to a
restricted agent would weaken the boundary. Its normal oMLX service and other
consumers are unchanged. The internal `frontier` and `private` routes select
providers for host Pi; they do not grant operating-system permissions. Host
Pi's `dev` preset selects tools, not authority.

The `cc` and `co` launchers accept `--restricted` and `--unrestricted`; Pi
uses the aliases above. Interactive unrestricted selection asks for confirmation.
An explicitly configured unrestricted remote provider can launch without that
interactive confirmation, but remains a host-authority workflow. Unrestricted
does not remove an operating-system sandbox inherited from a parent process or
disable native vendor approvals.

Direct vendor binaries, desktop agents, Zed built-ins/external agents, and Paseo
providers are not covered by this terminal boundary. A daemon or editor can
execute tool requests outside the agent process's sandbox. Neither an alias nor
a sandbox around one provider process contains those host callbacks. Restricted
Codex app-server and browser-integration routes are unsupported; the former
app-server helper and permissive static profiles are retired.

Use the [managed-surfaces reference](managed-surfaces.md) for deployment paths.
Prepare the native runtime, sync launchers, reload the shell, and start a fresh
process. Running processes keep their launch-time permissions and extensions.
Resuming a conversation also carries its old content: do not move confidential
local history to hosted inference without the owner's release.

### What the guards prove

The operating-system policy, not Pi's extension policy, enforces the restricted
terminal boundary. Positive controls must prove a program started before a
failed operation counts as a denial. Synthetic tests and interactive startup
probes verify specific blocked routes; they are not proof against every kernel
exploit, terminal callback, or future vendor feature.

Host Pi's permission-policy extension adds readable denials for credential
requests, connector access, browser operations, and shell effects. Its local
personal connectors require local unrestricted access; hosted unrestricted
access does not automatically grant cloud personal connector calls. These
tool-level checks are useful guidance, not isolation from arbitrary code in an
unrestricted process.

### Deliberate limits

- Admitted repository data, including Git history and ignored files, can leave through the permitted public network.
- Provider login files are deliberately readable by the selected restricted agent; existing provider account scopes may exceed inference access.
- Live repository edits can affect later host execution; there is no separate clone or required installation ceremony.
- Native containment shares the Mac kernel and is not VM-equivalent isolation or a confidentiality-compliance guarantee.
- Local inference does not imply network isolation; unrestricted extensions, browsers, credentials, and services retain host authority.
- Terminal clipboard callbacks are host actions and need separate terminal configuration; manual paste remains user-controlled.

Architectural choices and candidate replacements belong in
[`pi-build-philosophy.md`](pi-build-philosophy.md).

## Notes

- Context size is provider-specific. Pi (verified on 0.84.3) currently advertises GPT-5.6 Sol as 272K through the `openai-codex` subscription route and 1.1M through OpenRouter. The footer uses the active provider's model metadata; it must not relabel the subscription route as 1.1M without endpoint evidence.
- The extension API does not expose the auto-compaction toggle, but completed compactions appear as session entries and are counted in the footer. Codex subscription windows come from the authenticated local Codex app-server; no credentials or conversation content are read. Pi still has no direct thinking-level getter, so the footer reads `thinking_level_change` session entries.
- Footer convention: keep every data point the default footer had; additions must earn their width.
