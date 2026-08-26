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
private workflow layers
```

## Layers

### 1. [`dotfiles`](https://github.com/e-m-albright/dotfiles) — host foundation

Turns a fresh Mac into the working host: packages, shell, terminal, editors,
Git, macOS preferences, privacy utilities, and Tailscale-direct Paseo access. Owns the `dotfiles` Typer CLI. It installs Workbench and delegates agent configuration to it.

### 2. `workbench` (this repository) — agent intelligence and standards

Owns portable coding-agent behavior (rules, skills, MCP and plugin declarations,
safety hooks) and reusable engineering doctrine (playbook, health kit, review
skills). `workbench sync` deploys canonical sources into
each vendor's native configuration; `workbench drift` verifies the live result.
Workbench assumes a host provisioned by Dotfiles but runs from a standalone
checkout as well.

### 3. Private workflow layers

Private layers may sit above these public repositories. They apply the host
foundation and reusable agent conventions to personal workflows and
information. Their names, data, integrations, and operating details are
intentionally not published; neither public repository requires them.

## Ownership

| Concern | Owner |
| --- | --- |
| Fresh-Mac setup, packages, shell, terminal, editors, macOS configuration, remote access | `dotfiles` |
| Agent rules, skills, prompts, MCP/plugin declarations, hooks, permissions | `workbench` |
| Engineering doctrine, stack guidance, review skills, portable health tooling | `workbench` |
| Project architecture, domain rules, tests, project-specific policy | The individual project |
| Private knowledge, personal automation instances, generated operational state | Their private owning layer |
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
  the same meanings; `just typecheck` is the shared name for the type gate.
- Cross-layer contract: `dotfiles doctor` runs `workbench drift all` and treats
  exit 0 as clean and exit 1 as drift, reading the first non-empty output line
  as the drift detail. Change that verb or its exit semantics in both repos
  together.
- Live desired-state comparison only — no stored machine snapshots that go
  stale.
- Output stays readable without a TTY or ANSI support.

## Security and privacy boundary

Dotfiles and Workbench are public and must never contain credentials, personal
records, conversations, generated agent memory, or private operational state.
A private layer's name, domains, providers, schedules, integrations, schemas,
locations, and identities are not described in the public repositories. Public
agent rules may point to an optional machine-local private context file without
publishing its contents. Public CI never has access to a private repository.

## Reuse

Both public repositories are personal and opinionated — fork-and-adapt
material, not frameworks. Take the structure, conventions, and scripts that fit
your workflow; nothing here is designed to be depended on as a package.
