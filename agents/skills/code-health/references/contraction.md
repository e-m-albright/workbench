# Contraction cycle

Use this composition when the mandate is to make an entire codebase materially smaller without turning it into dense, cryptic, or fragile code. It combines `prune` with `align` and `deepen`; it is not another lens.

## Objective

Minimize the **maintained semantic surface**: the code, interfaces, configuration, representations, and compatibility paths a maintainer must understand and keep consistent.

Raw line count is evidence, not the objective. Count maintained application code, tests, generated code, vendored code, migrations, configuration, and documentation separately. A reduction is honest when behavior or accidental complexity disappears. It is dishonest when complexity merely moves into metaprogramming, configuration, dependencies, compressed syntax, or missing tests.

## Scout before editing

Start with a read-only scout. Read the repository instructions, domain language, architecture decisions, current backlog, and working-tree state. Treat active overlapping work as occupied: defer that area rather than reviewing or rewriting a moving target.

Establish the repository's native gates and available dead-code, dependency, duplication, complexity, and coverage tools. Their findings are leads, not deletion proof; dynamic dispatch and public interfaces still require caller checks.

### 1. Find high-value contraction

Look beyond ordinary unused symbols:

- dead features, exports, flags, dependencies, and unreachable branches
- completed migrations, compatibility paths, legacy names, and one-time bootstrap code that still runs
- competing implementations or successive design/configuration layers where later declarations override earlier ones
- pass-through modules, wrappers, facades, and aliases whose deletion removes rather than redistributes complexity
- duplicated contract or schema representations that can be generated transparently from one canonical source
- hardcoded mutable state embedded in startup or connection paths, especially when it can overwrite supported mutations
- speculative seams with one adapter, generic engines with one real use, and configuration whose values never vary
- tests that exist only to preserve code now eligible for deletion; remove them with the retired behavior, never to improve the ratio

Confirm each candidate through call sites, runtime entry points, persisted-state compatibility, and the repository's actual operating model.

### 2. Find architectural contraction

After deletion candidates are known, look for changes that reduce what callers must know:

- replace shallow layers with a deep module around a real domain concept
- concentrate policy currently repeated across callers
- isolate effects when doing so makes the deterministic core smaller and easier to test
- replace copied or synchronized representations with one canonical model and a transparent generated projection
- dissolve miscellaneous modules by moving behavior to existing conceptual owners, deleting the facade rather than adding another one
- simplify persistence and query paths that duplicate canonical state in another runtime representation

Architectural improvement may temporarily add lines. Accept that only when the resulting interface, dependency graph, or number of maintained representations becomes materially smaller.

## Candidate report

Rank a short list rather than producing an exhaustive smell catalogue. For each candidate report:

- **Files** - the affected modules
- **Evidence** - concrete call sites, repeated declarations, tool output, or ownership conflict
- **Category** - contraction, architectural contraction, or both
- **Payoff** - estimated maintained lines and interfaces removed, expressed as a range when uncertain
- **Move** - the plain-English change, without prematurely designing every interface
- **Risk and proof** - behavior that could regress and the checks needed
- **Coordination** - whether current work, an ADR, or an external consumer blocks it

Also state what the tools did **not** find. A healthy codebase should not receive invented work merely to satisfy the exercise.

## Cycle and stopping rule

For approved candidates:

1. Delete obsolete behavior and compatibility first.
2. Align and deepen what remains.
3. Verify each reviewable slice with focused tests, then run the broad native gate once.
4. Report net maintained lines, interfaces, configuration, and dependencies removed; report test changes separately.
5. Ratchet only stable, objective wins. Keep structural judgment human-gated.

Stop when the remaining reductions would primarily:

- compress readable code
- weaken tests, types, security, or error handling
- merge unrelated domain concepts
- hide behavior in magic, generated machinery without a clear source, or new dependencies
- move complexity rather than remove it
- churn stable code for a negligible surface reduction

At that point the codebase has reached a local contraction limit. Continue only when product retirement or a new architectural decision changes the constraints.
