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

set -eo pipefail

INPUT=$(cat 2>/dev/null || true)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // .command // empty' 2>/dev/null || true)
[[ -z "$CMD" ]] && exit 0

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

# --- Filesystem destruction --------------------------------------------------
# Block every recursive force-delete. Recursive deletion is intentionally a
# human-terminal operation; agents can use bounded file edits or plain `rm`.
# Robust to flag order
# (-rf / -fr / -r -f), case (-R), long flags (--recursive/--force), and quoting
# ("$HOME"). Quotes are stripped first; the command is split on separators so a
# dangerous segment can't be confused with a benign command in another.
fs_cmd=$(printf '%s' "$CMD" | tr -d "\"'")
while IFS= read -r seg; do
    printf '%s' "$seg" | grep -qE '(^|[[:space:]])rm([[:space:]]|$)' || continue
    printf '%s' "$seg" | grep -qE '[[:space:]]-[A-Za-z]*[rR]|[[:space:]]--recursive' || continue
    printf '%s' "$seg" | grep -qE '[[:space:]]-[A-Za-z]*[fF]|[[:space:]]--force' || continue
    block 'recursive force-delete. Perform recursive deletion manually outside the agent session.'
done <<< "$(printf '%s' "$fs_cmd" | sed -E 's/(&&|\|\||[;&|])/\n/g')"

case "$CMD" in
    *"sudo rm"*|*"sudo dd"*) block 'privileged destructive command.' ;;
esac

if printf '%s' "$CMD" | grep -qE '(^|[[:space:];|&])(diskutil[[:space:]]+(eraseDisk|partitionDisk)|mkfs(\.|[[:space:]]))'; then
    block 'destructive disk operation.'
fi

# --- Destructive git ---------------------------------------------------------
# Force push (any --force form)
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]]+push[[:space:]]+([^&;|]*[[:space:]])?(--force([^-]|$)|-f([[:space:]]|$))'; then
    block 'force push detected. Use --force-with-lease only with explicit user authorization.'
fi
# Hard reset
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]]+reset[[:space:]]+(--hard|-{1,2}h)([[:space:]]|$)'; then
    block 'git reset --hard discards uncommitted work.'
fi
# Clean -f
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]]+clean[[:space:]]+-[a-zA-Z]*f'; then
    block 'git clean -f deletes untracked files. Use git status / git stash first.'
fi
# Branch force-deletion
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]]+branch[[:space:]]+(-D|--delete[[:space:]]+--force)'; then
    block 'git branch -D destructively deletes branches without a merge check.'
fi
# Hook bypass
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]].*--no-verify'; then
    block '--no-verify bypasses pre-commit/pre-push hooks. Investigate the hook failure instead.'
fi
# Signing bypass
if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])git[[:space:]].*(--no-gpg-sign|-c[[:space:]]+commit\.gpgsign=false)'; then
    block 'GPG signing bypass detected. Sign commits unless the user explicitly opted out.'
fi

exit 0
