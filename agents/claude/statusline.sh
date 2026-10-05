#!/usr/bin/env bash
# Claude Code's compact shared statusline:
#
#   claude <cwd> (<git state>) │ hosted > restricted/unrestricted
#   ctx n% │ 5h n% left │ 1w n% left │ <model>
#
# Reads Claude's statusline JSON payload on stdin. Set NO_COLOR=1 to disable
# ANSI colors. Schema: https://code.claude.com/docs/en/statusline.md

# No -e: the statusline must render even when a probe (git, jq) fails.
set -uo pipefail

input="$(cat)"

j() {
    printf '%s' "$input" | jq -r "$1 // empty" 2>/dev/null
}

# Preserve literal false; jq's // operator treats it as absent.
jb() {
    printf '%s' "$input" | jq -r "if $1 == null then empty else ($1 | tostring) end" 2>/dev/null
}

if [[ -z "${NO_COLOR:-}" ]]; then
    # Palette contract: these RGB triples are the hex palette in
    # agents/pi/extensions/footer.ts; a pytest asserts they stay equal.
    R=$'\033[0m'
    DIM=$'\033[2m'
    NOTE=$'\033[38;2;128;166;173m'
    WARN=$'\033[38;2;217;145;61m'
    DANGER=$'\033[38;2;217;120;77m'
    GOLD=$'\033[38;2;211;177;95m'
    SAGE=$'\033[38;2;143;168;121m'
    BLUE=$'\033[38;2;129;162;190m'
    HOSTED=$'\033[38;2;240;198;116m'
    UNRESTRICTED=$'\033[1;38;2;255;80;80m'
else
    R='' DIM='' NOTE='' WARN='' DANGER='' GOLD='' SAGE=''
    BLUE='' HOSTED='' UNRESTRICTED=''
fi

ramp() {
    local pct_int
    pct_int=$(printf '%.0f' "${1:-0}")
    if   (( pct_int >= 90 )); then printf '%s' "$DANGER"
    elif (( pct_int >= 75 )); then printf '%s' "$WARN"
    elif (( pct_int >= 55 )); then printf '%s' "$GOLD"
    else printf '%s' "$SAGE"
    fi
}

home="${WORKBENCH_HOST_HOME:-${HOME:-}}"
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
fmt_tokens() {
    local n="${1:-0}"
    if (( n >= 1000000 )); then printf '%d.%dM' $(( n / 1000000 )) $(( (n % 1000000) / 100000 ))
    elif (( n >= 1000 )); then printf '%dk' $(( (n + 500) / 1000 ))
    else printf '%d' "$n"
    fi
}

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
ctx_size=$(j '.context_window.context_window_size')
ctx_tokens=$(j '[.context_window.total_input_tokens, .context_window.total_output_tokens] | map(select(. != null)) | if length == 0 then null else add end')
cost_usd=$(j '.cost.total_cost_usd')
cache_hit=$(j '.prompt_cache.hit_ratio')
cache_warm=$(jb '.prompt_cache.warm')
effort=$(j '.effort.level')
fast_mode=$(jb '.fast_mode')
thinking=$(jb '.thinking.enabled')
spend_used=$(j '.rate_limits.spend_limit.used_percentage')
spend_reset=$(j '.rate_limits.spend_limit.resets_at')
five_used=$(j '.rate_limits.five_hour.used_percentage')
five_reset=$(j '.rate_limits.five_hour.resets_at')
seven_used=$(j '.rate_limits.seven_day.used_percentage')
seven_reset=$(j '.rate_limits.seven_day.resets_at')
pr_number=$(j '.pr.number')
pr_state=$(j '.pr.review_state')

sep="${DIM} │ ${R}"
out="${NOTE}claude${R} ${DIM}$(short_path "${cwd:-?}")${R}"
git_text=$(git_segment "$cwd" "$worktree")
[[ -n "$git_text" ]] && out="${out} ${git_text}"
pr_text=$(pr_segment "$pr_number" "$pr_state")
[[ -n "$pr_text" ]] && out="${out} ${pr_text}"

location="${WORKBENCH_AGENT_LOCATION:-hosted}"
authority="${WORKBENCH_AGENT_AUTHORITY:-unrestricted}"
location_label=cloud
location_color="$HOSTED"
if [[ "$location" == local ]]; then
    location_label=local
    location_color="$BLUE"
fi
authority_label=host
authority_color="$UNRESTRICTED"
if [[ "$authority" == restricted ]]; then
    authority_label=repo
    authority_color="$BLUE"
fi
out="${out}${sep}${location_color}${location_label}${R} > ${authority_color}${authority_label}${R}"
printf '%s\n' "$out"
out=""

if [[ -n "$ctx_pct" ]]; then
    out="$(ramp "$ctx_pct")ctx $(printf '%.0f%%' "$ctx_pct")"
    [[ -n "$ctx_tokens" ]] && out="${out} $(fmt_tokens "$ctx_tokens")"
    [[ -n "$ctx_size" ]] && out="${out}/$(fmt_tokens "$ctx_size")"
    out="${out}${R}"
fi
if [[ -n "$five_used" ]]; then
    remaining=$(jq -nr --argjson used "$five_used" '100 - $used | [0, .] | max | [100, .] | min')
    out="${out}${out:+$sep}$(ramp "$five_used")5h $(printf '%.0f%%' "$remaining") left$(eta "$five_reset")${R}"
fi
if [[ -n "$seven_used" ]]; then
    remaining=$(jq -nr --argjson used "$seven_used" '100 - $used | [0, .] | max | [100, .] | min')
    out="${out}${out:+$sep}$(ramp "$seven_used")1w $(printf '%.0f%%' "$remaining") left$(eta "$seven_reset")${R}"
fi
if [[ -n "$spend_used" ]]; then
    out="${out}${out:+$sep}$(ramp "$spend_used")spend $(printf '%.0f%%' "$spend_used") used$(eta "$spend_reset")${R}"
fi
if [[ -n "$cost_usd" ]] && jq -en --argjson usd "$cost_usd" '$usd >= 0.01' >/dev/null; then
    out="${out}${out:+$sep}${NOTE}~$(printf '$%.2f' "$cost_usd")${R}"
fi
if [[ "$cache_warm" == false ]]; then
    out="${out}${out:+$sep}${WARN}cache cold${R}"
elif [[ -n "$cache_hit" ]]; then
    hit_pct=$(jq -nr --argjson ratio "$cache_hit" '$ratio * 100 | [0, .] | max | [100, .] | min')
    out="${out}${out:+$sep}$(ramp "$(jq -nr --argjson hit "$hit_pct" '100 - $hit')")cache $(printf '%.0f%%' "$hit_pct")${R}"
fi
if [[ -n "$model" ]]; then
    out="${out}${out:+$sep}${NOTE}${model}${R}"
    [[ -n "$effort" ]] && out="${out} ${DIM}${effort}${R}"
    [[ "$fast_mode" == true ]] && out="${out} ${GOLD}fast${R}"
    [[ "$thinking" == false ]] && out="${out} ${WARN}think off${R}"
fi

printf '%s\n' "$out"
