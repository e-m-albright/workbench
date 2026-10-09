"""Standalone native boundary: no imports or executable discovery from a checkout."""

import contextlib
import hashlib
import json
import os
import secrets
import shlex
import stat
import subprocess
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
; Certificate evaluation only; Go tools such as gh fail TLS checks without it.
(allow mach-lookup (global-name "com.apple.trustd.agent"))
; Chromium, as Playwright runs it, hands ports to its own children through a
; per-process name; refusing it aborts the browser at startup.
(allow mach-register mach-lookup
  (global-name-prefix "org.chromium.Chromium.MachPortRendezvousServer."))
; Match future environment files and confidential directories too, not just
; paths present at launch. Character classes make the match case-insensitive.
(deny file-read* file-write* file-write-create file-write-unlink
  (regex "/[.][Ee][Nn][Vv]($|/|[.]ENV_SUFFIX)")
  (regex "/[Cc][Oo][Nn][Ff][Ii][Dd][Ee][Nn][Tt][Ii][Aa][Ll]($|/)"))
"""


def _excluding(words: list[str]) -> str:
    """Match a path component that is not exactly one of the words, ignoring case.

    Seatbelt regex has no lookahead; an earlier lookahead silently inverted
    the rule, so the complement is spelled out as a prefix tree instead.
    """
    branches = [] if "" in words else ["($|/)"]
    heads = sorted({word[0].lower() for word in words if word})
    branches.append("[^/" + "".join(c + c.upper() for c in heads) + "]")
    for head in heads:
        rest = [word[1:] for word in words if word and word[0].lower() == head]
        branches.append(f"[{head}{head.upper()}]{_excluding(rest)}")
    return "(" + "|".join(branches) + ")"


ENV_TEMPLATES = ["example", "sample", "template"]
GUARD = GUARD.replace("ENV_SUFFIX", _excluding(ENV_TEMPLATES))


def loopback_rules(ports: list[int]) -> str:
    """Let a session serve locally and reach only the owner's listed loopback ports.

    Binding and inbound are local operations, so any address is safe there (the
    runtime explains why IPv4-mapped sockets need "*:*"). Outbound stays limited
    to the listed ports, never every service on the Mac's loopback.
    """
    if not ports:
        return ""
    if not all(isinstance(port, int) and 0 < port < 65536 for port in ports):
        raise ValueError("Loopback ports must be integers from 1 to 65535")
    rules = ['(allow network-bind (local ip "*:*"))', '(allow network-inbound (local ip "*:*"))']
    rules += [f'(allow network-outbound (remote ip "localhost:{port}"))' for port in ports]
    return "\n" + "\n".join(rules) + "\n"


def harden(command: str, ports: list[int] = ()) -> list[str]:
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


def git_identity(home: Path, cwd: Path) -> dict:
    """Carry the host's commit identity, not its gitconfig, into the isolated home.

    Only the owner's global file is read (cwd still selects includeIf blocks);
    the agent-writable repository config is never consulted outside the sandbox.
    """
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
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        value = result.stdout.strip()
        if result.returncode == 0 and value:
            identity.update(dict.fromkeys(names, value))
    return identity


REPOSITORY_GRANTS = {"github", "aws", "ports"}
# Git asks this helper for GitHub credentials; it answers from the launch token
# so neither a host credential helper nor the protected .git/config is needed.
GITHUB_HELPER = (
    '!f() { test "$1" = get && '
    "printf 'username=x-access-token\\npassword=%s\\n' \"$GH_TOKEN\"; }; f"
)


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

    `~/.config/workbench/repo-credentials.json` maps a checkout path to a
    Keychain service holding a GitHub token scoped to that repository, an AWS
    profile whose role should reach only a sandbox account, and the loopback
    ports its own services use. Provider-side scope is the real credential
    limit; the session can use or leak what it receives.
    """
    path = home / ".config/workbench/repo-credentials.json"
    if not path.is_file():
        return {}
    try:
        config = json.loads(path.read_text())
    except ValueError as error:
        raise ValueError(f"Unreadable {path}: {error}") from None
    if not isinstance(config, dict):
        raise ValueError(f"{path} must map checkout paths to credentials")
    entry = None
    for key, value in config.items():
        checkout = Path(str(home) + key[1:] if key.startswith("~/") else key)
        if checkout.resolve() == root:
            entry = value
    if entry is None:
        return {}
    names = (
        {key: value for key, value in entry.items() if key != "ports"}
        if isinstance(entry, dict)
        else None
    )
    if (
        names is None
        or not set(entry) <= REPOSITORY_GRANTS
        or not all(isinstance(v, str) and v for v in names.values())
        or not isinstance(entry.get("ports", []), list)
    ):
        raise ValueError(
            f"{path}: each checkout maps 'github' and 'aws' to names and 'ports' to a list"
        )
    loopback_rules(entry.get("ports", []))
    return entry


def repository_credentials(home: Path, root: Path, run=subprocess.run) -> dict:
    """Issue the GitHub token and AWS profile settings assigned to this checkout.

    AWS keys are written by `refresh_aws`, not passed here.
    """
    entry = repository_grants(home, root)
    issued = {}
    if "github" in entry:
        service = entry["github"]
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
    if "aws" in entry:
        profile = entry["aws"]
        # The session's profile shares the host profile's name, so a project
        # setting such as AWS_PROFILE resolves the same way inside and outside.
        issued["AWS_PROFILE"] = profile
        with contextlib.suppress(ValueError):
            command = [aws_command(), "configure", "get", "region", "--profile", profile]
            region = host_output(home, command, "", run)
            issued.update({"AWS_REGION": region, "AWS_DEFAULT_REGION": region})
    return issued


def refresh_aws(home: Path, agent_home: Path, profile: str, run=subprocess.run) -> None:
    """Write one profile's short-lived keys into the session's own credentials file.

    A role assumed from an SSO session lasts at most an hour, so the supervisor
    calls this again during the session; the host CLI reuses its cached keys
    until they near expiry. The SSO cache itself never enters the session.
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
    exported = host_output(home, [*command, "--format", "process"], failure, run)
    try:
        keys = json.loads(exported)
        lines = [
            f"[{profile}]",
            f"aws_access_key_id = {keys['AccessKeyId']}",
            f"aws_secret_access_key = {keys['SecretAccessKey']}",
        ]
    except (ValueError, KeyError, TypeError):
        raise ValueError(failure) from None
    if keys.get("SessionToken"):
        lines.append(f"aws_session_token = {keys['SessionToken']}")
    write_state_file(home, agent_home / ".aws/credentials", "\n".join(lines).encode() + b"\n")


def project_denials(root: Path, home: Path) -> tuple[list[str], list[str]]:
    """Honor a checkout's Claude sandbox deny lists, which can only tighten the boundary.

    The agent can edit these files, so allow lists are never read from them.
    Paths follow Claude Code's sandbox rules: absolute, ~/home, or project-relative.
    """
    found: dict[str, list[str]] = {"denyRead": [], "denyWrite": []}
    for name in ("settings.json", "settings.local.json"):
        path = root / ".claude" / name
        if not path.is_file():
            continue
        try:
            settings = json.loads(path.read_text())
        except ValueError as error:
            raise ValueError(f"Unreadable project policy {path}: {error}") from None
        filesystem = (settings.get("sandbox") or {}).get("filesystem") or {}
        for key, paths in found.items():
            entries = filesystem.get(key, [])
            if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
                raise ValueError(f"{path}: sandbox.filesystem.{key} must be a list of paths")
            for entry in entries:
                if entry == "~" or entry.startswith("~/"):
                    paths.append(str(home) + entry[1:])
                elif entry.startswith("/"):
                    paths.append(entry)
                else:
                    paths.append(str(root / entry.removeprefix("./")))
    return found["denyRead"], found["denyWrite"]


def build_plan(
    cwd: Path,
    home: Path,
    tools: dict,
    vendor: str,
    location: str,
    args: list,
    scratch=None,
    authority="restricted",
) -> dict:
    """Build a managed boundary around one checkout and isolated agent state."""
    if authority not in {"restricted", "unrestricted"}:
        raise ValueError("Unknown agent authority")
    if location != "hosted" and not (location == "local" and authority == "unrestricted"):
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
    manifest = runtime / "native/harness/manifest.json"
    if not manifest.is_file():
        raise ValueError("Missing shared harness; run workbench sync")
    harness = json.loads(manifest.read_text())[vendor]
    if vendor == "codex":
        command += [
            "-c",
            'default_permissions="cloud > repo"',
            "-c",
            'permissions={"cloud > repo"={filesystem={":root"="write"},network={enabled=true}}}',
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
        command += ["--settings", json.dumps({"sandbox": {"enabled": False}})]
        auth_files = [str(auth / ".credentials.json"), str(auth / ".storage-write.lock")]
        auth_env["CLAUDE_SECURESTORAGE_CONFIG_DIR"] = str(auth)
    elif vendor == "pi":
        command += ["--session-dir", str(agent_home / ".pi/sessions")]
        auth_files = [str(auth / "auth.json"), str(auth / "auth.json.lock")]
        auth_link = {"path": str(agent_home / ".pi/agent/auth.json"), "target": auth_files[0]}
        auth_env["PI_CODING_AGENT_DIR"] = str(agent_home / ".pi/agent")
        auth_env["WORKBENCH_PI_MODE"] = f"{location}-{authority}"
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
        # Organization-managed Claude Code policy; skipping it would drop admin rules.
        "/Library/Application Support/ClaudeCode",
        "/opt/homebrew/Cellar",
        "/opt/homebrew/opt",
        "/opt/homebrew/bin",
        "/usr/local/bin",
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
        str(home / ".npm-global/bin"),
        str(home / ".npm-global/global"),
        str(home / ".npm-global/lib/node_modules/agent-browser"),
        str(home / ".npm-global/lib/node_modules/pnpm"),
        *agent["read"],
        *harness["read"],
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

    def exclusions(name: str, required: bool) -> list[str]:
        path = home / ".config/workbench" / name
        if not path.is_file():
            if required:
                raise ValueError(f"Missing {name} policy; run workbench native prepare")
            return []
        return [
            line.strip().replace("~/", f"{home}/", 1)
            for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

    hard_excludes = exclusions("hard-deny-paths", True)
    private_excludes = exclusions("private-paths", authority == "restricted")
    excludes = [*hard_excludes, *private_excludes] if authority == "restricted" else hard_excludes
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
    # The owner's handoff folder; private and hard exclusions still apply inside it.
    desktop = str(home / "Desktop")
    if authority == "restricted":
        filesystem = {
            "denyRead": ["/", *excludes, *project_read],
            "allowRead": [*read, desktop],
            "allowWrite": [str(root), str(agent_home), str(temp), desktop, *auth_files],
            "denyWrite": [
                "/tmp/claude",
                "/private/tmp/claude",
                *excludes,
                *harness["read"],
                *project_write,
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
    else:
        # Unrestricted means broad host authority, not permission to cross the
        # owner's invariant machine-local exclusions.
        filesystem = {
            "denyRead": [*hard_excludes, *project_read],
            "allowRead": ["/"],
            "allowWrite": ["/"],
            "denyWrite": [*hard_excludes, *harness["read"], *project_write],
        }
        denied_domains = invariant_domains
        denied_addresses = []
    # Docker controls the whole host, so only host authority may reach it.
    sockets = []
    if authority == "unrestricted":
        sockets = [
            "/var/run/docker.sock",
            "/private/var/run/docker.sock",
            str(home / ".orbstack/run/docker.sock"),
            str(home / ".docker/run/docker.sock"),
        ]
    policy = {
        "filesystem": filesystem,
        "network": {
            "allowedDomains": [],
            "deniedDomains": denied_domains,
            "deniedResolvedAddresses": denied_addresses,
            # The runtime pairs local binding with outbound loopback, which
            # would reach every host service, so only host authority gets it.
            "allowLocalBinding": authority == "unrestricted",
            "allowUnixSockets": sockets,
        },
    }
    env = {key: os.environ[key] for key in ("TERM", "COLORTERM", "LANG") if key in os.environ}
    env.update(
        {
            "HOME": str(agent_home),
            "TMPDIR": str(temp),
            "CLAUDE_CODE_TMPDIR": str(temp),
            "PATH": (
                f"{node.parent}:{home}/.npm-global/bin:"
                "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
            ),
            "SHELL": "/bin/bash",
            "NODE_USE_ENV_PROXY": "1",
            "DEVELOPER_DIR": "/Library/Developer/CommandLineTools",
            "GIT_CONFIG_NOSYSTEM": "1",
            "PYTHONTZPATH": str(zoneinfo),
            "WORKBENCH_AGENT_AUTHORITY": authority,
            "WORKBENCH_AGENT_LOCATION": location,
            "WORKBENCH_HOST_HOME": str(home),
            **auth_env,
            **git_identity(home, root),
            "PLAYWRIGHT_BROWSERS_PATH": str(home / "Library/Caches/ms-playwright"),
            **repository_credentials(home, root),
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
        "harness": harness,
        "authority": authority,
        "aws_profile": env.get("AWS_PROFILE"),
        "ports": repository_grants(home, root).get("ports", []),
        "resume_hint": resume_hint(vendor, authority),
    }


def resume_hint(vendor: str, authority: str):
    """Name the launcher that can see this checkout's isolated session history."""
    if vendor != "claude":
        return None
    launcher = "ccu" if authority == "unrestricted" else "cc"
    return (
        "workbench: sessions live in this checkout's managed agent home, so bare "
        f"`claude --resume` cannot find them; run `{launcher} --resume <id>` from this checkout"
    )


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


def initialize_home(plan: dict, home: Path) -> None:
    """Share harness assets, refresh preferences, and retain isolated mutable state."""
    agent_home = Path(plan["env"]["HOME"])
    with state_directory(home, agent_home):
        pass
    harness = plan.get("harness", {"links": [], "files": []})
    links = [(agent_home / item["path"], item["target"], "harness") for item in harness["links"]]
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
        write_state_file(home, path, content)


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


def main() -> None:
    if sys.argv[1:2] == ["--apply"]:
        ports = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
        os.execv("/usr/bin/env", harden(sys.argv[2], ports))
    if sys.argv[1:2] == ["--refresh-aws"]:
        request = json.loads(sys.argv[2])
        refresh_aws(Path(request["home"]), Path(request["agent_home"]), request["profile"])
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
        authority = (
            sys.argv[3]
            if sys.argv[3:4] and sys.argv[3] in {"restricted", "unrestricted"}
            else "restricted"
        )
        arg_start = 4 if sys.argv[3:4] and sys.argv[3] in {"restricted", "unrestricted"} else 3
        plan = build_plan(
            Path.cwd(),
            home,
            tools,
            sys.argv[1],
            sys.argv[2],
            sys.argv[arg_start:],
            scratch=scratch,
            authority=authority,
        )
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
        location_label = "local" if plan["env"]["WORKBENCH_AGENT_LOCATION"] == "local" else "cloud"
        authority_label = "repo" if plan["authority"] == "restricted" else "host"
        label = f"{sys.argv[1].upper()} · {location_label} > {authority_label}"
        print(f"{label} · {Path(plan['root']).name}", file=sys.stderr, flush=True)
    runner = Path(__file__).with_suffix(".mjs")
    os.execve(plan["node"], [plan["node"], str(runner), json.dumps(plan)], plan["env"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f"native sandbox: {error}", file=sys.stderr)
        sys.exit(1)
