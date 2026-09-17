---
name: release
description: Cut a release end to end — detect the versioning scheme, choose the bump, write a human changelog from git history, tag, and publish with gh. Use for "cut a release", "bump the version", "tag v1.2.3", or "draft release notes".
---

# Release

Cut a release deliberately: preflight, version, changelog, tag, publish. Dry-run everything before mutating anything.

## Preflight — abort on any failure

1. **Clean tree**: `git status --porcelain` returns nothing. Stash or commit first; never release uncommitted work.
2. **On the default branch** (or the project's designated release branch): `git branch --show-current`. If not, stop and ask.
3. **Up to date with remote**: `git fetch` then compare against `origin/<branch>`.
4. **CI green** on the release commit: `gh run list --branch <branch> --limit 5`. A red or still-running head commit blocks the release.
5. **Last release**: `git describe --tags --abbrev=0` (or `gh release list --limit 1`). If no tags exist, this is the first release — confirm the initial version with the user.

## Detect the versioning scheme

Look, in order, for the project's source of truth — there is usually exactly one:

- `package.json` `"version"` (npm — bump via `npm version <level> --no-git-tag-version` so tagging stays in your control)
- `pyproject.toml` `version` (or dynamic versioning like hatch-vcs/setuptools-scm — then the tag *is* the version; skip the file edit)
- `Cargo.toml` `[package] version`
- A `VERSION` file
- Tags only (no manifest) — the tag is the release

If several disagree, stop: that mismatch is a bug to fix before releasing. Match the existing tag format exactly (`v1.2.3` vs `1.2.3`).

## Choose the bump

Read the history since the last tag: `git log <last-tag>..HEAD --oneline`.

- Conventional commits present: `feat!:`/`BREAKING CHANGE` → major, `feat:` → minor, `fix:`/everything else → patch.
- No convention: read the actual changes and propose a bump with one-line reasoning; ask if it's ambiguous (e.g. a behavior change dressed as a fix).
- User named an exact version ("tag v1.2.3"): use it, but sanity-check it against the last tag (no downgrades, no skipped majors without cause).

## Write the changelog

From `git log <last-tag>..HEAD`, produce grouped, human-edited notes — never a raw commit dump:

- Group under **Breaking changes / Features / Fixes / Internal** (omit empty groups).
- Rewrite each entry as a user-facing sentence: what changed and why it matters, not the commit subject verbatim. Merge related commits into one line; drop pure noise (typo fixes in internal docs, CI churn).
- If the repo has a `CHANGELOG.md`, prepend the new section in its existing format. If not, the notes live in the GitHub release only — don't create a changelog file unasked.

Show the draft notes to the user before tagging. This is the highest-leverage review point.

## Dry run, then execute

Present the full plan first: current version → new version, files to be edited, tag name, target commit, release title. Get confirmation, then:

1. Edit the version file(s) and changelog; commit as `release: v<X.Y.Z>` (or the project's established release-commit style — check prior release commits).
2. Push, and re-check CI if the version commit triggers it.
3. `git tag -a v<X.Y.Z> -m "v<X.Y.Z>"` and `git push origin v<X.Y.Z>`.
4. `gh release create v<X.Y.Z> --title "v<X.Y.Z>" --notes-file <notes>` (use `--draft` if the user wants to review on GitHub first; `--generate-notes` only as a fallback when the curated notes were declined).

## After

- Verify: `gh release view v<X.Y.Z>` and confirm any publish workflow (npm/PyPI/crates) triggered by the tag went green via `gh run list`.
- If anything failed mid-sequence, report exactly which steps completed — never silently re-run tag pushes or deletes. Fixing a bad tag is a user decision.
