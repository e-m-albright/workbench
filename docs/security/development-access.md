---
title: Development access and sandbox friction
lang: en
---

The operating-system boundary and command guards solve different problems.
Preserve demonstrated protections against unrelated private files, credential
stores, host services, and installed agent configuration. Do not treat every
blocked development command as evidence that those protections are necessary.

## Development contract

An admitted project should be able to run its documented tests, use its approved
GitHub identity, and inspect its approved deployment and logs. Failures should
name the missing executable, grant, service, credential, or policy rule. Copying
a checkout, disguising a command, or adding an interpreter wrapper is not a fix.

Project tooling stays with the project. Host tools and credential enrollment
stay with the host owner. Workbench owns the launch boundary and its
[per-checkout grants](https://github.com/e-m-albright/workbench/blob/main/docs/security/isolation.md#per-checkout-grants), not another project runner,
GitHub client, AWS client, or credential broker.

## Verified sources of friction

This is a source-level assessment on 2026-10-23, supplemented by the maintained
synthetic macOS probes. It is not a complete security audit or a claim that every
reported application failure has been reproduced.

| Friction | Existing cause | Next action |
| --- | --- | --- |
| A project gate needs a local database or Docker. | Pi permits authorized development containers and database migrations; managed sessions still need their checkout's Docker and loopback-port grants. | Reproduce the documented gate and identify missing service access. Docker control remains a broad owner-approved trust exception, not a database-only permission. |
| GitHub reads cannot authenticate. | Host Keychain and ordinary credential helpers are unavailable. The selected checkout needs its repository GitHub grant. | Check grant selection and token scope without printing token values. Do not infer that all `gh` commands are prohibited. |
| PR creation or merge was blocked despite standing authorization. | Pi permits normal `gh pr` commands. Repository instructions choose direct-to-main shipping or PRs; generic API writes and unrelated mutations remain guarded. | Follow the repository's chosen path and shared authorization. Normal push-triggered automation may be authorized; separate production mutations and destructive actions still require confirmation. |
| AWS inspection cannot authenticate or reach a service. | Only a granted AWS profile is projected. Private service destinations remain blocked. | Separate missing/expired profile authorization from network denial and provider-side authorization. Read-only assurance belongs in the AWS role's permissions, not a command-name heuristic. |
| A compound Git push or GitHub command is rejected. | The destructive-shell hook requires push and GitHub writes to run alone so native Claude review can see them. | Use the literal command alone. This heuristic does not inspect interpreter code and is not a security boundary. Review its value separately from OS containment. |
| A temporary checkout loses access. | Grants and persistent state are keyed by checkout path; managed entrypoints reject linked worktrees. | Determine why the copy was created. A copied checkout is not a supported substitute for fixing grants or preserving unrelated edits. |
| Toolchain wrappers emit temporary-cache permission errors. | The launch provides isolated scratch, while some system wrappers may still consult the host's per-user temporary directory. | Reproduce with the actual toolchain. Do not grant the entire host temporary directory read-write to silence a warning. |

A failed push ending with a project check failure does not establish a sandbox
denial. A successful push from another temporary checkout does not establish why
either copy was needed. Preserve the complete gate error before attributing
either outcome to containment.

## Remaining protection and its limits

The synthetic probes exercise admitted writes, denied outside reads/writes,
symlink escapes, environment-file denials, denied host sockets and services,
process inspection, terminal input injection, and inherited restrictions in
children. These are real operating-system restrictions, not just instructions.
Run them with `just native-canary`; see the
[verification contract](https://github.com/e-m-albright/workbench/blob/main/docs/security/isolation.md#verification-and-implementation).

They do not protect admitted source from damage or exfiltration. Provider tokens
remain readable by the selected agent. Pre-existing admitted hardlinks can expose
excluded content. Host callbacks and later host execution of agent-edited files
are outside the boundary. A granted Docker engine can mount host files and
therefore defeats this boundary for that checkout. The complete accepted limits
remain in the [isolation contract](https://github.com/e-m-albright/workbench/blob/main/docs/security/isolation.md#accepted-risks-and-limits).

## Database access is not Docker control

Database-backed integration tests need permission to reach their disposable test
database, not an exclusion from testing. An already running database can be
admitted through its specific loopback port and test-only credentials without
admitting the Docker engine socket. Creating or managing containers is a
separate capability. Prefer a trusted host or CI task that starts the service,
then give the agent the narrow database connection it needs.

Docker control is broader because the engine creates containers outside the
agent process's macOS sandbox. A caller controlling that engine can request a
container with a bind mount of a host directory. The engine performs that access
with its own authority; the agent's direct filesystem denials do not follow the
request. On macOS this is not automatically root access to the entire Mac: the
engine runs in a Linux VM and is limited by host sharing and host permissions.
It can nevertheless expose or alter host files the agent itself cannot open.
A read-only mount of the socket file does not make the Docker API read-only.

Docker documents both the daemon-side nature of bind mounts and the Desktop VM's
host-file-sharing behavior in its [bind-mount reference](https://docs.docker.com/engine/storage/bind-mounts/),
reviewed on 2026-10-24. Raw access to the normal engine should remain an explicit
trusted-development exception. Requiring full container control while retaining
strong file isolation calls for a separate engine with narrowly shared paths,
not another command-name denylist.

## Evidence needed before changing policy

For each failure, record the launch route, literal command, working directory,
complete error, enforcing layer, and documented alternative attempted. Keep
private account identifiers, grants, tokens, and application logs outside this
public repository. Compare another machine's configuration only after the owner
supplies a sanitized export or authorizes a specific read-only source.

The next policy decision should separate ordinary development execution,
read-only operational access, authorized repository writes, and destructive or
production actions. Do not remove all containment to resolve a command-guard
conflict, and do not claim containment is useful for a Docker-enabled checkout
without acknowledging that exception.
