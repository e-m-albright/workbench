#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
output_dir="${1:-$repo_root/artifacts/call-script-template}"
source="${2:-$script_dir/examples/call-script.md}"

if ! command -v pandoc >/dev/null 2>&1; then
  printf 'pandoc is required to render the call-script template.\n' >&2
  exit 1
fi

mkdir -p "$output_dir"

pandoc "$source" \
  --from='gfm+raw_html' \
  --to=html5 \
  --standalone \
  --section-divs \
  --toc \
  --toc-depth=2 \
  --template="$script_dir/call-script.html" \
  --output="$output_dir/index.html"

printf 'Rendered call-script template: %s/index.html\n' "$output_dir"
