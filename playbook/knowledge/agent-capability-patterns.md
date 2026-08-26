# Agent Capability Patterns

> **Last reviewed**: 2026-08. Notes on emerging agent-harness capabilities and orchestration patterns — what each is, how it reshapes the workflow, and the tradeoffs. Timestamps like `[source 01:38]` reference the announcement videos these notes were taken from; pricing and benchmark figures date from those announcements and age quickly. Vendor benchmark and pricing claims remain claims until independently reproduced.

## 1. Advisor Strategy

Addresses the trade-off between intelligence and cost. Pairs a high-intelligence model (Opus) with a more cost-effective model (Sonnet or Haiku).

**How it works**: Instead of standard task decomposition, the smaller model (executor) handles the primary work and tool calls. It only calls the "Advisor" via a tool call when it gets stuck or needs feedback. [source 01:38]

**Performance**: On multilingual SWE-bench, Sonnet + Opus (as advisor) scored 2% higher than Sonnet alone while reducing costs by approximately 11%. [source 02:58]

**Benefits**: Lower costs, increased execution speed, and improved reliability for complex tasks.

## 2. Monitor Tool (Claude Code)

Eliminates the need for "polling loops," where an agent constantly checks the status of background processes.

**How it works**: Claude can create background scripts that monitor progress, errors, and results. When a process finishes, it sends an interrupt to Claude. [source 05:42]

**Impact**: Significant token savings and the ability to run more background processes simultaneously within Claude Code. [source 06:08]

**Usage**: Not active by default — must be explicitly prompted (e.g., "use the monitor tool to observe for errors"). [source 06:38]

## 3. Managed Agents (Anthropic)

Managed infrastructure service that handles the "grunt work" of deploying agents to production.

**Core capabilities**: Anthropic provides secure sandboxing, authentication, logging, and tool execution. [source 08:06]

**Persistent sessions**: Supports long-running autonomous sessions (hours) where progress persists even if you disconnect. [source 08:14]

**Pricing**: Standard token rates apply plus a runtime fee of **$0.08 per session hour** (at announcement). [source 09:18]

## 4. OpenAI Agent Builder (competitor)

Visual, low-code canvas for composing multi-step agentic workflows. [source: [OpenAI video](https://www.youtube.com/watch?v=44eFf-tRiSg)]

**Core capabilities**:
- **Visual workflow construction** — drag-and-drop nodes to define task flow, branching, and loops
- **Handoffs** — route queries between specialized agents (e.g. general assistant -> "Coder" agent for technical questions)
- **Tool integration** — File Search, Code Interpreter, MCP (Model Context Protocol) for external data/app access
- **Guardrails** — constrain outputs to stay within safety/operational parameters

**Positioning**: Competes directly with LangGraph, n8n, and (less directly) with Claude Code's more code-first approach. The move is from "chatbots" (single-turn) to "agents" (developer defines architecture, runtime manages state and tool calls).

**Tradeoffs to watch**:
- **Error surface area** — every handoff and tool call is a new failure mode. A bad handoff in step 2 derails the whole chain
- **Latency** — multi-agent chains are meaningfully slower than single model calls; better fit for async background jobs than real-time UX
- **Lock-in** — visual builders hide the actual orchestration code. Migrating to a different runtime later usually means rebuilding the graph

**Principal-eng read**: The interesting bet is whether visual composition beats code. For prototyping, yes — anyone can sketch a workflow. For production, the usual pattern holds: visual builders get you to a demo fast, then teams hit a ceiling and rewrite in code (LangGraph, custom orchestration, or Anthropic's Agent SDK) for debuggability, version control, and testing. Worth tracking to see if OpenAI closes that gap with better eval/observability in-canvas.

## 5. Coordinated review and bug hunts

The useful pattern is not merely "run more agents." It is a staged review:

1. Independent finders search separate issue classes.
2. A skeptical pass attempts to disprove each candidate.
3. A verifier reproduces surviving claims against actual code behavior.
4. The parent ranks confirmed findings and owns the final report.

This is the architecture behind the strongest multi-agent review products and the Hunter/Skeptic/Referee pattern. It improves coverage while controlling false positives. It is appropriate for consequential audits, not routine edits. Workbench already expresses the small version through review skills plus `/consult`; Claude Code remains the fleet option when exhaustive review earns the cost.

## 6. Bounded local delegation

Local delegation has two distinct forms:

- **Read-only finders** can safely run in parallel when their scopes are independent.
- **Mutating workers** require separate worktrees, explicit ownership, and parent review.

Workbench Pi implements the narrow mutating form through the model-callable `worker` tool: one child Pi, one isolated worktree, no commit or push, and parent-owned adoption. The model may delegate, review, and discard without per-use approval. `/worker` remains a manual entrypoint. This is deliberately not a standing agent roster, chain engine, or autonomous merge system. Expand it only when repeated use identifies a specific missing capability such as read-only fan-out or better progress reporting.

## 7. Background work, schedules, and durable objectives

Modern harnesses increasingly provide detached tasks, recurring prompts, event-triggered agents, and long-lived goals. These are different capabilities:

- **Process continuity** keeps a running shell or agent alive after disconnect.
- **Monitoring** wakes the agent when a condition changes instead of spending turns polling.
- **Scheduling** starts work at a future time or in response to an event.
- **Durable objectives** repeatedly reassess an open goal over a longer period.

Do not combine these into a homemade scheduler inside a coding harness. Use the operating system, CI, or an automation repository for scheduled instances. Use Paseo for agent process continuity and mobile control. Use a hosted harness when cloud execution is the required trust and availability boundary.

## 8. Session continuity and mobile control

Terminal multiplexers and agent-aware clients solve different problems:

- **Paseo and vendor mobile clients** preserve agent runs while rendering events, approvals, tools, and transcripts for touch screens.
- **Terminal multiplexers** preserve arbitrary shell processes, but add no value when phone terminal access is not required.
- **A session launcher** lists and opens sessions, but is not itself a readable mobile transcript viewer.

A generic terminal in a phone browser is uniform across harnesses but remains a poor touch interface. Standardize on Paseo over Tailscale rather than maintaining a second terminal-shaped mobile path.

## 9. Code intelligence and edit primitives

The notable open-source experiments are:

- **Hash-anchored edits**, which bind patches to content hashes and reject stale references.
- **Language Server Protocol operations**, which provide definitions, references, diagnostics, and semantic rename.
- **Debug Adapter Protocol operations**, which let an agent set breakpoints, step, and inspect runtime state.

These are credible mechanisms, but adoption should follow observed local friction. Exact-text Edit already fails loudly on stale matches. Workbench's prior telemetry did not find a symbol-navigation bottleneck. Debugger control remains the most differentiated idea, but it still needs a real debugging workflow where ordinary command-line tools are the limiting factor.

## 10. Trust machinery is the autonomy limit

The practical ceiling on autonomy is set by sandboxing, permission scope, verification, attribution, spend limits, and kill switches rather than by model intelligence alone. The defensible norm remains: agents propose, tests and reviewers verify, humans merge. Workbench should continue using Claude Code or Codex for high-autonomy work against untrusted inputs because Pi's policy extensions are tool-call guardrails, not operating-system containment.

## 11. Workbench disposition after the August 2026 review

The major harnesses now share the same vocabulary: hooks, skills, subagents, plugins, cloud sessions, schedules, and review agents. Feature parity is therefore the wrong target. Workbench's durable choices are:

- Keep Pi compact and provider-portable.
- Let Pi call the `worker` tool autonomously for one bounded parallel implementation thread; keep adoption and verification with the parent.
- Use `/consult` or review skills for independent judgment.
- Use Claude Code for large coordinated fleets, hosted schedules, artifacts, and remote cloud work.
- Use Codex or Claude Code when operating-system sandboxing is required.
- Keep durable knowledge in repositories rather than adding opaque agent memory.
- Standardize mobile control on Paseo over Tailscale, not on a terminal multiplexer or a larger Pi core.

## 12. Cursor Automations patterns

Cursor Automations packages a trigger, prompt, tightly scoped tools, and cloud agent runtime into a reusable repository workflow. The public templates add several useful patterns beyond “run an agent on a schedule”:

- **Scheduled and event triggers:** daily runs, pull request opened, and pull request updated are first-class inputs.
- **Typed capability scope:** each template declares only the integrations it needs, such as Slack, reviewer assignment, or pull request comments.
- **Persistent deduplication ledger:** the critical-bug template keeps a small `MEMORIES.md` containing only open or rejected findings, with explicit cleanup rules. This is workflow state, not general agent memory.
- **Confidence-gated mutation:** the bug finder opens a pull request only for a concrete, high-severity trigger scenario; “no critical bugs found” is the expected safe result.
- **Re-evaluation after change:** the reviewer workflow reruns when a pull request changes and can revoke a prior approval when risk increases.
- **Untrusted-trigger handling:** pull request text, diffs, comments, filenames, and commit messages are explicitly treated as adversarial input.
- **Template distribution:** the automation definition is reviewable and reusable rather than hidden in an operator’s chat history.

### Disposition

Workbench should adopt these as workflow design criteria, not build Cursor’s scheduler into Pi. The runtime belongs in GitHub Actions or the private automation layer. A first automation should name one recurring trigger, a least-privilege tool set, an explicit no-op outcome, bounded durable state for deduplication, deterministic verification, and a human-owned merge boundary.

The research changed the design standard in four ways:

1. Treat the automation definition as reviewed source, not an operator prompt that lives only in chat history.
2. Persist only workflow-specific state needed to suppress duplicate work; do not turn a ledger into general agent memory.
3. Make no-op success a first-class result rather than pressuring every run to create an issue or pull request.
4. Re-evaluate prior decisions when the triggering artifact changes; an approval or risk rating is not permanent.

Automatic low-risk approval is not adopted. Model risk classification remains advisory unless deterministic policy independently permits the action. Cursor’s hosted runtime is also not adopted: hosted execution, credentials, billing, and vendor coupling do not earn a second automation control plane while existing owners can express the workflow.

### Research record

Reviewed 2026-08-26 from Cursor’s Automate product page and public marketplace templates:

- [Cursor Automate](https://cursor.com/automate) — product model for scheduled and event-triggered cloud agents with integrations.
- [Find critical bugs](https://cursor.com/marketplace/automations/find-critical-bugs) — evidence for high-confidence mutation, safe no-op runs, and a bounded `MEMORIES.md` deduplication ledger.
- [Assign pull request reviewers](https://cursor.com/marketplace/automations/assign-pr-reviewers) — evidence for declared integration scope and pull request event handling.

The durable conclusion is narrower than the product: copy the workflow contracts, not the scheduler. This is recorded both here and in `docs/decisions/tombstones.md` so future automation design can reuse the intelligence without reopening the Cursor adoption question.
