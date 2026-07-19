# Workbench

The portable intelligence and engineering-guidance layer for my development
environment.

Workbench is where I version the behavior I want Claude Code and Codex to share:
agent rules, skills, specialist agents, prompts, MCP declarations, safety policy,
engineering doctrine, and reusable project-health tools. It turns those canonical
sources into each vendor's native configuration and verifies the live result.

This is a personal, opinionated repository. It optimizes one workflow rather
than trying to become a general agent platform.

## Position in the Stack

Workbench is the middle layer of a three-repository capability stack, described
canonically in [`STACK.md`](STACK.md):

```text
dotfiles   host foundation and machine capabilities
    ↓
workbench  reusable agent intelligence and engineering standards
    ↓
notes      private knowledge and operating layer
```

[`dotfiles`](https://github.com/e-m-albright/dotfiles) provisions the host and
installs Workbench; a private knowledge-and-operations layer applies both public
layers to personal workflows through their CLI contracts. Each layer stands
alone — integration is composition and provisioning order, never
cross-repository Python imports.

## What It Does

Workbench gives me one place to answer four questions:

1. **How should my coding agents behave?** Shared rules, safety boundaries,
   reusable skills, and specialist-agent instructions live under `agents/`.
2. **How do those instructions reach each vendor?** `workbench sync` translates
   and deploys the canonical sources into Claude Code and Codex configuration.
3. **Has live configuration drifted?** `workbench drift` compares the deployed
   files and installed plugins directly with the repository.
4. **What engineering judgment should carry between projects?** The playbook,
   health kit, and review prompts preserve reusable decisions without coupling
   them to a particular codebase.

```text
                    canonical sources
              agents/   playbook/   health/
                           │
                  workbench sync all
                           │
              ┌────────────┴────────────┐
              │                         │
         Claude Code                 Codex
     rules, settings, hooks     rules, TOML, hooks
     skills, agents, plugins    skills, agents, plugins
              │                         │
              └────────────┬────────────┘
                           │
                 workbench drift all
                    live drift report
```

The repository is both the source material and the deployment contract. It does
not store a snapshot of the machine and compare against that stale observation.

## Ownership Boundaries

| Concern | Owner |
| --- | --- |
| Agent rules, skills, prompts, subagents, MCP declarations, hooks, and permissions | **Workbench** |
| Engineering doctrine, stack guidance, review rubrics, and portable health tooling | **Workbench** |
| Fresh-Mac setup, packages, shell, Git, terminal, editor, and macOS configuration | [`dotfiles`](https://github.com/e-m-albright/dotfiles) |
| Project architecture, domain rules, tests, and project-specific infrastructure policy | The individual project |
| Private notes, CRM data, conversations, personal automation instances, and generated operational state | Private `notes` repository |
| OAuth grants, account sessions, credentials, and vendor-generated memory | Live vendor state, never Git |

Dotfiles installs Workbench and links `workbench` plus its short alias `wb` into
`~/.local/bin`; Workbench then configures the supported agents. Individual
projects remain authoritative for their own `AGENTS.md`, architecture, domain
vocabulary, and safety policy.

## Capabilities

### Agent configuration

- One shared instruction file for Claude Code and Codex, with a small Codex
  appendix where the vendors genuinely differ.
- Reusable skills installed into both vendors.
- Shared Markdown specialist agents translated into native Codex TOML agents.
- Vendor-native hooks, permission rules, sandbox defaults, and status lines.
- Declarative plugin installation for both vendors.
- A shared MCP registry that preserves intentional external additions and
  removes explicitly retired integrations.

### Engineering guidance

- `playbook/` records durable engineering principles, stack preferences, and
  researched technology guidance.
- `health/` provides deterministic project checks, adoption contracts, and
  advisory review rubrics.
- `agents/prompts/` contains reusable prompts that do not warrant an always-on
  skill.
- `docs/decisions/tombstones.md` prevents rejected tools and approaches from
  being casually rediscovered and reintroduced.

## Install

On a fresh Mac, the normal entry point is the dotfiles installer:

```bash
mkdir -p ~/code/public
git clone https://github.com/e-m-albright/dotfiles.git ~/code/public/dotfiles
~/code/public/dotfiles/install.sh
```

Dotfiles clones this repository, installs the `workbench` and `wb` launchers in
`~/.local/bin`, runs `workbench sync all`, and requires `workbench drift all` to
pass.

For a standalone checkout:

```bash
git clone https://github.com/e-m-albright/workbench.git ~/code/public/workbench
cd ~/code/public/workbench
./bin/workbench --help
just check
```

Requirements are deliberately small: [uv](https://docs.astral.sh/uv/) (which
provisions Python 3.13+ and the Typer/Rich CLI environment on first run), Bash,
and the installed Claude/Codex CLIs. Skill deployment also uses `npx skills`.

## Daily Workflows

### Reconcile everything

```bash
workbench sync all
workbench drift all
```

`sync` preserves unmanaged vendor settings, writes only Workbench-owned values,
and keeps one `.bak` file before replacing live configuration. By default it
also reconciles skills and declared plugins.

Use narrower targets while developing or diagnosing one integration:

```bash
workbench sync claude
workbench drift claude

workbench sync codex
workbench drift codex
```

Skip the slower external installers when only configuration files need repair:

```bash
workbench sync all --no-skills --no-plugins
```

### Validate repository sources

```bash
just check       # format, lint, types, tests, and source validation
just test        # deterministic unit tests only
just lint        # skills, links, JSON, TOML, and shell syntax
```

### Understand an unexpected live item

```bash
workbench drift all
```

`DRIFT` (managed value missing or different, non-zero exit) is distinguished
from `EXTERNAL` (valid unmanaged addition, reported but passing). Details in
[`docs/managed-surfaces.md`](docs/managed-surfaces.md).

## Command Tree

Run `workbench`, `wb`, or either launcher's `--help` flag for the complete tree:

```text
workbench
├── sync [claude|codex|all]    deploy canonical configuration
│   ├── --no-skills            skip shared-skill installation
│   └── --no-plugins           skip declared-plugin installation
├── drift [claude|codex|all]   report managed drift and external additions
└── lint                       validate canonical repository sources
```

Run `just` for the repository-development command list. The CLI manages live
agent configuration; Just recipes develop and validate this repository.

## What `sync` Manages

`sync` deploys global instructions, vendor configuration, command policy,
hooks, specialist agents, skills, plugins, and MCP servers into Claude Code and
Codex. The per-vendor file map and drift semantics live in
[`docs/managed-surfaces.md`](docs/managed-surfaces.md).

## Repository Tour

```text
agents/
├── shared/              cross-vendor rules, hooks, and MCP registry
├── claude/              Claude settings fragments and plugin declarations
├── codex/               Codex rules, hooks, status line, and plugins
├── skills/              reusable on-demand workflows
├── subagents/           shared specialist-agent source documents
└── prompts/             reusable prompts below the skill threshold

playbook/                engineering doctrine, stack guidance, and research
health/                  portable deterministic checks and review rubrics
docs/decisions/          durable architectural decisions and tombstones
src/workbench/           Typer + Rich deployment and verification CLI
pyproject.toml           uv-managed project (Typer, Rich; pytest/Ruff/Pyright dev gate)
tests/                   deterministic CLI, sync, drift, and guard-hook tests
bin/workbench            relocatable shell launcher (execs via uv)
```

## Extending Workbench

Choose the smallest durable surface that fits the need:

1. Update `agents/shared/rules.md` only for behavior that should always apply to
   both coding agents.
2. Add or revise a skill for a recurring workflow that should load on demand.
3. Add a prompt when reusable wording is useful but executable workflow or
   automatic triggering is not.
4. Add an MCP or plugin declaration only when the integration has recurring
   value and a clear owner.
5. Put project-specific guidance in that project's `AGENTS.md`, not here.
6. Put private workflow instances and generated state in the private repository
   that owns their context.

After changing managed configuration:

```bash
just check
workbench sync all
workbench drift all
```

When removing a supported capability, record the reason where its off-switch
lives: the `RETIRED_*` mappings in `src/workbench/core.py`, `_*_disabled`
entries in the MCP registry, or `docs/decisions/tombstones.md` for decisions
with no code enforcement.

## Safety and Publishing Boundary

Workbench is public. It must never contain credentials, personal records,
conversations, generated memory, or private operational state.

Vendor sandboxes provide the filesystem boundary. Workbench adds concise
permission rules and PreToolUse hooks that deny sensitive-file edits, recursive
force-deletion, destructive Git operations, and disk erasure. Database and
infrastructure policy remains the responsibility of the project that owns those
resources.

For an independent read-only fact-check, use the
[`adversarial audit prompt`](docs/security/adversarial-audit-prompt.md).

Completion and approval notifications use each vendor's native notification
channel. Workbench installs no notification daemon or background service.

## Design Rules

1. Prefer declarative files and small scripts over a framework.
2. Add executable behavior only for an evidenced recurring workflow.
3. Keep deterministic checks separate from stochastic assessments.
4. Preserve unmanaged vendor configuration unless it violates an explicit
   retirement or safety rule.
5. Treat generated agent state as private and disposable.
6. Preserve rejected decisions as tombstones instead of repeatedly evaluating
   the same tools.

## Reuse

Workbench is fork-and-adapt material, not a framework or a package to depend
on. If you want something similar, take the shapes that fit your workflow — the
canonical-source-to-sync/drift model, the skills layout, the health kit — and
replace the opinions with your own. See [`STACK.md`](STACK.md) for how it
composes with the neighboring repositories.
