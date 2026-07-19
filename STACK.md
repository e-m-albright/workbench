# The Capability Stack

The canonical description of how my repositories compose. Each layer stands
alone, and each higher layer assumes the ones beneath it are installed and
documented. Integration happens through CLI and process contracts, never
through cross-repository Python imports.

```text
dotfiles   host foundation and machine capabilities
    ↓
workbench  reusable agent intelligence and engineering standards
    ↓
notes      private knowledge and operating layer
```

## Layers

### 1. [`dotfiles`](https://github.com/e-m-albright/dotfiles) — host foundation

Turns a fresh Mac into the working host: packages, shell, terminal, editors,
Git, macOS preferences, privacy utilities, local models, and remote session
control. Owns the `dotfiles` Typer CLI and Mission Control TUI. It installs
Workbench and delegates agent configuration to it.

### 2. `workbench` (this repository) — agent intelligence and standards

Owns portable coding-agent behavior (rules, skills, specialist agents, MCP and
plugin declarations, safety hooks) and reusable engineering doctrine (playbook,
health kit, review rubrics). `workbench sync` deploys canonical sources into
each vendor's native configuration; `workbench drift` verifies the live result.
Workbench assumes a host provisioned by Dotfiles but runs from a standalone
checkout as well.

### 3. `notes` — private knowledge and operations

A private knowledge-and-operations layer sits above these public repositories.
It applies the host foundation and reusable agent conventions to personal
workflows and information. Its data, integrations, and operating details are
intentionally not published; neither public repository requires it.

## Ownership

| Concern | Owner |
| --- | --- |
| Fresh-Mac setup, packages, shell, terminal, editors, macOS configuration, remote access | `dotfiles` |
| Agent rules, skills, prompts, subagents, MCP/plugin declarations, hooks, permissions | `workbench` |
| Engineering doctrine, stack guidance, review rubrics, portable health tooling | `workbench` |
| Project architecture, domain rules, tests, project-specific policy | The individual project |
| Private knowledge, personal automation instances, generated operational state | Private `notes` |
| OAuth grants, credentials, vendor-generated memory | Live vendor state, never Git |

## Integration contract

- **Composition, not imports.** Repositories integrate by invoking each other's
  documented CLIs (`dotfiles doctor`, `workbench sync all`,
  `workbench drift all`), never by importing each other's Python packages.
  Imports would couple releases, weaken standalone use, and make the private
  boundary harder to defend.
- **Provisioning order.** Dotfiles installs Workbench and requires
  `workbench drift all` to pass. The private layer consumes both public layers
  through the same stable CLI contracts.
- **Standalone operation.** Every layer must remain useful from its own
  checkout with its own documented verification.

## Shared vocabulary and CLI conventions

- Typer owns user-facing commands; `just` owns development recipes.
- Common verbs, used only where semantically accurate: `doctor` (live host
  health), `check` (repository validation), `drift` (live vs. desired state),
  `sync` (deploy desired state), `status`, `open`.
- Each repository exposes `just check` and `just audit` (where applicable) with
  the same meanings.
- Live desired-state comparison only — no stored machine snapshots that go
  stale.
- Output stays readable without a TTY or ANSI support.

## Security and privacy boundary

Dotfiles and Workbench are public and must never contain credentials, personal
records, conversations, generated agent memory, or private operational state.
The private layer's domains, providers, schedules, integrations, schemas,
locations, and identities are not described in the public repositories beyond
the summary above. Public CI never has access to the private repository.

## Reuse

Both public repositories are personal and opinionated — fork-and-adapt
material, not frameworks. Take the structure, conventions, and scripts that fit
your workflow; nothing here is designed to be depended on as a package.
