# Antigravity CLI

Dotfiles owns the `antigravity-cli` Homebrew cask, which installs the binary as
`agy`. Workbench owns global instructions, skills, and shell launcher naming.
The IDE and Gemini CLI remain retired.

## Launch names

| Workbench boundary | Native launch without adding that boundary |
| --- | --- |
| `p` | `pi` |
| `co` | `codex` |
| `cc` | `claude` |
| `agy` | `antigravity`, `antig`, `agrav`, `agravity` |

The native Antigravity functions use `command agy` to bypass the managed shell
function, preserving arguments and the installed binary's behavior. Native
names do not remove an already inherited sandbox. `antigravity --sandbox`
requests Google's terminal-only sandbox, not Workbench's whole-process boundary.

## Managed startup and login

`agy` uses the installed native boundary with a per-checkout isolated home and
read-only links to global rules and skills. Host settings, plugins, MCP
configuration, credentials, and session history are not imported. Remote
control and microphone servers are rejected. There is no automatic native
fallback.

CLI 1.4.7 requires a dynamic loopback listener even for its model-list command.
Workbench admits loopback binding and inbound traffic for Antigravity without
allowing outbound connections to arbitrary localhost services. It leaves the
upstream `allowLocalBinding` switch off because that also enables broad
outbound localhost access. macOS also accepts wildcard bindings under its
localhost listener filter; this is not a LAN exposure boundary. The CLI itself
binds `127.0.0.1`. Other agents' listener rules are unchanged.

Host Keychain access remains denied. Sign in interactively through `agy`; any
vendor file-storage fallback belongs to the isolated workspace home. Workbench
does not enroll a native Antigravity login or request OAuth grants on the
owner's behalf. Authentication remains user-controlled. A real terminal is
required for the interactive UI; the API shell reaches the TTY requirement but
cannot perform that sign-in. Session login sharing is deliberately not
implemented; add model-only enrollment only after its native storage contract
is verified.

Antigravity alone can reach these Google API hosts over HTTPS:

- `oauth2.googleapis.com` for OAuth.
- `www.googleapis.com` only for GET requests to `/oauth2/v2/userinfo` and
  `/oauth2/v3/tokeninfo`.
- `daily-cloudcode-pa.googleapis.com` and `cloudcode-pa.googleapis.com` for
  model and client services.

All other Google API hosts remain denied. Drive and mail domains, private
network destinations, and host sockets retain their existing denials. The
Antigravity proxy uses the pinned runtime's ephemeral TLS termination to apply
path checks on the shared `www.googleapis.com` host; opaque CONNECT and SOCKS
tunnels are refused so they cannot bypass those checks. The temporary CA is
trusted only by the managed session, not installed in the host trust store.
No request headers, bodies, or credentials are logged by Workbench. Other
agents retain their existing proxy mode.

Real macOS canaries verify loopback binding, denial of unrelated host
connections, identity endpoint reachability, and denial of
Drive access through both HTTP and SOCKS. `agy models` reaches the expected
sign-in response instead of the former bind failure. Account sign-in and an
authenticated model request remain unverified until the owner completes login.

## Configuration management

`workbench sync antigravity` deploys `agents/shared/rules.md` to
`~/.gemini/AGENTS.md` and skill trees to `~/.gemini/config/skills`. It also
installs shared launchers and the derived isolated harness. Preview,
rules-only, no-skills, backup, and drift behavior applies. `all` includes this
target for the personal profile; the work profile excludes it. Unmanaged skills
are reported as external.

The installed CLI migrates the legacy `~/.gemini/antigravity-cli/skills` path
into `~/.gemini/config/skills`. Workbench follows the resulting location rather
than recreating the legacy layout on every sync. The isolated-home migration
recognizes only the exact old Workbench skill link; foreign links still fail
closed. Existing legacy host skill copies are left for the vendor's native
migration, not deleted along with potential external additions.

Native settings, authentication, plugins, MCP configuration, and session state
remain untouched. The isolated harness starts from empty settings rather than
importing account or connector configuration.

## Native references

- [Global rules](https://antigravity.google/docs/rules/) include
  `~/.gemini/AGENTS.md`; repository `AGENTS.md` is discovered natively. The
  documented single-rule limit is 24,000 bytes.
- [Skills](https://antigravity.google/docs/skills/?tab=cli) use `SKILL.md` and
  become interactive slash commands. The 1.4.7 migration behavior above is
  verified locally; the documentation still lists the legacy CLI path.
- [CLI settings](https://antigravity.google/docs/cli/using/) live in
  `~/.gemini/antigravity-cli/settings.json`.
- [Authentication](https://antigravity.google/docs/install/?tab=cli) describes
  native keyring login and interactive authorization.
- [Permissions](https://antigravity.google/docs/permissions/) and the vendor
  sandbox remain distinct from Workbench's isolation contract.
