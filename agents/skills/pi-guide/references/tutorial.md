# Pi tutorial

Snapshot: Pi 1.4.0, with Workbench configuration reviewed on 2026-10-24.
Earlier version-specific observations remain dated
in the capability reference rather than serving as current guarantees.

Native references live in the installed `@earendil-works/pi-coding-agent` package
under `README.md` and `docs/`. Workbench decisions live in
[Pi build philosophy](https://github.com/e-m-albright/workbench/blob/main/docs/agents/pi/decisions.md) and the current
[capability inventory](https://github.com/e-m-albright/workbench/blob/main/docs/agents/pi/README.md).

## Daily workflow

1. Start `p` inside an ordinary repository checkout for the managed boundary, or
   native `pi` from the host for workflows that need host access. Pi discovers
   project instructions and asks for trust before loading project-local resources.
2. State the goal and constraints. For consequential work, agree on scope before
   implementation.
3. Let Pi use `read`, `bash`, precise `edit`, and `write`. Expand collapsed tool
   output with Ctrl+O when evidence is missing.
4. Queue a follow-up during generation with Alt+Enter. Restore queued text with
   Alt+Up.
5. Cycle thinking with Shift+Tab. Select a model with Ctrl+L. Do not confuse
   thinking effort with provider Fast mode.
6. Name an important thread with `/name <name>`. Workbench automatically gives
   unnamed sessions a compact first-prompt name.
7. Verify through the repository's own task runner before accepting a change.
8. Use `/session` to inspect context and `/compact` when old detail is crowding the
   active task.

## Essential keys

| Key | Native action |
|---|---|
| Escape | Interrupt the active agent operation or cancel a picker |
| Ctrl+C | Clear the editor; press twice to quit |
| Ctrl+D | Exit when the editor is empty |
| Ctrl+G | Open the prompt in the configured external editor |
| Shift+Enter or Ctrl+J | Insert a newline |
| Alt+Enter | Queue a follow-up while the agent works |
| Alt+Up | Restore queued messages to the editor |
| Ctrl+O | Expand or collapse tool output |
| Ctrl+X | Copy the last assistant message |
| Ctrl+L | Open the model selector |
| Shift+Tab | Cycle thinking level |
| Ctrl+T | Expand or collapse thinking blocks |
| Ctrl+V | Paste an image from the clipboard on macOS |
| Ctrl+Z, then `fg` | Suspend Pi and return to it on Unix terminals |

Editor movement follows familiar shell bindings: Ctrl+A/End, Ctrl+E, Ctrl+B,
Ctrl+F, Ctrl+W, Ctrl+U, Ctrl+K, Ctrl+Y, and Alt+Y. Custom bindings live in
`~/.pi/agent/keybindings.json`; `/reload` applies changes.

Managed settings use fullscreen mode. Pi owns the viewport, Ctrl+Shift+F searches the transcript, and Ctrl+Shift+Up/Down jump between user-prompt markers. Fullscreen intentionally renders the same transcript, so short sessions look almost identical to regular mode. On macOS, prefer Ctrl+Shift+Up/Down if a window manager captures Ctrl+Up/Down. Fn+Up/Down only pages, and `/tree` is a branch navigator rather than a full-prompt reader. Fullscreen does not provide final-answer landmarks or compact work summaries; the former custom reader was retired because those additions did not earn their code surface.

## Session commands

| Command | Effect |
|---|---|
| `/resume` | Select an existing project session |
| `/new` | Start a new session |
| `/name <name>` | Set a durable display name |
| `/session` | Show session path, ID, messages, tokens, and cost |
| `/tree` | Browse the current session tree |
| `/fork` | Start a new session from a prior user message |
| `/clone` | Copy the current active branch into a new session |
| `/compact [prompt]` | Summarize older context into a compaction entry |
| `/export [file]` | Export the session as HTML |
| `/share` | Upload a private GitHub gist; this is external state |

In `/tree`, Up/Down previews entries and Escape exits without changing the branch.
Enter selects the entry and changes the active leaf. Selecting a user message puts
its text into the editor for a new branch. Use `/tree` for related alternatives,
`/fork` for a separate thread from history, and `/clone` before independently
continuing the current branch.

Resume picker keys: Ctrl+P toggles paths, Ctrl+S changes sorting, Ctrl+N filters to
named sessions, Ctrl+R renames, and Ctrl+D deletes after confirmation.

## Native capability map

### Tools

Pi's stock coding loop is intentionally small: read files, run shell commands,
apply exact edits, and write complete files. Prefer precise Edit because it fails
when the expected old text no longer matches. Read before editing and run the
project's verification command afterward.

### Skills

Skills are on-demand workflows. Pi reads names and descriptions at startup, then
loads the full `SKILL.md` only when relevant. Force a skill with
`/skill:<name> [arguments]`. Skills can contain executable code and instructions,
so review third-party skills before use.

### Prompt templates

Markdown files under `~/.pi/agent/prompts/` become `/name` expansions. Templates
are best for short repeatable prompts; skills are better for multi-step workflows,
references, and scripts.

### Packages

Packages can bundle extensions, skills, prompts, and themes. They execute with the
agent process's permissions, including any inherited operating-system sandbox. Prefer pinned npm versions such as
`npm:package@1.2.3`; unversioned packages expand supply-chain drift. Use a temporary
`pi -e npm:package` trial before permanent installation when practical.

### Models and thinking

Ctrl+L selects a model; Shift+Tab changes reasoning effort. The active provider
route controls context size, authentication, cost, and available service tiers.
The same model name through two providers can have different limits.
Personal hosted sessions default to `openai-codex/gpt-6.1-sol` with medium thinking;
the work profile leaves provider and model selection to the host's policy.

### Project trust

Project-local instructions, extensions, skills, settings, and packages can execute
or steer work. Trust only repositories whose contents are safe to load. Workbench's
managed shortcut `p` contains Pi and its children within the admitted checkout,
public code, Desktop, and Downloads, with private exclusions. Native `pi` adds no
Workbench outer boundary when started from the host. Project trust does not expand
an inherited operating-system boundary.

## Workbench custom setup

| Addition | Purpose |
|---|---|
| Activity title | Spinner, Git-root project, deterministic thread label, active tool |
| Welcome mark | Visible confirmation that managed Pi configuration loaded, plus the authoritative installed Pi version |
| Footer | Git state, model, thinking, context, tokens, cost, speed, compaction, quota |
| Permission policy | Blocks protected paths, risky shell effects, and non-allowlisted MCP calls |
| Safe Git | Adds approval gates around destructive history operations |
| Upstream subagent | Loads Pi's installed subagent example. The implementer inherits the parent's model; the parent prepares worktrees for parallel editing and reviews adoption. |
| Strava read-only | Owned activity tools (`/strava-auth`, `/strava-status`); free personal API |
| Native Agent Browser | Structured wrapper around the trusted Agent Browser CLI |

Managed `p` and native `pi` share deployed extensions. Native local inference uses
`pi --route private --provider omlx` from the host. The Google connector is
retired; Gmail, Calendar, and Drive remain outside the coding-agent boundary.
Strava tools require the local provider and their own OAuth grant. The global
handoff queue also sits outside the managed grants; return continuation text in
the conversation and save it from an authorized native session.

Ask for a bounded task to be delegated to `implementer`. For parallel editing,
prepare a separate worktree within the launcher's admitted roots and pass its path
as `cwd`. The upstream call waits for completion rather than returning a background
job. Review the diff, verify adoption, and clean up only after preserving useful
work. Sequential editing can use the current checkout when no other writer is
active. The implementer is instructed not to delegate, commit, push, install, or
merge. Native `defaultTools` adds grep, find, and ls; there is no preset framework
or consult command.

Terminal titles use the first user prompt unless `/name` supplies an explicit
name. There is no separate completion notification daemon or Fast-mode label.

## Build philosophy

The setup values transparency, small trusted surfaces, provider portability, and
measured local value over feature parity. It does not attempt to recreate Codex,
Claude Code, Oh My Pi, or a graphical control deck.

Currently absent on purpose:

- Fast-mode controls whose provider state cannot be observed reliably
- a separate completion notification daemon without observed missed completions
- visible request-ledger ceremony
- a custom transcript reader beyond native fullscreen
- a broad Pi Web UI or public network listener
- a permanent subagent roster or uncontrolled concurrent writers
- wholesale replacement of native read/edit/search tools with hashline machinery
- LSP, AST, and semantic indexing before repeated work identifies a concrete bottleneck
- broad Web Access provider and extraction fallbacks before a recurring gap

Research candidates have explicit evidence thresholds and removal paths in
[Pi build philosophy](https://github.com/e-m-albright/workbench/blob/main/docs/agents/pi/decisions.md). The right response to an interesting community
feature is: name the local problem, test the smallest version, and keep it only if
it reduces errors, latency, context, or manual rework.
