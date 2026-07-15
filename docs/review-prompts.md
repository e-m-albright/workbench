# Review Prompts

Run these in separate fresh chats. Each starts read-only so the reviewer forms
an independent view before changing the system. Every prompt is informational:
the reviewer must present findings and proposed direction, then wait for your
explicit approval before editing anything.

## 1. Refactor Loss Audit

```text
Audit the completed split between ~/code/public/dotfiles and
~/code/public/workbench. Begin read-only. Read both AGENTS.md files, repository
status, current diffs, and relevant history. Compare deleted or moved material
against its new canonical destination using Git, not memory.

Find anything unintentionally lost, weakened, duplicated, misplaced, or left
stale. Pay special attention to agent rules, skills and their references, MCPs,
permissions, tombstones, Deno/Node/web-stack decisions, remote/session tooling,
health principles, prompts, research automation, and fresh-Mac behavior.

Classify every finding as LOSS, DUPLICATION, STALE REFERENCE, INTENTIONAL
RETIREMENT, or UNCERTAIN. Cite exact files and evidence. Do not equate fewer
files with loss: judge preserved capability and decision content. Do not edit
until presenting findings and agreeing on the smallest repairs. Prefer deletion,
movement, or a sentence over new machinery.
```

## 2. Workbench Capability Audit

```text
Audit ~/code/public/workbench as a personal Claude Code and Codex workbench.
Begin read-only. Its remit is portable agent behavior, engineering taste,
project-health tools, and reusable automation mechanics. It is not a fleet
platform, compliance system, or general product.

Evaluate whether its rules, 19 canonical skills, subagents, MCPs, permissions,
status lines, playbook, health kit, and experimental automation are coherent,
powerful, progressively disclosed, and non-overlapping. Inspect actual bodies
and references, not only filenames. Check current official vendor behavior when
making compatibility claims. Identify capabilities that are missing, redundant,
too broad, too verbose, weakly triggered, or better supplied by a native vendor
feature or project-local rule.

Use a strict complexity budget. Recommend ADD only when a recurring workflow
cannot be served by an existing capability, native feature, or short reference.
Report KEEP, MERGE, PRUNE, REWRITE, and ADD decisions with expected capability
impact and approximate LOC/context change. Then propose the smallest ordered
implementation pass. Do not implement before review.
```

## 3. Fresh-Mac and Deployment Audit

```text
Audit ~/code/public/dotfiles and Workbench deployment as if preparing one new
personal MacBook. Begin read-only. Trace the documented install from clone to a
usable shell, packages, editors, remote access, Mission Control, Claude Code,
Codex, skills, MCPs, permissions, notifications, tombstones, and drift checks.

Check that canonical sources, install destinations, symlinks, doctor checks,
shell paths, package tombstones, and workbench sync/check agree. Separate real
enforcement from advisory instructions. Use temporary HOME directories and
dry-run/parser tests where possible; do not change macOS settings, credentials,
remote login, or destructive paths.

Find broken first-run assumptions, stale paths, unsupported vendor settings,
silent failures, missing verification, and complexity that does not earn its
maintenance cost. The desired result is a direct, idempotent personal bootstrap,
not resilience for arbitrary machines. Return severity-ordered findings, a
fresh-machine capability checklist, and the smallest fixes. Do not build new
frameworks, snapshots, schedulers, dashboards, or policy layers.
```

## 4. Coverage and Delivery Audit

```text
Audit test coverage, quality gates, and CI/CD for ~/code/public/dotfiles and
~/code/public/workbench. Begin read-only and make no changes. Inspect the actual
test suites, coverage configuration, Just recipes, hooks, GitHub Actions,
release/deployment behavior, and branch protections that can be observed with
read-only tools.

Explain what each current gate proves, what it does not prove, where coverage is
meaningfully weak, and whether the split introduced untested contracts between
the repositories. Distinguish useful line/branch coverage from tests written
only to raise a number. Check whether CI matches local commands, whether fresh
bootstrap and Workbench deployment can be tested safely, and whether any CD is
actually warranted for repositories whose main output is local configuration.

Return severity-ordered findings followed by KEEP, PRUNE, FIX, and ADD
recommendations. For every proposed tool or workflow, state the failure it
prevents, maintenance cost, and smallest native alternative. Favor a few clear
gates over a quality platform. Do not add coverage ratchets, matrix jobs,
scheduled workflows, release automation, or third-party services without
evidence that their complexity pays for itself. Wait for explicit approval
before editing files, changing repository settings, or installing tools.
```

## 5. Dotfiles Refactor and Architecture Audit

```text
Audit the current large refactor in ~/code/public/dotfiles. Begin read-only.
Read AGENTS.md, repository status, the complete working diff, relevant history,
and the implementations and tests that remain after the deletions. Treat the
working tree as valuable uncommitted work and do not modify it.

Check whether the refactor leaves a coherent personal macOS host-configuration
repository. Pay particular attention to ownership boundaries with
~/code/public/workbench; obsolete agent, research, health, repository, snapshot,
and benchmark behavior; CLI command registration; package and settings sources
of truth; dead compatibility paths; duplicated helpers; misleading names; stale
imports, documentation, completions, hooks, and Just recipes; and abstractions
that survived after their reason for existing was removed.

Trace important behavior through entry point, service, adapter, and user-facing
output rather than reviewing files independently. Compare deletions and moves
against Git history and the Workbench destination before calling anything lost.
Classify findings as CORRECTNESS, LOST CAPABILITY, STALE SURFACE, OWNERSHIP
VIOLATION, DUPLICATION, or UNNECESSARY COMPLEXITY. Cite exact evidence and rank
by severity. End with KEEP, PRUNE, MOVE, RENAME, and FIX recommendations plus the
smallest ordered implementation pass. Do not edit before review and approval.
```

## 6. Dotfiles Host and Bootstrap Audit

```text
Audit ~/code/public/dotfiles as the desired-state definition for one personal
Mac. Begin read-only. Read AGENTS.md and trace install.sh, bin/dotfiles, the
Just recipes, macos/packages.toml, macOS scripts, shell startup files, terminal
configuration, editor deployment, hooks, and documentation from a fresh clone
through repeated use.

Check idempotency, quoting, shell failure propagation, architecture and PATH
assumptions, package tombstones, source-versus-destination clarity, symlink and
copy behavior, partial-install recovery, optional-tool behavior, and whether
doctor detects the important live drift without snapshots. Distinguish settings
that are truly applied from documentation or advisory checks. Use temporary HOME
directories, parser checks, and dry runs where possible. Do not change macOS
settings, installed packages, credentials, login items, or the real home state.

Return severity-ordered findings, then a fresh-machine and repeat-run checklist
showing PASS, FAIL, or UNPROVEN with exact evidence. Recommend the smallest
repairs. Do not add a framework, state database, general multi-machine support,
or defensive complexity for hypothetical users. Do not edit before review and
approval.
```

## 7. Dotfiles Operational CLI Audit

```text
Audit the user-visible `dotfiles` CLI and Mission Control TUI in
~/code/public/dotfiles. Begin read-only. Read AGENTS.md, command registration,
models, services, adapters, tests, snapshots, completions, and documentation.
Exercise safe read-only paths and use fakes or temporary state for mutating
flows.

Review doctor, brew, remote, session, email, and the dashboard as complete user
journeys. Look for commands that disappeared unintentionally during the refactor,
dead registrations, inconsistent option or exit-code semantics, swallowed
errors, subprocess and HTTP boundary mistakes, stale snapshots or completions,
unsafe destructive actions, hidden environmental coupling, and UI states that
misrepresent reality. Check that core remote/session behavior still works while
removed agent/repo/snapshot/benchmark responsibilities leave no active residue.

Report severity-ordered findings with reproduction evidence and identify which
tests genuinely protect each journey. Then give KEEP, PRUNE, FIX, and TEST
recommendations and the smallest ordered repair pass. Do not update snapshots
merely to make tests green, and do not edit before review and approval.
```

## Shared Standard

For every audit: preserve unrelated changes, verify before claiming success,
and distinguish deterministic evidence from model judgment. Low LOC is a design
pressure, not a metric to game. A short implementation that hides ambiguity or
loses an important capability is worse than a slightly longer clear one; every
line still needs to earn its place. The first response is informational only.
Do not edit files, install tools, change settings, commit, push, or open pull
requests until the owner explicitly approves a proposed direction.
