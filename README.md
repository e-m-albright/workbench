# <img src="assets/brand/icon.svg" alt="" width="48" /> Workbench

The portable intelligence and engineering-guidance layer for my development
environment.

Workbench is where I version the behavior I want Pi, Claude Code, and Codex to
share: agent rules, skills, prompts, safety policy,
engineering doctrine, and reusable project-health tools. It turns those canonical
sources into each harness's native configuration and verifies the live result.

This is a personal, opinionated repository. It optimizes one workflow rather
than trying to become a general agent platform.

## Position in the Stack

Workbench is the agent-intelligence layer of the capability stack described
canonically in [`STACK.md`](STACK.md):

```text
dotfiles   host foundation and machine capabilities
    ↓
workbench  reusable agent intelligence and engineering standards
    ↓
private workflow layers
```

[`dotfiles`](https://github.com/e-m-albright/dotfiles) provisions the host and
installs Workbench; private workflow layers may apply both public layers through
their CLI contracts. Each layer stands alone - integration is composition and
provisioning order, never cross-repository Python imports.

## What It Does

Workbench gives me one place to answer four questions:

1. **How should my coding agents behave?** Shared rules, safety boundaries,
   reusable skills, and review guidance live under `agents/`.
2. **How do those instructions reach each harness?** `workbench sync` translates
   and deploys the canonical sources into Pi, Claude Code, and Codex configuration.
3. **Has live configuration drifted?** `workbench drift` compares the deployed
   files and installed plugins directly with the repository.
4. **What engineering judgment should carry between projects?** The playbook,
   health kit, and review skills preserve reusable decisions without coupling
   them to a particular codebase.

```text
                    canonical sources
              agents/   playbook/   health/
                           │
                  workbench sync all
                           │
          ┌───────────────┼───────────────┐
          │               │               │
         Pi          Claude Code         Codex
  rules, settings,   rules, settings,   rules, TOML,
  skills, extensions skills, plugins    skills, plugins
          │               │               │
          └───────────────┼───────────────┘
                          │
                workbench drift all
                    live drift report
```

The repository is both the source material and the deployment contract. It does
not store a snapshot of the machine and compare against that stale observation.

## Ownership Boundaries

| Concern | Owner |
| --- | --- |
| Agent rules, skills, prompts, MCP declarations, hooks, and permissions | **Workbench** |
| Engineering doctrine, stack guidance, review skills, and portable health tooling | **Workbench** |
| Fresh-Mac setup, packages, shell, Git, terminal, editor, and macOS configuration | [`dotfiles`](https://github.com/e-m-albright/dotfiles) |
| Project architecture, domain rules, tests, and project-specific infrastructure policy | The individual project |
| Private records, conversations, workflow instances, and generated operational state | Their private owning layer |
| OAuth grants, account sessions, credentials, and vendor-generated memory | Live vendor state, never Git |

Dotfiles installs Workbench and links `workbench` plus its short alias `wb` into
`~/.local/bin`; Workbench then configures the supported agents. Individual
projects remain authoritative for their own `AGENTS.md`, architecture, domain
vocabulary, and safety policy.

## Capabilities

### Agent configuration

- One shared instruction file for Pi, Claude Code, and Codex, with a small Codex
  appendix where the harnesses genuinely differ.
- Reusable skills installed for all three harnesses.
- Vendor-native hooks, permission rules, sandbox defaults, and status lines.
- Declarative plugin installation for Claude and Codex.
- A shared MCP registry that preserves intentional external additions and
  removes explicitly retired integrations.

### Antigravity CLI

Antigravity CLI is enabled separately from the retired Antigravity IDE and
Gemini CLI. Dotfiles installs the `antigravity-cli` Homebrew cask, which provides
`agy`. Workbench includes its global rules and skills in `sync all` and
`drift all`; it can also be targeted directly:

```bash
workbench sync antigravity --dry-run
workbench sync antigravity
workbench drift antigravity
antigravity
```

Rules deploy to `~/.gemini/AGENTS.md`; skills deploy to
`~/.gemini/antigravity-cli/skills`. Existing settings, plugins, MCP servers,
credentials, and session history remain vendor-owned and untouched. Sign in
through the interactive CLI when needed; Workbench does not enroll its login.
Antigravity is personal-profile only. The shell names `antigravity`, `antig`,
and `agravity` launch the native Homebrew binary without adding Workbench's
boundary. `agy` enters the same whole-process boundary as `co`, `cc`, and `p`,
but is **experimental and currently blocked at normal startup**: CLI 1.4.7
requires a dynamically allocated loopback listener. It does not fall back to
native execution. Host Keychain and Google API denials remain unchanged;
authenticated managed use has not been verified. See the
[integration notes](docs/agents/antigravity.md). The native command's `--sandbox`
flag is Google's narrower terminal sandbox, not the Workbench boundary.

### Engineering guidance

- [The playbook](playbook/README.md) groups reusable knowledge by agents,
  engineering, languages, systems, and product. Filenames expose the subjects;
  [the watchlist](playbook/watchlist.md) holds only unresolved questions and triggers.
- `health/` provides deterministic project-check patterns and adoption contracts;
  advisory review behavior lives in the relevant skills.
- `agents/prompts/` contains reusable prompts that do not warrant an always-on
  skill.
- `docs/decisions/tombstones.md` prevents rejected tools and approaches from
  being casually rediscovered and reintroduced.
- `docs/agents/pi/decisions.md` records what the Pi harness adopts, rejects, and
  holds for evidence, while `docs/agents/pi/README.md` records current behavior.

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
pnpm install --frozen-lockfile
just check
```

Requirements are deliberately small: [uv](https://docs.astral.sh/uv/) (which
provisions the Python 3.13 development line pinned in `.python-version` and the Typer/Rich CLI environment on first run), Bash,
[Node 26.12.1 or newer within Node 26](https://nodejs.org/) and [pnpm](https://pnpm.io/) for the locked Pi
extension test and development tools, and the installed Pi/Claude/Codex
CLIs. [Pandoc](https://pandoc.org/) is required only to render and verify the
maintained reading and call-script document templates. Workbench stages and atomically replaces managed skills; Pi and Codex discover one shared real-file deployment under `~/.agents/skills`, avoiding duplicate Pi skill warnings.

TypeScript formatting stays with Biome. `just lint-ts` runs the two selected
Oxlint promise checks; `just check` includes formatting, linting, tests, and
type checking. Vite+ remains on the [watchlist](playbook/watchlist.md).

All 31 reusable skills are tracked in this repository. The Archify archive
download pipeline is retired; sync removes retired skills and drift flags their
reintroduction. Retirement reasons live with `RETIRED_SKILLS` in
[`src/workbench/core.py`](src/workbench/core.py).

## Daily Workflows

### Reconcile everything

```bash
workbench sync all --dry-run
workbench sync all
workbench drift all
```

Preview reports paths, permission repairs, removals, and plugin operations without
writing configuration or installing plugins. It never prints configuration values.

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

Skip skills and plugin installation when only configuration files need repair:

```bash
workbench sync all --no-skills --no-plugins
```

Managed work computers use the fail-closed work profile:

```bash
workbench sync all --profile work
workbench drift all --profile work
```

The work profile targets only Claude Code and Pi and excludes personal
integrations. The exact exclusions, model defaults, and preservation rules live
in the [configuration reference](docs/configuration.md).

Sync and drift use `DOTFILES_PROFILE` when set, otherwise `personal`; an explicit
`--profile` overrides that default. `just deploy` chains sync and drift so a deploy
is verified in one command. It accepts a vendor, `--profile`, and `--no-plugins`;
use `just sync` for partial deployments with `--no-skills` or `--rules-only`.

### Validate repository sources

```bash
just check       # format, lint, types, tests, and source validation
just test        # deterministic unit tests only
just lint        # skills, links, JSON, TOML, and shell syntax
just check-documents  # render-smoke the maintained document templates
just native-canary    # real macOS boundary probes; synthetic state, no model requests
```

### Understand an unexpected live item

```bash
workbench drift all
```

`DRIFT` (managed value missing or different, non-zero exit) is distinguished
from `EXTERNAL` (valid unmanaged addition, reported but passing). Details in
[`docs/configuration.md`](docs/configuration.md).

## Command Tree

Run `workbench`, `wb`, or either launcher's `--help` flag for the complete tree:

```text
workbench
├── sync [claude|codex|pi|antigravity|all] deploy canonical configuration
│   ├── --profile              personal or work; defaults to DOTFILES_PROFILE
│   ├── --no-skills            skip shared-skill installation
│   ├── --no-plugins           skip declared-plugin installation
│   ├── --dry-run              preview changes without applying them
│   └── --rules-only           deploy only global instruction files
├── drift [claude|codex|pi|antigravity|all] report managed drift and external additions
│   └── --profile              personal or work; defaults to DOTFILES_PROFILE
├── lint                       validate canonical repository sources
└── native
    ├── prepare [--authorize]  install the managed runtime and optional model logins
    ├── authorize <vendor>     enroll one login; --replace backs up and replaces it
    ├── status [vendor]        inspect paths and login metadata without token reads
    └── run <vendor> -- ...    launch codex, claude, pi, or a diagnostic shell
```

Run `just` for the repository-development command list. The CLI manages live
agent configuration; Just recipes develop and validate this repository.

## What `sync` Manages

`sync` deploys each harness's managed subset: global instructions, configuration,
command policy, extensions or hooks, skills, plugins, and MCP servers where supported. The per-harness file map and drift semantics live in
[`docs/configuration.md`](docs/configuration.md).

## Repository Tour

```text
agents/
├── shared/              cross-vendor rules, hooks, and MCP registry
├── claude/              Claude settings fragments and plugin declarations
├── codex/               Codex rules, hooks, status line, and plugins
├── pi/                  Pi settings, models, agent definitions, permission policy, and extensions
├── skills/              reusable on-demand workflows
└── prompts/             reusable prompts below the skill threshold

playbook/                reusable knowledge, discovered by subject
├── agents/              models, harnesses, tools, orchestration, and authority
├── engineering/         design, verification, review, and delivery practices
├── languages/           language idioms, libraries, and framework guides
├── systems/             services, data, infrastructure, and host tools
└── product/             discovery, design tools, and interfaces

health/                  portable deterministic project-check patterns
docs/                    current Workbench behavior, architecture, and decisions
src/workbench/           Typer + Rich deployment and verification CLI
pyproject.toml           uv-managed project (Typer, Rich; pytest/Ruff/Pyright dev gate)
tests/                   deterministic CLI, sync, drift, guard-hook, and Pi extension tests
bin/workbench            relocatable shell launcher (execs via uv)
```

## Extending Workbench

Choose the smallest durable surface that fits the need:

1. Update `agents/shared/rules.md` only for behavior that should always apply to
   Pi, Claude Code, and Codex.
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

The shortcuts `co`, `cc`, and `p`, plus the experimental `agy`, contain the entire agent process and its
children in Workbench's native macOS boundary. Full commands `codex`, `claude`,
and `pi` launched from the host retain native behavior without that outer
boundary. Starting a native binary inside an already managed session does not
remove its inherited restrictions.

The [isolation contract](docs/security/isolation.md) owns setup, permissions,
project grants, session history, and accepted risks. The
[launch design catalogue](docs/agents/launch-design.md) compares launch routes;
the [independent review disposition](docs/decisions/managed-launch-review.md)
records the reviewed corrections and remaining limits. Database and
infrastructure policy belongs to the project that owns those resources.

For an independent read-only fact-check, use the
[`adversarial audit prompt`](agents/prompts/workbench-audit.md).

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
