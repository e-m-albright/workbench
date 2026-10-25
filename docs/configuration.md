# Managed Surfaces

The exhaustive map of what `workbench sync` deploys and `workbench drift`
verifies, per harness. The README keeps only the summary; this document is the
reference.

The `personal` profile is the complete configuration described by the
table. Sync and drift default to `DOTFILES_PROFILE` when set, otherwise `personal`;
an explicit `--profile` overrides that default. The fail-closed `work` profile targets only Claude Code and Pi. It deploys
shared rules, tracked skills, hooks, and permission guards, but omits Codex and Antigravity,
Claude plugins and Desktop configuration, MCP servers, local-model routing,
and browser and personal connector extensions. It
still deploys the shared launchers and native Claude/Pi harnesses. Run both sync and drift with the same
`--profile` value.

Managed terminal sessions use the same instructions, skills, extensions, and presentation through
a derived configuration that excludes connector credentials and unrelated host state.
Their isolated state and access boundary are described below and in the
[boundary reference](security/isolation.md).

Personal root defaults are `openai-codex/gpt-6.1-sol` with medium thinking for Pi,
`gpt-6.1-sol` with medium reasoning for Codex, and `opus` with medium effort for
Claude. Vendor precedence still applies to explicit command-line or project
overrides. The work profile keeps Claude's defaults and leaves Pi provider and
model selection to host policy. Known personal Pi settings, providers,
extensions, and excluded skills cause work-profile drift if reintroduced.

Codex sync preserves an explicit approval reviewer. When its effective approval
policy is `on-request` and no reviewer is selected, it defaults to native automatic
review (`approvals_reviewer = "auto_review"`). This changes who reviews exceptions,
not filesystem or network access. Noninteractive and granular policies remain
unchanged. Existing desktop chats may need **Approve for me** selected in their
permissions control. See [OpenAI's automatic-review documentation](https://learn.chatgpt.com/docs/sandboxing/auto-review).

| Surface | Pi | Claude Code / Desktop | Codex |
| --- | --- | --- | --- |
| CLI presence | `pi` on `PATH` | Checked when managing plugins | Checked when managing plugins |
| Global instructions | `~/.pi/agent/AGENTS.md` | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` |
| Harness configuration | `~/.pi/agent/{settings,models}.json` | `~/.claude/settings.json`, `~/.claude.json` | `~/.codex/config.toml` |
| Desktop configuration | None | Claude Desktop MCPs and seeded preference defaults | ChatGPT connector plugins through the Codex plugin CLI |
| Command policy | Host `~/.pi/agent/permission-policy.json` and permission-policy/safe-git extensions; separate native terminal boundary | Host Claude permissions and sandbox settings; separate native terminal boundary | Host `~/.codex/rules/default.rules`; separate native terminal boundary |
| Extensions / hooks | `~/.pi/agent/extensions/*.ts` | Claude settings plus shared runtime scripts | `~/.codex/hooks.json` plus shared runtime scripts |
| Shared local CLIs | native Pi tools; `apple-contacts` is owned and deployed by a machine-local private layer; Apple Notes is blocked | the contacts CLI via shell | the contacts CLI via shell |
| Specialist agents | Not managed | Native external additions are preserved | Native external additions are preserved |
| Skills | Shared skills in `~/.agents/skills`; Pi-only external skills may remain in `~/.pi/agent/skills` | Claude global skill directory | `~/.agents/skills` |
| Plugins / packages | `packages` in managed Pi settings | IDs from `agents/claude/plugins.json` | IDs from `agents/codex/plugins.json` |
| MCP servers | None by design | Shared registry plus preserved external servers | Shared registry plus preserved external servers |
| Generated/private state | Contents preserved and unmanaged; session filesystem permissions enforced private | Preserved vendor state | Preserved vendor state |

Antigravity CLI is an additional personal-profile configuration target, included
in `all`. It manages `~/.gemini/AGENTS.md`, canonical skill trees under
`~/.gemini/antigravity-cli/skills`, shared launchers, and an isolated harness
without host settings or credentials. Native settings, logins, MCPs, and plugins
remain unmanaged. Sync and drift do not require a CLI login or contact a model.
`agy` enters Workbench's boundary, but normal CLI startup remains blocked by its
dynamic loopback listener. `antigravity`, `antig`, and `agravity` launch natively.
The [Antigravity integration](agents/antigravity.md) records the demonstrated
blocker and authentication limits; Dotfiles owns installation of the binary.

The shared shell runtime deploys `agent-launchers.zsh`, `agent-sandbox.zsh`, and
the `native-sandbox.py` / `native-sandbox.mjs` entrypoints under
`~/.local/share/workbench/shell/`. `workbench native prepare` installs the locked
runtime dependencies and resolved tool paths under
`~/.local/share/workbench/native/`. Sync removes the retired permissive Seatbelt
profiles and Codex app-server helper; Lima is not an active implementation.

Claude Code comes from the native installer when `~/.local/bin/claude` exists,
whatever Node version is active; otherwise `prepare` falls back to the `claude`
on `PATH`. The native launcher is a symlink into
`~/.local/share/claude/versions/`, and auto-update replaces the version file it
names. `prepare` therefore records the launcher rather than the version file and
admits the versions directory read-only. Each `cc` launch runs the version the
launcher names at that moment, so re-running `prepare` after an update is not
needed. Managed sessions set `DISABLE_AUTOUPDATER=1`, because the host install
owns updates and an isolated home should not download its own copy.

The standalone launch interface is
`/bin/zsh -f ~/.local/share/workbench/shell/agent-sandbox.zsh VENDOR LOCATION AUTHORITY [native args]`:
`VENDOR` is `pi`, `claude`, `codex`, or experimental `antigravity`; the only supported pair is `LOCATION=hosted`
and `AUTHORITY=managed`. The shortcuts `p`, `cc`, and `co` use this pair and show
`cloud > managed`. They admit the selected ordinary Git checkout,
`~/code/public`, `~/Desktop`, and `~/Downloads`, with all private exclusions.
The isolated HOME maps the scratch directory names to their host destinations.
The full commands `pi`, `claude`, and `codex` retain native behavior, shared
settings, skills, and soft guards without adding an outer sandbox. Native local
Pi uses `pi --route private --provider omlx`; it has no Workbench outer boundary.
The [launch design catalogue](agents/launch-design.md) owns the comparison.
Retired `--restricted`, `--daily`, and `--unrestricted` flags fail with migration
guidance; sourcing the launcher removes obsolete aliases such as `cou`, `ccu`,
`pih`, `pihr`, `pihu`, and `pil`. Editor and Paseo host tool callbacks are not
contained by this terminal boundary. Running processes retain their existing
boundary, including native binaries they launch as children.

Per-repository state lives under `~/.local/share/workbench/agent-state/`.
Sync derives shared harness preferences and approved code paths under
`~/.local/share/workbench/native/harness/`; launches refresh those preferences
into isolated state and admit the code assets read-only. These installed code
trees are trusted assets, not recursively sanitized collections; keep private
data outside them. This projection is
generated from the normal installed harness, not maintained as another profile.
Optional `workbench native prepare --authorize` enrollment copies only selected
provider login material into `~/.local/share/workbench/model-auth/`; it preserves
existing managed logins without claiming they authenticate. Use
`workbench native authorize VENDOR --replace` after signing in natively to back
up and replace one vendor's login. `workbench native status [VENDOR]` reports
preparation, projection, state paths, and login metadata without token or history
reads.

The managed boundary blocks the Keychain service, so `cc` stores Claude's login
only in the enrolled credential file. Claude saves that file by renaming a
sibling `.credentials.json.tmp.*` file over it, so the boundary admits writes to
exactly that file and those staging names. `/login` and token refreshes inside
`cc` therefore persist to the managed login. To replace the managed login with
the host's instead, sign in with `claude` outside `cc` and run
`workbench native authorize claude --replace`, which backs up the old managed
login and copies the new one from the Keychain.

These deliberately agent-readable credentials keep
their provider account scopes and are not inference-only grants. Machine-local
`~/.config/workbench/private-paths` exclusions remain enforced in managed
sessions. `~/.config/workbench/hard-deny-paths` also applies to every managed
launch. Its defaults deny every case variant of a directory named
`confidential`, all local Google Drive trees, email stores, browser profiles,
and Google connector credentials. The selected checkout is otherwise the
repository owner's approved decision boundary;
current defaults exclude raw meeting recordings rather than an entire curated
vault.

The global instructions conditionally consult
`~/.config/workbench/private-context.md` for machine-local repository aliases
and capability ownership. That file is intentionally not a managed surface:
the private layer owns it, while the Workbench CLI neither reads, copies, nor
checks it for drift. Agents use it only to find the owning repository, then
follow that repository's `AGENTS.md` and documented interfaces.

Pi settings and models preserve unknown top-level entries while
Workbench replaces its managed entries. Pi and Codex share one deployed copy of
portable skills under `~/.agents/skills`, which both harnesses discover. This
avoids Pi's duplicate-skill warning; Pi-only external skills remain under
`~/.pi/agent/skills`. Unknown Pi extensions, skills, and model providers
are reported as `EXTERNAL`, not deleted. The retired preset configuration is
removed. Pi's upstream implementer definition is deployed under `~/.pi/agent/agents`. Native Claude and Codex specialist-agent
additions are likewise external; sync removes only explicitly retired Workbench agents. Pi extensions
are deployed as real files rather than repository symlinks so moving a checkout
cannot silently disable the harness.

All 31 managed skills are tracked local sources. Archify and its archive download
pipeline are retired; sync removes its deployed trees, and drift flags them in
both shared and Pi-native skill directories. Retirement reasons live with the
enforcement in `RETIRED_SKILLS` in `src/workbench/core.py`.

Claude Desktop preference defaults fill missing keys but preserve explicit owner
choices; drift therefore checks key presence rather than exact preference values.
MCP entries remain exact managed values.
The Google connector implementation is retired. Pi's remaining Strava connector
requires local inference and its own OAuth grant.

Drift checks each exact managed Pi npm pin against the installed package's name
and version under `~/.pi/agent/npm/node_modules/`. Missing or malformed metadata
fails drift even when settings match. This verifies installation metadata, not
package content integrity; configuration sync does not install Pi npm packages.

Plugin IDs are version-controlled and drift-checked. Marketplace installation
resolves the vendor's current plugin content, so identity is declarative but the
artifact itself is not reproducibly pinned. OAuth consent and account sessions remain interactive vendor state; credentials,
session transcripts, trust decisions, and OAuth grants never belong in
Workbench. Sync repairs Pi session directories to `0700` and existing transcript files to
`0600` without reading or changing their contents. The permission-policy extension
also sets the active transcript to `0600` on each session start. If Pi has not created
the file yet during session rebinding, it retries before the first model turn so new
transcripts do not wait for the next sync.

The Claude launchers select native permission modes while sharing the normal
harness preferences. `cc` keeps native auto permission handling
inside the managed boundary; `ccr` selects native plan mode for review.
`cca --feedback 'review text'` addresses supplied feedback in the current
checkout; it does not retrieve authenticated reviews, comment, commit, or push.
`ccc` and managed `--chrome` are retired with guidance to launch `claude --chrome`
explicitly from the host. Entering an existing linked worktree is unsupported
by the managed launcher. Native auto
handling is an automatic approval classifier, not a prompt before every action.
The retired `--dev`, `--scout`, and `--yolo` permission-profile flags are rejected;
old machine-local profile files are not loaded by these launchers.

Managed projection preserves Claude's auto-compaction preferences. Managed
Claude also reads organizational settings under
`/Library/Application Support/ClaudeCode` without write access. The launcher
copies repository-local `user.name` and `user.email` into its clean environment,
with global defaults when absent. It does not import local includes, hooks,
credential helpers, or arbitrary host Git configuration. Project Claude sandbox
`denyRead` and `denyWrite` lists are snapshotted at startup and applied to every
managed vendor; allow lists are ignored. Invalid or symlinked policy fails
closed. Mandatory denials are emitted after all grants. See the
[boundary reference](security/isolation.md) for overlap and file-alias limits.

Managed Codex refresh retains only selected-checkout folder trust and unchanged
projected hook decisions. Unsupported trust syntax prompts again; arbitrary
agent-written settings never survive the refresh. Managed Pi preserves valid
worker timeout settings and rejects explicit private/local startup intent.
Pi workers can run in admitted sibling locations, inherit the parent's model
selection and boundary, and require explicit adoption/rejection before discarding
changed output. Unique commits remain preserved and recursive worker entrypoints
are blocked.

Managed Claude keeps an isolated settings home but links only the matching native
`~/.claude/projects/<encoded cwd>` transcript namespace. Initial migration requires
stopped managed sessions; conflicts preserve both copies and refuse launch. Native
namespace encoding is lossy and can collide. The
[history contract](security/isolation.md#claude-session-history) owns migration,
supported path encodings, and the boundary around other host state.
Pi and Codex histories remain separate from native sessions; a moved checkout has
a new managed state identity.

Codex sync seeds ordinary workspace-write and on-request defaults and repairs a
broad ordinary sandbox setting. It preserves stricter read-only settings,
confined noninteractive `never` policies, structured approval policies, and
explicit named profiles. `never` disables approval prompts; it does not by
itself grant an escape from a sandbox. The coupled ordinary
`danger-full-access`/`never` posture is repaired to workspace-write/on-request.

## Sync preview

`workbench sync [vendor] --dry-run` runs the same merge and rendering functions
as sync, holding planned managed text and skill-tree replacements in memory.
It prints `CREATE`, `UPDATE`, `REMOVE`, and `MODE` paths plus `PLUGIN` actions.
It does not write files, change modes, harden transcripts, delete retired
surfaces, or run plugin installation/enabling commands. Unknown settings survive
the same bounded merges; configuration values and credentials are never printed.
The normal profile, skill, plugin, and rules-only options apply.

Plugin inventory is read through the vendor CLI. A planned installation cannot
predict the marketplace's resulting code assets, so dependent projections must
be verified after real installation. Preview is not a lock: concurrent changes
or vendor updates can change the subsequent sync. `just deploy` rejects preview
and partial-sync flags because its contract is an applied, verified deployment.

## Drift semantics

`workbench drift` distinguishes two states:

- `DRIFT` - a Workbench-managed value is missing or differs; the command exits
  non-zero.
- `EXTERNAL` - a valid unmanaged addition remains in the live harness config. It
  is reported for visibility but does not fail the command.
- `NOTE` - verification was skipped (for example, a vendor CLI is absent); the
  item is neither drift nor external and is counted separately.

Drift also checks required entries in both machine-local denylists, obsolete Pi
state paths, and each selected vendor's derived harness manifest and rendered
configuration. Projection verification uses the same read-only renderer as sync;
it does not repair state or read provider login files. A changed installed
preference or code-asset inventory may require another sync even when canonical
source files have not changed.

`sync` preserves unmanaged configuration, writes only Workbench-owned values,
and keeps one `.bak` file before replacing live configuration. It reports each
path it changed, including replaced skill trees and removals, and ends with a
changed-path count, so an unchanged run reads
"nothing to change".

Known limitation: Codex records hook trust against each hook's hash, so after
`sync` updates `~/.codex/hooks.json` the changed hooks are skipped until
re-trusted via `/hooks` inside Codex. Drift compares bytes only and cannot see
untrusted-but-deployed hooks; sync prints a reminder when the file changes.
