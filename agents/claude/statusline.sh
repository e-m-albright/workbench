#!/usr/bin/env bash
# Claude Code's compact shared statusline:
#
#   claude <cwd> (<branch> [wt:name] [!n] [+n] [*n] [?n] [⇡n] [⇣n]) [#PR state] · ctx: n% · 5h: n% (resets ..) · 7d: n% (resets ..) · <model>
#
# Reads Claude's statusline JSON payload on stdin. Set NO_COLOR=1 to disable
# ANSI colors. Schema: https://code.claude.com/docs/en/statusline.md

set -uo pipefail

input="$(cat)"

j() {
    printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
}

if [[ -z "${NO_COLOR:-}" ]]; then
    R=$'\033[0m'
    DIM=$'\033[2m'
    NOTE=$'\033[38;2;128;166;173m'
    WARN=$'\033[38;2;217;145;61m'
    DANGER=$'\033[38;2;217;120;77m'
    AMBER_HOT=$'\033[38;2;217;120;77m'
    AMBER=$'\033[38;2;217;145;61m'
    GOLD=$'\033[38;2;211;177;95m'
    SAGE=$'\033[38;2;143;168;121m'
else
    R='' DIM='' NOTE='' WARN='' DANGER='' AMBER_HOT='' AMBER='' GOLD='' SAGE=''
fi

ramp() {
    local pct_int
    pct_int=$(printf '%.0f' "${1:-0}")
    if   (( pct_int >= 90 )); then printf '%s' "$AMBER_HOT"
    elif (( pct_int >= 75 )); then printf '%s' "$AMBER"
    elif (( pct_int >= 55 )); then printf '%s' "$GOLD"
    else printf '%s' "$SAGE"
    fi
}

home="${HOME:-}"
short_path() {
    local path="$1"
    if [[ -n "$home" && "$path" == "$home"* ]]; then
        printf '~%s' "${path#"$home"}"
    else
        printf '%s' "$path"
    fi
}

count_git_porcelain() {
    local staged=0 unstaged=0 untracked=0 conflicts=0 line status index worktree
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        status="${line:0:2}"
        index="${status:0:1}"
        worktree="${status:1:1}"
        if [[ "$status" == "??" ]]; then
            untracked=$((untracked + 1))
            continue
        fi
        case "$status" in
            DD|AU|UD|UA|DU|AA|UU) conflicts=$((conflicts + 1)); continue ;;
        esac
        [[ -n "$index" && "$index" != " " && "$index" != "?" ]] && staged=$((staged + 1))
        [[ -n "$worktree" && "$worktree" != " " && "$worktree" != "?" ]] && unstaged=$((unstaged + 1))
    done
    printf '%s %s %s %s' "$staged" "$unstaged" "$untracked" "$conflicts"
}

git_segment() {
    local cwd="$1" worktree_name="$2"
    [[ -z "$cwd" ]] && return 0
    cd "$cwd" 2>/dev/null || return 0
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0

    local branch counts staged unstaged untracked conflicts ahead=0 behind=0 upstream_counts parts=()
    branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || printf 'detached')

    counts=$(git --no-optional-locks status --porcelain 2>/dev/null | count_git_porcelain)
    read -r staged unstaged untracked conflicts <<< "$counts"
    upstream_counts=$(git rev-list --left-right --count 'HEAD...@{u}' 2>/dev/null || true)
    if [[ -n "$upstream_counts" ]]; then
        read -r ahead behind <<< "$upstream_counts"
    fi

    parts+=("$branch")
    [[ -n "${worktree_name:-}" ]] && parts+=("${NOTE}wt:${worktree_name}${R}")
    (( conflicts > 0 )) && parts+=("${DANGER}!${conflicts}${R}")
    (( staged > 0 )) && parts+=("${WARN}+${staged}${R}")
    (( unstaged > 0 )) && parts+=("${WARN}*${unstaged}${R}")
    (( untracked > 0 )) && parts+=("${WARN}?${untracked}${R}")
    (( ahead > 0 )) && parts+=("${NOTE}⇡${ahead}${R}")
    (( behind > 0 )) && parts+=("${WARN}⇣${behind}${R}")
    if (( ${#parts[@]} == 1 )); then
        parts+=("${SAGE}✓${R}")
    fi

    local IFS=' '
    printf '%s%s%s' "${DIM}(" "${parts[*]}" ")${R}"
}

# Compact time-until-reset for a rate-limit window, e.g. (resets 1h) / (resets 3d).
eta() {
    local resets_at="$1" now remaining
    [[ -z "$resets_at" ]] && return 0
    now=$(date +%s)
    remaining=$(( resets_at - now ))
    (( remaining <= 0 )) && return 0
    if   (( remaining >= 172800 )); then printf ' (resets %dd)' $(( remaining / 86400 ))
    elif (( remaining >= 3600 ));   then printf ' (resets %dh)' $(( remaining / 3600 ))
    else printf ' (resets %dm)' $(( remaining / 60 ))
    fi
}

pr_segment() {
    local number="$1" state="$2" color glyph
    [[ -z "$number" ]] && return 0
    case "$state" in
        approved)          color="$SAGE"   glyph='✓' ;;
        changes_requested) color="$DANGER" glyph='✗' ;;
        draft)             color="$DIM"    glyph='◌' ;;
        *)                 color="$NOTE"   glyph='○' ;;
    esac
    printf '%s#%s%s%s' "$color" "$number" "$glyph" "$R"
}

model=$(j '.model.display_name')
cwd=$(j '.workspace.current_dir')
worktree=$(j '.workspace.git_worktree')
ctx_pct=$(j '.context_window.used_percentage')
five_used=$(j '.rate_limits.five_hour.used_percentage')
five_reset=$(j '.rate_limits.five_hour.resets_at')
seven_used=$(j '.rate_limits.seven_day.used_percentage')
seven_reset=$(j '.rate_limits.seven_day.resets_at')
pr_number=$(j '.pr.number')
pr_state=$(j '.pr.review_state')

sep="${DIM} · ${R}"
out="${NOTE}claude${R} ${DIM}$(short_path "${cwd:-?}")${R}"
git_text=$(git_segment "$cwd" "$worktree")
[[ -n "$git_text" ]] && out="${out} ${git_text}"
pr_text=$(pr_segment "$pr_number" "$pr_state")
[[ -n "$pr_text" ]] && out="${out} ${pr_text}"

if [[ -n "$ctx_pct" ]]; then
    out="${out}${sep}$(ramp "$ctx_pct")ctx: $(printf '%.0f%%' "$ctx_pct")${R}"
fi
if [[ -n "$five_used" ]]; then
    out="${out}${sep}$(ramp "$five_used")5h: $(printf '%.0f%%' "$five_used")$(eta "$five_reset")${R}"
fi
if [[ -n "$seven_used" ]]; then
    out="${out}${sep}$(ramp "$seven_used")7d: $(printf '%.0f%%' "$seven_used")$(eta "$seven_reset")${R}"
fi
if [[ -n "$model" ]]; then
    out="${out}${sep}${DIM}${model}${R}"
fi

printf '%s\n' "$out"
