---
name: dependency-upgrades
description: Find and apply dependency and host-tool upgrades, including valuable release features. Use for "upgrade dependencies", "bump versions", "what's outdated", or cross-repository upgrade waves.
---

# Dependency Upgrades

Refresh dependencies on demand without introducing a scheduler, bot, or package-management layer. Use native ecosystem tools for mechanics and agent judgment for release research, compatibility, sequencing, and verification.

## Choose the mode

Infer the narrowest mode from the request:

- **Inventory:** Report outdated packages, vulnerabilities, runtime drift, and worthwhile release features. Keep the workspace read-only.
- **Upgrade:** Apply approved bumps, compatibility migrations, and focused tests.
- **Upgrade wave:** Coordinate the same refresh across several repositories or host-managed tools.

If the user asks to “check” or asks what is available, start with inventory. Treat “upgrade,” “bump,” or “update” as authority to edit the named scope, but preserve user control over host installs, pushes, releases, deployments, and other consequential external effects.

## 1. Establish scope

1. Read repository instructions and manifests before running package commands.
2. For personal shorthand such as “main repos,” resolve repository identities from machine-local context. Keep private identities and paths out of portable or public files.
3. Record the branch, working-tree state, package-manager owner, runtime declarations, lockfiles, CI pins, and project verification gate.
4. Identify pre-existing edits. Preserve them and keep upgrade commits separable; do not reformat or stage unrelated work.
5. When several repositories are in scope, choose the smallest representative repository as the canary unless the user names one.

Use [ecosystem commands](references/ecosystems.md) as a menu, not as a script. Prefer repository recipes and declared package managers over generic commands.

## 2. Build the upgrade set

Collect current, wanted, and latest versions from native tooling. Include:

- Direct and development dependencies.
- Package-manager and runtime declarations.
- Lockfile format and peer constraints.
- CI actions and installer pins.
- Host tools only when the request includes host state.
- Vulnerability and deprecated-package findings.

Classify each candidate:

- **Routine:** compatible patch and minor releases that can move together.
- **Review:** major versions, runtimes, build tools, framework integrations, or changed peer contracts.
- **Security:** known vulnerabilities, install-script changes, provenance changes, or newly introduced transitive risk.
- **Defer:** incompatible, unmaintained, low-value, or blocked by an upstream contract.

Do not force “latest” through peer overrides or broad compatibility shims. The newest compatible version is a valid result.

## 3. Research what changed

Research review and security candidates from dated primary sources: official release notes, migration guides, compatibility tables, advisories, and package metadata. Ground current-version claims in live evidence.

Look beyond breaking changes. Identify features that can simplify configuration, improve security, shorten feedback, remove custom code, or provide stronger deterministic gates. Adopt a feature only when it has a concrete local use; new surface area by itself is not value.

For each consequential candidate, record:

- Why it is worth taking now.
- Required migration work.
- Runtime, peer, lockfile, and CI compatibility.
- Security or install-script implications.
- A rollback path.

## 4. Apply in reviewable slices

1. Start with the canary and make one coherent ecosystem update at a time.
2. Use the native package manager to update manifests and regenerate lockfiles together.
3. Inspect install-script approvals, peer diagnostics, deprecations, and lockfile diffs before changing source.
4. Make the smallest source or configuration migration required by the upstream contract.
5. Add focused regression coverage when an API, generated output, configuration contract, or install path changes.
6. Adopt useful release features in the same slice only when they directly strengthen the repository.
7. Expand to the remaining repositories after the canary passes.

Do not create competing legacy and new paths. Remove superseded overrides, shims, and configuration once the replacement works.

## 5. Verify each slice

Run focused checks while iterating, then run the repository’s full declared gate once after the final mutation. Verification should cover, where available:

- Formatting, lint, and static types.
- Peer-dependency and frozen-lockfile integrity.
- Unit, integration, and browser tests.
- Production build.
- Vulnerability audit and supply-chain policy.
- Project health or complexity ratchets.
- `git diff --check` and a final review of the intended diff.

For cross-repository work, keep results separate. A passing canary does not prove another repository passes. If unrelated pre-existing work blocks a full gate, run the strongest isolated checks available and report the exact blocker without weakening the gate.

Create separate, reviewable commits only when requested. Before any commit, summarize the intended staged set and verification. Confirm before pushing or triggering remote workflows unless the user already authorized that exact external action.

## Report

Lead with the outcome, then provide:

1. **Upgraded:** package or tool, old and new versions, and meaningful adopted features.
2. **Verified:** exact gates and material test counts.
3. **Deferred:** candidate, reason, and revisit condition.
4. **Blocked:** exact command or authority needed.
5. **Workspace state:** whether changes are committed, pushed, or still local.

Keep raw outdated-package noise out of the main report. Include every item that requires a user decision.
