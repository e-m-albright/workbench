"""Standalone native boundary: no imports or executable discovery from a checkout."""

import contextlib
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import shlex
import socket
import stat
import subprocess
import sys
import tempfile
import termios
from datetime import datetime
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
; Certificate evaluation only; Go tools such as gh fail TLS checks without it.
(allow mach-lookup (global-name "com.apple.trustd.agent"))
; Chromium, as Playwright runs it, hands ports to its own children through a
; per-process name; refusing it aborts the browser at startup.
(allow mach-register mach-lookup
  (global-name-prefix "org.chromium.Chromium.MachPortRendezvousServer."))
; Match future environment files and confidential directories too, not just
; paths present at launch. Seatbelt does not support regex lookahead; exclude
; templates with native filters instead. Character classes ignore case.
(deny file-read* file-write* file-write-create file-write-unlink
  ; A template basename cannot exempt a file inside an environment directory.
  (regex "/[.][Ee][Nn][Vv]([.][^/]*)?/")
  (require-all
    (regex "/[.][Ee][Nn][Vv]($|/|[.])")
    (require-not (require-any
      (regex "/[.][Ee][Nn][Vv][.][Ee][Xx][Aa][Mm][Pp][Ll][Ee]$")
      (regex "/[.][Ee][Nn][Vv][.][Ss][Aa][Mm][Pp][Ll][Ee]$")
      (regex "/[.][Ee][Nn][Vv][.][Tt][Ee][Mm][Pp][Ll][Aa][Tt][Ee]$"))))
  (regex "/[Cc][Oo][Nn][Ff][Ii][Dd][Ee][Nn][Tt][Ii][Aa][Ll]($|/)"))
"""

# The guardian verifies this suffix before it applies the profile or broadcasts.
SESSION_SIGNAL_GUARD = "\n(deny signal)\n(allow signal (target same-sandbox))\n"


def loopback_rules(ports: list[int]) -> str:
    """Let a session serve locally and reach only the owner's listed loopback ports.

    Binding and inbound are local operations, so any address is safe there (the
    runtime explains why IPv4-mapped sockets need "*:*"). Outbound stays limited
    to the listed ports, never every service on the Mac's loopback.
    """
    if not ports:
        return ""
    if not all(type(port) is int and 0 < port < 65536 for port in ports):
        raise ValueError("Loopback ports must be integers from 1 to 65535")
    rules = ['(allow network-bind (local ip "*:*"))', '(allow network-inbound (local ip "*:*"))']
    rules += [f'(allow network-outbound (remote ip "localhost:{port}"))' for port in ports]
    return "\n" + "\n".join(rules) + "\n"


def harden(
    command: str, browser_port: int = 0, mandatory_rules: str = "", ports: list[int] = ()
) -> list[str]:
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
    args[sandbox + 2] += GUARD + loopback_rules(list(ports))
    if browser_port:
        if not 1024 <= browser_port <= 65535:
            raise ValueError("Invalid browser control port")
        for operation, endpoint in (
            ("network-bind", "local"),
            ("network-inbound", "local"),
            ("network-outbound", "remote"),
        ):
            args[sandbox + 2] += f'\n(allow {operation} ({endpoint} ip "localhost:{browser_port}"))'
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
    # Compiled by the pinned runtime's path helpers, after ALL admission grants.
    args[sandbox + 2] += mandatory_rules
    args[sandbox + 2] += SESSION_SIGNAL_GUARD
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


def git_identity(home: Path, cwd: Path) -> dict:
    """Import attribution scalars only; local values win without local includes."""
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1"}
    identity = {}
    for key, names in (
        ("user.name", ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME")),
        ("user.email", ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL")),
    ):
        try:
            result = subprocess.run(
                ["/usr/bin/git", "config", "--global", "--includes", "--get", key],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        value = result.stdout.strip()
        if result.returncode == 0 and value:
            identity.update(dict.fromkeys(names, value))
        # Git config reads no hooks or helpers. Disable repository includes so a
        # planted include cannot make the unsandboxed bootstrap open private data.
        config = cwd / ".git/config"
        try:
            with os.fdopen(
                os.open(config, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
            ) as stream:
                metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 1024 * 1024:
                    raise ValueError("Unsafe repository Git configuration")
                local = subprocess.run(
                    ["/usr/bin/git", "config", "--file", "-", "--no-includes", "--get", key],
                    input=stream.read(),
                    capture_output=True,
                    env=env,
                    timeout=5,
                    check=False,
                )
            value = local.stdout.decode().strip()
            if local.returncode == 0 and value:
                identity.update(dict.fromkeys(names, value))
        except FileNotFoundError:
            pass
    return identity


GRANTS = ".config/workbench/repository-grants.json"
REPOSITORY_GRANTS = {"github", "aws", "ports", "docker", "paths"}
# Git asks this helper for GitHub credentials; it answers from the launch token
# so neither a host credential helper nor the protected .git/config is needed.
GITHUB_HELPER = (
    '!f() { test "$1" = get && '
    "printf 'username=x-access-token\\npassword=%s\\n' \"$GH_TOKEN\"; }; f"
)
DOCKER_SOCKETS = (
    "/var/run/docker.sock",
    "~/.orbstack/run/docker.sock",
    "~/.docker/run/docker.sock",
    "~/.colima/default/docker.sock",
)
DOCKER_CLIENTS = ("/usr/local/bin/docker", "/opt/homebrew/bin/docker")


def host_output(home: Path, command: list[str], failure: str, run=subprocess.run) -> str:
    """Run a host credential tool with the owner's home, returning its trimmed output."""
    env = {"HOME": str(home), "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"}
    try:
        result = run(command, env=env, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError(failure) from None
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError(failure)
    return result.stdout.strip()


def aws_command() -> str:
    candidates = ("/opt/homebrew/bin/aws", "/usr/local/bin/aws")
    return next((path for path in candidates if Path(path).exists()), "aws")


def repository_grants(home: Path, root: Path) -> dict:
    """Read what the owner assigned to this checkout, failing on any typo.

    `~/.config/workbench/repository-grants.json` maps a checkout path to a
    Keychain service holding a GitHub token scoped to that repository, an AWS
    profile whose role should reach only a sandbox account, the loopback ports
    its own services use, Docker access, and extra read-write directories.
    Sessions cannot edit this file. Provider-side scope is the real credential
    limit; the session can use or leak what it receives.
    """
    path = home / GRANTS
    # A leftover legacy file would otherwise silently withhold the grants it holds.
    if (home / ".config/workbench/repo-credentials.json").is_file():
        raise ValueError(
            f"Merge ~/.config/workbench/repo-credentials.json into ~/{GRANTS}, then delete it"
        )
    if not path.is_file():
        return {}
    try:
        config = json.loads(path.read_text())
    except ValueError as error:
        raise ValueError(f"Unreadable {path}: {error}") from None
    if not isinstance(config, dict):
        raise ValueError(f"{path} must map checkout paths to grants")
    entry = None
    for key, value in config.items():
        checkout = Path(str(home) + key[1:] if key.startswith("~/") else key)
        if checkout.resolve() == root:
            entry = value
    if entry is None:
        return {}
    if (
        not isinstance(entry, dict)
        or not set(entry) <= REPOSITORY_GRANTS
        or not all(
            isinstance(entry[key], str) and entry[key] for key in {"github", "aws"} & set(entry)
        )
        or not isinstance(entry.get("ports", []), list)
        or not isinstance(entry.get("docker", False), bool)
        or not isinstance(entry.get("paths", []), list)
        or not all(isinstance(item, str) and item for item in entry.get("paths", []))
    ):
        raise ValueError(
            f"{path}: each checkout maps 'github' and 'aws' to names, 'ports' and 'paths' "
            "to lists, and 'docker' to true or false"
        )
    loopback_rules(entry.get("ports", []))
    paths = []
    for item in entry.get("paths", []):
        directory = Path(str(home) + item[1:] if item.startswith("~/") else item)
        if not directory.is_absolute() or not directory.is_dir():
            raise ValueError(f"{path}: extra path {item!r} must be an existing absolute directory")
        directory = directory.resolve()
        if directory == home or directory in home.parents:
            raise ValueError(f"{path}: extra path {item!r} cannot be the home or an ancestor")
        paths.append(str(directory))
    return {**entry, "paths": paths}


def repository_credentials(home: Path, grants: dict, run=subprocess.run) -> dict:
    """Issue the GitHub token and AWS profile settings assigned to this checkout.

    AWS keys are written by `refresh_aws`, not passed here.
    """
    issued = {}
    if "github" in grants:
        service = grants["github"]
        token = host_output(
            home,
            ["/usr/bin/security", "find-generic-password", "-s", service, "-w"],
            f"No GitHub token in Keychain service {service!r}; add it with "
            f"`security add-generic-password -s {service} -a github -w`",
            run,
        )
        issued.update(
            {
                "GH_TOKEN": token,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "credential.https://github.com.helper",
                "GIT_CONFIG_VALUE_0": GITHUB_HELPER,
            }
        )
    if "aws" in grants:
        profile = grants["aws"]
        # The session's profile shares the host profile's name, so a project
        # setting such as AWS_PROFILE resolves the same way inside and outside.
        issued["AWS_PROFILE"] = profile
        with contextlib.suppress(ValueError):
            command = [aws_command(), "configure", "get", "region", "--profile", profile]
            region = host_output(home, command, "", run)
            issued.update({"AWS_REGION": region, "AWS_DEFAULT_REGION": region})
    return issued


def refresh_aws(
    home: Path, agent_home: Path, profile: str, run=subprocess.run, *, launching=True
) -> None:
    """Write one profile's short-lived keys into the session's own credentials file.

    A role assumed from an SSO session lasts at most an hour, so the supervisor
    calls this again during the session; the host CLI reuses its cached keys
    until they near expiry and re-assumes the role once SSO is valid again.
    The SSO cache itself never enters the session.
    """
    # A role profile signs in through its source profile, so name that one.
    try:
        source = host_output(
            home,
            [aws_command(), "configure", "get", "source_profile", "--profile", profile],
            "",
            run,
        )
    except ValueError:
        source = profile
    failure = f"AWS profile {profile!r} has no session; run `aws sso login --profile {source}`"
    command = [aws_command(), "configure", "export-credentials", "--profile", profile]
    try:
        keys = json.loads(host_output(home, [*command, "--format", "process"], failure, run))
        lines = [
            f"[{profile}]",
            f"aws_access_key_id = {keys['AccessKeyId']}",
            f"aws_secret_access_key = {keys['SecretAccessKey']}",
        ]
        if keys.get("SessionToken"):
            lines.append(f"aws_session_token = {keys['SessionToken']}")
    except (ValueError, KeyError, TypeError):
        if launching:
            raise ValueError(failure) from None
        # Stale keys read as a bare ExpiredToken; this makes every AWS call name the sign-in.
        report = f"echo {shlex.quote(failure)} >&2; exit 1"
        lines = [f"[{profile}]", f"credential_process = {shlex.join(['/bin/sh', '-c', report])}"]
    write_state_file(home, agent_home / ".aws/credentials", "\n".join(lines).encode() + b"\n")


def docker_access(home: Path) -> dict:
    """Find the running engine's socket and the client installation it needs.

    The Docker socket is a full escape from this boundary: a container can mount
    any host path the engine shares. Only checkouts the owner lists receive it.
    """
    socket_path = next(
        (
            path.resolve()
            for name in DOCKER_SOCKETS
            if (path := Path(name.replace("~/", f"{home}/", 1))).exists()
        ),
        None,
    )
    if socket_path is None:
        raise ValueError(
            "Docker is granted to this checkout, but no engine socket exists; start it"
        )
    read = [str(socket_path)]
    plugins = []
    client = next((Path(name) for name in DOCKER_CLIENTS if Path(name).exists()), None)
    if client:
        binary = client.resolve()
        bundle = next((parent for parent in binary.parents if parent.suffix == ".app"), None)
        read.append(str(bundle / "Contents" if bundle else binary.parent))
        for directory in (
            binary.parent,
            *([bundle / "Contents/Resources/cli-plugins"] if bundle else []),
        ):
            if (directory / "docker-compose").exists():
                plugins.append(str(directory))
    return {"socket": str(socket_path), "read": read, "plugins": plugins}


def screenshot_directory() -> list[str]:
    """macOS hands dragged screenshots to the terminal from the user's temporary items."""
    try:
        temporary = os.confstr("CS_DARWIN_USER_TEMP_DIR")
    except (ValueError, OSError):
        return []
    directory = Path(temporary or "/nonexistent") / "TemporaryItems"
    return [str(directory.resolve())] if directory.is_dir() else []


def project_denials(root: Path, home: Path) -> tuple[list[str], list[str]]:
    """Snapshot project Claude sandbox denials; agent-editable allow lists never widen access."""
    found = {"denyRead": [], "denyWrite": []}
    try:
        directory = os.open(root / ".claude", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return [], []
    except OSError:
        raise ValueError("Unsafe project policy directory") from None
    try:
        for name in ("settings.json", "settings.local.json"):
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            except FileNotFoundError:
                continue
            with os.fdopen(fd) as stream:
                metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 1024 * 1024:
                    raise ValueError("Unsafe project policy file")
                value = json.load(stream)
            for key in ("sandbox", "filesystem"):
                if not isinstance(value, dict):
                    raise ValueError("Invalid project policy object")
                value = value.get(key, {})
            if not isinstance(value, dict):
                raise ValueError("Invalid project policy filesystem")
            for key, paths in found.items():
                entries = value.get(key, [])
                if not isinstance(entries, list) or not all(
                    isinstance(entry, str) and entry and "\0" not in entry for entry in entries
                ):
                    raise ValueError("Invalid project policy deny paths")
                for entry in entries:
                    if entry == "~" or entry.startswith("~/"):
                        entry = str(home) + entry[1:]
                    elif not entry.startswith("/"):
                        entry = str(root / entry)
                    paths.append(os.path.normpath(entry))
    except (OSError, ValueError):
        raise ValueError(
            "Unreadable or invalid project policy; check .claude/settings*.json"
        ) from None
    finally:
        os.close(directory)
    return found["denyRead"], found["denyWrite"]


def claude_project_key(cwd: Path):
    """Use Claude's documented working-directory namespace, without guessing hashes."""
    value = str(cwd)
    key = re.sub(r"[^a-zA-Z0-9]", "-", value)
    # Claude hashes long paths; non-BMP characters also depend on JS code units.
    # Keep those sessions isolated until an authoritative vendor key is available.
    return key if len(key) <= 200 and all(ord(char) <= 0xFFFF for char in value) else None


def build_plan(
    cwd: Path,
    home: Path,
    tools: dict,
    vendor: str,
    location: str,
    args: list,
    scratch=None,
    authority="managed",
    browser_port=0,
) -> dict:
    """Build a managed boundary around one checkout and isolated agent state."""
    if authority != "managed":
        raise ValueError("Unknown agent authority")
    if location != "hosted":
        raise ValueError(
            "Managed local inference has no approved inference-only interface; use native pi"
        )
    if vendor not in {"codex", "claude", "pi", "shell"}:
        raise ValueError("Unknown native agent")
    if any(arg in {"app-server", "mcp-server", "--chrome", "--sdk-url"} for arg in args):
        raise ValueError(
            "Managed launches support terminals only; "
            "start the full vendor command from the host for integrations"
        )
    root = workspace_root(cwd, home)
    grants = repository_grants(home, root)
    docker = docker_access(home) if grants.get("docker") else None
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
    executable = Path(command[0])
    if executable.is_symlink():
        # A stable launcher survives vendor auto-update; run the version it names now.
        target = executable.resolve(strict=True)
        if not any(target.is_relative_to(Path(path)) for path in agent["read"]):
            raise ValueError("Agent launcher points outside its admitted installation")
        command[0] = str(target)
    auth = runtime / "model-auth" / vendor
    auth_files = []
    auth_staging = []
    vendor_env = {}
    auth_link = None
    claude_sessions = None
    manifest = runtime / "native/harness/manifest.json"
    if not manifest.is_file():
        raise ValueError("Missing shared harness; run workbench sync")
    harness = json.loads(manifest.read_text())[vendor]
    if vendor == "codex":
        label = "cloud > managed"
        command += [
            "-c",
            f'default_permissions="{label}"',
            "-c",
            f'permissions={{"{label}"={{filesystem={{":root"="write"}},network={{enabled=true}}}}}}',
            "-c",
            'approval_policy="on-request"',
            "-c",
            'cli_auth_credentials_store="file"',
            "-c",
            "features.apps=false",
        ]
        auth_files = [str(auth / "auth.json")]
        auth_link = {"path": str(agent_home / ".codex/auth.json"), "target": auth_files[0]}
        vendor_env["CODEX_HOME"] = str(agent_home / ".codex")
    elif vendor == "claude":
        command += ["--settings", json.dumps({"sandbox": {"enabled": False}})]
        auth_files = [str(auth / ".credentials.json"), str(auth / ".storage-write.lock")]
        # Claude saves logins and refreshed tokens by renaming a sibling temp file over the file.
        auth_staging = [str(auth / ".credentials.json.tmp.*")]
        vendor_env["CLAUDE_SECURESTORAGE_CONFIG_DIR"] = str(auth)
        # The host install owns updates; an isolated home must not grow its own copy.
        vendor_env["DISABLE_AUTOUPDATER"] = "1"
        key = claude_project_key(cwd.resolve())
        if key:
            claude_sessions = {
                "path": str(agent_home / ".claude/projects" / key),
                "target": str(home / ".claude/projects" / key),
            }
    elif vendor == "pi":
        command += ["--session-dir", str(agent_home / ".pi/sessions")]
        auth_files = [str(auth / "auth.json"), str(auth / "auth.json.lock")]
        auth_link = {"path": str(agent_home / ".pi/agent/auth.json"), "target": auth_files[0]}
        vendor_env["PI_CODING_AGENT_DIR"] = str(agent_home / ".pi/agent")
        vendor_env["WORKBENCH_PI_MODE"] = f"{location}-{authority}"
    # Use the canonical target directly: resolving /usr/share/zoneinfo would
    # require traversing /var before the child sandbox policy is installed.
    zoneinfo = Path("/private/var/db/timezone/zoneinfo")
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
        # Keep organization-managed Claude policy visible in the isolated home.
        "/Library/Application Support/ClaudeCode",
        "/usr/local/bin",
        "/opt/homebrew/Cellar",
        "/opt/homebrew/opt",
        "/opt/homebrew/bin",
        "/dev/null",
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/fd",
        "/dev/tty",
        str(zoneinfo),
        str(node.parent),
        str(node.parent.parent / "lib/node_modules/npm"),
        # Managed tool installations only, not host settings or package caches.
        str(home / ".local/share/uv/python"),
        # Browsers the host installed; Playwright's download host redirects to
        # Google storage, which the invariant domain list denies.
        str(home / "Library/Caches/ms-playwright"),
        *screenshot_directory(),
        *(docker["read"] if docker else []),
        str(home / ".npm-global/bin"),
        str(home / ".npm-global/global"),
        str(home / ".npm-global/lib/node_modules/agent-browser"),
        str(home / ".npm-global/lib/node_modules/pnpm"),
        str(runtime / "shell/native-sandbox.py"),
        *agent["read"],
        *harness["read"],
        str(root),
        str(agent_home),
        str(temp),
        *auth_files,
        *([claude_sessions["target"]] if claude_sessions else []),
    ]
    browser = tools.get("browser")
    if browser:
        read.append(str(Path(browser).parent))
    shared = [
        *(str(home / name) for name in ("code/public", "Desktop", "Downloads")),
        *grants.get("paths", []),
    ]
    # Node runs the supervisor before containment. Protect its executable and
    # loader tree from every launch-specific write grant, including symlink targets.
    bootstrap = node.resolve().parent
    if bootstrap.name == "bin":
        bootstrap = bootstrap.parent
    # Agent installations must also stay read-only so no session can alter later ones.
    installed = [
        bootstrap,
        executable.parent.resolve(),
        *(Path(path).resolve() for path in agent["read"]),
    ]
    for writable in [root, agent_home, temp, *(Path(path) for path in shared), auth]:
        writable = writable.resolve()
        for tool in installed:
            if tool == writable or tool in writable.parents or writable in tool.parents:
                raise ValueError(
                    "Managed write access overlaps the supervisor installation "
                    "or an agent installation; move the tool or checkout"
                )
    read.extend(shared)
    for grant in read:
        path = Path(grant)
        if not path.is_absolute() or any(char in grant for char in "*?[]"):
            raise ValueError("Read grants must be absolute literal paths, without glob characters")
        if path == home or path in home.parents:
            raise ValueError("Read grants cannot include the host home or its ancestors")

    def exclusions(name: str, required: bool) -> list[str]:
        path = home / ".config/workbench" / name
        if not path.is_file():
            if required:
                raise ValueError(f"Missing {name} policy; run workbench native prepare")
            return []
        entries = [
            line.strip().replace("~/", f"{home}/", 1)
            for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if any(not entry.startswith("/") or "\0" in entry or "\n" in entry for entry in entries):
            raise ValueError(f"Invalid absolute path in {name}")
        return entries

    hard_excludes = exclusions("hard-deny-paths", True)
    private_excludes = exclusions("private-paths", True)
    excludes = [*hard_excludes, *private_excludes]
    project_read, project_write = project_denials(root, home)
    invariant_domains = [
        "mail.google.com",
        "outlook.live.com",
        "outlook.office.com",
        "drive.google.com",
        "docs.google.com",
        "sheets.google.com",
        "slides.google.com",
        "*.googleapis.com",
        "*.googleusercontent.com",
    ]
    filesystem = {
        "denyRead": ["/", *excludes, *project_read],
        "allowRead": read,
        "allowWrite": [
            str(root),
            str(agent_home),
            str(temp),
            *shared,
            *auth_files,
            *auth_staging,
            *([claude_sessions["target"]] if claude_sessions else []),
        ],
        "denyWrite": [
            "/tmp/claude",
            "/private/tmp/claude",
            *excludes,
            *harness["read"],
            *project_write,
            *(str(runtime / name) for name in ("native", "shell", "hooks")),
        ],
    }
    denied_domains = ["localhost", *invariant_domains]
    denied_addresses = [
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
    ]
    policy = {
        "filesystem": filesystem,
        "network": {
            "allowedDomains": [],
            "deniedDomains": denied_domains,
            "deniedResolvedAddresses": denied_addresses,
            # Upstream also grants all outbound localhost ports with this option.
            "allowLocalBinding": False,
            # The browser daemon needs local IPC; host service sockets stay denied.
            "allowUnixSockets": [str(temp / "browser"), *([docker["socket"]] if docker else [])],
        },
    }
    env = {key: os.environ[key] for key in ("TERM", "COLORTERM", "LANG") if key in os.environ}
    env.update(
        {
            "HOME": str(agent_home),
            "TMPDIR": str(temp),
            "CLAUDE_CODE_TMPDIR": str(temp),
            # Keep Agent Browser's Unix sockets inside the per-session sandbox.
            # Separate doctor cleanup from the sandbox proxy's own socket files.
            "PI_AGENT_BROWSER_SOCKET_DIR": str(temp / "browser"),
            "AGENT_BROWSER_SOCKET_DIR": str(temp / "browser"),
            "PATH": (
                f"{node.parent}:{home}/.npm-global/bin:"
                "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            ),
            "SHELL": "/bin/bash",
            "NODE_USE_ENV_PROXY": "1",
            # Public trust roots, without admitting the Keychain service or credentials.
            "SSL_CERT_FILE": "/etc/ssl/cert.pem",
            "DEVELOPER_DIR": "/Library/Developer/CommandLineTools",
            "GIT_CONFIG_NOSYSTEM": "1",
            "PYTHONTZPATH": str(zoneinfo),
            "WORKBENCH_AGENT_AUTHORITY": authority,
            "WORKBENCH_AGENT_LOCATION": location,
            "WORKBENCH_HOST_HOME": str(home),
            "PLAYWRIGHT_BROWSERS_PATH": str(home / "Library/Caches/ms-playwright"),
            **({"DOCKER_HOST": f"unix://{docker['socket']}"} if docker else {}),
            **vendor_env,
            **git_identity(home, root),
            **repository_credentials(home, grants),
        }
    )
    if browser and browser_port:
        env.update(
            {
                "AGENT_BROWSER_EXECUTABLE_PATH": browser,
                # One fresh automation browser per session. Multiprocess Chromium
                # needs a separately reviewed, session-scoped Mach service design.
                "AGENT_BROWSER_ARGS": (
                    "--no-sandbox,--single-process,--no-zygote,"
                    f"--remote-debugging-port={browser_port}"
                ),
                "AGENT_BROWSER_PROFILE": str(temp / "browser-profile"),
                "WORKBENCH_BROWSER_PORT": str(browser_port),
            }
        )
    else:
        # Fail clearly instead of attempting incompatible full Chrome startup.
        env["AGENT_BROWSER_EXECUTABLE_PATH"] = str(runtime / "native/headless-shell-not-prepared")
    return {
        "root": str(root),
        "resume_hint": (
            "workbench: sessions live in this checkout's managed agent home; "
            "run `cc --resume <id>` from this checkout"
            if vendor == "claude" and claude_sessions is None
            else None
        ),
        "cwd": str(cwd.resolve()),
        "policy": policy,
        "env": env,
        "command": (
            [
                "/Library/Developer/CommandLineTools/usr/bin/python3",
                "-I",
                "-S",
                str(Path(__file__).resolve()),
                "--browser-session",
            ]
            if browser and browser_port
            else []
        )
        + [*command, *args],
        "node": str(node),
        "auth_link": auth_link,
        "claude_sessions": claude_sessions,
        "harness": harness,
        "mandatory_read": [*excludes, *project_read],
        "mandatory_write": [*excludes, *project_write],
        "scratch_links": [
            {"path": name, "target": str(home / name)} for name in ("Desktop", "Downloads")
        ],
        "authority": authority,
        "browser_port": browser_port if browser else 0,
        "ports": grants.get("ports", []),
        "aws_profile": grants.get("aws"),
        # Compose and other CLI plugins live in the client installation, not the isolated home.
        "docker_config": {"cliPluginsExtraDirs": docker["plugins"]} if docker else None,
    }


@contextlib.contextmanager
def state_directory(home: Path, directory: Path):
    """Open state directories without following links planted by earlier sessions."""
    relative = directory.relative_to(home)
    if ".." in relative.parts:
        raise ValueError("Agent state must stay inside its home")
    descriptor = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in relative.parts:
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
        yield descriptor
    finally:
        os.close(descriptor)


def share_claude_sessions(home: Path, source: Path, target: Path) -> None:
    """Join this native project namespace without parsing transcripts or discarding a copy."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    kept = []

    def names(descriptor):
        with os.scandir(descriptor) as entries:
            return [entry.name for entry in entries]

    def relation(src, dst, name):
        """Compare bytes only: equal, one copy extends the other, or they differ."""
        with contextlib.ExitStack() as stack:
            left, right = (
                stack.enter_context(
                    os.fdopen(os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd), "rb")
                )
                for fd in (src, dst)
            )
            while True:
                a, b = left.read(1 << 20), right.read(1 << 20)
                common = min(len(a), len(b))
                if a[:common] != b[:common]:
                    return "differ"
                if len(a) != len(b):
                    if a[common:] and not b[common:]:
                        return "differ" if right.read(1) else "managed-extends"
                    return "differ" if left.read(1) else "native-extends"
                if not a:
                    return "equal"

    def set_aside(src, name, relative):
        """Keep a conflicting copy outside the shared namespace instead of refusing launch."""
        with contextlib.ExitStack() as stack:
            current = os.dup(parent)
            stack.callback(lambda: os.close(current))
            for part in (f"{source.name}.conflicts", *relative):
                with contextlib.suppress(FileExistsError):
                    os.mkdir(part, mode=0o700, dir_fd=current)
                child = os.open(part, flags, dir_fd=current)
                os.close(current)
                current = child
            destination = name
            while True:
                try:
                    os.stat(destination, dir_fd=current, follow_symlinks=False)
                except FileNotFoundError:
                    break
                destination = f"{name}.{secrets.token_hex(4)}"
            os.rename(name, destination, src_dir_fd=src, dst_dir_fd=current)
        kept.append("/".join((*relative, name)))

    def reconcile(src, dst=None, relative=()):
        for name in names(src):
            info = os.stat(name, dir_fd=src, follow_symlinks=False)
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError("Claude session storage contains a link or special file")
            existing = None
            if dst is not None:
                with contextlib.suppress(FileNotFoundError):
                    existing = os.stat(name, dir_fd=dst, follow_symlinks=False)
            if (
                existing is None
                or (info.st_dev, info.st_ino) == (existing.st_dev, existing.st_ino)
                or (stat.S_ISDIR(info.st_mode) and stat.S_ISDIR(existing.st_mode))
            ):
                pass
            elif stat.S_ISREG(info.st_mode) and stat.S_ISREG(existing.st_mode):
                if name == "sessions-index.json":
                    continue
                # The same session resumed on both sides usually only appended records.
                outcome = relation(src, dst, name)
                if outcome in ("equal", "native-extends"):
                    os.unlink(name, dir_fd=src)
                elif outcome == "managed-extends":
                    # Keep the shorter native inode aside so a live writer cannot lose records.
                    set_aside(dst, name, ("native", *relative))
                else:
                    set_aside(src, name, relative)
                continue
            else:
                set_aside(src, name, relative)
                continue
            if stat.S_ISDIR(info.st_mode):
                with contextlib.ExitStack() as stack:
                    child = os.open(name, flags, dir_fd=src)
                    stack.callback(os.close, child)
                    other = None
                    if existing is not None:
                        other = os.open(name, flags, dir_fd=dst)
                        stack.callback(os.close, other)
                    reconcile(child, other, (*relative, name))

    def move(src, dst):
        for name in names(src):
            info = os.stat(name, dir_fd=src, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                with contextlib.suppress(FileExistsError):
                    os.mkdir(name, mode=0o700, dir_fd=dst)
                with contextlib.ExitStack() as stack:
                    child = os.open(name, flags, dir_fd=src)
                    stack.callback(os.close, child)
                    other = os.open(name, flags, dir_fd=dst)
                    stack.callback(os.close, other)
                    move(child, other)
                os.rmdir(name, dir_fd=src)
            elif stat.S_ISREG(info.st_mode):
                destination = (
                    f".workbench-index-{secrets.token_hex(12)}.bak"
                    if name == "sessions-index.json"
                    else name
                )
                # Preserve open descriptors; first migration still needs stopped sessions.
                with contextlib.suppress(FileExistsError):
                    os.link(
                        name, destination, src_dir_fd=src, dst_dir_fd=dst, follow_symlinks=False
                    )
                linked = os.stat(destination, dir_fd=dst, follow_symlinks=False)
                current = os.stat(name, dir_fd=src, follow_symlinks=False)
                if (
                    not stat.S_ISREG(linked.st_mode)
                    or (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino)
                    or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino)
                ):
                    raise ValueError("Claude session changed during migration; copies preserved")
                os.unlink(name, dir_fd=src)
            else:
                raise ValueError("Claude session storage contains a link or special file")

    with state_directory(home, source.parent) as parent:
        try:
            lock_fd = os.open(
                ".workbench-sessions.lock",
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
        except FileExistsError:
            lock_fd = os.open(".workbench-sessions.lock", os.O_RDWR | os.O_NOFOLLOW, dir_fd=parent)
        with os.fdopen(lock_fd, "r+") as lock:
            metadata = os.fstat(lock.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("Unsafe Claude session migration lock")
            fcntl.flock(lock, fcntl.LOCK_EX)
            with state_directory(home, target) as destination:
                try:
                    original = os.stat(source.name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    original = None
                if original and stat.S_ISLNK(original.st_mode):
                    if os.readlink(source.name, dir_fd=parent) != str(target):
                        raise ValueError("Unexpected Claude session link")
                    return
                if original:
                    with contextlib.ExitStack() as stack:
                        src = os.open(source.name, flags, dir_fd=parent)
                        stack.callback(os.close, src)
                        reconcile(src, destination)
                        if names(src):
                            # Native Claude rebuilds this cache from the merged JSONL files.
                            with contextlib.suppress(FileNotFoundError):
                                os.rename(
                                    "sessions-index.json",
                                    f".workbench-index-{secrets.token_hex(12)}.bak",
                                    src_dir_fd=destination,
                                    dst_dir_fd=destination,
                                )
                        move(src, destination)
                    try:
                        os.rmdir(source.name, dir_fd=parent)
                    except OSError as error:
                        if error.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                            raise
                        raise ValueError(
                            "Stop managed Claude sessions before first migration; "
                            "both transcript copies are preserved"
                        ) from error
                os.symlink(str(target), source.name, dir_fd=parent)
    if kept:
        print(
            f"workbench: kept {len(kept)} conflicting Claude history file(s) in "
            f"{source.parent / (source.name + '.conflicts')}",
            file=sys.stderr,
        )


def sync_codex_auth(home: Path, destination: Path) -> bool:
    """Refresh the isolated Codex login when the host has a newer OAuth rotation."""
    source = home / ".codex/auth.json"
    if not source.exists() or not destination.exists():
        return False

    def read_login(path: Path) -> bytes:
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_mode & 0o077
            ):
                raise ValueError("Model login file must be an owner-only regular file")
            return stream.read()

    source_bytes = read_login(source)
    source_value = json.loads(source_bytes)
    destination_value = json.loads(read_login(destination))
    if not isinstance(source_value, dict) or not isinstance(destination_value, dict):
        raise ValueError("Codex login file must contain an object")

    def refreshed_at(value: dict):
        raw = value.get("last_refresh")
        if not isinstance(raw, str):
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    source_refresh = refreshed_at(source_value)
    destination_refresh = refreshed_at(destination_value)
    if (
        source_refresh is None
        or destination_refresh is None
        or source_refresh <= destination_refresh
    ):
        return False

    with state_directory(home, destination.parent) as descriptor:
        temporary = f".workbench-auth-{secrets.token_hex(12)}"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=descriptor)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(source_bytes)
            os.replace(temporary, destination.name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=descriptor)
    return True


def prior_state(home: Path, path: Path) -> bytes:
    """Read bounded ordinary state, ignoring planted links and unsupported files."""
    with state_directory(home, path.parent) as descriptor:
        try:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
        except OSError:
            return b""
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_size > 1024 * 1024
            ):
                return b""
            return stream.read(1024 * 1024)


def codex_trust_tables(content: bytes) -> dict:
    """Accept only Codex's simple trust tables, never arbitrary TOML settings."""
    try:
        text = content.decode("utf-8")
    except UnicodeError:
        return {}
    # Intentional ceiling: unsupported TOML is discarded and Codex asks again.
    # A general parser belongs in the host projection, not this Python 3.9 bootstrap.
    if '"""' in text or "'''" in text:
        return {}
    records, current = {}, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            current = None
            match = re.fullmatch(r'\[(projects|hooks\.state)\.("(?:[^"\\]|\\.)*")\]', line)
            if match:
                try:
                    key = json.loads(match[2])
                except ValueError:
                    continue
                if json.dumps(key, ensure_ascii=False) != match[2]:
                    continue
                current = (match[1], key)
                records[current] = None if current in records else {}
        elif current and line and not line.startswith("#") and records[current] is not None:
            key, separator, raw = line.partition("=")
            key = key.strip()
            try:
                value = json.loads(raw.strip())
            except ValueError:
                value = None
            if not separator or key in records[current] or value is None:
                records[current] = None
            else:
                records[current][key] = value
    return {key: value for key, value in records.items() if value is not None}


def retain_codex_trust(content, previous, old_hooks, new_hooks, agent_home, root):
    """Carry this checkout's trust and unchanged, indexed projected hook records."""
    previous = codex_trust_tables(previous)
    tables = codex_trust_tables(content)
    hook_keys = set()
    try:
        for event, groups in json.loads(new_hooks).get("hooks", {}).items():
            snake = re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
            for group_index, group in enumerate(groups):
                for hook_index, _ in enumerate(group["hooks"]):
                    hook_keys.add(
                        f"{agent_home}/.codex/hooks.json:{snake}:{group_index}:{hook_index}"
                    )
    except (ValueError, TypeError, AttributeError, KeyError):
        hook_keys.clear()
    if old_hooks and old_hooks == new_hooks:
        tables.update(previous)
    else:
        project = previous.get(("projects", root))
        if project is not None:
            tables[("projects", root)] = project
    lines, skipping = [], False
    for line in content.decode("utf-8").splitlines(keepends=True):
        if line.lstrip().startswith("["):
            skipping = line.lstrip().startswith("[hooks.state.")
        if not skipping:
            lines.append(line)
    for (kind, key), values in sorted(tables.items()):
        project = (
            kind == "projects"
            and key == root
            and set(values) == {"trust_level"}
            and values["trust_level"] in ("trusted", "untrusted")
        )
        hook = (
            kind == "hooks.state"
            and key in hook_keys
            and set(values) == {"enabled", "trusted_hash"}
            and isinstance(values["enabled"], bool)
            and isinstance(values["trusted_hash"], str)
            and re.fullmatch(r"[a-fA-F0-9]{64}", values["trusted_hash"])
        )
        if project or hook:
            lines.append(f"\n[{kind}.{json.dumps(key, ensure_ascii=False)}]\n")
            lines.extend(f"{field} = {json.dumps(value)}\n" for field, value in values.items())
    return "".join(lines).encode("utf-8")


def initialize_home(plan: dict, home: Path) -> None:
    """Share harness assets, refresh preferences, and retain isolated mutable state."""
    agent_home = Path(plan["env"]["HOME"])
    with state_directory(home, agent_home):
        pass
    if plan.get("claude_sessions"):
        entry = plan["claude_sessions"]
        share_claude_sessions(home, Path(entry["path"]), Path(entry["target"]))
    harness = plan.get("harness", {"links": [], "files": []})
    # Snapshot before any projected file changes; manifest order is not significant.
    codex_files = {item["path"]: item["source"] for item in harness["files"]}
    previous_config = previous_hooks = new_hooks = b""
    if ".codex/config.toml" in codex_files:
        previous_config = prior_state(home, agent_home / ".codex/config.toml")
        previous_hooks = prior_state(home, agent_home / ".codex/hooks.json")
        if ".codex/hooks.json" in codex_files:
            new_hooks = Path(codex_files[".codex/hooks.json"]).read_bytes()
    links = [(agent_home / item["path"], item["target"], "harness") for item in harness["links"]]
    links += [
        (agent_home / item["path"], item["target"], "scratch")
        for item in plan.get("scratch_links", [])
    ]
    if plan.get("auth_link"):
        item = plan["auth_link"]
        links.append((Path(item["path"]), item["target"], "model login"))
    for path, target, label in links:
        path.relative_to(agent_home)
        with state_directory(home, path.parent) as descriptor:
            try:
                os.symlink(target, path.name, dir_fd=descriptor)
            except FileExistsError:
                try:
                    matches = os.readlink(path.name, dir_fd=descriptor) == target
                except OSError:
                    matches = False
                if matches:
                    continue
                try:
                    existing = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
                except OSError:
                    existing = None
                # Older projections copied some shared harness assets into the
                # isolated home. Exact manifest paths remain Workbench-owned, so
                # migrate only ordinary files; foreign links and directories fail.
                if label == "harness" and existing and stat.S_ISREG(existing.st_mode):
                    os.unlink(path.name, dir_fd=descriptor)
                    os.symlink(target, path.name, dir_fd=descriptor)
                    continue
                raise ValueError(f"Unexpected {label} link; refusing to overwrite") from None
    for item in harness["files"]:
        path = agent_home / item["path"]
        path.relative_to(agent_home)
        content = Path(item["source"]).read_bytes()
        if item["path"] == ".codex/config.toml":
            escaped_home = json.dumps(str(agent_home), ensure_ascii=False)[1:-1].encode()
            content = content.replace(b"__WORKBENCH_AGENT_HOME__", escaped_home)
            content = retain_codex_trust(
                content, previous_config, previous_hooks, new_hooks, agent_home, plan["root"]
            )
        write_state_file(home, path, content)
    if plan.get("docker_config"):
        content = json.dumps(plan["docker_config"]).encode()
        write_state_file(home, agent_home / ".docker/config.json", content)


def write_state_file(home: Path, path: Path, content: bytes) -> None:
    """Replace a file in agent-writable state without following planted links."""
    with state_directory(home, path.parent) as descriptor:
        # Atomic replacement also breaks hostile hardlinks; never truncate a state file.
        temporary = f".workbench-{secrets.token_hex(12)}"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=descriptor)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
            os.replace(temporary, path.name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=descriptor)


def browser_session(command: list[str]) -> None:
    """Verify a fresh browser's identity before allowing any vendor model input."""
    temporary = os.environ.get("TMPDIR", "")
    profile = os.environ.get("AGENT_BROWSER_PROFILE", "")
    port = os.environ.get("WORKBENCH_BROWSER_PORT", "")
    if (
        not command
        or os.environ.get("WORKBENCH_AGENT_AUTHORITY") != "managed"
        or not temporary
        or not Path(temporary).is_absolute()
        or profile != str(Path(temporary) / "browser-profile")
        or not port.isdecimal()
        or not 1024 <= int(port) <= 65535
    ):
        raise ValueError("Browser startup requires a prepared managed launch")
    environment = dict(os.environ)
    environment.pop("AGENT_BROWSER_CDP", None)
    environment.pop("AGENT_BROWSER_AUTO_CONNECT", None)
    browser = ["agent-browser", "--session", "workbench-startup", "--profile", profile]

    def invoke(arguments: list[str]) -> str:
        try:
            result = subprocess.run(
                browser + arguments,
                env=environment,
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise ValueError("Browser startup timed out; no agent input was submitted") from None
        if result.returncode:
            raise ValueError("Browser startup failed; no agent input was submitted")
        return result.stdout.strip()

    # The launcher owns a new scratch directory. Never remove or reuse an existing
    # profile: its endpoint could belong to a prior browser or another process.
    with contextlib.ExitStack() as stack:
        descriptor = os.open(temporary, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, descriptor)
        # Pi's wrapper requires private socket storage; the CLI otherwise creates
        # this directory with its default 0755 mode during eager startup.
        os.mkdir("browser", mode=0o700, dir_fd=descriptor)
        os.mkdir("browser-profile", mode=0o700, dir_fd=descriptor)
        profile_fd = os.open(
            "browser-profile", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
        )
        stack.callback(os.close, profile_fd)
        invoke(["open", "about:blank"])
        endpoint_fd = os.open(
            "DevToolsActivePort", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=profile_fd
        )
        stack.callback(os.close, endpoint_fd)
        metadata = os.fstat(endpoint_fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_size > 256:
            raise ValueError("Invalid browser endpoint file")
        content = os.read(endpoint_fd, 257).decode("ascii", errors="replace").splitlines()
        if (
            len(content) != 2
            or content[0] != port
            or not re.fullmatch(
                r"/devtools/browser/[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", content[1]
            )
        ):
            raise ValueError("Browser endpoint does not match this managed launch")
        endpoint = f"ws://127.0.0.1:{port}{content[1]}"
        if invoke(["get", "cdp-url"]) != endpoint:
            raise ValueError("Browser identity mismatch; no agent input was submitted")
    environment["AGENT_BROWSER_CDP"] = endpoint
    os.execvpe(command[0], command, environment)


def apply_profile(profile: str) -> None:
    """Apply once in this process, before any descendant gains the same identity."""
    import ctypes

    library = ctypes.CDLL("/usr/lib/libsandbox.1.dylib", use_errno=True)
    library.sandbox_init.argtypes = [
        ctypes.c_char_p,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    library.sandbox_init.restype = ctypes.c_int
    error = ctypes.c_char_p()
    if library.sandbox_init(profile.encode(), 0, ctypes.byref(error)):
        message = error.value.decode(errors="replace") if error.value else "unknown error"
        if error.value:
            library.sandbox_free_error(error)
        raise ValueError(f"Cannot apply managed session sandbox: {message}")


def apply_session(args: list[str], control_fd: int = 3) -> None:
    """Report the vendor exit privately, then end this sandbox's process lifetime."""
    import signal

    sandbox = args.index("/usr/bin/sandbox-exec")
    profile = args[sandbox + 2]
    if "\0" in profile or not profile.endswith(SESSION_SIGNAL_GUARD):
        raise ValueError("Managed session requires the final signal isolation guard")
    mode = os.fstat(control_fd).st_mode
    if not (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)):
        raise ValueError("Managed session requires a private supervisor status pipe")
    os.set_inheritable(control_fd, False)
    env = dict(os.environ)
    for assignment in args[1:sandbox]:
        key, value = assignment.split("=", 1)
        env[key] = value
    # Nothing below may execute without successful kernel-enforced signal isolation.
    # A separately applied identical profile cannot signal these descendants.
    apply_profile(profile)
    child = None
    code = 1

    def terminate(*_args):
        if child is not None:
            with contextlib.suppress(ProcessLookupError):
                child.terminate()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, lambda *_args: None)
    try:
        # fd3 must never reach vendor code, including a shell or detached child.
        child = subprocess.Popen(args[sandbox + 3 :], env=env, close_fds=True)
        status = child.wait()
        code = status if status >= 0 else 128 - status
    except (OSError, ValueError) as error:
        print(f"native sandbox: {error}", file=sys.stderr, flush=True)
    finally:
        try:
            os.write(control_fd, f"{code}\n".encode("ascii"))
            os.close(control_fd)
        finally:
            # macOS includes this guardian in kill(-1). The host consumes fd3's
            # exit code only when this guardian then dies from SIGKILL. A hostile
            # child can kill the guardian early; absence of status is an error.
            os.kill(-1, signal.SIGKILL)
    raise RuntimeError("Managed session cleanup did not terminate its guardian")


def main() -> None:
    if sys.argv[1:2] == ["--browser-session"]:
        browser_session(sys.argv[2:])
        return
    if sys.argv[1:2] == ["--apply"]:
        apply_session(
            harden(
                sys.argv[2],
                int(sys.argv[3]) if len(sys.argv) > 3 else 0,
                sys.argv[4] if len(sys.argv) > 4 else "",
                json.loads(sys.argv[5]) if len(sys.argv) > 5 else [],
            )
        )
    if sys.argv[1:2] == ["--refresh-aws"]:
        request = json.loads(sys.argv[2])
        home, agent_home = Path(request["home"]), Path(request["agent_home"])
        refresh_aws(home, agent_home, request["profile"], launching=False)
        return
    if sys.platform != "darwin":
        raise ValueError("The native boundary requires macOS")
    if len(sys.argv) < 3:
        raise ValueError("Usage: native-sandbox.py VENDOR LOCATION [AUTHORITY] [agent arguments]")
    home = Path.home().resolve()
    runtime = Path(__file__).resolve().parents[1] / "native"
    config = runtime / "tools.json"
    if not config.is_file():
        raise ValueError("Native runtime is not prepared; run workbench native prepare")
    # macOS Unix socket names are short; a nested project-state TMPDIR exceeds the limit.
    scratch = Path(tempfile.mkdtemp(prefix="wb-native-", dir="/private/tmp"))
    try:
        tools = json.loads(config.read_text())
        browser_port = 0
        if tools.get("browser"):
            # Selection is not reservation. The contained browser verifies this
            # endpoint before vendor startup; a competing listener fails closed.
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                browser_port = listener.getsockname()[1]
        if sys.argv[3:4] and sys.argv[3] in {"restricted", "daily", "unrestricted"}:
            raise ValueError("Retired authority; use co, cc, or p for managed launches")
        arg_start = 4 if sys.argv[3:4] == ["managed"] else 3
        plan = build_plan(
            Path.cwd(),
            home,
            tools,
            sys.argv[1],
            sys.argv[2],
            sys.argv[arg_start:],
            scratch=scratch,
            authority="managed",
            browser_port=browser_port,
        )
        if sys.argv[1] == "codex":
            sync_codex_auth(home, Path(plan["auth_link"]["target"]))
        initialize_home(plan, home)
        if plan["aws_profile"]:
            refresh_aws(home, Path(plan["env"]["HOME"]), plan["aws_profile"])
            plan["aws_refresh"] = {
                "home": str(home),
                "agent_home": plan["env"]["HOME"],
                "profile": plan["aws_profile"],
            }
    except Exception:
        scratch.rmdir()
        raise
    if sys.argv[1] == "shell":
        label = f"{sys.argv[1].upper()} · cloud > managed"
        print(f"{label} · {Path(plan['root']).name}", file=sys.stderr, flush=True)
    runner = Path(__file__).with_suffix(".mjs")
    os.execve(plan["node"], [plan["node"], str(runner), json.dumps(plan)], plan["env"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f"native sandbox: {error}", file=sys.stderr)
        sys.exit(1)
