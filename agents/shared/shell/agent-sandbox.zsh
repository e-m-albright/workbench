#!/bin/zsh -f
# Standalone interface for the same managed shortcut boundary.
set -eu
vendor=${1:?vendor required}
location=${2:?location required}
authority=${3:?authority required}
shift 3
case "$vendor:$location:$authority" in
    pi:hosted:managed|claude:hosted:managed|codex:hosted:managed|antigravity:hosted:managed) ;;
    *) print -u2 'Retired mode; use co, cc, p, or agy for Workbench; full vendor names for native'; exit 2 ;;
esac
exec /usr/bin/python3 -I -S "$HOME/.local/share/workbench/shell/native-sandbox.py" \
    "$vendor" "$location" "$authority" "$@"
