# Agent Harness Landscape — Watch

**Status:** OPEN / ongoing survey. Not an active build — a tracked view of the
coding-agent tooling landscape and where our own harness ambitions sit.

**Last surveyed:** 2026-08-26 · **Next review cue:** when a tracked tool ships a
step-change, or roughly quarterly.

**Project this belongs to:** *own our coding surface.* The install-manifest side
of this watch lives in [`macos/packages.toml`](https://github.com/e-m-albright/dotfiles/blob/main/macos/packages.toml) (the
`AI CLI Tools` / `IDE` sections). This doc is the reasoning and capability view.

---

## The bet

The long-term aim is to **own the coding harness** — the layer between us and the
model — rather than rent it. Owning it buys transparency (nothing injected behind
your back), stability (your workflow doesn't break when a vendor reshapes their
prompts), and eventually **privacy/control** by pairing a self-owned harness with
a self-hosted open model. That last part is a different problem for a different
day (see [local-llm-stack.md](https://github.com/e-m-albright/dotfiles/blob/main/docs/local-llm-stack.md)) — the fantasy endpoint is
wiring a minimal harness like Pi to a Kimi K2/K3-class open model we control.

This is explicitly **not** a bet on agent velocity for its own sake.

## Current stance (2026-08-26)

**Decision: use Pi as the primary interactive trial; retain Codex and Claude Code
as specialist fallbacks.** Do not uninstall either yet. Rationale:

- **Subscription economics are no longer a blocker.** Pi can use ChatGPT-backed
  `openai-codex` auth while retaining its transparent, provider-neutral surface.
- **Pi is now pleasant enough to test as the daily driver.** The restored
  Workbench extensions cover permission policy, safe-git, presets, model routing,
  consult, a rich footer, and the branded startup surface. AGENTS.md and skills
  already carry across harnesses.
- **Codex still owns several hard capabilities:** OS sandboxing, cloud/async
  agents, GitHub PR review, first-class MCP, and some provider-specific controls.
  Keep it installed for those jobs while Pi earns the rest.
- **Maintenance tax remains real.** The Jul 15 move left Pi config symlinks broken
  for a week without an error. Full migration requires Workbench to deploy and
  verify Pi declaratively, not another hand-maintained link farm.
- **No armies/factories of agents.** Large fleets of concurrent agents remain the
  wrong default. One-to-a-few observable agents is the local ceiling; use a
  vendor's verified fleet only for an exceptional exhaustive review.

### August capability review

The major proprietary harnesses have converged on hooks, skills, plugins,
subagents, cloud sessions, schedules, remote clients, and specialized review.
That convergence does not create a Pi parity requirement. It makes model access,
orchestration quality, distribution, and trust boundaries the meaningful
choices.

Current Workbench dispositions:

- **Bounded orchestration:** the model-callable `worker` tool is Pi's implementation answer: one worktree-isolated mutating delegate with parent review. The `dev` preset may delegate, review, and discard without per-use approval. `/worker` remains a manual entrypoint; this is not autonomous fan-out.
- **Independent judgment:** `/consult` and the review skills cover the normal
  second-opinion need. Claude Code is the deliberate escape hatch for coordinated
  finder/verifier fleets.
- **Native Pi 0.84.3:** fullscreen transcript search, prompt jumping, selection,
  deferred tool loading, parallel tool execution, stronger RPC/SDK session
  control, and project trust reduce the list of custom features worth owning.
- **Editing and code intelligence:** hash anchors, Language Server Protocol
  refactors, and Debug Adapter Protocol control remain evidence-gated. The prior
  local trial found no ordinary symbol-navigation bottleneck, and exact-text Edit
  already rejects stale matches.
- **Automation:** schedules, hosted routines, durable goals, artifacts, and cloud
  execution belong to vendor or automation surfaces rather than a larger local Pi
  core.
- **Memory:** durable facts stay in repository documentation; temporary handoffs
  remain explicit. Do not add an opaque cross-session memory service.
- **Mobile:** Paseo over Tailscale is the sole cross-harness phone surface. Phone terminal access is not required, so Zellij, tmux, Mosh, and the Mission Control session manager were retired rather than retained as a second path.

### Guiding principles

- **Velocity is gated by human comprehension, not agent count.** Spinning up more
  concurrent agents doesn't raise real throughput once you can't hold what they're
  doing in your head — it lowers it. More running things makes comprehension
  worse, not better.
- **Maintenance tax is the true cost of owning the bleeding edge.** A self-owned
  harness means every brilliant idea that lands in some other tool becomes work to
  port or forgo.
- **Distance from the frontier is a feature, not a bug.** A harness that
  intentionally separates you from the week-to-week churn is doing you a favor.
  Pi's minimalism is this stance made concrete.
- **Prefer the smallest thing that holds.** Higher-level abstractions that hide
  the agent loop (agent inboxes, orchestrators) are off the table while they hide
  more than they reveal.

### Evidence update: minimum viable harness

Recent sources point in the same direction without proving one universal recipe:

- OpenAI's greenfield software-factory case study credits repository legibility, short map-like instructions, executable architecture constraints, isolated environments, and direct access to tests, logs, traces, and the UI. Its million-line, first-party internal experiment is evidence that those conditions can support high autonomy, not that an established personal codebase should copy the factory or relax merge boundaries.
- Anthropic reports removing more than 80% of Claude Code's system prompt for newer models without measurable loss on its own evaluations. The transferable practice is to delete duplicated guidance, prefer expressive interfaces, and progressively disclose specialized workflows. Safety policy remains explicit and enforced.
- Hugo Bowne-Anderson frames harness scope through action complexity and context complexity. Add memory, compaction, subagents, or hooks only when a real task occupies the part of that matrix that needs them, then reconsider the machinery as models improve.
- A 2026 study of 2,853 public repositories found context files were usually the only adopted configuration mechanism, with `AGENTS.md` emerging as the cross-tool convention. This is an adoption baseline, not evidence that advanced mechanisms never help.
- METR's February 2026 update says current developer uplift is likely better than its early-2025 slowdown result, but selection effects prevent a reliable estimate. Its separate transcript analysis finds high time savings on selected Claude Code tasks, especially with concurrency, while explicitly treating those numbers as soft upper bounds on productivity.

The decision rule remains: start from repository context, native tools, deterministic gates, and one observable execution loop. Add a harness feature only for a named recurring failure with a removal path and measurable verification. Do not use vendor throughput as a proxy for owner value or maintainability.

Sources: OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/); Anthropic, [The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models); O'Reilly, [Stop Overengineering Your Agent Harness](https://www.oreilly.com/radar/stop-overengineering-your-agent-harness/); Galster et al., [Harness Engineering for Agentic AI Coding Tools](https://arxiv.org/abs/2602.14690); METR, [developer productivity experiment update](https://metr.org/blog/2026-02-24-uplift-update/) and [transcript-analysis note](https://metr.org/notes/2026-02-17-exploratory-transcript-analysis-for-estimating-time-savings-from-coding-agents/).

---

## How to read the landscape — tiers

Tools are grouped by **how much they hide** — which is the axis that matters for
the "own your surface" goal.

| Tier | What it is | Hides | Our posture |
|---|---|---|---|
| **1 — Terminal harness** | Agent loop in your terminal; you see every tool call | Least | Candidates for a self-owned surface |
| **2 — Editor-integrated** | Agent embedded in an IDE/editor | Some (editor + cloud) | Useful, but not "ours" |
| **3 — Orchestration / inbox** | Manages fleets of agents, worktrees, or an "agent inbox" | Most | Deliberately avoided for now |

---

## Catalog

Everything on the watch list, grouped by tier. The deep-profiled comparison set
(Tier 1, seven tools) has a full capability matrix below; the additions are
catalogued at the positioning level and flagged for later deep-profiling.

### Tier 1 — terminal harnesses

| Tool | Lineage | License | Positioning / why it's here |
|---|---|---|---|
| **Pi** | Mario Zechner → earendil-works | MIT | The minimal, transparent, self-extensible core. Our primary "own it" candidate. Sub-1k-token prompt, 4 tools, deep extension API, 3-ecosystem subscription auth. |
| **Oh My Pi** (`omp`) | can1357 fork of Pi | MIT | Batteries-included Rust reimplementation. Already builds most of what base Pi omits (LSP, DAP, subagents, hash-anchored edits) and *inherits* existing `.claude`/`.codex` configs. The "already assembled" version of the Pi bet. |
| **Claude Code** | Anthropic | proprietary | Current daily driver. Subscription (Claude Pro/Max). Mature, deep hooks/skills/subagents/sandbox. |
| **Codex** | OpenAI | Apache-2.0 | Current daily driver. ChatGPT-subscription auth. Real OS sandboxing, V4A `apply_patch`, MCP client *and* server, cloud/async. |
| **Open Interpreter** | Codex fork (Open Interpreter) | Apache-2.0 | Relaunched in July 2026 as a Rust coding agent for low-cost/open models; the original Python computer-use project moved to a community fork. Emulates provider-recommended harnesses (Kimi Code, Qwen Code, DeepSeek TUI, Claude Code, SWE-agent), retains Codex sandbox/MCP/approval foundations, and speaks Codex exec + ACP. Direct Pi competitor at the CLI layer, but differentiated around harness emulation rather than a tiny self-owned core. Very popular and a strong tool to try later; no need to evaluate it today. *Deep-profile pending.* |
| **Amp** | Sourcegraph | proprietary | Frontier-pushing, heavily built-out. Mode-dial instead of model choice; Orbs remote agents; Oracle/Librarian sub-agents. Watch, not adopt. |
| **Droid** | Factory.ai | proprietary | Frontier-pushing. Model-routing philosophy, Missions orchestration, broadest surface (CLI/IDE/Web/Slack/Linear/Jira). Top Terminal-Bench claims. Watch, not adopt. |
| **OpenCode** | sst (Anomaly) | MIT | Vendor-neutral, 75+ providers, client/server + SDK, ACP everywhere, reads `CLAUDE.md`. The open-source neutral option. |
| **Aider** | Paul Gauthier | Apache-2.0 | The OG minimal git-native terminal pair-programmer. BYOK, repo-map, commit-per-change, maintains the Polyglot leaderboard we already cite. Closest philosophical cousin to Pi's minimalism. *Deep-profile pending.* |
| **Gemini CLI** | Google | Apache-2.0 | Open-source terminal agent, generous free tier on Gemini. **Largely superseded by Antigravity** (Google's agentic IDE) — tracking mainly for the local-model/free-tier angle. *Deep-profile pending.* |

### Tier 2 — editor-integrated agents

| Tool | License | Positioning |
|---|---|---|
| **Cursor** | proprietary | AI-native VS Code fork (Anysphere). Subscription. Strong inline + agent modes; increasingly pushing **cloud/background agents** (drifts toward Tier 3). Previously evaluated and tombstoned in our manifest. |
| **Cline** | open source | Autonomous coding agent as a VS Code extension. BYOK, MCP-heavy, plan/act split. Notable as an open, editor-embedded option. *Not host software — lives in the editor, so catalogued here, not in the manifest.* |
| **Antigravity** (IDE) | proprietary | Google's agentic IDE; the successor surface to Gemini CLI. Introduces **agent-inbox / agent-manager** UX — see Tier 3 note. Tombstoned in our manifest. |

### Tier 3 — orchestration / multiplexers / agent inboxes

These manage *fleets* of agents. Explicitly **avoided for now** — they hide the
agent loop and lean into the concurrency-as-progress framing we're skeptical of.

| Tool | Positioning | Our take |
|---|---|---|
| **Conductor** | Mac app that runs many Claude Code agents in parallel across git worktrees | Too much fleet, too little comprehension for us. Tombstoned. |
| **cmux** | Terminal workspace/multiplexer for agent sessions | Didn't beat Ghostty + Zellij session control. Tombstoned. |
| **Cursor agents** | Cursor's cloud/background agent surface | Heavy; hides execution. Not our direction. |
| **Antigravity agent inbox** | Manage/triage a queue of autonomous agents | Hides far too much right now. Firmly not going this way. |
| **[Isomux](https://isomux.com/)** | Visual agent office for coordinating sessions, state, and handoffs | Useful inspiration for one operator doorway, glanceable working/ready/blocked state, and concise evidence handoffs. Patterns mined; do not adopt another permanent orchestration layer unless measured friction creates a concrete need. |

---

## Historical capability snapshot — deep-profiled set (2026-07-20)

This table is retained as a dated research snapshot, not a maintained parity
matrix. Current decisions live above and in `docs/pi-build-philosophy.md`; the
cross-vendor matrix format was retired because fast vendor churn made it drift.

Legend: **●** native / first-class · **◐** partial / limited / via-IDE ·
**◈** only by building or installing an extension · **○** absent (by design or unbuilt).

A richer, theme-aware visual version of this matrix was generated as a companion
report; this table is the durable source of truth.

| Capability | Pi | Oh My Pi | Claude Code | Codex | Amp | Droid | OpenCode |
|---|---|---|---|---|---|---|---|
| **License** | MIT | MIT | proprietary | Apache-2.0 | proprietary | proprietary | MIT |
| **Implementation** | TS/Node | Rust+TS | TS/Node | Rust | TS/Node | proprietary | TS/Bun |
| **BYOK breadth** | ● 20+ | ● 40+ | ◐ Anthropic-centric | ◐ OpenAI+local | ○ none | ● multi+custom | ● 75+ |
| **Subscription auth** | ● Claude+ChatGPT+Copilot | ● Anthropic/Gemini/Copilot | ● Claude Pro/Max | ● ChatGPT | ◐ ChatGPT link | ○ own plan | ○ BYOK only |
| **Per-role model routing** | ◐ | ● 5 roles | ◐ | ● per-subagent | ● mode | ● complexity | ◐ |
| **Edit primitive** | string | hash-anchored | string | V4A apply_patch | string | Edit/ApplyPatch | string+apply_patch |
| **Stale-edit safety** | ◐ read-first | ● reject-on-drift | ◐ read-first | ◐ context-anchor | ◐ | ◐ | ◐ |
| **Background shell** | ○ (tmux) | ● | ● | ● | ◐ | ◐ | ● |
| **AGENTS.md / CLAUDE.md** | ● | ● reads 8 fmts | ● | ● | ● +globs | ● | ● +CLAUDE fallback |
| **Auto-compaction** | ● | ● | ● | ● | ◐ | ◐ | ● |
| **Cross-session memory** | ○ DIY | ● retain/recall | ◐ | ◐ | ◐ | ◐ | ○ |
| **Built-in subagents** | ○ tmux/ext | ● task+smol | ● Agent+types | ● worker/explorer | ● auto | ● custom droids | ● explore/scout |
| **Multi-agent orchestration** | ◈ ext | ● swarm DAG | ● Workflow | ● threads+CSV | ◐ Orbs | ● Missions | ◐ task |
| **Parallel worktree isolation** | ○ | ● COW | ● worktree | ◐ | ◐ | ● | ◐ |
| **Background / async tasks** | ○ | ● | ● | ● +cloud | ● Orbs | ● Computers | ◐ Actions |
| **Plugins / custom tools** | ● deep | ● | ● +MCP | ● | ● | ● | ● |
| **Lifecycle hooks** | ● 30+ | ◐ stream-rules | ● | ● | ◐ 5 | ● | ● |
| **Skills (SKILL.md)** | ● | ● +8 fmts | ● originated | ● | ● | ● | ● +.claude |
| **MCP client** | ◈ build ext | ● +inherits cfg | ● | ● | ● | ● | ● |
| **MCP server (expose self)** | ○ | ◐ | ◐ serve | ● mcp-server | ○ | ○ | ○ |
| **Approval / permission modes** | ○ DIY | ● prompt+remember | ● modes+rules | ● policies | ◐ off-default | ● autonomy | ● allow/ask/deny |
| **OS-level sandbox** | ○ | ◐ COW (not syscall) | ● Seatbelt | ● Seatbelt/bwrap | ○ | ◐ | ○ |
| **LSP integration** | ○ | ● 14 ops | ◐ via IDE | ○ | ○ | ○ | ◐ 28 servers |
| **Semantic rename** | ○ | ● | ○ | ○ | ○ | ○ | ◐ |
| **DAP live debugging** | ○ | ● 28 ops | ○ | ○ | ○ | ○ | ○ |
| **Browser / computer use** | ○ | ● CDP+Electron | ◈ via MCP | ● computer use | ◐ screenshot | ○ | ○ |
| **IDE plugins** | ○ RPC only | ◐ Zed/ACP | ● VS Code+JB | ● VS Code+JB+Xcode | ● 4 editors | ● VS Code+JB | ● VS Code+ACP |
| **ACP (editor protocol)** | ◐ | ● Zed | ◐ Zed | ○ | ● Zed | ○ | ● Zed/JB/Nvim |
| **Cloud / async agents** | ○ | ○ ssh only | ● web+Actions | ● Codex cloud | ● Orbs | ● Computers | ◐ Actions |
| **GitHub PR review bot** | ○ gist | ◐ pr:// | ● @claude | ● @codex review | ◐ push-branch | ● @droid | ● /oc |
| **Git / PR workflow** | ○ gist | ● commit-split | ● | ● | ● push-branch | ● | ● /undo(git) |
| **Cost / token tracking** | ● footer | ◐ | ● /cost | ● /usage | ● usage | ● dash | ● stats |
| **Telemetry (OTel)** | ◐ install-ping | ◐ fork | ● | ● opt-in | ◐ | ◐ | ◐ local |
| **Session branch / undo** | ● tree/fork | ● checkpoint/rewind | ● resume/rewind | ● resume/fork | ◐ | ◐ fork | ● undo/redo |
| **Config format** | JSON `.pi/` | YAML `~/.omp/` | JSON settings | TOML config | JSON settings | JSON `.factory/` | JSON opencode |

### Open Interpreter vs Pi — overlap, but a different bet

The current Open Interpreter is a direct competitor to Pi in the broad sense:
both are open-source terminal coding-agent harnesses that can run across model
providers. It is not simply “another Pi,” though:

- **Pi minimizes and exposes the harness.** Its value is a very small core, broad
  provider/subscription support, and a deep extension surface we can understand
  and own.
- **Open Interpreter emulates model-specific harnesses.** It is a July 2026 Rust
  fork of Codex that switches among Kimi Code, Qwen Code, DeepSeek TUI, Claude
  Code, SWE-agent, and other prompt/tool conventions. Its value proposition is
  getting cheap/open models closer to the environment they were trained for,
  while retaining Codex-derived sandboxing, MCP, approvals, hooks, skills, ACP,
  and Codex SDK compatibility.
- **For our current setup, it is mostly redundant.** Pi is the transparent daily
  trial, and Codex already supplies the mature sandboxed path. Open Interpreter
  becomes useful if provider-specific harness emulation materially improves an
  open/low-cost model, or if a drop-in self-hosted Codex-compatible agent is
  needed.

**Traction snapshot (2026-07-25):** the repository has about 67.3k GitHub stars
and 5.8k forks, versus about 77.5k stars and 9.5k forks for `badlogic/pi-mono`.
Open Interpreter is therefore a very popular, highly visible project, though not
currently more starred than Pi. Its headline count is partly inherited from the
2023–24 Python project, so it does not measure adoption of the new Rust agent by
itself. The relaunch is active but young: ten Rust releases landed from July
14–18, the latest release assets have roughly 7.2k downloads, and recent merged
work is heavily maintainer-led. It looks like a strong tool to try later, after
the current product has had time to mature.

**Watch trigger:** no action today. Revisit after the Rust product has had a
quarter to stabilize, or sooner if open-model testing shows a material
harness-dependent quality gain.

### Pi vs Oh My Pi — the pair worth knowing

Same thesis ("the model is the moat, the harness is the bridge"), opposite
defaults:

- **Base Pi** — a tiny transparent core you own and build on. Standout perk:
  three-ecosystem subscription auth (Claude Max + ChatGPT + Copilot) in one tool,
  plus 20+ BYOK and local `llama.cpp`. Cost: a rebuild tax for anything beyond
  read/write/edit/bash.
- **Oh My Pi** — a ~55k-LOC Rust fork (single maintainer, young) that has already
  built the rebuild list and **inherits your existing `.claude`/`.codex`/`AGENTS.md`/MCP
  config** natively. The "already assembled" path.

**Key realization:** the "what must I rebuild?" question is really a *base-Pi*
question. Pick Oh My Pi and most of it evaporates — but you take on a large
opinionated fork instead of a small core you own.

### Pi UI surface experiments

- **Native fullscreen mode (Pi 0.84.3)** — adopted as the managed default. It owns the viewport and adds transcript search, scrolling, text selection, links, and previous/next user-prompt jumps. It intentionally renders the same transcript, so a short session looks almost identical to regular mode. The custom `/reader` was retired; its final-answer landmarks and compact work summaries did not earn the extension surface.
- **[@firstpick/pi-package-webui](https://pi.dev/packages/@firstpick/pi-package-webui)**
  — **interesting, but don't migrate now.** Third-party, MIT-licensed local
  browser companion by Firstp1ck. It runs Pi through RPC and adds multi-tab
  sessions, streaming output, model controls, uploads, workspace/Git views,
  extension widgets, notifications, and PIN-gated network access. Its real wins
  are multi-session management and remote access; the terminal footer now covers
  the information-density advantages. Revisit only if those two needs become
  real, and audit the package first because Pi packages execute with full user
  privileges.
- **[pi-gui](https://github.com/minghinmatthewlam/pi-gui)** — okay-ish looking,
  but not compelling enough yet; the visual direction does not inspire an
  immediate switch. It is **not an official Earendil/Pi app**: it is an
  MIT-licensed open-source Electron client by independent developer Matthew Lam
  (`minghinmatthewlam`). It wraps the official `@earendil-works/pi-coding-agent`
  runtime and keeps Pi session files as its source of truth, but lives in the
  developer's own repository and release channel.
- **[Open WebUI Computer](https://github.com/open-webui/computer) (`cptr`)** —
  **evaluated on mobile (2026-07-25), iceboxed.** Source-available (Open Use
  License) FastAPI/SvelteKit app that drives Pi/Claude Code/Codex alongside a
  terminal, a computer-use browser, filesystem tools, and chat — self-hosted over
  Tailscale. It is genuinely capable and the direction is appealing, but it
  didn't address a pain point we actually have, and the mobile experience (chat
  reliability and the low-contrast, hard-to-read interface) wasn't there for us;
  making it feel good would take meaningful custom-CSS/theming work, since it
  ships no high-contrast option. Paseo covers our daily phone-driving need far
  more pleasantly, so cptr is parked, not adopted. Worth another look if its
  mobile UI matures or we grow into its browser/computer-use capabilities. Fully
  removed from `dfs remote`; if a nicer-looking alternative is wanted later,
  [CloudCLI (siteboon/claudecodeui)](https://github.com/siteboon/claudecodeui)
  is the candidate to trial.

A listing in the pi.dev package gallery means a package is discoverable in Pi's
community ecosystem, not that Earendil authors or endorses it.

### If we ever migrate Codex/Claude Code → base Pi: the rebuild list

Ordered by pain. This is the deferred work, captured so future-us doesn't
re-derive it.

| Severity | What we'd lose | Pi's answer | In Oh My Pi? |
|---|---|---|---|
| **Critical** | Sandbox + approval gating | **Partly built:** permission-policy + safe-git hooks; still no OS syscall sandbox. Accept explicitly or wrap Pi in Seatbelt/container before retiring Codex. | Partial (prompts + COW, no syscall sandbox) |
| **High** | MCP servers | write/install an MCP extension | Yes (+inherits config) |
| **High** | Subagents / orchestration | tmux fan-out or thin extension | Yes (task/swarm/hub) |
| **High** | Cloud/async + PR-review bot | not locally replicable — keep Codex/CC for this | No |
| **Medium** | Browser / computer use | custom extension | Yes |
| **Medium** | Plan mode / to-dos | `PLAN.md` file pattern | Partial |
| **Medium** | IDE / ACP | RPC/JSON embedding, no shipped plugin | Yes (Zed/ACP) |
| **Medium** | Git / PR workflow | bash or extension | Yes |
| **Low** | LSP / semantic rename | *not a regression* — Codex/CC lack it too | Yes |
| **Low** | DAP debugging | *nobody but Oh My Pi has it* | Yes |

---

## Open-model inference

The model, runtime, router, managed-host, and serverless-GPU landscape now lives in
[open-model-inference.md](open-model-inference.md). This page owns agent harnesses;
it should refer to that comparison rather than preserving another volatile provider
or model ranking.

## Open questions / to-do (tracked)

- [ ] **Cross-harness mobile control:** Paseo over Tailscale is adopted. Do not build a replacement until Paseo fails a concrete workflow and an existing cross-harness client cannot satisfy it. A Pi-only browser UI cannot meet the requirement.
- [ ] **Deep-profile the additions** to matrix parity: Open Interpreter, Aider,
      Gemini CLI, Cline, Cursor (agent surface), plus Conductor/cmux positioning
      detail.
- [ ] **Local + open model path:** Pi now has explicit frontier/private/auto
      routing and oMLX is under local acceptance testing. Finish the measured A/B,
      tool-loop verification, and privacy-router evaluation before calling the path
      adopted; see [open-model-inference.md](open-model-inference.md).
- [ ] **Re-verify churny facts** before any decision: model IDs (Amp/Codex change
      weekly), Oh My Pi LOC/stars, "Amp subagent messaging", Pi subagent "parallel
      mode". All flagged as fast-moving.
- [ ] **Revisit the "own the harness" build** when the maintenance tax visibly
      drops (Oh My Pi stabilizes) or a genuine step-change lands. Not before.
- [ ] **Trigger to re-open the decision:** subscription economics change, a
      privacy requirement appears, or Codex/Claude Code degrade.

## Sources (primary, 2026-07)

- Pi — [badlogic/pi-mono](https://github.com/badlogic/pi-mono),
  [design blog](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/), pi.dev
- Oh My Pi — [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi), blog.can.ac
- Codex — [openai/codex](https://github.com/openai/codex), learn.chatgpt.com/docs
- OpenCode — [sst/opencode](https://github.com/sst/opencode), opencode.ai/docs
- Amp — [ampcode.com/manual](https://ampcode.com/manual)
- Droid — docs.factory.ai
- Open Interpreter — [OpenInterpreter/open-interpreter](https://github.com/OpenInterpreter/open-interpreter),
  [terminal docs](https://www.openinterpreter.com/docs/terminal)
- Aider — aider.chat · Cline — github.com/cline/cline · Gemini CLI —
  github.com/google-gemini/gemini-cli · Cursor — cursor.com · Antigravity — Google
- Claude Code — first-hand feature knowledge.

*Fast-moving category — re-verify before committing to anything.*
