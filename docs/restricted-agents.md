# Restricted terminal agents

Workbench's restricted terminal launchers use a native macOS sandbox around the
entire agent process and its children. Lima and its editor/mobile bridges are
retired. The [launch matrix](pi-capabilities.md#launch-modes-and-permission-guardrails)
owns command aliases; this document owns the security boundary and its limits.

## Daily use

Run `co`, `pi`, or `cc` from an ordinary Git checkout. All three show
`hosted > restricted` in their footer, without a separate startup banner.
The boundary admits that checkout without creating a VM, copying a
repository, or requiring an update step after edits. Linked Git worktrees are
not supported. A launch fails closed if its runtime, policy, repository, or
sandbox validation fails; it never silently becomes unrestricted.

Explicit unrestricted launchers remain available for host workflows. Local Pi
uses only `pil`, asks for confirmation, and has host authority. There is no
restricted tunnel to the local inference service, and its other consumers are
unchanged.

Zed built-ins, external editor agents, Paseo providers, desktop agents, and
direct vendor binaries are not covered by this boundary. An editor or daemon
can execute an agent's tool request with its own host permissions, even when
the requesting agent process is sandboxed. Do not label those integrations
restricted without independently containing the host tools.

## Setup and persistent login

```sh
workbench native prepare
# Optional, once: seed existing provider logins without other host credentials.
workbench native prepare --authorize
workbench sync
cd /path/to/repository
co
pi
# Diagnostic commands; no model request:
workbench native run codex -- --version
workbench native run claude -- --version
workbench native run pi -- --version
workbench native run shell -- -c 'git status --short'
```

Preparation installs a pinned dependency tree with lifecycle scripts disabled,
resolves available agent binaries, and copies the small launch runtime outside
the checkout. A missing vendor does not block the other vendors. Provider
authentication and subscriptions remain separate prerequisites for model use.

Each repository gets an isolated agent home under
`~/.local/share/workbench/agent-state/`. Provider login files persist separately
under `~/.local/share/workbench/model-auth/` and are shared across repositories:

- Codex links its project-specific authentication file to its shared login file.
- Pi links only its authentication file to the shared login; the canonical target supplies the shared refresh lock. Settings, project-trust decisions and sessions stay in its isolated project home.
- Claude copies only the AI-login section of its credential entry, not the connector credentials stored alongside it, and shares its file refresh lock.

Enrollment preserves already usable native credentials rather than replacing
refreshed logins. An empty Claude login is reported as unavailable. After a
provider login is restored, repeat preparation with `--authorize` if its native
cache has not been enrolled. Changing repositories or restarting a session does
not intentionally require another login. Provider revocation, expiry, and
refresh interactions with unrestricted host sessions can still require one.

These are provider account credentials, not newly issued inference-only tokens.
Their existing account scopes may grant more than model inference. The selected
restricted agent can deliberately read, change, or steal its admitted login
file; this exposure is an accepted tradeoff. No browser credentials, general
Keychain access, connector grants, host sessions, or credential-bearing MCP
configuration are imported. Codex's account-backed apps feature is disabled,
but that setting does not reduce a stolen token's provider-side scopes.

Keeping ordinary provider login simple is the chosen tradeoff. A separate
credential broker is not required for this workflow; reconsider it only if
provider-token exposure stops being acceptable. Pi enrollment may include
multiple provider logins from its authentication store.

## Enforced permissions

| Resource | Restricted terminal policy |
| --- | --- |
| Selected checkout | Read and write, including Git history, ignored files, and untracked files unless explicitly excluded. |
| Machine-local private paths | Denied for reads and writes, including paths inside the selected checkout. Existing vault exclusions remain; choosing its repository does not authorize the vault. |
| Environment files | `.env` and `.env.*` paths are denied at every depth, including files created after launch. |
| Other repositories and personal files | Not admitted merely because they are open or used by another agent. |
| Agent state | One persistent home per repository plus a private temporary directory for the session. |
| Provider credentials | Only the selected vendor's enrolled login and necessary refresh-lock paths are admitted. |
| Host integrations | Keychain and tested application-service routes, host process arguments, private network destinations, and host API sockets are blocked. |
| Public network | Public HTTP and HTTPS are permitted through the runtime proxy; literal IP and private resolved destinations are denied. |
| Harness configuration | Shared instructions, skills, extensions, prompts, themes, installed plugin code, model preferences, and interface settings. Host code assets are read-only; settings and caches remain in the isolated home. |
| Local inference and editor/mobile protocols | Unsupported by the restricted launcher. |

The machine-local policy is `~/.config/workbench/private-paths`; its absence
fails closed. Its exclusions supplement a default-deny read policy, rather than
being the sole protection for other Mac files. Necessary system and installed
tool paths are also admitted. The launcher starts with a clean environment,
without ambient credential variables, shell startup overrides, or inherited
upstream proxy settings.

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
blocks terminal callbacks.

Restricted and unrestricted launches use the same harness. `workbench sync`
derives a credential-free configuration projection from the installed settings
under `native/harness/`; there is no separately maintained restricted theme,
model default, or skill catalogue. Each launch refreshes those preferences into
its isolated home and links the shared code assets read-only. Private connector
grants, environment secrets, host conversation history, and unrelated project
state are excluded. Tools remain subject to the outer sandbox even when their
extensions load normally. A shared tool that requires protected host access
cannot acquire that access by being enabled in the harness.

Codex's native permissions item labels the outer boundary. Its named inner
full-access profile does not replace that boundary. Unrestricted Codex retains its
inner workspace profile, and explicit caller permission/profile overrides keep
their native labels. Pi's separate Codex-login quota probe is disabled inside
the native boundary. These display settings import no host tools or credentials.

The vendor's nested operating-system sandbox is disabled inside this enforced
outer policy because macOS does not support nesting those policies. Vendor
action approvals remain a separate layer and cannot expand the outer boundary.

## Accepted risks and limits

Readable repository content can be sent to public destinations. Review Git
history, ignored files, caches, recovery exports, and other retained data before
admitting a repository; a clean working-tree diff is not a privacy review.
Neither this boundary nor local inference determines confidentiality obligations.
Removing old history can eliminate retired content from an active checkout, but
the retained root snapshot remains readable. Approve that snapshot explicitly;
preserve recovery copies outside admitted paths and account for other refs,
reflogs, remote copies, and clones before claiming historical removal.

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

## Verification and implementation

Unit tests cover configuration parity, credential exclusion, repository admission,
clean environments, per-repository state, missing policy, credential enrollment,
planted state symlinks and hardlinks, and adaptation of
the pinned runtime. The macOS CI job runs integration tests with a disposable
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
binary startup works; a signed-out account does not establish authenticated
Claude operation. Synthetic authentication tests cover persistence and startup,
not long-lived OAuth refresh or every vendor feature.

The maintained implementation is:

- `agents/shared/shell/native-sandbox.py`: repository admission, state setup, credential paths, policy, and checked sandbox entry.
- `agents/shared/shell/native-sandbox.mjs`: pinned runtime and network proxy lifecycle.
- `agents/shared/sandbox/package.json` and its lockfile: runtime dependency pin.
- `src/workbench/native.py`: installation and optional credential enrollment.
- `src/workbench/native_config.py`: derived shared harness configuration without host data or connector credentials.
- `agents/shared/shell/agent-launchers.zsh`: interactive aliases and unrestricted confirmation.
- `agents/shared/shell/agent-sandbox.zsh`: explicit authority routing for standalone launches.
- `tests/test_native*.py` and `tests/test_agent_launchers.py`: regression and canary coverage.

Lima was removed to avoid VM provisioning, duplicated guest tools, mounts, and
guest login management. Reconsider stronger isolation if live host execution
can no longer be an accepted risk or a shared-kernel boundary is insufficient;
do not retain a second unused sandbox implementation.
