# Antigravity CLI

Re-enabled at the owner's request on 2026-10-25. Dotfiles owns the
`antigravity-cli` Homebrew cask, which installs the binary as `agy`. Workbench
owns global instructions, skills, and shell launcher naming. The IDE and
Gemini CLI remain retired.

## Launch names

| Workbench boundary | Native launch without adding that boundary |
| --- | --- |
| `p` | `pi` |
| `co` | `codex` |
| `cc` | `claude` |
| `agy` (experimental; startup blocked) | `antigravity`, `antig`, `agrav`, `agravity` |

The native Antigravity functions use `command agy` to bypass the managed shell
function, preserving arguments and the installed binary's behavior. Native
names do not remove an already inherited sandbox. `antigravity --sandbox`
requests Google's terminal-only sandbox, not Workbench's whole-process boundary.

## Managed launch limitation

`agy` routes through the installed native boundary with an isolated home and
read-only links to global rules and skills. Host settings, plugins, MCP
configuration, credentials, and session history are not imported. There is no
Antigravity model-login enrollment command; status labels its isolated login
unverified. Remote control and microphone servers are rejected.

On CLI 1.4.7, `agy --help` succeeds inside the real macOS boundary, but
`workbench native run antigravity -- models` fails before normal startup:

```text
Failed to start: listen tcp 127.0.0.1:0: bind: operation not permitted
```

The CLI needs a dynamically allocated local listener. The existing boundary
allows only owner-assigned loopback destinations, not arbitrary host services.
Its normal authentication also uses the OS keyring, which Workbench deliberately
denies. Do not enable unrestricted loopback or Keychain access to bypass these
limits. `agy` remains fail-closed, without automatic native fallback. A supported
fixed-port or Unix-socket transport and a reviewed model-only login path are
needed before claiming operational managed support. Existing Google API denials
also remain unchanged; no authenticated model request has been tested.

## Configuration management

`workbench sync antigravity` deploys `agents/shared/rules.md` to
`~/.gemini/AGENTS.md` and the canonical skill trees to
`~/.gemini/antigravity-cli/skills`. It also installs shared launchers and the
derived isolated harness. Preview, rules-only, no-skills, backup, and drift
behavior applies. `all` includes this target for the personal profile; the work
profile excludes it. Unmanaged skills are reported as external.

Native settings, authentication, plugins, MCP configuration, and session state
remain untouched. The isolated harness starts from empty settings rather than
importing account or connector configuration.

Current native contracts:

- [Global rules](https://antigravity.google/docs/rules/) include
  `~/.gemini/AGENTS.md`; repository `AGENTS.md` is discovered natively. The
  documented single-rule limit is 24,000 bytes.
- [CLI skills](https://antigravity.google/docs/skills/?tab=cli) use
  `~/.gemini/antigravity-cli/skills` and become interactive slash commands.
- [CLI settings](https://antigravity.google/docs/cli/using/) live in
  `~/.gemini/antigravity-cli/settings.json`.
- [Authentication](https://antigravity.google/docs/install/?tab=cli) uses the
  native OS keyring, with an interactive sign-in flow when no login exists.
- [Permissions](https://antigravity.google/docs/permissions/) and the vendor
  sandbox remain distinct from Workbench's isolation contract.
