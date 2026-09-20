# Workbench development and deployment tasks. Run `just` for grouped help.

# ── Quality ───────────────────────────────────────────────────────────────────

# Validate skills, local links, JSON, TOML, and shell syntax.
[group('quality')]
lint:
    ./bin/workbench lint

# Ruff lint over the CLI sources.
[group('quality')]
lint-py:
    uv run --locked ruff check .

# Biome format for the TypeScript surface. `just fmt-ts check` verifies only.
[group('quality')]
fmt-ts mode='write':
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{mode}}" in
        write | all) pnpm exec biome format --write agents/pi/extensions tests vitest.config.ts ;;
        --check | check) pnpm exec biome format agents/pi/extensions tests vitest.config.ts ;;
        *)
            printf 'fmt-ts: unknown mode %q (try --check, check)\n' "{{mode}}" >&2
            exit 1
            ;;
    esac

# ShellCheck over every tracked shell script, including the extensionless bin/ CLIs.
[group('quality')]
lint-shell:
    git ls-files -z '*.sh' | xargs -0 shellcheck -S warning
    shellcheck -S warning bin/workbench

# Format Python sources. `just fmt --check` (or `just fmt check`) verifies only.
[group('quality')]
fmt mode='write':
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{mode}}" in
        write | all) uv run --locked ruff format . ;;
        --check | check) uv run --locked ruff format --check . ;;
        *)
            printf 'fmt: unknown mode %q (try --check, check)\n' "{{mode}}" >&2
            exit 1
            ;;
    esac

# Pyright typecheck.
[group('quality')]
typecheck:
    uv run --locked pyright

# Run the complete deterministic development gate.
[group('quality')]
check:
    just fmt --check
    just lint-py
    just typecheck
    just test
    just test-pi
    just typecheck-pi
    just lint
    just lint-shell
    just fmt-ts check
    just check-documents

# Print reproducible catalogue counts; add --include-untracked during a review.
[group('quality')]
catalogue *args:
    uv run --locked python scripts/catalogue.py {{args}}

# ── Testing ───────────────────────────────────────────────────────────────────

# Run deterministic unit tests. Example: `just test -k budget`.
[group('testing')]
test *args:
    uv run --locked pytest -v {{args}}

# Run Pi extension behavior tests on Node. Example: `just test-pi tests/pi-presets.test.ts`.
[group('testing')]
test-pi *args='tests/*.test.ts':
    pnpm exec vitest run {{args}}


# Typecheck Pi extensions against the installed Pi API; skips when Pi is absent.
[group('testing')]
typecheck-pi:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v pi >/dev/null 2>&1; then
        echo "typecheck-pi: pi CLI not found; skipping"
        exit 0
    fi
    resolved="$(readlink -f "$(command -v pi)")"
    # The package root is everything before /dist/ — robust to the CLI entry
    # moving deeper (0.82 shipped dist/cli.js; 0.84 ships dist/cli/...).
    pkg="${resolved%%/dist/*}"
    if [[ "$pkg" == "$resolved" ]]; then
        pkg="$(dirname "$(dirname "$resolved")")"
    fi
    deps="$pkg/node_modules"
    if [[ ! -d "$deps/typebox" ]]; then
        # Support inherited hoisted global npm layouts as well as nested installs.
        deps="$(dirname "$(dirname "$pkg")")"
    fi
    cfg="{{justfile_directory()}}/.pi-tsconfig.generated.json"
    trap 'rm -f "$cfg"' EXIT
    cat > "$cfg" <<EOF
    {
      "compilerOptions": {
        "noEmit": true,
        "strict": true,
        "skipLibCheck": true,
        "target": "es2022",
        "module": "esnext",
        "moduleResolution": "bundler",
        "typeRoots": ["$deps/@types"],
        "paths": {
          "@earendil-works/pi-coding-agent": ["$pkg/dist/index.d.ts"],
          "@earendil-works/*": ["$deps/@earendil-works/*/dist/index.d.ts"],
          "typebox": ["$deps/typebox/build/index.d.mts"]
        }
      },
      "include": ["{{justfile_directory()}}/agents/pi/extensions/*.ts"]
    }
    EOF
    pnpm exec tsc -p "$cfg"

# ── Documents ────────────────────────────────────────────────────────────────

# Render the reusable Notes-style call-script HTML template.
[group('documents')]
call-script-template output='artifacts/call-script-template':
    bash agents/templates/documents/render-examples.sh "{{output}}"

# Verify that the maintained document template renders as standalone HTML.
[group('documents')]
check-documents:
    #!/usr/bin/env bash
    set -euo pipefail
    output="$(mktemp -d)"
    trap 'find "$output" -depth -delete' EXIT
    bash agents/templates/documents/render-examples.sh "$output"
    test -s "$output/index.html"
    grep -q '<!doctype html>' "$output/index.html"

# ── Dependencies ──────────────────────────────────────────────────────────────

# Audit locked Python, development Node, and native sandbox dependencies.
[group('dependencies')]
audit:
    uv run --locked pip-audit --cache-dir tmp/pip-audit-cache
    pnpm audit
    npm --prefix agents/shared/sandbox audit --package-lock-only --ignore-scripts

# ── Deployment ────────────────────────────────────────────────────────────────

# Deploy canonical configuration. Example: `just sync codex --no-plugins`.
[group('deployment')]
sync *args:
    ./bin/workbench sync {{args}}

# Compare live configuration with canonical sources. Example: `just drift claude`.
[group('deployment')]
drift *args:
    ./bin/workbench drift {{args}}

# Sync then immediately verify: closes the deploy loop in one command.
[group('deployment')]
deploy *args:
    ./bin/workbench sync {{args}}
    ./bin/workbench drift {{args}}

# ── Help (default) ────────────────────────────────────────────────────────────

# Show grouped Workbench development and deployment commands.
[default]
help:
    #!/usr/bin/env bash
    export JUST_LIST_HEADING=$'\e[1;38;2;230;57;86m workbench CLI\e[0m · dev tasks (cwd: repository root)\n'
    exec just --justfile "{{justfile()}}" --list --unsorted
