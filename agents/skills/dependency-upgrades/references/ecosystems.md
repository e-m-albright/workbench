# Ecosystem Commands

Use only the sections that match the repository. Read the repository task runner first; an established recipe takes precedence.

## Node and browser tooling

Determine ownership from `packageManager`, the lockfile, and workspace files.

### pnpm

```bash
pnpm --version
pnpm outdated --recursive
pnpm audit
pnpm peers check
```

Apply compatible updates with `pnpm update`, or explicitly reviewed majors with `pnpm update --latest`. Review `pnpm-workspace.yaml`, build-script approvals, minimum-release-age policy, peer output, and the lockfile diff. Use the version declared by the repository rather than Corepack or an ambient fallback.

### npm, Yarn, and Bun

```bash
npm outdated && npm audit
yarn outdated
bun outdated && bun audit
```

Use the matching update and frozen-install commands documented by the repository. Do not generate a second lockfile with another package manager.

### Deno

```bash
deno outdated
deno audit
deno task check
```

Keep Deno as owner when the repository uses `deno.json` and `deno.lock`.

For browser-facing majors, inspect framework adapters, compiler peers, browser support, test-runner browsers, and production-build behavior together.

## Python

For uv-owned projects:

```bash
uv --version
uv lock --check
uv tree --outdated
uv run pip-audit
```

Use `uv lock --upgrade-package <name>` for a targeted update or `uv lock --upgrade` for an approved refresh. Keep supported Python ranges and platform markers intact.

For requirements-only environments, use the environment’s documented installer plus:

```bash
python -m pip list --outdated
python -m pip_audit
```

## Go

```bash
go list -m -u all
govulncheck ./...
go test ./...
```

Use `go get module@version` for reviewed bumps and `go mod tidy` only when the resulting manifest changes are understood.

## Rust

```bash
cargo outdated
cargo audit
cargo test
```

Inspect feature changes and minimum supported Rust version before taking majors. Keep `Cargo.toml` and `Cargo.lock` changes in the same slice.

## GitHub Actions

Inspect every `uses:` reference. Prefer immutable commit pins when repository policy requires them, preserve the readable version comment, and verify new major permissions and runtime changes from the action’s official release notes.

## Host tools

Inventory without mutation:

```bash
brew outdated
brew outdated --cask
```

Apply only with authority for host package installation:

```bash
brew upgrade <formula>
brew upgrade --cask <cask>
```

After upgrading a daemon, desktop application, runtime, or package manager, verify the live binary version and service topology rather than trusting the package receipt. Preserve the declared owner: for example, fnm owns Node versions, uv owns Python project resolution, and Homebrew owns installed formulae and casks.

## Release evidence

Prefer sources in this order:

1. Official migration guide or release announcement.
2. Official changelog or repository release.
3. Package registry metadata and peer declarations.
4. Advisory database entry.

Use secondary summaries only for discovery. Link the primary evidence that informed a consequential decision in the final report.
