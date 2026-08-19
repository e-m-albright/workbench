---
name: tree-ontology
description: Decide where a new module, command, route, or directory belongs and what to name it; audit trees for mixed sibling axes, compound names, and hierarchy. Use for "where should this live", "what should I call this", or "organize this CLI".
---

# Tree Ontology

A tree is predictable when a reader can infer where something belongs, what neighboring nodes mean, and how the structure grows without memorizing exceptions.

Most ontology decisions are not audits. They are one person adding one node and picking a name, dozens of times between audits. That is where structure is actually set, so start with the fast path and escalate only when the placement resists.

Change files or public command paths only when the user asks for implementation.

## Placing a single node

When adding a module, command, route, or directory, work through this before creating the file. It takes under a minute and it is the highest-leverage moment in the tree's life — a node placed by reflex is the sediment a future audit has to excavate.

1. **Name the axis of the parent you are about to join.** What single question do that parent's existing children answer — domain? operation? lifecycle? external system? If you cannot state it in one phrase, the parent is already mixed, and adding to it deepens the problem.
2. **Check the node answers that same question.** A node that answers a different question is the first grain of a mixed sibling set, no matter how convenient the location.
3. **Test the name against its siblings, not in isolation.** Read the full path aloud. It should narrow from broad concept to specific intent, in the vocabulary the domain already uses.
4. **If the name needs a prefix or suffix to disambiguate, the affix is a missing directory.** `cli_actions.py`, `cli_world.py`, and `vault_lint.py` are a `cli/` package and a `vault/` package spelled with underscores. Create the level instead.
5. **If placement is genuinely ambiguous, that is information.** Ambiguity usually means the tree has no axis at this level, or the node does two jobs and wants splitting. Say so rather than picking the least-bad slot silently.

## Preference model

Apply these unless the project documents a stronger domain-specific rule:

1. **Canonical names use complete words.** Prefer `organizations`, `investors`, `database` over `orgs`, `vcs`, `db`. Keep abbreviations as ergonomic aliases, never as the canonical form.
2. **One segment carries one concept.** Prefer `query connectors capacity` over `query connector-capacity`. A compound name usually hides a missing level.
3. **Hierarchy earns qualification.** Add a level when it distinguishes a durable subtype, view, target, or operation and gives future siblings somewhere logical to live.
4. **Siblings share an axis.** Children of one node should all be domains, views, operations, lifecycle stages, audiences, or another single kind of distinction. A mixed sibling set is the primary ontology smell.
5. **Nouns precede qualifiers; mutations end in verbs.** Prefer `hypotheses stale` and `person action set`.
6. **Bare parents have a useful default.** Let `query connectors` show the primary actionable view. Add `--all` or a child only for a materially different projection.
7. **Plurality communicates cardinality.** Plural for collections, singular for one entity or mutation target. Apply consistently within a tree.
8. **Canonical structure and typing convenience are separate layers.** Preserve a clear full path, then add exact aliases or deterministic unique-prefix matching. Ambiguous prefixes fail with candidates. Typos suggest but never execute, especially for mutations.
9. **Bounded context beats grammatical purity.** Do not force every node under a generic verb when that obscures ownership. If `query` means world-model reads, application status such as `jobs` belongs outside it.
10. **One concept has one home.** Other paths point, alias, import, or delegate; they never grow competing implementations or duplicated state.
11. **A package's exported names must not collide with its sibling modules.** An `__init__` that re-exports `app` beside an `app.py` shadows the module, and the failure surfaces far from the cause.

These are preferences, not a demand for depth. A one-word node is better when it is already precise and has no meaningful sibling distinction.

## Choosing the axis

For anything larger than a single node, the axis is the whole design. Two habits separate a finding from an opinion.

**Measure the coupling before you choose.** Candidate axes are cheap to argue about and cheap to test. Build the actual dependency graph — imports for a file tree, shared options and output shapes for a command tree — and count edges between candidate groupings. A real axis shows up as overwhelmingly one-directional flow. In one restructure, a tree that looked like it needed subject-matter grouping turned out to have a clean dependency gradient hiding in it: 66 edges from the surface layer down to data, 44 from domain modules down to primitives, and almost nothing upward. The measurement chose the axis; taste would have chosen worse. Measurement also settles ordering disputes: two candidate tiers separated by one edge each way are genuinely arbitrary, and knowing that is worth more than a confident guess.

**Prefer the axis you can enforce.** When two ontologies are both defensible, the tiebreaker is which one yields a mechanical invariant. Grouping by dependency direction gives you "no module imports a layer above it" — a check that runs in CI. Grouping by subject gives you nothing checkable. This matters because unenforced structure decays silently: hand-maintained directory listings drift, and the drift is found by the next person who trusts them.

That criterion also justifies levels that look thin. A node with only two children still earns its place when it is the level a rule is stated over — the rule needs a name to attach to.

**A rule that constrains tools has to be a check, not a sentence.** Prose conventions bind whoever reads them, and generators read nothing. A repository that had documented "no new top-level directories without approval" for months grew one anyway, because a review script defaulted its output path there. When a tree sprouts a node nobody chose, find what wrote it: deleting the artifact while the generator stands means it returns next run. Tools that write into a repository they do not own should default to an ignored scratch location and take an explicit flag to put anything durable elsewhere.

**Ship the enforcement in the same change.** A reorganization plus "we will add the lint later" is a reorganization that decays. Encode the invariant as a check, and seed it with an honest baseline of the violations that already exist, each annotated with the fix it implies. Fail on new violations, and fail on baseline entries that no longer occur, so the list can only shrink and cannot rot into a record of things fixed long ago.

## Auditing an existing tree

### 1. Establish the boundary

Identify who uses the tree (humans, agents, scripts, several audiences), whether it represents domains, effects, artifacts, workflows, lifecycle, or navigation, which names are public contracts, and what glossaries, decisions, and rejected designs already exist.

Implementation categories such as `views`, `helpers`, or `services` may be useful internally and still make poor public paths.

### 2. Inventory what is actually there

Use the repository's native tooling and inspect rendered output — actual CLI help, the real filesystem — rather than registration source alone.

For command trees capture visible commands at every level, parent defaults and options, hidden aliases and prefix behavior, side effects (read, local mutation, workflow, external mutation), and every caller: help text, examples, tests, scripts, automation.

For file trees capture directories, entrypoints, indexes, generated areas, the imports that reveal real ownership, duplicate concepts, forwarding modules, suffix families such as `*_v2`, and miscellaneous buckets.

**Treat every inventory finding as a hypothesis until you check it.** Claims of deadness are the ones that bite: a path that no longer exists may be a retired concept, or a transient buffer sitting empty in its correct steady state. Confirm what a thing is *for* before calling it dead — and re-verify findings that arrive from a subagent or an earlier session.

### 3. Name the axis at every branch

Write a short label for what each level separates:

```text
query                 axis: world-model domain
  connectors          axis: connector projection
    capacity
    coverage

write                 axis: entity
  person              axis: owned sub-concept or mutation
    action            axis: mutation
      set
```

A branch whose label needs several concepts joined by "and" is mixing axes. Split it, or justify the exception explicitly.

### 4. Run the ontology tests

- **Prediction:** given one known path, can a newcomer guess where a sibling belongs?
- **Sibling axis:** do siblings answer the same kind of question?
- **Read aloud:** does the path move from broad concept to precise intent?
- **Vocabulary:** are domain terms used consistently, without unexplained synonyms or abbreviations? Prefer a word the project's own glossary already uses over a term of art imported from elsewhere. Where one concept crosses surfaces — a CLI command, an HTTP route, a module, a type — it drifts into a different spelling per surface unless something checks the correspondence; a generated or test-enforced mirror between two of them is what keeps the vocabulary honest.
- **Compound:** would splitting a hyphenated or suffixed name expose a useful hierarchy?
- **Default:** is the bare parent useful, or merely another help screen?
- **Boundary:** do read, mutation, workflow, and external effects sit behind honest boundaries?
- **Depth:** does each level add information? Collapse pass-through levels, unless the level carries a stated rule.
- **Collision:** will aliases or prefixes become ambiguous as known siblings arrive?
- **Resolution:** if references resolve leniently — by basename, by unique prefix, by fuzzy match — resolve them strictly once and compare. Leniency hides rot: a link to a deleted page can quietly resolve to the page containing it, or to an unrelated file that happens to share a name, and a link checker sharing that leniency reports success.
- **Ownership:** is there one canonical home, with compatibility paths delegating to it?

Separate structural defects from taste. Rename when the new shape improves prediction, ownership, safety, or extensibility.

### 5. Propose the canonical form

Show the proposed tree and a migration table:

| Current | Canonical | Compatibility | Reason |
|---|---|---|---|
| `query candidate-overlap` | `query connectors overlap` | hidden old alias | domain first; hierarchy replaces compound |
| `write person action-set` | `write person action set` | hidden old alias | owned concept before mutation |

State canonical names, defaults and `--all` behavior, aliases and prefix rules, any intentional axis exception, and what is explicitly not being reorganized.

For a consequential public tree, get approval on representative examples before migrating everything.

## Migrating

Renaming is a data migration, not a text edit — the imports are the easy part, and the references that break are rarely the ones grep finds first. Read [migration.md](references/migration.md) before executing any multi-file move.

## Output contract

For an audit, report:

1. **Conclusion** — whether the ontology is coherent, and the main source of friction.
2. **Current axes** — what each level actually separates today.
3. **Findings** — evidence-backed inconsistencies, ordered by impact.
4. **Canonical proposal** — complete tree plus current-to-proposed mapping.
5. **Compatibility and safety** — aliases, ambiguity behavior, migration risks.
6. **Verification plan** — the exact checks that prove the new organization landed.

For a build, finish with the implemented tree, compatibility behavior, verification evidence, and any deliberately deferred branches.
