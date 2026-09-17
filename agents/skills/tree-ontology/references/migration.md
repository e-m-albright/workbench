# Migrating a tree

Executing a rename or a bulk move. The mechanical import rewrite is the easy half and the half everyone plans for; these are the parts that actually break.

## Before you move

**Claim an exclusive window.** A bulk move conflicts violently with any concurrent editor, and the conflict is silent: you inventory 70 files, another session deletes one, and your move script fails partway with half the tree relocated. Re-inventory immediately before executing, not from a listing taken earlier in the session, and confirm no other agent or editor is working in the tree.

**Give the address one home first.** A node is expensive to move in proportion to how many places know its address. When several modules each hard-code the same path prefix, moving it is a repo-wide sweep; when one module owns it, the move is one edit. If the reference count is large, centralizing the address is a separate, safe, valuable change that should land before the move — and it is worth doing even if the move never happens.

**Commit and push first.** The working tree is the undo buffer.

## The reference shapes a move breaks

Rewriting `package.module` dotted paths catches maybe half of what a move breaks. Walk this list explicitly; each shape needs its own search.

| Shape | Example | Why grep for the dotted form misses it |
|---|---|---|
| Dotted module paths | `from pkg.old import x` | caught by the obvious rewrite |
| Aliased and parenthesized imports | `from pkg import (a as b, c)` | needs an AST-aware rewrite to preserve bindings, not a regex |
| Path-shaped strings in config | `per-file-ignores`, type-checker `strict` lists, secret-scanner allowlists | slash-separated, so a dot-separated search never sees them |
| Module-as-command invocations | `python -m pkg.old` in task runners, CI, git hooks, service definitions | lives outside the language's source tree |
| Paths derived from `__file__` | `Path(__file__).parents[1]` | silently resolves to the wrong directory at a new depth; nothing errors, the app just reads the wrong place |
| Test doubles addressed by string | `monkeypatch.setattr("pkg.old.CONST", ...)` | a string literal, invisible to import analysis |
| Packaging entry points | `console_scripts`, service manifests | breaks only on reinstall, long after the change |
| Prose references | docs, agent instructions, runbooks | some are executable instructions that fail at the worst moment |

Two of these deserve extra attention because they fail quietly rather than loudly:

**Paths anchored on a parent hop count.** `parents[1]` encodes the module's depth. Re-anchor on a named landmark — search upward for the package root by name — so a future move cannot repoint the application without any test failing.

**Config allowlists scoped by exact path.** A secret scanner or lint exemption keyed to `src/thing.py` stops applying the moment the file moves, and the result is a gate that suddenly fails on code that did not change. Make the pattern tolerate a directory prefix.

## While you move

Use history-preserving moves so the diff reads as motion. Verify afterwards that the tool actually recorded renames rather than delete-plus-add; if it did not, the change is unreviewable.

Keep the move commit free of logic changes. If a genuine fix is needed to make things pass, land it separately — a diff that is 95% motion and 5% behavior hides the 5%.

**A reorganization can convert a tolerated violation into a hard failure.** An
upward dependency that a codebase has lived with often survives only because
import order happened to resolve it. Regrouping files changes that order — and a
latent layering violation becomes a circular import. This is the tree telling the
truth rather than a new bug: fix the coupling, or remove whatever amplifies it,
and note that a package `__init__` which eagerly re-exports from a large sibling
is the usual amplifier, since it turns importing any one module into importing
all of them.

**Expect one collision class the rewrite cannot see:** a package `__init__` that re-exports a symbol sharing a name with a sibling module. The symbol wins, the module becomes unreachable, and the errors appear far from the cause. If a module and an exported name collide, rename the module to something the package does not export.

## When a split is blocked by a test seam

Before splitting a large module, check what its tests reach into. A module-level
global that tests monkeypatch — a repository root, a clock, a config handle — is
a seam the whole suite is wired to. Moving functions that read it into sibling
modules breaks every patch at once, and the tempting fix (importing the global
back across modules) rebuilds the coupling the split was meant to remove.

The real fix is to pass that state explicitly, through the context object the
functions already share, and to update the patches in the same change. That is a
behavior-risky refactor in its own right — size it separately, and do not smuggle
it inside a reorganization. Finding the seam is a reason to stop and re-scope,
not a detail to work around.

## Retiring the old names

Where the project keeps a tripwire for retired terminology, only names that **changed** need entries. A node that moved but kept its basename still reads true in prose and still resolves wherever resolution is by basename. Applying this distinction keeps a retirement list proportionate — dozens of entries rather than hundreds — and keeps it meaningful.

## Verifying

Source-level checks are necessary and not sufficient. Type checks and unit tests pass happily while an application reads from the wrong directory.

- Run the linter, formatter, type checker, and full test suite.
- Exercise every entry point the project actually ships, including each `python -m` style invocation used by task runners, hooks, CI, and scheduled services.
- Run the real application and confirm it produces real data, not just that it imports.
- Restart long-running services. A daemon started before the move holds the old modules in memory; it keeps serving until restarted, then either recovers or reveals a genuine break. Distinguish the two before concluding anything from its responses.
- Search the repository for every retired form, excluding history deliberately rather than rewriting it.
- Rewrite any hand-maintained structure listing to describe directories rather than enumerate files. A per-file listing has no mechanism keeping it true and will drift; that drift is often what motivated the audit in the first place.
