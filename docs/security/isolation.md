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
grants, including overlapping checkout or scratch roots. A missing vendor does
not block the other vendors. Provider
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
Keychain access, connector grants, host sessions, or credential-bearing MCP
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
| Other repositories and personal files | `~/code/public`, `~/Desktop`, and `~/Downloads` are also admitted. Unselected private repositories, ingress, personal files, credentials, and host startup files remain outside the grants. |
| Agent state | One persistent home per repository plus a private temporary directory for the session. |
| Provider credentials | Only the selected vendor's enrolled login and necessary refresh-lock paths are admitted. |
| Host integrations | Keychain and tested application-service routes, host process arguments, private network destinations, and host API sockets are blocked. One ephemeral browser control port is admitted; unrelated localhost services remain blocked. |
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
terminal configuration must deny programmatic clipboard reads and confirm
programmatic writes through OSC 52; manual paste remains an explicit user
action. Do not infer that blocking a clipboard command inside the agent also
blocks terminal callbacks. The installed Ghostty configuration has
`clipboard-read = deny` and `clipboard-write = ask`; its parser and host gate
pass. Existing Ghostty windows require **Command+Shift+Comma** or **Reload Config**
to load the settings. Other terminal applications are not verified by this check.

Managed shortcuts use an isolated projection of the native harness. Full native
commands launched from the host have no Workbench outer boundary. `workbench sync`
derives a credential-free configuration projection from the installed settings
under `native/harness/`; there is no separately maintained managed theme,
model default, or skill catalogue. Each launch refreshes those preferences into
its isolated home and links the shared code assets read-only. Private connector
grants, environment secrets, host conversation history, and unrelated project
state are excluded. Tools remain subject to the outer sandbox even when their
extensions load normally. A shared tool that requires protected host access
cannot acquire that access by being enabled in the harness. Read-only installed
plugin and extension trees are trusted code assets, not recursively sanitized
file collections. Keep credentials and private data outside those admitted trees.

Managed Claude reads organizational policy under
`/Library/Application Support/ClaudeCode` without write access. `/usr/local/bin`
is admitted for installed tools. Repository-local `user.name` and `user.email`
override global identity defaults in the clean environment. Only these scalar
values are imported; local includes, host Git configuration, hooks, and credential
helpers are not imported. Claude compaction
preferences survive projection. On terminal exit, managed Claude names
`cc --resume <id>` because native Claude uses a different session home.

Project `.claude/settings.json` and `.claude/settings.local.json` filesystem
`denyRead` and `denyWrite` lists are snapshotted at startup and applied to every
managed vendor. Final mandatory denials make them tighten the launch grants
after every allow; allow lists are ignored. Malformed or symlinked policy is
refused. This is a startup snapshot of agent-writable project configuration,
not immutable owner policy; machine-local exclusions remain the owner boundary.
Changes require a new launch. No repository AWS credential broker, Docker socket,
or general repository-port grants are added.

Codex keeps selected-root folder trust and unchanged projected hook decisions
across preference refresh. Retention accepts only narrow canonical trust tables;
malformed or unsupported syntax causes a fresh prompt. It never imports arbitrary
agent-written permissions, preferences, other roots, or linked state files.
Changed hook projection invalidates retained hook decisions. Managed Pi preserves
a valid worker timeout while explicit private/local startup intent fails closed.

For contained Codex sessions, the native permissions item labels the outer
boundary. Its named inner full-access profile does not replace that boundary.
Explicit caller permission/profile overrides keep their native labels.
Pi's separate Codex-login quota probe is disabled inside
the native boundary. These display settings import no host tools or credentials.

The vendor's nested operating-system sandbox is disabled inside this enforced
outer policy because macOS does not support nesting those policies. Vendor
action approvals remain a separate layer and cannot expand the outer boundary.

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
Final live acceptance for this revised startup path remains required.

Lifecycle cleanup applies the policy once through macOS `libsandbox`, with a
contained guardian and inherited policy for the vendor and its descendants.
The guardian reports the vendor's exit through a private descriptor and uses
same-sandbox process termination to remove remaining children. Final lifecycle
canaries must verify the revised path before claiming complete cleanup. A
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
