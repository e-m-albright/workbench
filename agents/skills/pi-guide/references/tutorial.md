# Pi tutorial

Snapshot: Pi 0.81.1, reviewed 2026-07-21.

Native references live in the installed `@earendil-works/pi-coding-agent` package
under `README.md` and `docs/`. Workbench decisions live in
`docs/pi-build-philosophy.md` and the current inventory in
`docs/pi-capabilities.md`.

## Daily workflow

1. Start `pi` inside the repository you intend to change. Pi discovers project
   instructions and asks for trust before loading project-local resources.
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
| Ctrl+C | Copy selection, or clear the editor when there is no selection |
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

Ghostty's Command-Up/Down prompt-zone navigation is terminal behavior, not a Pi
keybinding. Pi emits OSC 133 zones, but semantic jumping remains unverified in the
current setup. Do not claim it works until the controlled test passes.

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
user's full permissions. Prefer pinned npm versions such as
`npm:package@1.2.3`; unversioned packages expand supply-chain drift. Use a temporary
`pi -e npm:package` trial before permanent installation when practical.

### Models and thinking

Ctrl+L selects a model; Shift+Tab changes reasoning effort. The active provider
route controls context size, authentication, cost, and available service tiers.
The same model name through two providers can have different limits.

### Project trust

Project-local instructions, extensions, skills, settings, and packages can execute
or steer work. Trust only repositories whose contents are safe to load. Use Codex
or Claude Code's stronger containment for high-autonomy work against untrusted
content.

## Workbench custom setup

| Addition | Purpose |
|---|---|
| Activity title | Spinner, Git-root project, deterministic thread label, active tool |
| Welcome mark | Visible confirmation that managed Pi configuration loaded |
| Footer | Git state, model, thinking, context, tokens, cost, speed, compaction, quota |
| Permission policy | Blocks protected paths, risky shell effects, and non-allowlisted MCP calls |
| Safe Git | Adds approval gates around destructive history operations |
| Presets | Switches coherent model/tool/behavior profiles |
| Consult | Explicit independent second opinion |
| Discovery telemetry | Temporary local measurement of navigation and verification friction |
| MCP adapter | Token-efficient remote-tool discovery; OAuth remains explicit and constrained |
| Native Agent Browser | Structured wrapper around the trusted Agent Browser CLI |

Terminal titles use the first user prompt unless `/name` supplies an explicit
name. There are intentionally no completion notifications and no Fast-mode label.

## Build philosophy

The setup values transparency, small trusted surfaces, provider portability, and
measured local value over feature parity. It does not attempt to recreate Codex,
Claude Code, Oh My Pi, or a graphical control deck.

Currently absent on purpose:

- Fast-mode controls whose provider state cannot be observed reliably
- completion notifications without observed missed completions
- visible request-ledger ceremony
- a private transcript viewport implementation
- a broad Pi Web UI or public network listener
- a permanent subagent roster or concurrent writers
- wholesale replacement of native read/edit/search tools with hashline machinery
- LSP, AST, and semantic indexing before telemetry identifies the bottleneck
- broad Web Access provider and extraction fallbacks before a recurring gap

Research candidates have explicit evidence thresholds and removal paths in
`docs/pi-build-philosophy.md`. The right response to an interesting community
feature is: name the local problem, test the smallest version, and keep it only if
it reduces errors, latency, context, or manual rework.
