"""Standalone native boundary: no imports or executable discovery from a checkout."""

import contextlib
import hashlib
import json
import os
import shlex
import sys
import tempfile
import termios
from pathlib import Path

GUARD = """
; Host credentials, application services, shared IPC and process arguments are private.
(deny mach-lookup
  (global-name "com.apple.securityd.xpc")
  (global-name "com.apple.SecurityServer")
  (global-name "com.apple.coreservices.launchservicesd"))
(deny ipc-posix-shm)
(deny ipc-posix-sem)
(deny distributed-notification-post)
(deny sysctl-read (sysctl-name-prefix "kern.proc"))
(deny process-info*)
; Match future environment files too, not just files present at launch.
(deny file-read* file-write* file-write-create file-write-unlink
  (regex "/[.]env($|[./])"))
"""


def harden(command: str) -> list[str]:
    """Adapt the pinned upstream's quoted argv, refusing an unfamiliar output shape."""
    args = shlex.split(command)
    if not args or args[0] != "env":
        raise ValueError("Unexpected sandbox runtime command")
    sandbox = args.index("/usr/bin/sandbox-exec")
    if len(args) != sandbox + 6 or args[sandbox + 1] != "-p":
        raise ValueError("Unexpected sandbox runtime argument count or profile")
    if args[sandbox + 3 : sandbox + 5] != ["/bin/bash", "-c"]:
        raise ValueError("Unexpected sandbox runtime shell")
    if any("=" not in item or item.startswith("-") for item in args[1:sandbox]):
        raise ValueError("Unexpected sandbox runtime environment")
    if not args[sandbox + 2].startswith("(version 1)\n(deny default"):
        raise ValueError("Sandbox runtime no longer denies by default")
    args[sandbox + 2] += GUARD
    # Admit only inherited terminal devices, never every other terminal on the Mac.
    terminals = set()
    for descriptor in (0, 1, 2):
        with contextlib.suppress(OSError):
            terminals.add(os.ttyname(descriptor))
    for terminal in terminals:
        args[sandbox + 2] += (
            f"\n(allow file-read* file-write-data file-ioctl (literal {json.dumps(terminal)}))"
        )
    # A terminal must not be usable to enqueue commands into the parent host shell.
    args[sandbox + 2] += f"\n(deny file-ioctl (ioctl-command {termios.TIOCSTI}))\n"
    return args


def workspace_root(cwd: Path, home: Path) -> Path:
    """Admit a normal Git checkout, never the entire home or a linked worktree."""
    cwd = cwd.resolve(strict=True) if cwd.exists() else cwd
    for root in (cwd, *cwd.parents):
        marker = root / ".git"
        if marker.exists():
            if any(char in str(root) for char in "*?[]"):
                raise ValueError("Workspace paths must be literal, without glob characters")
            if root == home.resolve() or root in home.resolve().parents:
                raise ValueError("Refusing the home directory or an ancestor")
            if marker.is_symlink() or not marker.is_dir():
                raise ValueError("Linked worktrees are not supported by the native boundary")
            return root
    raise ValueError("Run from a Git repository")


def build_plan(
    cwd: Path, home: Path, tools: dict, vendor: str, location: str, args: list, scratch=None
) -> dict:
    """Build an allowlist around one checkout and a separate per-project agent home."""
    if location != "hosted":
        raise ValueError("Restricted local inference has no approved inference-only interface")
    if vendor not in {"codex", "claude", "pi", "shell"}:
        raise ValueError("Unknown native agent")
    if any(arg in {"app-server", "mcp-server", "--chrome", "--sdk-url"} for arg in args):
        raise ValueError("The native boundary supports terminal sessions only")
    root = workspace_root(cwd, home)
    runtime = home / ".local/share/workbench"
    if root == runtime or root in runtime.parents or runtime in root.parents:
        raise ValueError("The installed boundary cannot be a writable workspace")
    identity = hashlib.sha256(os.fsencode(root)).hexdigest()[:20]
    state = runtime / "agent-state" / identity
    agent_home, temp = state / "home", scratch or state / "tmp"
    node = Path(tools["node"])
    agent = tools["agents"].get(vendor)
    if vendor == "shell":
        agent = {"command": ["/bin/bash", "--noprofile", "--norc"], "read": []}
    if not agent:
        raise ValueError(f"Native tool not prepared: {vendor}")
    command = [*agent["command"]]
    auth = runtime / "model-auth" / vendor
    auth_files = []
    auth_env = {}
    auth_link = None
    if vendor == "codex":
        command += [
            "-c",
            'sandbox_mode="danger-full-access"',
            "-c",
            'approval_policy="on-request"',
            "-c",
            'cli_auth_credentials_store="file"',
            "-c",
            "features.apps=false",
        ]
        auth_files = [str(auth / "auth.json")]
        auth_link = {"path": str(agent_home / ".codex/auth.json"), "target": auth_files[0]}
        auth_env["CODEX_HOME"] = str(agent_home / ".codex")
    elif vendor == "claude":
        command += ["--settings", '{"sandbox":{"enabled":false}}']
        auth_files = [str(auth / ".credentials.json"), str(auth / ".storage-write.lock")]
        auth_env["CLAUDE_SECURESTORAGE_CONFIG_DIR"] = str(auth)
    elif vendor == "pi":
        # One credential path also gives every project the same refresh lock.
        command += [
            "--session-dir",
            str(agent_home / ".pi/sessions"),
            "--no-extensions",
            "--no-skills",
            "--no-prompt-templates",
            "--no-themes",
        ]
        auth_files = [str(auth / "auth.json"), str(auth / "auth.json.lock")]
        auth_env["PI_CODING_AGENT_DIR"] = str(auth)
    read = [
        "/System/Library",
        "/usr/bin",
        "/usr/sbin",
        "/usr/lib",
        "/usr/libexec",
        "/usr/share",
        "/bin",
        "/sbin",
        "/etc",
        "/private/etc",
        "/private/var/select",
        "/Library/Developer/CommandLineTools",
        "/opt/homebrew/Cellar",
        "/opt/homebrew/opt",
        "/opt/homebrew/bin",
        "/dev/null",
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/fd",
        "/dev/tty",
        str(node.parent),
        str(node.parent.parent / "lib/node_modules/npm"),
        # Managed tool installations only, not host settings or package caches.
        str(home / ".local/share/uv/python"),
        str(home / ".npm-global/bin"),
        str(home / ".npm-global/global"),
        str(home / ".npm-global/lib/node_modules/pnpm"),
        str(home / ".bun/bin"),
        *agent["read"],
        str(root),
        str(agent_home),
        str(temp),
        *auth_files,
    ]
    for grant in read:
        path = Path(grant)
        if not path.is_absolute() or any(char in grant for char in "*?[]"):
            raise ValueError("Read grants must be absolute literal paths, without glob characters")
        if path == home or path in home.parents:
            raise ValueError("Read grants cannot include the host home or its ancestors")
    private = home / ".config/workbench/private-paths"
    if not private.is_file():
        raise ValueError("Missing private-data policy; run workbench native prepare")
    excludes = [
        line.strip().replace("~/", f"{home}/", 1)
        for line in private.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    policy = {
        "filesystem": {
            "denyRead": ["/", *excludes],
            "allowRead": read,
            "allowWrite": [str(root), str(agent_home), str(temp), *auth_files],
            "denyWrite": ["/tmp/claude", "/private/tmp/claude", *excludes],
        },
        "network": {
            "allowedDomains": [],
            "deniedDomains": ["localhost"],
            "deniedResolvedAddresses": [
                "0.0.0.0/8",
                "10.0.0.0/8",
                "100.64.0.0/10",
                "127.0.0.0/8",
                "169.254.0.0/16",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "224.0.0.0/4",
                "::/128",
                "::1/128",
                "fc00::/7",
                "fe80::/10",
                "ff00::/8",
            ],
        },
    }
    env = {key: os.environ[key] for key in ("TERM", "COLORTERM", "LANG") if key in os.environ}
    env.update(
        {
            "HOME": str(agent_home),
            "TMPDIR": str(temp),
            "CLAUDE_CODE_TMPDIR": str(temp),
            "PATH": (
                f"{node.parent}:{home}/.npm-global/bin:{home}/.bun/bin:"
                "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            ),
            "SHELL": "/bin/bash",
            "NODE_USE_ENV_PROXY": "1",
            "DEVELOPER_DIR": "/Library/Developer/CommandLineTools",
            "WORKBENCH_AGENT_AUTHORITY": "restricted",
            **auth_env,
        }
    )
    return {
        "root": str(root),
        "cwd": str(cwd.resolve()),
        "policy": policy,
        "env": env,
        "command": [*command, *args],
        "node": str(node),
        "auth_link": auth_link,
    }


def initialize_home(plan: dict, home: Path) -> None:
    """Create state without following a link planted by a prior sandboxed session."""
    link = plan.get("auth_link")
    directory = Path(link["path"]).parent if link else Path(plan["env"]["HOME"])
    descriptor = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in directory.relative_to(home).parts:
            with contextlib.suppress(FileExistsError):
                os.mkdir(part, mode=0o700, dir_fd=descriptor)
            try:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
                )
            except OSError as error:
                raise ValueError("Agent state contains a symlink or non-directory") from error
            os.close(descriptor)
            descriptor = child
        if link:
            try:
                os.symlink(link["target"], "auth.json", dir_fd=descriptor)
            except FileExistsError:
                try:
                    target = os.readlink("auth.json", dir_fd=descriptor)
                except OSError as error:
                    raise ValueError(
                        "Unexpected model login link; refusing to overwrite"
                    ) from error
                if target != link["target"]:
                    raise ValueError("Unexpected model login link; refusing to overwrite") from None
    finally:
        os.close(descriptor)


def main() -> None:
    if sys.argv[1:2] == ["--apply"]:
        os.execv("/usr/bin/env", harden(sys.argv[2]))
    if sys.platform != "darwin":
        raise ValueError("The native boundary requires macOS")
    if len(sys.argv) < 3:
        raise ValueError("Usage: native-sandbox.py VENDOR LOCATION [agent arguments]")
    home = Path.home().resolve()
    runtime = Path(__file__).resolve().parents[1] / "native"
    config = runtime / "tools.json"
    if not config.is_file():
        raise ValueError("Native runtime is not prepared; run workbench native prepare")
    # macOS Unix socket names are short; a nested project-state TMPDIR exceeds the limit.
    scratch = Path(tempfile.mkdtemp(prefix="wb-native-", dir="/private/tmp"))
    try:
        plan = build_plan(
            Path.cwd(),
            home,
            json.loads(config.read_text()),
            sys.argv[1],
            sys.argv[2],
            sys.argv[3:],
            scratch=scratch,
        )
        initialize_home(plan, home)
    except Exception:
        scratch.rmdir()
        raise
    print(
        f"{sys.argv[1].upper()} · NATIVE RESTRICTED · {Path(plan['root']).name}",
        file=sys.stderr,
        flush=True,
    )
    runner = Path(__file__).with_suffix(".mjs")
    os.execve(plan["node"], [plan["node"], str(runner), json.dumps(plan)], plan["env"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f"native sandbox: {error}", file=sys.stderr)
        sys.exit(1)
