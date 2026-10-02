#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
output_dir="${1:-$repo_root/artifacts/reading-template}"
source="${2:-$script_dir/examples/reading.md}"

if ! command -v pandoc >/dev/null 2>&1; then
  printf 'pandoc is required to render the reading template.\n' >&2
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
  --template="$script_dir/reading.html" \
  --lua-filter="$script_dir/reading.lua" \
  --output="$output_dir/index.html"

printf 'Rendered reading template: %s/index.html\n' "$output_dir"
