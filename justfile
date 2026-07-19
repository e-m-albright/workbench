# Workbench development and deployment tasks. Run `just` for grouped help.

# ── Quality ───────────────────────────────────────────────────────────────────

# Validate skills, local links, JSON, TOML, and shell syntax.
[group('quality')]
lint:
    ./bin/workbench lint

# Ruff lint over the CLI sources.
[group('quality')]
lint-py:
    uv run ruff check .

# Format Python sources. `just fmt --check` (or `just fmt check`) verifies only.
[group('quality')]
fmt mode='write':
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{mode}}" in
        write | all) uv run ruff format . ;;
        --check | check) uv run ruff format --check . ;;
        *)
            printf 'fmt: unknown mode %q (try --check, check)\n' "{{mode}}" >&2
            exit 1
            ;;
    esac

# Pyright typecheck.
[group('quality')]
typecheck:
    uv run pyright

# Run the complete deterministic development gate.
[group('quality')]
check:
    just fmt --check
    just lint-py
    just typecheck
    just test
    just lint

# ── Testing ───────────────────────────────────────────────────────────────────

# Run deterministic unit tests with verbose output.
[group('testing')]
test:
    uv run pytest -v

# ── Dependencies ──────────────────────────────────────────────────────────────

# pip-audit dependency vulnerabilities.
[group('dependencies')]
audit:
    uv run pip-audit

# ── Deployment ────────────────────────────────────────────────────────────────

# Deploy canonical configuration. Example: `just sync codex --no-plugins`.
[group('deployment')]
sync *args:
    ./bin/workbench sync {{args}}

# Compare live configuration with canonical sources. Example: `just drift claude`.
[group('deployment')]
drift *args:
    ./bin/workbench drift {{args}}

# ── Help (default) ────────────────────────────────────────────────────────────

# Show grouped Workbench development and deployment commands.
[default]
help:
    #!/usr/bin/env bash
    export JUST_LIST_HEADING=$'\e[1;38;2;230;57;86m workbench CLI\e[0m · dev tasks (cwd: repository root)\n'
    exec just --justfile "{{justfile()}}" --list --unsorted
