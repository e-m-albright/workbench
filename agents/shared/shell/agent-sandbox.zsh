#!/bin/zsh -f
# Usage: agent-sandbox.zsh VENDOR LOCATION AUTHORITY [native args...]
# One native restricted boundary; host workflows remain explicitly unrestricted.
set -eu
vendor=${1:?vendor required}
location=${2:?location required}
authority=${3:?authority required}
shift 3
case "$vendor:$location:$authority" in
    pi:hosted:restricted|pi:hosted:unrestricted|pi:local:unrestricted|claude:hosted:restricted|claude:hosted:unrestricted|codex:hosted:restricted|codex:hosted:unrestricted) ;;
    *) print -u2 'Unsupported mode; restricted local inference is retired'; exit 2 ;;
esac
if [[ "${WORKBENCH_AGENT_AUTHORITY:-}" == restricted && "$authority" == unrestricted ]]; then
    print -u2 'A restricted process cannot start an unrestricted agent'; exit 2
fi
if [[ "$authority" == restricted ]]; then
    exec /usr/bin/python3 -I -S "$HOME/.local/share/workbench/shell/native-sandbox.py" "$vendor" "$location" "$@"
fi
binary=$(whence -p "$vendor")
export WORKBENCH_AGENT_AUTHORITY=$authority
export WORKBENCH_AGENT_LOCATION=$location
if [[ "$vendor" == pi ]]; then
    export WORKBENCH_PI_MODE="$location-$authority"
    route=frontier
    if [[ "$location" == local ]]; then
        route=private
        pending=""
        for arg in "$@"; do
            [[ "$arg" == -- ]] && break
            value=$arg
            kind=$pending
            pending=""
            case "$arg" in
                --provider|--model) pending=${arg#--}; continue ;;
                --provider=*) kind=provider; value=${arg#*=} ;;
                --model=*) kind=model; value=${arg#*=} ;;
                --no-extensions|-ne) print -u2 'Local mode requires the inference guard'; exit 2 ;;
            esac
            if [[ "$kind" == provider && "$value" != omlx ]] || [[ "$kind" == model && "$value" == */* && "$value" != omlx/* ]]; then
                print -u2 'Local mode cannot start a hosted model'; exit 2
            fi
        done
        set -- --provider omlx "$@"
    fi
    set -- --route "$route" "$@"
fi
if [[ "$authority" == unrestricted ]]; then
    if [[ "$vendor" == codex ]]; then
        # Name the outer authority without widening Codex's managed inner workspace profile.
        # Explicit caller policy/profile choices keep their own native footer label.
        label_default=true
        for arg in "$@"; do
            case "$arg" in
                -s|--sandbox|--sandbox=*|-p|--profile|--profile=*|--permissions|--permissions=*|--yolo|--dangerously-bypass-approvals-and-sandbox|*sandbox_mode=*|*default_permissions=*|permissions.*|permissions=*) label_default=false ;;
            esac
        done
        if [[ "$label_default" == true ]]; then
            set -- -c 'default_permissions="hosted > unrestricted"' \
                -c 'permissions={"hosted > unrestricted"={extends=":workspace"}}' "$@"
        fi
    fi
    exec "$binary" "$@"
fi
