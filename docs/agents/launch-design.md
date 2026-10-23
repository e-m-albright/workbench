# Terminal launch design catalogue

The October 13, 2026 design has one Workbench managed authority. Use `co`, `cc`,
or `p` for a hosted session inside its macOS boundary. Use full `codex`, `claude`,
or `pi` commands for native behavior. Both routes retain shared configuration,
skills, and applicable soft guards. The distinction is whether Workbench adds
an outer operating-system policy.

The owner approved corrections from the [six-model review](../decisions/managed-launch-review.md)
after discussing its findings. That record distinguishes implemented fixes,
verification evidence, and accepted limits. The original review assessed the
October 13 source; it was not rerun against the corrections.

## Commands and access

| Choice | Command | Inference | Workbench outer policy |
| --- | --- | --- | --- |
| Managed Codex | `co` | Hosted | Selected ordinary checkout, public code, Desktop, Downloads; exclusions enforced |
| Managed Claude | `cc` | Hosted | Same policy; native auto approval remains a separate layer |
| Managed Pi | `p` | Hosted | Same policy; native `-r` still resumes |
| Native vendor | `codex`, `claude`, `pi` | Vendor configuration | None added when launched from the host |
| Native local Pi | `pi --route private --provider omlx` | Local | None added when launched from the host |

Managed footers show `cloud > managed`. Admitted shared paths are
`~/code/public`, `~/Desktop`, and `~/Downloads`. There is no managed repository-only
variant or broad local host variant. Retired `--restricted`, `--daily`, and
`--unrestricted` flags fail with actionable guidance. Reloading the launcher
removes obsolete functions including `cou`, `ccu`, `pih`, `pihr`, `pihu`, and `pil`.
This reduces authority choices to the shortcut or native command. Reconsider a
second managed authority only for an evidenced workflow that this distinction
cannot serve safely.

## What each layer does

| Layer | Responsibility | Limit |
| --- | --- | --- |
| Shared configuration and skills | Consistent instructions, models, tools, presentation, and workflows | Instructions do not contain arbitrary code |
| Hooks and permission extensions | Explain denials and request approvals for sensitive actions | A soft guard is not an operating-system boundary |
| Vendor native permissions | Vendor approvals and native sandbox behavior | Native behavior differs by vendor and installed settings |
| Workbench outer sandbox | Constrain the whole managed process tree and its file, network, service, and process access | Shares the Mac kernel; admits provider login files and live writable source |
| External host callbacks | Editor, terminal, or daemon actions outside the process tree | Require their own controls; the child sandbox does not contain them |

Managed sessions disable a nested vendor operating-system sandbox because macOS
does not support nesting those policies. Vendor action approvals still apply.
Executing a native binary from a managed parent, even with a cleared environment,
preserves the inherited outer restrictions. Starting a native command from the
host is the distinct choice that does not add them.

The outer policy denies host files by default, admits necessary installed tools
and isolated state, and enforces private-path and invariant exclusions inside
every admitted directory. It blocks tested host services and process arguments.
Public web access uses a proxy. Admitted files, Git history, ignored content,
and selected provider credentials remain readable to the agent and can leave
through permitted network access. The [security contract](../security/isolation.md)
owns exact policy and accepted risks; [configuration](../configuration.md) owns
deployment and isolated harness projection.

## Incorporated submitted fixes

The relevant submissions are [PR #7](https://github.com/e-m-albright/workbench/pull/7)
and the [managed resume submission](https://github.com/e-m-albright/workbench/commit/0fb2846).
Their changes were selected by behavior rather than merging either branch. The
owner then closed PR #7 unmerged and deleted both remote branches. Local archive
refs initially preserved their reviewed tips; the October 20 cleanup backed them
up in a local Git bundle before removing the superseded refs.

- Managed Claude can read organizational policy, while `/usr/local/bin` supports installed tools.
- Repository-local Git identity scalars override global attribution without importing host configuration, local include files, hooks, or credential helpers.
- Project Claude filesystem deny lists apply to every managed vendor at startup. Allow lists are ignored; malformed and symlinked policy is refused. Mandatory denials are emitted after all read/write grants; machine-local exclusions remain independent.
- Claude auto-compaction preferences survive configuration projection. The submitted `cc` resume hint is retained for unsupported namespace paths; current transcript sharing is described below.
- Existing local fixes retain environment-file protection, disabled broad loopback access, deployment-profile defaults, and current-launcher canary setup.

The change initially left out the submissions' AWS credential broker, Docker
socket access, repository loopback ports, and Chromium rendezvous grants. They
were later adopted by owner decision as opt-in per-checkout grants; see
[isolation](../security/isolation.md#per-checkout-grants). The
cleanup skill retains hook-respecting authorization and re-inventory guidance
rather than bypassing failed hooks. The destructive-command guard rewrite was
initially left out and later adopted by owner decision; see
[isolation](../security/isolation.md#enforced-permissions).

## Daily behavior and recovery

The isolated HOME maps `~/Desktop` and `~/Downloads` to the actual host
scratch directories. Private exclusions still apply. Managed Pi rejects an
explicit private/local route rather than silently submitting to hosted inference.
Its native welcome describes shared configuration without claiming containment.

`ccr` reviews available local changes. `cca --feedback 'review text'` works from
supplied feedback; it does not fetch authenticated reviews, comment, commit, or
push. `ccc` and managed `--chrome` return guidance for an explicit host-terminal
`claude --chrome` launch. No shortcut silently changes authority.

Codex retains only the selected checkout's folder trust and unchanged projected
hook trust across preference refresh. Unsupported trust syntax is discarded and
Codex asks again. Other agent-written configuration does not survive projection.
Managed Pi preserves a valid `worker.timeoutMs` preference.

`workbench native status` reports runtime, checkout state, projection, and login
file metadata without reading tokens or sessions. After signing in with the full
vendor command from the host, use `workbench native authorize VENDOR --replace`
to back up and replace that vendor's managed login. File presence does not prove
that a provider will accept it.

Managed entrypoints reject linked worktrees. Pi workers preflight sibling
placement under public code, Desktop, or Downloads before creating Git state.
Their direct child Pi inherits the parent boundary; the resulting worktree is
not a new managed entrypoint. The child retains the selected provider, model, and
thinking level. The parent reviews against the captured starting commit and must
mark changed output adopted or rejected before discarding it. Unique commits and
failed Git inspections preserve the worktree; worker entrypoints reject recursive
delegation. `/consult` requires a separate native Pi session because other vendors'
credentials are not admitted.

Managed Claude now shares only its matching native project transcript namespace,
while settings and credential enrollment remain separate. The earlier history
split was an isolation side effect. Initial migration needs stopped managed
sessions; conflicts preserve both copies and refuse launch. Native namespace
encoding can collide, and unsupported path encodings retain isolated
history with the `cc` hint. This does not share rewind or file history. The
[history contract](../security/isolation.md#claude-session-history) owns exact
scope and migration limits. Pi and Codex histories remain separate from native
sessions.

## Security corrections and accepted limits

Owner and project exclusions now remain mandatory after explicit path grants.
Synthetic macOS canaries cover equal, ancestor, nested, and glob overlaps.
Preparation and startup reject bootstrap executable placement beneath managed
write grants. Installed plugin and extension trees remain trusted code assets,
not recursively sanitized collections; keep credentials outside those trees.

The host's Ghostty configuration denies clipboard queries and permits
prompt-free writes. The owner accepts clipboard replacement by terminal programs
for convenient copying. Existing Ghostty windows require **Command+Shift+Comma**
or **Reload Config** to load that policy. The child sandbox cannot enforce
terminal callbacks by itself.

The browser supervisor starts a fresh contained browser before the vendor and
pins its validated `DevToolsActivePort` identity. Port collisions fail closed.
Lifecycle cleanup applies one inherited policy through macOS `libsandbox`; a
contained guardian reports the vendor exit and kills remaining processes in the
same sandbox. Final live acceptance for these changes is recorded in the
[security contract](../security/isolation.md). A malicious process that kills
the guardian first can prevent its cleanup; this is not guaranteed revocation.

A pre-existing admitted hardlink to excluded content remains readable. Synthetic
checks distinguish that accepted alias limit from denied new link creation and
denied renaming of an ancestor containing protected paths. Keep sensitive aliases
outside admitted directories. Provider login exposure, public transmission of
admitted content, later host execution of modified source, and the shared Mac
kernel also remain accepted risks. No broad localhost, Docker, or credential
broker grants were added.

## Verification

The previously recorded deployed acceptance reached installed `co`'s ready prompt
and verified installed Pi browsing, interaction, screenshots, PDF export, text extraction,
rendered inspection, private-file denial, browser closure, and scratch cleanup.
All six commands passed version startup; managed Desktop and Downloads passed
read/write checks. The full project gate and all 15 synthetic macOS canaries
passed. The [review record](../decisions/managed-launch-review.md) records the
evidence separately from the original source assessments and their scores.

The current [Claude history checks](../security/isolation.md#claude-session-history)
separately establish native resume-picker discovery and namespace containment.
They do not establish provider continuation or rewind.

Claude binary startup is verified, but unauthenticated onboarding does not prove
authenticated model operation. Existing processes retain their launch policy
after sync. Local inference changes the model destination, not native host access.
