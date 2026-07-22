# Pi build philosophy

Decision record for the owner's Pi harness. This page owns why capabilities are
adopted, rejected, or held for evidence. [`pi-capabilities.md`](pi-capabilities.md)
owns the current operational inventory. [`experiments.md`](experiments.md) owns
active time-boxed experiments. [`decisions/tombstones.md`](decisions/tombstones.md)
owns rejected approaches that should stay absent.

Last reviewed: 2026-07-21.

## Goal

Build a compact, legible daily-driver harness that takes advantage of Pi's native
capabilities and adds only high-leverage improvements. Pi should remain easier to
understand than Claude Code or Codex, portable across model providers, and small
enough that the owner knows what executes in every session.

The target is not a homemade Codex clone or a smaller Oh My Pi. Use Codex and
Claude Code when their stronger sandbox, browser, cloud, document, or fleet
capabilities are the right boundary.

## Selection rules

A capability earns adoption when it:

1. Solves a recurring observed problem rather than an imagined parity gap.
2. Is not already covered by Pi, the terminal, Git, or a trusted CLI.
3. Improves correctness, latency, context efficiency, or orientation enough to
   justify its permanent metadata, dependencies, and trust surface.
4. Fails loudly and has a clear removal path.
5. Preserves inspectability and provider portability.
6. Can be pinned, tested, and managed by Workbench.

Prefer, in order:

1. Native Pi capability.
2. Terminal or operating-system capability.
3. Existing trusted CLI exposed through a small skill.
4. Small Workbench-owned extension.
5. Pinned and reviewed third-party package.
6. A broader distribution or fork only after the smaller options fail.

Stars, demos, and feature count are discovery signals, not adoption evidence.
Useful evidence includes repeated local friction, controlled comparisons, reduced
fix cycles, lower context use, fewer stale edits, and safer failure behavior.

## Trust model

Pi packages run arbitrary code with the user's full account permissions. Skills
can instruct the model to run arbitrary commands. OAuth tokens stored by an
extension are readable by that extension and by any other process running as the
same user. Pi's permission extension is a guardrail around tool calls, not an OS
sandbox or an information-flow control system.

Consequences:

- Pin third-party packages to reviewed versions. Upgrade deliberately.
- Keep OAuth automatic authorization off.
- Request the narrowest OAuth scopes and enforce a local tool allowlist as a
  second layer.
- Treat email, calendar, activity, browser, and web content as untrusted data,
  never instructions.
- Do not send, upload, quote, or embed private source content in another service
  without explicit user direction.
- Prefer temporary browser sessions. Do not attach authenticated profiles unless
  the task requires them and the user understands the exposure.
- Use Codex or Claude Code for high-autonomy execution against untrusted content.

No community package is risk-free. Static review and pinning reduce supply-chain
risk but cannot prove the absence of malicious behavior. A package that can read
Gmail or control an authenticated browser belongs in the highest trust tier.

## Adopted

| Capability | Decision and evidence | Guardrail / removal |
|---|---|---|
| Upstream Pi TUI | Primary transparent, provider-neutral harness. Native sessions, trees, skills, prompt templates, model switching, thinking controls, extensions, RPC, and project trust cover the core workflow. | Stay near upstream. Do not fork core without a demonstrated blocker. |
| Workbench-managed Pi | Settings, providers, presets, extensions, skills, permission policy, and MCP routing are deployed and drift-checked from one public source. | Credentials, sessions, trust decisions, and telemetry remain private live state. |
| Custom footer | Restores native information and adds repository state, context, cost, speed, compaction, and Codex quota evidence. | Every field must earn its width. Remove annotations that do not change behavior. |
| Activity title and deterministic session name | Terminal tabs now show spinner, repository, concise first-prompt label, and active tool. Resumed unnamed sessions remain findable; explicit names win. | No completion notification. Remove if titles become noisy or inaccurate. |
| Permission policy and safe Git | Block protected reads/writes, dependency-tree writes, uploads, destructive Git, and risky shell mutations before execution. | These are not containment. Keep tests aligned with real failure modes. |
| Consult | Supplies an explicit independent review without a permanent subagent fleet. | User-invoked and bounded. |
| Discovery telemetry | Time-boxed local evidence for navigation and verification friction before adding code intelligence. | Review after one week; remove completely if it does not change a decision. |
| MCP discovery proxy | `pi-mcp-adapter` keeps large remote tool catalogs out of the system prompt. Version 2.11.0 is pinned. | Automatic OAuth is off. Remote tools are read-only allowlisted. Do not grant high-value tokens without reviewing client, server, scopes, and storage. |
| Native Agent Browser wrapper | `pi-agent-browser-native` 0.2.71 is a thin Pi tool around the already-adopted Agent Browser CLI. It adds structured results, context spills, redaction, stale-ref checks, session recovery, and artifact metadata. | Pin the version, use temporary sessions by default, keep optional web-search credentials disabled, and remove if native wrapping does not reduce browser failures or context. |
| Internal multipart reconciliation | Agents track all user requests and close them in the final answer. | Show a visible ledger only when it materially improves coordination. |

## Explicitly absent

These decisions are intentional. Re-evaluate only when the named condition changes.

| Capability | Decision | Why absent | Revisit when |
|---|---|---|---|
| Fast-mode control or display | Rejected | The Codex subscription route does not expose reliable state; priority service changes usage economics; thinking level is not Fast mode. Silent custom inference would be misleading. | Pi exposes authoritative provider-route state and the owner wants the cost tradeoff. |
| Completion notifications | Rejected | They interrupt flow and duplicate visible terminal state. | Long unattended runs become common and missed completions are observed. |
| Visible request ledger on every multipart prompt | Retired | It added ceremony and awkward tone without preventing a demonstrated omission. | Internal reconciliation repeatedly drops independent requests. |
| Custom transcript viewport or overlay | Rejected for now | Pi exposes no public scrollback viewport API. Rebuilding the transcript renderer would depend on private internals and compete with terminal-native navigation. | Ghostty semantic navigation is proven insufficient and Pi exposes a supported viewport API. |
| Multi-session GUI tabs | Rejected for now | Terminal tabs and session resume cover the real need without another session manager. | Cross-session visibility becomes recurring friction that terminal titles cannot solve. |
| Broad Pi Web UI migration | Rejected | Network-listening trust surface and GUI overlap exceed the current phone-access need. | A supervised phone workflow proves valuable and Tailscale plus SSH or an audited loopback UI is insufficient. |
| Oh My Pi migration | Rejected | Its batteries-included fork bundles a large tool, runtime, memory, browser, subagent, collaboration, and editor surface that conflicts with the compact upstream-first goal. | Several independently validated capabilities require coordinated core changes that extensions cannot provide. |
| Hashline tool-suite replacement | Deferred, not adopted | Hash anchors provide stale-line verification and compact edit references, but exact-text Edit already fails loudly. No comparative model benchmark or independent evaluation was found, and the available package replaces most core filesystem tools plus Bash output. | Telemetry shows stale edit failures or material read/edit token waste; a narrow controlled trial beats exact replacement. |
| LSP, AST, or semantic index by default | Deferred | Plausible leverage, but no local evidence yet identifies definitions, references, diagnostics, or repository mapping as the dominant bottleneck. | Discovery telemetry names a repeated failure and a bounded trial reduces it. |
| Persistent subagent fleet | Rejected for now | A roster and parallel writers add coordination, trust, and reconciliation cost. `/consult` covers independent review. | Two or more independent threads recur and bounded delegation measurably reduces latency or protects context. |
| Automatic parallel writers | Rejected | Shared-checkout mutation races and unclear ownership are worse than sequential work. | Every writer is isolated in a worktree with explicit ownership and parent verification. |
| `pi-web-access` | Deferred | Useful search/fetch coverage, but it combines multiple providers, automatic repository cloning, browser-cookie access, local-video upload, and several fallback egress paths in one 7 MB package. | Existing retrieval repeatedly blocks work and a constrained configuration can prove provider and data-flow boundaries. |
| Broad community package bundle | Rejected | Permanent metadata and arbitrary-code surface grow faster than proven value. | Each package independently passes the selection rules. |
| Duplicate diff approval UI | Rejected | Git diff, precise Edit failures, tests, and review skills already provide the verification loop. | A recurring bad patch bypasses those layers and a preview gate would have caught it. |

## Research tracks

### Prompt navigation

- **Question:** Can Ghostty's OSC 133 semantic navigation provide read-only prompt
  movement without changing Pi's branch or editor?
- **Current evidence:** Pi emits semantic zones and Ghostty binds prompt jumping,
  but the observed session jumped to scrollback extremes.
- **Next test:** fresh un-compacted session with several prompts, then compacted and
  resumed sessions.
- **Adopt:** document the working key and stop.
- **Escalate:** file an interoperability issue or request a Pi viewport API.
- **Do not build:** a private transcript renderer.

### Code intelligence

- **Candidates:** https://github.com/samfoy/pi-lsp-extension and
  https://github.com/narumiruna/pi-extensions/tree/main/extensions/pi-lsp
- **Next test:** after the telemetry review, trial diagnostics, definitions,
  references, and symbol overview in one representative repository.
- **Evidence threshold:** fewer search/read cycles, earlier error detection, or
  shorter first-mutation latency without noisy false diagnostics.
- **Avoid:** installing LSP, AST search, repository maps, and semantic indexing as
  one indivisible stack.

### Hash-anchored edits

- **Candidate:** https://github.com/coctostan/pi-hashline-readmap
- **Claim worth testing:** `LINE:HASH` references may lower edit payload and detect
  stale lines with less repeated context.
- **Evidence gap:** repository tests validate implementation behavior, not model
  success against exact-string Edit. No comparative benchmark was found in the
  candidate or Oh My Pi repositories during the 2026-07-21 review.
- **Next test:** count exact-match failures and edit payload from telemetry, then
  compare a narrow hash-edit primitive on the same tasks.
- **Adopt only if:** it measurably beats exact replacement. Do not begin by
  replacing read, edit, grep, find, list, write, and Bash together.

### Interactive shell, subagents, and worktrees

- **Candidate:** https://github.com/nicobailon/pi-interactive-shell
- **Useful existing work:** observable PTY overlay, takeover, background sessions,
  dispatch completion, structured Pi/Codex/Claude spawning, attach/dismiss, and
  worktree isolation.
- **Risk:** arbitrary interactive process execution, hidden background work,
  completion-triggered turns, and easy over-parallelization.
- **Next test:** one read-only reviewer in dispatch mode. Then one mutating worker
  in an isolated worktree with parent-owned review and verification.
- **Adopt only if:** delegation saves time or context on repeated decomposable work.
- **Never adopt:** concurrent writers in one checkout or autonomous merge/push.

### Web access

- **Current path:** public `curl`, `gh`, current-documentation retrieval skills,
  and Agent Browser for interactive pages.
- **Candidate:** https://github.com/nicobailon/pi-web-access
- **Next test:** log recurring cases where the current path cannot discover or
  extract sources. If a gap appears, trial search/fetch only with browser cookies,
  local file upload, video upload, automatic cloning, and unnecessary providers
  disabled.
- **Alternative:** use the native Agent Browser wrapper's optional search only if
  one explicitly trusted provider is configured.

### Remote and phone access

- **Candidate:** the existing community Pi Web UI, audited before use.
- **Preferred boundary:** loopback service exposed through Tailscale Serve, or SSH
  into a terminal session. Never expose Pi directly to the public network.
- **Evidence threshold:** a real recurring phone workflow, not feature curiosity.

### Source connectors

- **Goal:** Pi can read Gmail, Google Calendar, Granola, and Strava so communication
  tracking does not depend on Claude Code.
- **Google server provenance:** Gmail and Calendar endpoints are on official
  `googleapis.com` domains and advertise Google Accounts authorization metadata.
- **Client provenance:** `pi-mcp-adapter` is community-maintained, not official Pi
  or Google support. It stores tokens in plaintext JSON with mode 0600 and executes
  with full user permissions.
- **Current gate:** no Gmail, Calendar, or Strava OAuth token is granted until the
  pinned adapter, scopes, allowlist, endpoint metadata, and revocation path are
  documented and accepted.
- **Fallback:** use the working Claude connectors while building a smaller
  Workbench-owned read-only adapter if the generic client's trust is unacceptable.
- **Cut criterion:** remove the generic adapter if constrained OAuth and local
  allowlisting cannot make its residual trust acceptable.

## Community watchlist

Track ideas, not feature counts:

- Upstream Pi: https://github.com/earendil-works/pi
- Oh My Pi: https://github.com/can1357/oh-my-pi
- Armin Ronacher's extensions: https://github.com/mitsuhiko/agent-stuff
- Pi Interactive Shell: https://github.com/nicobailon/pi-interactive-shell
- Pi MCP Adapter: https://github.com/nicobailon/pi-mcp-adapter
- Pi Web Access: https://github.com/nicobailon/pi-web-access
- Native Agent Browser: https://github.com/fitchmultz/pi-agent-browser-native
- Hashline and readmap: https://github.com/coctostan/pi-hashline-readmap
- Modular extensions: https://github.com/narumiruna/pi-extensions
- Monopi: https://github.com/ifiokjr/monopi
- Curated ecosystem index: https://github.com/BubblePtr/awesome-pi
- Gondolin sandbox: https://github.com/earendil-works/gondolin

Review quarterly or when a local problem names a capability. Do not browse this
list merely to find something to install.

## Changing a decision

When evidence changes:

1. State the observed problem and baseline.
2. Name the smallest candidate and its trust boundary.
3. Define success, removal, and review date before installation.
4. Pin and test the candidate.
5. Update this record, capabilities, experiment state, and tombstones in the same
   change so no surface preserves the old decision.
6. Remove failed experiments completely. A rejected capability can be reconsidered;
   it should not linger half-installed.
