#!/usr/bin/env bash
# Block edits/writes to sensitive files (credentials, private keys, env secrets).
# Vendor-agnostic: reads the target path from whichever JSON key the harness uses
# (Claude/Codex: .tool_input.file_path · Cursor: .filePath / .file_path).
# Exit 2 with a stderr message to BLOCK; exit 0 to allow.
#
# Deployed verbatim to every hook-capable vendor so the safety contract is uniform.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
    printf 'BLOCK: jq is required by the workbench sensitive-file guard and is not on PATH.\n' >&2
    exit 2
fi

INPUT=$(cat 2>/dev/null || true)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .filePath // .file_path // empty' 2>/dev/null || true)
[[ -z "$FILE" ]] && exit 0

# Match on the lowercased basename so a bare `.env` (no leading dir) is caught
# — the old */.env globs required a slash and silently allowed `.env` and
# `.env.local`, the most common secret files — and so case variants (`.ENV`,
# `secrets.JSON`) can't dodge the guard on case-insensitive filesystems.
# Templates (.env.example) and *.pub public keys are explicitly allowed.
# Vector contract: tests/test_workbench.py (guard hook tests).
base=$(printf '%s' "${FILE##*/}" | tr '[:upper:]' '[:lower:]')
deny=""
case "$base" in
    .env.example | .env.sample | .env.template | .env.dist | *.pub) ;; # safe templates / public keys
    .env | .env.* | *.env | *credentials* | *secrets.json | *secrets.yaml | *secrets.yml) deny=1 ;;
    id_rsa | id_dsa | id_ecdsa | id_ed25519 | id_rsa.* | id_dsa.* | id_ecdsa.* | id_ed25519.*) deny=1 ;;
    *.pem | *.p12 | *.pfx | *.key | *.keystore | *.jks | .netrc | .pgpass | .npmrc | .pypirc) deny=1 ;;
    # Cloud / OAuth credential files common in 2026 agent workflows.
    *service-account*.json | *service_account*.json | token.json | *oauth*token* | gha-creds-*.json) deny=1 ;;
esac

if [[ -n "$deny" ]]; then
    printf 'BLOCK: %s is a sensitive file — edit it manually.\n' "$FILE" >&2
    printf 'Blocked by the workbench sensitive-file guard.\n' >&2
    exit 2
fi

exit 0
