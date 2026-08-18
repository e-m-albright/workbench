---
name: tree-ontology
description: Design or audit command trees and file trees for coherent vocabulary, sibling axes, hierarchy, defaults, and safe aliases. Use for "organize this CLI", "audit this file tree", naming cleanup, information architecture, or deciding where something belongs.
---

# Tree Ontology

Use this skill to make a command tree or file tree predictable: a reader should infer where something belongs, what neighboring nodes mean, and how the structure can expand without memorizing exceptions.

Audit by default. Change files or public command paths only when the user explicitly asks for implementation.

## Preference model

Apply these preferences unless the project documents a stronger domain-specific rule:

1. **Canonical names use complete words.** Prefer `organizations`, `investors`, and `database` over `orgs`, `vcs`, and `db`. Keep common abbreviations as ergonomic aliases when useful; do not present them as canonical.
2. **One segment carries one concept.** Prefer `query connectors capacity` over `query connector-capacity`. A compound name usually hides a missing level.
3. **Hierarchy earns qualification.** Add a level when it distinguishes a durable subtype, view, target, or operation and gives future siblings somewhere logical to live.
4. **Siblings share an axis.** Children of one node should all be domains, views, operations, lifecycle stages, audiences, or another single kind of distinction. A mixed sibling set is the primary ontology smell.
5. **Nouns precede qualifiers; mutations end in verbs.** Prefer `hypotheses stale` and `person action set`. The path should narrow from broad concept to specific action.
6. **Bare parents have a useful default.** Let `query connectors` show the primary actionable view. Add `--all` or a child only for a materially different projection.
7. **Plurality communicates cardinality.** Use plural nouns for collections and singular nouns for one entity or mutation target. Apply the chosen policy consistently within a tree.
8. **Canonical structure and typing convenience are separate layers.** Preserve a clear full path, then add exact aliases or deterministic unique-prefix matching. Ambiguous prefixes fail with candidates. Typos suggest but do not execute automatically, especially for mutations.
9. **Bounded context beats grammatical purity.** Do not force every node under a generic verb when that obscures ownership. If `query` means world-model reads, application status such as `jobs` should remain outside it.
10. **One concept has one home.** Other paths point, alias, import, or delegate; they do not grow competing implementations or duplicated state.

These rules are preferences, not a demand for maximum depth. A one-word node is better when it is already precise and has no meaningful sibling distinction.

## Choose the mode

### Build from scratch

Start from user intent and domain vocabulary before naming directories or commands. Produce the smallest tree that handles current needs and has an obvious extension point for already-anticipated siblings.

### Audit an existing tree

Inventory the live structure, entrypoints, aliases, documentation, and call sites. Report the current ontology before proposing a replacement. Preserve behavior and compatibility unless the user approves a breaking migration.

## Workflow

### 1. Establish the boundary

Identify:

- Who uses the tree: humans, agents, scripts, libraries, or several audiences.
- Whether it represents domains, effects, artifacts, workflows, lifecycle, deployment, or navigation.
- Which names are public contracts and which are internal identifiers.
- Existing domain glossaries, architecture decisions, compatibility promises, and rejected designs.

Do not confuse implementation categories with user intent. Labels such as `views`, `helpers`, or `services` may be useful internally but often make poor public paths.

### 2. Inventory the actual tree

For command trees, capture:

- Visible commands at every level.
- Defaults and options on parent groups.
- Hidden aliases, abbreviations, prefix behavior, and typo handling.
- Side effects: read, local mutation, workflow, external mutation.
- Help text, examples, tests, scripts, and automation that call old paths.

For file trees, capture:

- Directories, representative files, entrypoints, indexes, and generated areas.
- Imports and references that reveal real ownership.
- Duplicate concepts, forwarding modules, suffix families such as `*_v2`, and miscellaneous buckets.
- Public package paths or links that make moves consequential.

Use the repository's native inventory tools. Inspect the rendered CLI help or actual filesystem, not only registration source.

### 3. Name the axis at every branch

Write a short label for what each level separates. Examples:

```text
query                 axis: world-model domain
  connectors          axis: connector projection
    capacity
    coverage
    offers

write                 axis: entity
  person              axis: owned sub-concept or mutation
    action            axis: mutation
      set
      clear
```

If one branch requires several axis labels joined by “and,” it probably mixes concepts. Either split it or explicitly justify the exception.

### 4. Run the ontology tests

Evaluate each branch with these tests:

- **Prediction:** Given one known path, can a newcomer guess where a sibling belongs?
- **Sibling axis:** Do siblings answer the same kind of question?
- **Read aloud:** Does the path read from broad concept to precise intent?
- **Vocabulary:** Are exact domain terms used consistently, without unexplained synonyms or abbreviations?
- **Compound:** Would splitting a hyphenated or suffixed name expose a useful hierarchy?
- **Default:** Is the bare parent useful, or merely another help screen?
- **Boundary:** Do read, mutation, workflow, and external effects live behind honest boundaries?
- **Depth:** Does each level add information? Collapse pass-through levels.
- **Collision:** Will aliases or prefixes become ambiguous as known siblings are added?
- **Ownership:** Is there one canonical home, with compatibility paths delegating to it?

Distinguish a structural defect from a taste preference. Rename only when the new shape improves prediction, ownership, safety, or extensibility.

### 5. Propose the canonical form

Show the proposed tree and a complete migration table:

| Current | Canonical | Compatibility | Reason |
|---|---|---|---|
| `query candidate-overlap` | `query connectors overlap` | hidden old alias | domain first; hierarchy replaces compound |
| `write person action-set` | `write person action set` | hidden old alias | owned concept before mutation |

State:

- Canonical full names.
- Defaults and `--all` behavior.
- Exact aliases and unique-prefix rules.
- Any intentional exception to the sibling axis.
- What is explicitly not being reorganized.

For a consequential public tree, get user approval on representative examples before implementing the entire migration.

### 6. Migrate without parallel implementations

When implementation is approved:

1. Register the canonical path as the only active implementation.
2. Point old paths at it as hidden compatibility aliases when breakage would be costly.
3. Keep fuzzy matching advisory; use only exact aliases and unique prefixes for execution.
4. Update help, documentation, examples, tests, automation, and generated templates.
5. Add deterministic coverage for the ontology when possible: every saved query has one canonical path, visible segments contain no banned abbreviations, or every workflow is mapped deliberately.
6. Record a removal condition for compatibility aliases rather than keeping them indefinitely by habit.

For file moves, use history-preserving moves, update imports and links, and leave forwarding files only when an external compatibility contract requires them.

### 7. Verify the rendered result

Verify behavior rather than source shape alone:

- Render every affected help level or list the final file tree.
- Exercise full names, aliases, unique prefixes, ambiguous prefixes, and typo suggestions.
- Confirm old compatibility paths delegate correctly and stay out of canonical help.
- Run tests, lint, type checks, link checks, and documentation-command validation relevant to the repository.
- Search current documentation for retired canonical forms. Exclude historical snapshots deliberately rather than rewriting history blindly.

## Output contract

For an audit, report:

1. **Conclusion** - whether the ontology is coherent and the main source of friction.
2. **Current axes** - what each level actually separates today.
3. **Findings** - evidence-backed inconsistencies, ordered by impact.
4. **Canonical proposal** - complete tree plus current-to-proposed mapping.
5. **Compatibility and safety** - aliases, ambiguity behavior, migration risks.
6. **Verification plan** - exact checks that prove the new organization landed.

For a build, finish with the implemented tree, compatibility behavior, verification evidence, and any intentionally deferred branches.
