---
name: paseo-management
description: Diagnose and repair Paseo desktop, daemon, mobile, authentication, renderer registry, and Tailscale-direct connections on macOS. Use when Paseo will not start, stays Connecting, rejects a password, or mobile cannot connect.
---

# Paseo Management

Repair Paseo by reconciling four layers: installed version, daemon process, daemon configuration, and each client's saved connection registry. A healthy daemon does not prove the desktop renderer is selecting the right endpoint.

## Preserve the intended topology

Ask or infer which topology the user wants before changing network settings:

- **Desktop only:** daemon listens on `127.0.0.1:6767`; desktop connects to localhost.
- **Tailscale direct:** daemon listens on the Mac's current Tailscale IPv4 address; desktop and mobile both connect to that address; relay stays disabled.
- **Paseo relay:** enable only after explicit approval because it creates an external connection.

Preserve an established Tailscale-direct workflow unless the user asks to replace it. Do not present relay as required for mobile access.

## Use the matching CLI

Prefer the CLI bundled with the installed desktop app:

```bash
PASEO=/Applications/Paseo.app/Contents/Resources/bin/paseo
"$PASEO" --version
"$PASEO" daemon status --json
```

A stale global CLI may be an older release and report or launch incompatible state. Compare versions before trusting it.

## Diagnose in order

1. Inspect the daemon status with the bundled CLI.
2. Inspect the listener and owning process:
   ```bash
   lsof -nP -iTCP:6767 -sTCP:LISTEN
   ```
3. Inspect the current Tailscale address when direct access is intended:
   ```bash
   tailscale ip -4
   ```
4. Inspect configuration shape without printing password hashes or credentials:
   - `~/.paseo/config.json`
   - daemon listen target
   - relay enabled state
   - whether `daemon.auth` exists
5. Read recent evidence from:
   - `~/.paseo/daemon.log`
   - `~/Library/Logs/Paseo/main.log`
6. Distinguish these states:
   - Port conflict or stale daemon
   - Daemon unreachable at the selected endpoint
   - `auth_required` or invalid password
   - Daemon healthy while the renderer remains stuck on Connecting

Stop stale daemons with Paseo's graceful command before considering process signals:

```bash
"$PASEO" daemon stop --timeout 15 --json
```

Restart through the desktop app or supported daemon command. Avoid force-killing unless graceful shutdown times out and the user approves escalation.

## Back up before configuration changes

Create a timestamped copy of `~/.paseo/config.json` before editing. Change only the fields supported by the diagnosis. Preserve `~/.paseo/agents` and the rest of the Paseo home.

Do not reset all Application Support data to repair one stale connection. Never print or repeat a password, pairing secret, or password verifier in the response.

## Tailscale-direct topology

For the tested Paseo 0.4.x direct topology:

1. Resolve the Mac's current Tailscale IPv4 address.
2. Set `daemon.listen` to `<tailscale-ip>:6767`.
3. Keep `daemon.relay.enabled` false.
4. Point both desktop and mobile at `<tailscale-ip>:6767` with TLS off unless the user's setup explicitly adds TLS.
5. Use Tailscale identity, encryption, and access-control lists as the network boundary.

Bind to the Tailscale interface itself rather than `0.0.0.0`; the latter also exposes Paseo on other interfaces. If the Tailscale address changes, update both daemon configuration and client registries.

### Authentication limitation

In Paseo 0.4.x, `daemon.auth` applies to localhost as well as remote clients. Adding a password while the desktop registry has no matching credential produces `auth_required` and can lock the desktop out even though the daemon is healthy.

Do not restore an old password verifier merely because a backup contains one. First prove every client has the matching plaintext credential. For the direct topology above, prefer Tailscale access controls over an unverified stale Paseo password.

## Repair stale desktop renderer state

When the daemon is reachable but the desktop stays Connecting, inspect the renderer registry instead of resetting all user data. The relevant local-storage key is:

```text
@paseo:daemon-registry
```

A stale registry may retain a retired IP, duplicate connection IDs, a wrong preferred connection, or an obsolete password after the daemon configuration has changed.

Use Electron remote debugging only as a temporary, local repair mechanism:

1. Quit Paseo gracefully.
2. Relaunch temporarily with `--remote-debugging-port=9222`.
3. Attach with `agent-browser` through CDP.
4. Inspect local-storage keys first, then return a sanitized registry that replaces credentials with `[set]` or omits them.
5. Update only `@paseo:daemon-registry`:
   - Preserve the existing `serverId`.
   - Replace duplicate or retired connections with one intended endpoint.
   - Set `preferredConnectionId` to that connection.
   - Omit obsolete passwords.
6. Reload and verify the full workspace UI appears.
7. Close the browser session, quit Paseo, and relaunch normally.
8. Confirm nothing listens on port 9222.

Treat renderer local storage as user state. Do not clear the entire directory when one key is sufficient.

## Verify the repair

Require evidence for every relevant surface:

- Correct process listens on the intended address and port.
- A TCP probe reaches the Tailscale endpoint when using direct mode.
- Desktop logs show `Client connected via hello` from the intended endpoint.
- The desktop displays the full workspace UI, not merely a running process.
- Mobile logs show a connection from a different Tailscale peer address when the phone is online.
- `validationFailed`, `originRejected`, `hostRejected`, and invalid-password counters remain clear for the new session.
- Relay state matches the user's choice.
- Temporary debugging port 9222 is closed.
- Projects, workspaces, and agent records remain present.

Report what was directly verified and ask the user to test only surfaces that were unavailable during verification.

## Common causal chain

When an upgrade appears to break everything, check for compounded drift rather than choosing one symptom:

1. An old CLI-managed daemon still owns the port.
2. The desktop-managed daemon starts with different listen or auth settings.
3. The renderer persists the old endpoint independently of `config.json`.
4. Mobile persists its own copy of that endpoint and credential.

Reconcile all four layers to one topology. Fixing only the daemon can leave the renderer Connecting; fixing only the renderer can make mobile unreachable.
