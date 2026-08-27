---
name: capability-health
description: Assess which capabilities to keep, sharpen, cut, replace, or add. Use for capability health, feature audits, catalogue drift, or product grooming.
allowed-tools: Read Grep Glob Bash(git:*) Bash(rg:*) Bash(ls:*) Bash(wc:*) Agent WebSearch WebFetch
---

# Capability Health

Assess whether the project owns the right capabilities. This is portfolio
judgment, not implementation critique: ask **what should exist and why?** Use
`code-health` for implementation structure and `repository-health` for the
repository's operating layer.

The skill is read-only. Deliver a decision-oriented report; make catalogue or
code changes only in a separately authorized follow-up.

## Scope

Start from the project's stated purpose, users, constraints, and maintained
feature map. In Workbench, `CATALOGUE.md` is canonical. Elsewhere, use the
closest equivalent or construct a provisional map from code, commands, config,
and documentation.

Assess capabilities at the level a user or maintainer would recognize. Do not
mistake every module, adapter, or configuration file for a capability.

## Workflow

1. **Map actual capabilities.** Read the feature map, README, command surface,
   configuration registries, and primary implementation entry points. Record
   capabilities that exist in code but not in the map, and mapped capabilities
   with no maintained implementation.
2. **Gather evidence of value and cost.** Look for active callers, tests,
   deployment paths, documentation, recurring workflow use, maintenance burden,
   duplicated ownership, and explicit decisions. Absence of telemetry is
   uncertainty, not proof of disuse.
3. **Classify every capability.** Choose one posture:
   - **Keep** — valuable, appropriately scoped, and adequately maintained.
   - **Sharpen** — valuable but incomplete, awkward, unreliable, or hard to use.
   - **Cut** — no longer earns its surface area or has no demonstrated owner.
   - **Consolidate** — duplicates another capability's trigger, workflow, or
     contract.
   - **Replace** — still needed, but a stable upstream or simpler native option
     now owns the job better.
   - **Add** — a demonstrated recurring need has no adequate owner.
4. **Verify external claims.** Research current upstream behavior only for a
   concrete parity, replacement, or missing-capability question. Cite dated
   primary sources. Do not perform an unconstrained frontier scan; novelty is
   not evidence of fit.
5. **Reconcile the map.** Propose exact feature-map changes for additions,
   removals, consolidations, posture changes, and material expansions.
6. **Rank decisions.** Order by user value, risk reduction, and maintenance
   saved relative to effort. Deletions and consolidations receive equal footing
   with additions.

## Focus modes

Use these as bounded passes when a full portfolio review is unnecessary.

### Upstream parity

Check local extensions, adapters, wrappers, and compatibility layers against
current native vendor behavior. Prefer one active implementation. Recommend
removal only after verifying equivalent behavior, migration cost, and trust
boundary differences.

### Skill portfolio

For each skill, compare its trigger, workflow, and output contract with its
neighbors. Merge skills only when those substantially overlap; shared subject
matter alone is not duplication. Flag stale references, compatibility entries
whose migration has completed, and workflows that do not reduce rework enough
to justify permanent trigger metadata.

### Feature-map reconciliation

Perform a fast truth pass: implementation missing from the map, map entries
missing from implementation, stale posture, and material scope changes. Do not
turn a documentation reconciliation into speculative roadmap work.

## Report

1. **Portfolio verdict** — what the project should become and the largest gap.
2. **Capability decisions** — one row per capability with posture, evidence,
   confidence, and recommended action.
3. **Catalogue drift** — exact additions, removals, and wording changes.
4. **Additions considered** — include rejected candidates and why they do not
   clear the bar.
5. **Research notes** — dated primary sources used for parity or replacement
   claims.
6. **Open uncertainties** — evidence needed before a cut, replacement, or major
   addition is safe.

A healthy result may recommend no new features. The goal is a coherent,
maintained portfolio, not a longer catalogue.
