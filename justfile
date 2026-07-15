# Show available commands
@default:
    just --list --unsorted --list-heading $'\e[1;34m Available Commands:\e[0m\n'

# --- Quality ---

# Validate workbench sources
lint:
    ./bin/workbench lint

# Run deterministic tests and source validation
check: test lint

# --- Testing ---

# Run deterministic unit tests
test:
    python3 -m unittest discover -s tests -v

# --- Deployment ---

# Deploy canonical configuration to Claude Code and Codex
sync *args:
    ./bin/workbench sync {{args}}

# Compare deployed configuration with canonical sources
drift *args:
    ./bin/workbench check {{args}}
