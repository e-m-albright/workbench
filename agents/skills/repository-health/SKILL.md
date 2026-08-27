---
name: repository-health
description: Audit documentation, dependencies, automation, CI, feedback, and chores. Use for repository health, maintenance audits, or repo grooming.
allowed-tools: Read Grep Glob Bash(git:*) Bash(rg:*) Bash(ls:*) Bash(wc:*) Bash(just:*) Bash(fd:*) Agent WebSearch WebFetch
---

# Repository Health

Assess whether the repository remains truthful, current, and efficient to
operate. This is the operating-layer review: documentation, configuration,
dependencies, automation, checks, decisions, and maintenance workflows.

Use `capability-health` to decide what the project should provide. Use
`code-health` for naming, abstractions, module structure, effects, and other
implementation-form concerns. Use `review` for a pending change.

This skill is read-only. It reports evidence and recommended workstreams; fixes
happen only after explicit authorization.

## Workflow

1. **Orient.** Read project instructions, README, task runner, manifests,
   top-level tree, CI, feature map, and decision records. Judge against the
   repository's purpose and policies rather than a generic ideal.
2. **Check previous state.** Read open health findings, issues, baselines, and
   recent relevant history when available. Mark repeated findings rather than
   presenting them as discoveries. Do not reopen a recorded rejection unless
   its revisit condition has changed.
3. **Run the operating-layer sweep.** Work every lens below, using focused
   specialist skills or native project tools where named.
4. **Verify.** Confirm every finding against a file, command result, or dated
   primary source. Distinguish a reproduced defect from a recommendation.
5. **Synthesize.** Deduplicate, group related fixes into workstreams, and rank by
   impact relative to effort. Prefer deletion and native project mechanisms
   over new infrastructure.
6. **Record recurrence.** Recommend a deterministic check for a repeated,
   objectively detectable problem. Judgment-heavy findings remain advisory and
   human-gated.

## Lenses

### Truth and drift

- README, command examples, feature maps, architecture notes, and comments that
  disagree with current behavior.
- Broken links, renamed paths, obsolete setup instructions, stale generated
  files, and configuration keys with no owner.
- Decision records and health baselines whose assumptions or revisit conditions
  have changed.

Feature-map drift may be reported here, but portfolio decisions route to
`capability-health`.

### Automation and feedback

- Setup, bootstrap, release, CI, hooks, recipes, and scheduled jobs that fail,
  duplicate one another, or require undocumented manual sequencing.
- Slow, noisy, or missing feedback loops; checks that exist only in memory; CI
  that does not run the same project-owned gate used locally.
- Recurring chores that merit a small recipe, hook, or scheduled routine after
  their trigger, permissions, output, cost ceiling, and verification are clear.
- Existing automation that no longer catches a real regression and should be
  retired.

### Dependency and supply-chain maintenance

Route lockfile vulnerability, version, unused-dependency, and license analysis
to `dep-audit`. Inspect pinning, installer provenance, abandoned dependencies,
and update ownership. Route exploitability and trust-boundary questions to
`security-review`; do not duplicate its rubric here.

### Test-suite health

When tests themselves are the concern, use the audit mode in `testing`. Look for
flakes, weak assertions, inappropriate mocks, slow default tiers, skipped tests,
and load-bearing behavior with no effective coverage. Repository health owns
whether the suite provides timely feedback; `testing` owns test design.

### Documentation and guidance currency

Review maintained prose for stale versions, repeated doctrine, conflicting
advice, and guidance with no active consumer. Large playbooks deserve a bounded
currency pass by section rather than a superficial whole-tree skim. Preserve
current canonical doctrine and delete sediment.

### Policy and public-boundary hygiene

Check tracked files for secrets, private identifiers, personal absolute paths,
unsupported employment/status signals, and policy drift. Treat history cleanup
as a separate consequential operation. Use `security-review` when exposure or
exploitability needs deeper assessment.

### Repository debris

Find orphaned assets, abandoned experiments, compatibility shims whose migration
is complete, duplicate configuration, and files outside the repository's stated
ownership. Dead implementation and speculative code abstractions route to the
`prune` lens in `code-health`.

## Focus modes

- **Playbook currency:** review one maintained guidance area for staleness,
  duplication, and active consumers.
- **Automation retirement:** identify jobs, hooks, recipes, and generated state
  that no longer earn their maintenance cost.
- **Documentation truth:** reconcile commands, paths, feature descriptions, and
  setup guidance with live behavior.
- **Feedback-loop health:** assess local checks, CI, test tiers, and time to a
  useful failure.

## Report

1. **Repository verdict** — overall operating health and the largest source of
   maintenance drag.
2. **Workstreams, ranked** — coherent sessions of work with payoff and scope.
3. **Findings** — title, lens, impact, effort, evidence, recurrence status, and
   recommended action.
4. **Deletion and retirement candidates** — visible as a first-class list.
5. **Specialist results** — dependency, security, or test-suite findings routed
   through their owning skills.
6. **Deterministic follow-ups** — repeated findings that can become project-owned
   checks or ratchets.
7. **Checked, clean** — lenses examined without findings.

Do not report an unbounded backlog merely because it exists. Include every
verified high-value finding, combine duplicates, and separate lower-value debt
that does not justify action now.
