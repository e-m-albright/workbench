#!/usr/bin/env bash
# Block destructive shell/git commands and hook/signing bypasses.
# Vendor-agnostic: reads the command from whichever JSON key the harness uses
# (Claude/Codex PreToolUse: .tool_input.command · Cursor beforeShellExecution: .command).
# Exit 2 with a stderr message to BLOCK; exit 0 to allow.
#
# Policy aligns with the canonical workbench rules:
#   - Never run destructive git operations unless explicitly authorized.
#   - Never skip hooks (--no-verify) or bypass signing.
# Deployed verbatim to every hook-capable vendor so the safety contract is uniform.
#
# This is a friction layer, not a security boundary. The command is split into
# simple commands with shell quoting respected, and each rule applies only where
# its word is the command being run, so text inside quotes, grep patterns, and
# heredocs fed to non-shell programs does not trigger it. Command and process
# substitutions, `sh -c` strings, and `find -exec` commands are inspected as
# commands. Code run by an interpreter (python -c, node -e) is not inspected;
# the OS sandbox is the hard boundary. Any internal failure blocks.

set -Eeuo pipefail
set -f
trap 'printf "BLOCK: the workbench destructive-command guard failed unexpectedly.\n" >&2; exit 2' ERR

if ! command -v jq >/dev/null 2>&1; then
    printf 'BLOCK: jq is required by the workbench destructive-command guard and is not on PATH.\n' >&2
    exit 2
fi

INPUT=$(cat 2>/dev/null || true)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // .command // empty' 2>/dev/null || true)
[[ -z "$CMD" ]] && exit 0
DIR=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)
[[ -n "$DIR" ]] || DIR=$PWD

block() {
    local reason="$1"
    {
        printf 'BLOCK: %s\n' "$reason"
        printf 'Command: %s\n' "$CMD"
        printf '\nBlocked by the workbench destructive-command guard.\n'
        printf 'If genuinely needed, the user must authorize this specific command explicitly.\n'
    } >&2
    exit 2
}

US=$'\037'
SUBST=__WB_SUBST__

# Print one line per simple command, words separated by US, quotes removed.
# Substitutions are replaced by $SUBST in their word and printed as their own
# commands. Heredoc bodies are dropped unless a shell on that line reads them;
# unquoted bodies still contribute their substitutions.
TOKENIZER='
function push(text) { q[nq++] = text }
function word_end() { if (started) { seg = seg (n ? US : "") w; n++ } w = ""; started = 0 }
function seg_end() { word_end(); if (n) print seg; seg = ""; n = 0 }
function close_paren(s, i,   depth, c, j, L) {
    L = length(s); depth = 1
    for (; i <= L; i++) {
        c = substr(s, i, 1)
        if (c == "\\") { i++; continue }
        if (c == "\047") { j = index(substr(s, i + 1), "\047"); if (j == 0) return L + 1; i += j; continue }
        if (c == "(") depth++
        else if (c == ")") { depth--; if (depth == 0) return i }
    }
    return L + 1
}
function close_tick(s, i,   c, L) {
    L = length(s)
    for (; i <= L; i++) { c = substr(s, i, 1); if (c == "\\") { i++; continue } if (c == "`") return i }
    return L + 1
}
function subs_only(s,   L, i, c, j) {
    L = length(s)
    for (i = 1; i <= L; i++) {
        c = substr(s, i, 1)
        if (c == "\\") { i++; continue }
        if (c == "$" && substr(s, i + 1, 1) == "(" && substr(s, i + 2, 1) != "(") {
            j = close_paren(s, i + 2); push(substr(s, i + 2, j - i - 2)); i = j
        } else if (c == "`") { j = close_tick(s, i + 1); push(substr(s, i + 1, j - i - 1)); i = j }
    }
}
function parse(s,   L, i, c, nx, state, j, k, d, strip, quoted, delim, line, m, body, nh, hdel, hq, hs, shell, start) {
    L = length(s); state = 0; w = ""; started = 0; seg = ""; n = 0; nh = 0; start = 1
    for (i = 1; i <= L; i++) {
        c = substr(s, i, 1)
        if (state == 1) { if (c == "\047") state = 0; else w = w c; continue }
        if (state == 2) {
            if (c == "\"") { state = 0; continue }
            if (c == "\\") {
                nx = substr(s, i + 1, 1)
                if (nx == "\n") { i++; continue }
                if (nx == "$" || nx == "`" || nx == "\"" || nx == "\\") { w = w nx; i++; continue }
                w = w c; continue
            }
            if (c == "$" && substr(s, i + 1, 1) == "(" && substr(s, i + 2, 1) != "(") {
                j = close_paren(s, i + 2); push(substr(s, i + 2, j - i - 2)); w = w SUBST; i = j; continue
            }
            if (c == "`") { j = close_tick(s, i + 1); push(substr(s, i + 1, j - i - 1)); w = w SUBST; i = j; continue }
            w = w c; continue
        }
        if (c == "\\") { nx = substr(s, i + 1, 1); i++; if (nx == "\n") continue; w = w nx; started = 1; continue }
        if (c == "\047") { state = 1; started = 1; continue }
        if (c == "\"") { state = 2; started = 1; continue }
        if (c == "#" && !started) { while (i < L && substr(s, i + 1, 1) != "\n") i++; continue }
        if (c == " " || c == "\t") { word_end(); continue }
        if (c == "$" && substr(s, i + 1, 1) == "(" && substr(s, i + 2, 1) != "(") {
            j = close_paren(s, i + 2); push(substr(s, i + 2, j - i - 2)); w = w SUBST; started = 1; i = j; continue
        }
        if (c == "`") { j = close_tick(s, i + 1); push(substr(s, i + 1, j - i - 1)); w = w SUBST; started = 1; i = j; continue }
        if ((c == "<" || c == ">") && substr(s, i + 1, 1) == "(") {
            word_end(); j = close_paren(s, i + 2); push(substr(s, i + 2, j - i - 2)); i = j; continue
        }
        if (c == "<" && substr(s, i + 1, 2) == "<<") { word_end(); i += 2; continue }
        if (c == "<" && substr(s, i + 1, 1) == "<") {
            word_end(); i += 2; strip = 0
            if (substr(s, i, 1) == "-") { strip = 1; i++ }
            while (substr(s, i, 1) == " " || substr(s, i, 1) == "\t") i++
            delim = ""; quoted = 0
            for (; i <= L; i++) {
                d = substr(s, i, 1)
                if (d ~ /[ \t\n;&|<>()]/) break
                if (d == "\047" || d == "\"" || d == "\\") { quoted = 1; continue }
                delim = delim d
            }
            i--
            hdel[nh] = delim; hq[nh] = quoted; hs[nh] = strip; nh++
            continue
        }
        if (c == "&" && (substr(s, i - 1, 1) ~ /[<>]/ || substr(s, i + 1, 1) == ">")) { w = w c; started = 1; continue }
        if (c == "\n") {
            seg_end()
            if (nh) {
                line = substr(s, start, i - start)
                shell = (line ~ /(^|[^A-Za-z0-9_.\/-])(bash|sh|zsh|dash|ksh|source)([^A-Za-z0-9_.-]|$)/)
                for (k = 0; k < nh; k++) {
                    body = ""
                    while (i < L) {
                        j = index(substr(s, i + 1), "\n")
                        if (j == 0) { line = substr(s, i + 1); i = L } else { line = substr(s, i + 1, j - 1); i += j }
                        m = line; if (hs[k]) sub(/^\t+/, "", m)
                        if (m == hdel[k]) break
                        body = body line "\n"
                    }
                    if (shell) push(body); else if (!hq[k]) subs_only(body)
                }
                nh = 0
            }
            start = i + 1
            continue
        }
        if (c == ";" || c == "&" || c == "|" || c == "(" || c == ")") { seg_end(); continue }
        w = w c; started = 1
    }
    seg_end()
}
{ src = src (NR > 1 ? "\n" : "") $0 }
END { q[0] = src; nq = 1; for (qi = 0; qi < nq; qi++) parse(q[qi]) }
'

tokenize() {
    printf '%s' "$1" | awk -v US="$US" -v SUBST="$SUBST" "$TOKENIZER"
}

# Regenerable directories that agents routinely clear inside a checkout.
ARTIFACT_DIRS=" __pycache__ node_modules .venv venv .pytest_cache .ruff_cache .mypy_cache \
.hypothesis htmlcov coverage .coverage dist build .svelte-kit .next .turbo .parcel-cache \
.terraform .tox "

# A recursive force-delete is allowed only when every operand is a literal path
# inside a temporary directory, or a relative path naming a regenerable artifact.
safe_delete_target() {
    local target=$1 base prefix tmp=${TMPDIR:-/tmp}
    [[ -n "$target" && "$target" != *"$SUBST"* ]] || return 1
    case "/$target/" in */../*|*/./) return 1 ;; esac
    for prefix in '$TMPDIR' '${TMPDIR}' "${tmp%/}" /tmp /private/tmp /var/folders /private/var/folders; do
        if [[ "$target" == "$prefix"/* ]]; then
            base=${target#"$prefix"/}
            [[ "$base" =~ [^*?/.] ]] && return 0
            return 1
        fi
    done
    [[ "$target" != /* && "$target" != '~'* && "$target" != *'$'* ]] || return 1
    base=${target%/}
    base=${base##*/}
    [[ "$ARTIFACT_DIRS" == *" $base "* ]]
}

check_rm() {
    local recursive=0 force=0 operands=0 options=1 arg
    for arg in "$@"; do
        if ((options)) && [[ "$arg" == -- ]]; then options=0; continue; fi
        if ((options)) && [[ "$arg" == --* ]]; then
            [[ "$arg" == --recursive ]] && recursive=1
            [[ "$arg" == --force ]] && force=1
            continue
        fi
        if ((options)) && [[ "$arg" == -?* ]]; then
            [[ "$arg" == *[rR]* ]] && recursive=1
            [[ "$arg" == *f* ]] && force=1
            continue
        fi
        operands=$((operands + 1))
    done
    ((recursive && force)) || return 0
    ((operands)) || block 'recursive force-delete of paths the guard cannot see. Name the paths directly.'
    options=1
    for arg in "$@"; do
        if ((options)) && [[ "$arg" == -- ]]; then options=0; continue; fi
        if ((options)) && [[ "$arg" == -* ]]; then continue; fi
        safe_delete_target "$arg" || block "recursive force-delete outside a temporary directory or a regenerable build directory: $arg. Perform it manually outside the agent session."
    done
}

resolve_dir() {
    local base=$1 path=$2
    [[ -n "$base" && "$path" != *'$'* && "$path" != *"$SUBST"* && "$path" != - ]] || return 0
    case "$path" in
        '~') path=$HOME ;;
        \~/*) path=$HOME/${path#\~/} ;;
    esac
    if [[ "$path" == /* ]]; then printf '%s' "$path"; else printf '%s/%s' "$base" "$path"; fi
}

# A branch is preserved when its tip is also reachable from a tag or remote branch.
branch_preserved() {
    local dir=$1 name=$2 sha found
    [[ -n "$dir" && "$name" != *"$SUBST"* ]] || return 1
    # Substitutions inherit the ERR trap, so expected failures end in `|| true`.
    sha=$(git -C "$dir" rev-parse -q --verify "refs/heads/$name^{commit}" 2>/dev/null || true)
    [[ -n "$sha" ]] || return 1
    found=$(git -C "$dir" for-each-ref --count=1 --contains "$sha" --format=x refs/tags refs/remotes 2>/dev/null || true)
    [[ -n "$found" ]]
}

check_git() {
    local dir=$DIR sub arg force=0 delete=0 names=0
    while (($#)) && [[ "$1" == -* ]]; do
        case "$1" in
            -C) dir=$(resolve_dir "$dir" "${2:-}"); shift 2 || shift ;;
            -c)
                if [[ "$(printf '%s' "${2:-}" | tr '[:upper:]' '[:lower:]')" == commit.gpgsign=false ]]; then
                    block 'GPG signing bypass detected. Sign commits unless the user explicitly opted out.'
                fi
                shift 2 || shift
                ;;
            --git-dir|--work-tree|--namespace|--exec-path|--super-prefix|--config-env) shift 2 || shift ;;
            *) shift ;;
        esac
    done
    (($#)) || return 0
    sub=$1
    shift
    for arg in "$@"; do
        [[ "$arg" == --no-verify ]] && block '--no-verify bypasses pre-commit/pre-push hooks. Investigate the hook failure instead.'
        [[ "$arg" == --no-gpg-sign ]] && block 'GPG signing bypass detected. Sign commits unless the user explicitly opted out.'
    done
    case "$sub" in
        push)
            if ((SEGMENTS > 1)); then
                block 'git push combined with other commands, pipes, or redirects runs inside the sandbox without review. Run git push as its own command.'
            fi
            for arg in "$@"; do
                [[ "$arg" == --force || "$arg" =~ ^-[A-Za-z]*f[A-Za-z]*$ ]] &&
                    block 'force push detected. Use --force-with-lease only with explicit user authorization.'
                [[ "$arg" == +?* ]] &&
                    block 'force push via +refspec detected. Force refspecs rewrite remote history.'
            done
            ;;
        reset)
            for arg in "$@"; do
                [[ "$arg" == --hard ]] && block 'git reset --hard discards uncommitted work.'
            done
            ;;
        clean)
            for arg in "$@"; do
                [[ "$arg" == --force || "$arg" =~ ^-[A-Za-z]*f ]] &&
                    block 'git clean -f deletes untracked files. Use git status / git stash first.'
            done
            ;;
        commit)
            for arg in "$@"; do
                [[ "$arg" == -n ]] && block '--no-verify bypasses pre-commit/pre-push hooks. Investigate the hook failure instead.'
            done
            ;;
        branch)
            for arg in "$@"; do
                case "$arg" in
                    --delete) delete=1 ;;
                    --force) force=1 ;;
                    --*) ;;
                    -*)
                        [[ "$arg" == *D* ]] && delete=1 && force=1
                        [[ "$arg" == *d* ]] && delete=1
                        [[ "$arg" == *f* ]] && force=1
                        ;;
                esac
            done
            ((delete && force)) || return 0
            for arg in "$@"; do
                [[ "$arg" == -* ]] && continue
                names=$((names + 1))
                branch_preserved "$dir" "$arg" ||
                    block "git branch -D would lose commits on $arg that no tag or remote branch holds. Tag or push it first in a separate command, or use git branch -d."
            done
            ((names)) || block 'git branch -D without a branch name the guard can check.'
            ;;
        stash)
            [[ "${1:-}" == drop || "${1:-}" == clear ]] && block 'git stash drop/clear permanently discards stashed work.'
            ;;
        reflog)
            [[ "${1:-}" == expire ]] && block 'git reflog expire destroys recovery history.'
            ;;
    esac
    return 0
}

# gh calls that only read run inside the sandbox; anything else must run alone
# so it matches the sandbox exclusion and goes through review.
check_gh() {
    ((SEGMENTS > 1)) || return 0
    local sub=${1:-} action=${2:-} arg
    case "$sub" in
        api)
            for arg in "$@"; do
                case "$arg" in
                    -X|--method|-X*|--method=*|-f|-F|--field|--raw-field|--input|-f*|-F*|--field=*|--raw-field=*|--input=*)
                        block 'gh api with a method or fields, combined with other commands, runs inside the sandbox without review. Run it as its own command.'
                        ;;
                esac
            done
            return 0
            ;;
        status|search|browse|help|--version|version|auth) return 0 ;;
    esac
    case "$action" in
        view|list|status|checks|diff|watch|download|"") return 0 ;;
    esac
    block "gh $sub $action combined with other commands, pipes, or redirects runs inside the sandbox without review. Run it as its own command."
}

check_find() {
    local depth=$1
    shift
    local -a sub
    while (($#)); do
        case "$1" in
            -exec|-execdir|-ok|-okdir)
                shift
                sub=()
                while (($#)) && [[ "$1" != ';' && "$1" != '+' ]]; do sub+=("$1"); shift; done
                ((${#sub[@]})) && analyze_tokens $((depth + 1)) "${sub[@]}"
                ;;
        esac
        (($#)) && shift
    done
    return 0
}

analyze_tokens() {
    local depth=$1
    shift
    local sudo=0 name arg
    while (($#)); do
        if [[ "$1" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then shift; continue; fi
        name=${1##*/}
        case "$name" in
            sudo)
                sudo=1
                shift
                while (($#)) && [[ "$1" == -* ]]; do
                    case "$1" in -u|-g|-C|-D|-h|-p|-r|-t|-U) shift ;; esac
                    (($#)) && shift
                done
                ;;
            command|builtin|exec|nohup|time|then|do|else|elif|if|while|until|'!'|'{'|'}')
                shift
                while (($#)) && [[ "$1" == -* ]]; do shift; done
                ;;
            nice)
                shift
                [[ "${1:-}" == -n ]] && shift 2 && continue
                [[ "${1:-}" == -* ]] && shift
                ;;
            timeout|gtimeout)
                shift
                while (($#)) && [[ "$1" == -* ]]; do
                    case "$1" in -s|-k) shift ;; esac
                    (($#)) && shift
                done
                (($#)) && shift
                ;;
            env)
                shift
                while (($#)); do
                    case "$1" in
                        -S) analyze_command $((depth + 1)) "${2:-}"; return 0 ;;
                        -u|-C|-P) shift; (($#)) && shift ;;
                        -*) shift ;;
                        *) [[ "$1" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] && shift || break ;;
                    esac
                done
                ;;
            xargs)
                shift
                while (($#)) && [[ "$1" == -* ]]; do
                    case "$1" in -I|-J|-L|-n|-P|-R|-s|-E|-d|-a) shift ;; esac
                    (($#)) && shift
                done
                ;;
            *) break ;;
        esac
    done
    (($#)) || return 0
    name=${1##*/}
    shift
    if ((sudo)) && [[ "$name" == rm || "$name" == dd ]]; then
        block 'privileged destructive command.'
    fi
    case "$name" in
        eval) block 'eval hides the real command from the guard. Run the underlying command directly.' ;;
        rm) check_rm "$@" ;;
        mkfs|mkfs.*) block 'destructive disk operation.' ;;
        diskutil)
            [[ "${1:-}" == eraseDisk || "${1:-}" == partitionDisk ]] && block 'destructive disk operation.'
            ;;
        git) check_git "$@" ;;
        gh) check_gh "$@" ;;
        find) check_find "$depth" "$@" ;;
        bash|sh|zsh|dash|ksh)
            while (($#)); do
                if [[ "$1" =~ ^-[A-Za-z]*c[A-Za-z]*$ ]]; then
                    analyze_command $((depth + 1)) "${2:-}"
                    break
                fi
                shift
            done
            ;;
        cd) DIR=$(resolve_dir "$DIR" "${1:-$HOME}") ;;
    esac
    return 0
}

analyze_command() {
    local depth=$1 text=$2 segs seg
    ((depth <= 4)) || block 'command nesting is too deep for the guard to inspect.'
    segs=$(tokenize "$text")
    [[ -n "$segs" ]] || return 0
    local -a lines toks
    local IFS=$'\n'
    read -r -d '' -a lines <<<"$segs" || true
    ((depth > 0)) || SEGMENTS=${#lines[@]}
    for seg in "${lines[@]}"; do
        IFS=$US
        read -r -a toks <<<"$seg"
        IFS=$'\n'
        ((${#toks[@]})) && analyze_tokens "$depth" "${toks[@]}"
    done
    return 0
}

SEGMENTS=1
analyze_command 0 "$CMD"
exit 0
