# Workbench development and deployment tasks. Run `just` for grouped help.

# ── Quality ───────────────────────────────────────────────────────────────────

# Validate skills, local links, JSON, TOML, and shell syntax.
[group('quality')]
lint:
    ./bin/workbench lint

# Run the complete deterministic development gate.
[group('quality')]
check: test lint

# ── Testing ───────────────────────────────────────────────────────────────────

# Run deterministic unit tests with verbose output.
[group('testing')]
test:
    python3 -m unittest discover -s tests -v

# ── Deployment ────────────────────────────────────────────────────────────────

# Deploy canonical configuration. Example: `just sync codex --no-plugins`.
[group('deployment')]
sync *args:
    ./bin/workbench sync {{args}}

# Compare live configuration with canonical sources. Example: `just drift claude`.
[group('deployment')]
drift *args:
    ./bin/workbench check {{args}}

# ── Help (default) ────────────────────────────────────────────────────────────

# Show grouped Workbench development and deployment commands.
[default]
help:
    #!/usr/bin/env bash
    export JUST_LIST_HEADING=$'\e[1;38;2;230;57;86m workbench CLI\e[0m · dev tasks (cwd: repository root)\n'
    exec just --justfile "{{justfile()}}" --list --unsorted
