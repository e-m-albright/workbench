# Managed terminal agents

Workbench's terminal launchers use a native macOS sandbox around the
entire agent process and its children. Lima and its editor/mobile bridges are
retired. The [launch matrix](../agents/pi/README.md#launch-modes-and-permission-guardrails)
owns command aliases; this document owns the security boundary and its limits.

## Daily use

Run `co`, `cc`, or `p` from an ordinary Git checkout. Each shows
`cloud > managed` and admits the selected checkout, `~/code/public`, `~/Desktop`,
and `~/Downloads`, with machine-local exclusions enforced throughout. The
isolated HOME maps those two scratch names to the actual host directories. There is
one hosted managed authority. Linked worktrees are not supported as managed
entrypoints. Invalid runtime, policy, repository, or sandbox state fails closed.

Full commands `codex`, `claude`, and `pi` keep native behavior and shared
configuration without adding this outer boundary. Native local Pi uses
`pi --route private --provider omlx`. Native vendor approval and sandbox settings
still apply. A full binary invoked inside a managed parent inherits its outer
restrictions; changing the executable name or clearing environment variables
cannot remove that policy. The [launch design catalogue](../agents/launch-design.md)
compares the routes and layers.

The `--restricted`, `--daily`, and `--unrestricted` shortcut flags are retired and
fail with migration guidance. Sourcing the launcher removes obsolete functions
including `cou`, `ccu`, `pih`, `pihr`, `pihu`, and `pil`. Pi's `-r` retains native
resume behavior.

Zed built-ins, external editor agents, Paseo providers, and desktop agents are
not covered by this terminal boundary. An editor or daemon can execute tool
requests with its own host permissions. Containing the requesting process does
not independently contain those host callbacks.

## Setup and persistent login

```sh
workbench native prepare
# Optional, once: seed existing provider logins without other host credentials.
workbench native prepare --authorize
# Metadata only: paths, projection, and login presence, not authentication.
workbench native status
# After signing in natively, explicitly replace one enrolled login with backup.
workbench native authorize codex --replace
workbench sync
cd /path/to/repository
co
p
cc
# Diagnostic commands; no model request:
workbench native run codex -- --version
workbench native run claude -- --version
workbench native run pi -- --version
workbench native run shell -- -c 'git status --short'
```

Preparation installs a pinned dependency tree with lifecycle scripts disabled,
applies the verified [dependency repair](dependencies.md),
resolves available agent binaries, and copies the small launch runtime outside
the checkout. It also records an already installed Playwright Chromium Headless
Shell. Host package installation remains the host repository's responsibility;
the launcher does not download a browser or fall back to personal Chrome.
Preparation and launch reject bootstrap executables beneath managed write
grants, including overlapping checkout or scratch roots. The same check covers
agent installations, both where a launcher link sits and where it points, so no
session can alter the agent binary that later sessions run. Claude's native
installer links a stable `~/.local/bin/claude` to a replaceable file under
`~/.local/share/claude/versions/`. Preparation records the link and admits the
versions directory read-only; each launch resolves the link and refuses a target
outside that directory. The pinned runtime canonicalizes read grants, so the
launch hands Seatbelt the resolved file rather than the link. A missing vendor
does not block the other vendors. Provider
authentication and subscriptions remain separate prerequisites for model use.

The clean environment sets `SSL_CERT_FILE=/etc/ssl/cert.pem`. Codex needs these
public certificate roots because Keychain access is deliberately denied. Without
them, Codex 0.162.1 fails during account routing with an `UnknownIssuer` TLS
error, surfaced as `workspace routing discovery failed`. The certificate fix
works with the existing network proxy; direct network grants are unnecessary.

Each repository gets an isolated agent home under
`~/.local/share/workbench/agent-state/`. Provider login files persist separately
under `~/.local/share/workbench/model-auth/` and are shared across repositories:

- Codex links its project-specific authentication file to its shared login file.
- Pi links only its authentication file to the shared login; the canonical target supplies the shared refresh lock. Settings, project-trust decisions and sessions stay in its isolated project home.
- Claude copies only the AI-login section of its credential entry, not the connector credentials stored alongside it, and shares its file refresh lock.

Enrollment preserves existing managed login material rather than overwriting a
refreshed login implicitly. Presence does not prove provider validity. An empty
Claude login is reported as unavailable. Sign in through the full vendor command
from the host, then use `workbench native authorize VENDOR --replace` to back up
and replace that vendor's managed login. `workbench native status [VENDOR]`
reports preparation, state paths, projection, and login file metadata without
reading tokens or history. Changing repositories or restarting does not
intentionally require another login; revocation, expiry, and refresh interaction
with native sessions can still require recovery.

These are provider account credentials, not newly issued inference-only tokens.
Their existing account scopes may grant more than model inference. The selected
managed agent can deliberately read, change, or steal its admitted login
file; this exposure is an accepted tradeoff. No browser credentials, general
Keychain access, connector grants, unrelated host session namespaces, or credential-bearing MCP
configuration are imported. Codex's account-backed apps feature is disabled,
but that setting does not reduce a stolen token's provider-side scopes.

Keeping ordinary provider login simple is the chosen tradeoff. A separate
credential broker is not required for this workflow; reconsider it only if
provider-token exposure stops being acceptable. Pi enrollment may include
multiple provider logins from its authentication store.

## Enforced permissions

| Resource | Managed terminal policy |
| --- | --- |
| Selected checkout | Read and write, including curated vault prose, structured world-model state, reviewed meeting notes, Git history, ignored files, and untracked files unless explicitly excluded. |
| Machine-local private paths | Denied for reads and writes, including named paths inside the selected checkout. Raw meeting recordings, transcripts, and sidecars remain excluded; choosing a repository does not authorize those sources. |
| Environment files | Real `.env` and `.env.*` paths are denied at every depth, including files created after launch. Documentation templates ending in `.example`, `.sample`, or `.template` remain usable. |
| Other repositories and personal files | `~/code/public`, `~/Desktop`, and `~/Downloads` are also admitted, plus any directories the owner grants the checkout. The user's macOS temporary items directory is readable so dragged screenshots open. Unselected private repositories, ingress, personal files, credentials, and host startup files remain outside the grants. |
| Agent state | One persistent home per repository plus private session scratch. Claude shares only the matching native project transcript namespace as described [below](#claude-session-history). |
| Provider credentials | Only the selected vendor's enrolled login and necessary refresh-lock paths are admitted. |
| Host integrations | Keychain and tested application-service routes, host process arguments, private network destinations, and host API sockets are blocked. One ephemeral browser control port and any loopback ports granted to the checkout are admitted; unrelated localhost services remain blocked. Docker is admitted only to checkouts granted it. |
| Public network | Public TCP destinations on ports 80 and 443 are permitted through the runtime proxy. This is a port policy, not application-protocol verification. Private resolved destinations and configured email, Google Drive, and shared Google API/content endpoints are denied. |
| Harness configuration | Shared instructions, skills, extensions, prompts, themes, installed plugin code, model preferences, and interface settings. Host code assets are read-only; settings and caches remain in the isolated home. |
| Local inference and editor/mobile protocols | Unsupported by the managed launcher. |

Managed private-source policy lives at
`~/.config/workbench/private-paths`; its absence fails closed. Invariant policy
lives at `~/.config/workbench/hard-deny-paths`; it is required for every managed launch. The default invariant policy blocks any directory named
`confidential` regardless of case, all local Google Drive trees, local email
stores, browser profiles, and Google connector credentials. Owner additions
remain machine-local rather than entering this public repository. These
exclusions supplement the managed default-deny read policy, rather than
being the sole protection for other Mac files. Necessary system and installed
tool paths are also admitted. The launcher starts with a clean environment,
without ambient credential variables, shell startup overrides, or inherited
upstream proxy settings. Owner and project exclusions are emitted as final
mandatory denials after all read/write grants. Synthetic canaries cover equal,
ancestor, nested, and glob overlaps; an overlap cannot silently reopen a denied
path merely because a tool or checkout requires it.

Managed Python, Node/npm and pnpm installations are readable so existing
repository tooling works. Their host configuration and package caches are not
imported; new per-project caches live in the isolated home.

A pinned [Anthropic Sandbox Runtime](https://github.com/anthropics/sandbox-runtime)
generates the Seatbelt policy and network proxies. Workbench validates the
generated command shape and adds denials for host process inspection,
credential/application services, shared memory, distributed notifications,
and environment files. Only the inherited terminal devices are admitted, and
terminal input injection through `TIOCSTI` is denied.

The terminal application remains outside the child process sandbox. Host
terminal configuration denies programmatic clipboard reads. The owner accepts
prompt-free writes through OSC 52 for convenient copying; terminal programs can
replace clipboard contents. Manual paste remains an explicit user action.
Do not infer that blocking a clipboard command inside the agent also
blocks terminal callbacks. The installed Ghostty configuration has
`clipboard-read = deny` and `clipboard-write = allow`; its parser and host gate
pass. Existing Ghostty windows require **Command+Shift+Comma** or **Reload Config**
to load the settings. Other terminal applications are not verified by this check.

Managed shortcuts use an isolated projection of the native harness. Full native
commands launched from the host have no Workbench outer boundary. `workbench sync`
derives a credential-free configuration projection from the installed settings
under `native/harness/`; there is no separately maintained managed theme,
model default, or skill catalogue. Each launch refreshes those preferences into
its isolated home and links the shared code assets read-only. Private connector
grants, environment secrets, unrelated host conversation namespaces, and unrelated
project state are excluded. Claude's transcript exception is described below.
Tools remain subject to the outer sandbox even when their
extensions load normally. A shared tool that requires protected host access
cannot acquire that access by being enabled in the harness. Read-only installed
plugin and extension trees are trusted code assets, not recursively sanitized
file collections. Keep credentials and private data outside those admitted trees.

Managed Claude reads organizational policy under
`/Library/Application Support/ClaudeCode` without write access. `/usr/local/bin`
is admitted for installed tools. Repository-local `user.name` and `user.email`
override global identity defaults in the clean environment. Only these scalar
values are imported; local includes, host Git configuration, hooks, and credential
helpers are not imported. Claude compaction preferences survive projection.

### Claude session history

Managed Claude retains an isolated settings home while its matching
`.claude/projects/<encoded cwd>` directory links to the same namespace under
native `~/.claude/projects/`. The earlier transcript split was a side effect of
isolated storage. Sharing this directory changes history storage; it does not
share settings, credentials, all host transcripts, rewind state, or file history.
The matching namespace is readable and writable inside the managed boundary.

Stop managed Claude sessions before the first migration and avoid concurrent
writers while it runs. Existing disjoint transcript files merge without parsing
their contents; conflicting paths preserve both copies and refuse launch.
Session index caches are backed up for Claude to rebuild. The migration lock
serializes Workbench launches and does not make arbitrary live writer migration
safe.

Native namespace encoding replaces characters outside ASCII letters and digits
with hyphens, so different working directories can collide. This is a shared native namespace,
not a guarantee of history belonging to exactly one checkout. Workbench supports
ordinary encoded paths of at most 200 characters whose original code points lie
within the Basic Multilingual Plane. Longer paths and characters outside that
range retain isolated transcripts and a `cc --resume <id>` hint; the launcher does
not guess the vendor's hashing scheme. The current working directory determines
the namespace, while the ordinary Git checkout determines the managed state home.

Pi and Codex transcripts continue to use isolated managed storage. Resuming any
confidential local conversation with a hosted model still requires its owner's
release.

October 20, 2026 acceptance verified synthetic selected-namespace reads and
appends inside the real macOS boundary while sibling namespace reads and writes
were denied. Native Claude 2.1.304's `--bare --resume` picker discovered a migrated
synthetic transcript after index-cache removal. No prompt or model request was
submitted; this establishes picker discovery, not provider continuation or rewind.

### Project policy and vendor state

Project `.claude/settings.json` and `.claude/settings.local.json` filesystem
`denyRead` and `denyWrite` lists are snapshotted at startup and applied to every
managed vendor. Final mandatory denials make them tighten the launch grants
after every allow; allow lists are ignored. Malformed or symlinked policy is
refused. This is a startup snapshot of agent-writable project configuration,
not immutable owner policy; machine-local exclusions remain the owner boundary.
Changes require a new launch.

### Per-checkout grants

`~/.config/workbench/repository-grants.json` lists what one checkout receives
beyond the default boundary. Sessions cannot read or edit it. Each key is a
checkout path, and each value may contain:

- `github`: a Keychain service holding a GitHub token scoped to that
  repository. The launch exports it as `GH_TOKEN` with a Git credential helper,
  so `git push` and `gh` work without host credential helpers.
- `aws`: one AWS profile. The supervisor writes that profile's short-lived keys
  into the session's own credentials file and refreshes them every five minutes.
  The SSO cache never enters the session.
- `ports`: loopback ports the checkout's own services use, such as its local
  database. The session can serve on any local address but reach only these
  host ports.
- `docker`: `true` admits the running engine's socket (Docker Desktop,
  OrbStack, or Colima), sets `DOCKER_HOST`, and reads the client installation
  so `docker compose` works.
- `paths`: extra existing directories, such as a sibling checkout, admitted
  read-write. Machine-local exclusions still apply inside them.

```json
{
  "~/code/example/app": {
    "github": "workbench-github-app",
    "ports": [5432],
    "docker": true,
    "paths": ["~/code/example/app-ci"]
  }
}
```

Docker access removes this boundary for that checkout: a container can mount
any host path the engine shares and run with the owner's file permissions.
Grant it only to checkouts whose agent work you would also run unsandboxed.
Provider-side scope remains the limit for GitHub and AWS credentials; a session
can use or leak what it receives. Every managed session can also launch
Playwright's multiprocess Chromium, which needs its per-process rendezvous
Mach service, from the host's `~/Library/Caches/ms-playwright` install.

Codex keeps selected-root folder trust and unchanged projected hook decisions
across preference refresh. Retention accepts only narrow canonical trust tables;
malformed or unsupported syntax causes a fresh prompt. It never imports arbitrary
agent-written permissions, preferences, other roots, or linked state files.
Changed hook projection invalidates retained hook decisions. Managed Pi preserves
a valid worker timeout while explicit private/local startup intent fails closed.
Pi workers may create sibling worktrees under public code, Desktop, or Downloads;
their direct child processes inherit the parent's selected provider, model,
thinking level, and outer boundary. Changed output requires an explicit
adopted/rejected disposition before cleanup. Unique commits and failed Git
inspections preserve the worktree. Worker entrypoints reject recursive delegation;
this is a workflow guard rather than an additional operating-system boundary.

The Google connector implementation is retired; its credential and endpoint
denials remain. Strava's remaining read-only tools require local inference and
their own OAuth grant, which is unavailable to managed hosted sessions.

For contained Codex sessions, the native permissions item labels the outer
boundary. Its named inner full-access profile does not replace that boundary.
Explicit caller permission/profile overrides keep their native labels.
Pi's separate Codex-login quota probe is disabled inside
the native boundary. These display settings import no host tools or credentials.

The vendor's nested operating-system sandbox is disabled inside this enforced
outer policy because macOS does not support nesting those policies. Vendor
action approvals remain a separate layer and cannot expand the outer boundary.

The destructive guard, `agents/shared/hooks/guard-destructive-shell.sh`, runs
before every shell command in every hook-capable harness, inside or outside
the launcher. It is a friction layer, not a security boundary. It parses each
command with shell quoting respected and applies a rule only when the word is
the command being run, so text in quotes, grep patterns, and heredocs do not
trigger it. Recursive deletes are allowed under temporary directories and for
build output such as `node_modules`, `.venv`, `__pycache__`, and `dist`.
`git branch -D` is allowed when a tag or remote branch already contains the
branch's commits. `git push` and `gh` writes that are chained, piped, or
redirected are blocked, so they run alone and reach the normal approval. Code
run by an interpreter, such as `python -c`, is not inspected. If the guard
fails internally, it blocks the command.

## Accepted risks and limits

Readable repository content can be sent to public destinations. Selecting a
repository is therefore an explicit release of its admitted decision-ready
content to the active provider, not permission to inspect unrelated machine
state or excluded raw sources. Review Git history, ignored files, caches,
recovery exports, and other retained data before admitting a repository; a
clean working-tree diff is not a privacy review.
Neither this boundary nor local inference determines confidentiality obligations.
Removing old history can eliminate retired content from an active checkout, but
the retained root snapshot remains readable. Approve that snapshot explicitly;
preserve recovery copies outside admitted paths and account for other refs,
reflogs, remote copies, and clones before claiming historical removal.

This is a pathname policy, not content labeling. A pre-existing hardlink inside
an admitted directory can expose the same bytes as an excluded filename. A
synthetic probe reproduced that limitation. Separate probes deny creating a new
hardlink from the protected name and renaming an ancestor containing protected
paths. Keep private aliases outside all admitted directories; detecting arbitrary
pre-existing aliases would require a different content-admission design.

Edits are live. An agent can damage admitted repository files or change source,
shell configuration, hooks, or services that the owner later runs outside the
sandbox. That later host execution is an explicitly accepted workflow risk,
not a vulnerability fixed by native isolation or the former VM.

Native isolation shares the Mac's kernel and is not equivalent to a separate VM.
It does not promise safety against every operating-system exploit, every
terminal feature, or future vendor behavior. Publicly exposed personal services
also remain public destinations; the network policy cannot infer ownership.

Repository-specific session history persists until deliberately removed. Do not
resume confidential local conversations with a cloud provider without release.
Existing processes retain their launch-time boundary and tools after sync; start
a fresh process to use the current policy.

## Browser workflow

The contained browser uses installed Chromium Headless Shell with a fresh
session profile, an ephemeral control port, and private daemon sockets.
`--single-process --no-zygote` avoids Chromium's cross-process Mach rendezvous;
no broad Mach service grants are added. Chromium's nested sandbox is disabled
because the whole process already runs inside the Workbench Seatbelt boundary.
The intentional ceiling is one automation browser per agent session, without
Chromium's internal process isolation. Multiprocess browsing requires a reviewed
session-specific service design. Personal browser profiles remain denied.

The supervisor starts a fresh browser inside containment before the vendor
starts. It validates that browser's `DevToolsActivePort` port and UUID against
the endpoint before pinning Agent Browser to it. A process that claims the chosen
port cannot silently become the automation endpoint; startup fails closed.
Installed acceptance verified both free-port startup and collision rejection.

Existing Playwright exporters must honor the managed browser interface. In a
managed session, connect with `chromium.connectOverCDP(process.env.AGENT_BROWSER_CDP)`
and create a page in `browser.contexts()[0]`. Do not launch the desktop Chrome
channel or create an additional browser context: the contained browser uses
one fresh context and a single process. Missing managed endpoints must fail
clearly rather than falling back to host Chrome.

Playwright's streamed `page.pdf()` transfer fails with `IO.read: Read failed`
in this contained browser. For bounded documents, use the Chromium DevTools
`Page.printToPDF` command with `transferMode: "ReturnAsBase64"`, then write the
returned PDF bytes to an admitted output path. Preserve the document's explicit
print options, tagging, and page ranges. This buffers the PDF in memory; large
document workflows need a separately verified streaming design. Installed Pi
acceptance exercised an actual project exporter producing tagged 2-, 3-, and
16-page PDFs, including overflow and content checks. Agent Browser's successful
PDF command alone does not establish compatibility with every project exporter.

Lifecycle cleanup applies the policy once through macOS `libsandbox`, with a
contained guardian and inherited policy for the vendor and its descendants.
The guardian reports the vendor's exit through a private descriptor and uses
same-sandbox process termination to remove remaining children. Live synthetic
checks verified ordinary exit cleanup, including detached children. A
malicious child can kill the guardian first; forced supervisor termination also
cannot promise graceful cleanup or revoke every surviving descendant's rights.

October 13, 2026 acceptance covered installed Agent Browser 0.38.1 and Pi's
installed browser wrapper: public HTTPS navigation, synthetic HTML interaction,
snapshots, screenshots, PDF export, PDF text extraction, rendered PDF inspection,
and synthetic private-file denial. Supervisor cleanup was exercised by leaving
the browser open on agent exit, then checking that its control port closed and
session scratch disappeared. The reusable probe is
`tests/fixtures/native-browser-probe.mjs`.

Agent Browser 0.38.1 still treats inherited proxy settings as a reason to launch
a browser for URL `read`. The contained Headless Shell makes that path usable,
but it is not browserless. The earlier 0.39.0 patch remains uninstalled; package
upgrades belong to the host repository. Full desktop Chrome and attachment to
personal browser sessions are not supported by this boundary.

## Verification and implementation

Unit tests cover configuration parity, credential exclusion, repository admission,
clean environments, per-repository state, missing policy, credential enrollment,
planted state symlinks and hardlinks, and adaptation of
the pinned runtime. Focused correction tests cover private-route rejection,
trust retention, login replacement, scratch mappings, bootstrap placement,
worktree preflight, and filesystem aliases. The macOS CI job runs integration tests with a disposable
prepared home, synthetic files and host services, and a public HTTPS positive
control. The same tests remain opt-in for local runs:

```sh
WORKBENCH_NATIVE_CANARY_HOME=/private/tmp/example-pilot \
  uv run pytest tests/test_native_canary.py
```

Prepare the disposable home first with `workbench.native.prepare(home)`.
Canaries exercise workspace edits and child inheritance, outside reads/writes,
symlink escapes, future nested environment files, Python and Git, host TCP/Unix
sockets, process arguments, and macOS service handles. Terminal startup and shell
probes have been exercised with Codex and Pi without paid model requests. Claude
binary startup works; unauthenticated onboarding remains a limit, and a signed-out
account does not establish authenticated Claude operation. Synthetic authentication tests cover persistence and startup,
not long-lived OAuth refresh or every vendor feature.

The maintained implementation is:

- `agents/shared/shell/native-sandbox.py`: repository admission, state setup, credential paths, policy, and checked sandbox entry.
- `agents/shared/shell/native-sandbox.mjs`: pinned runtime and network proxy lifecycle.
- `agents/shared/sandbox/package.json` and its lockfile: runtime dependency pin.
- `src/workbench/native.py`: installation and optional credential enrollment.
- `src/workbench/native_config.py`: derived shared harness configuration without host data or connector credentials.
- `agents/shared/shell/agent-launchers.zsh`: managed shortcuts and native-command separation.
- `agents/shared/shell/agent-sandbox.zsh`: single managed authority for standalone launches.
- `tests/test_native*.py` and `tests/test_agent_launchers.py`: regression and canary coverage.

Lima was removed to avoid VM provisioning, duplicated guest tools, mounts, and
guest login management. Reconsider stronger isolation if live host execution
can no longer be an accepted risk or a shared-kernel boundary is insufficient;
do not retain a second unused sandbox implementation.

The [design catalogue](../agents/launch-design.md) records the chosen routes and
layers. The [six-model review](../decisions/managed-launch-review.md) records the
original findings, owner-approved corrections, synthetic evidence, and accepted
limits. Original acceptance predates the correction pass; final deployment and
installed browser/PDF verification must follow its last source change.
