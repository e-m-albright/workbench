# Agent Capability Patterns

> **Last reviewed**: 2026-08-28. Notes on emerging agent-harness capabilities and orchestration patterns — what each is, how it reshapes the workflow, and the tradeoffs. Timestamps like `[source 01:38]` reference the announcement videos these notes were taken from; pricing and benchmark figures date from those announcements and age quickly. Vendor benchmark and pricing claims remain claims until independently reproduced.

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

Philipp Schmid's four-pattern ladder is a useful complexity test: begin with one inline worker, add bounded fan-out only for independent work, add persistent agent pools only when repeated coordination needs durable identities and shared state, and use direct agent teams only when peer communication is itself necessary. Workbench intentionally stops at the first two levels. More autonomy is not progress if the coordination mechanism costs more than it returns.

Franck Verrot's "convergence engineering" is the matching control principle. The loop is only a mechanism; the real design object is an externally testable invariant that each pass moves toward, such as a green test suite, a reproduced browser state, or a review rubric with no surviving high-confidence findings. A loop without an acceptance condition can repeat, spend, and still drift. This reinforces Workbench's existing rule: give agents deterministic feedback and a bounded stop condition rather than asking them to keep improving an output abstractly.

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

Treat “works while the Mac is locked” as an execution-location claim, not permission to control a locked computer. A hosted Codex task can continue in OpenAI's environment after the local app disconnects; a local agent still inherits the operating system's lock, sleep, credential, and application constraints. Decide between local continuity and hosted execution by the data and trust boundary, not by the convenience headline.

## 9. Code intelligence and edit primitives

The notable open-source experiments are:

- **Hash-anchored edits**, which bind patches to content hashes and reject stale references.
- **Language Server Protocol operations**, which provide definitions, references, diagnostics, and semantic rename.
- **Debug Adapter Protocol operations**, which let an agent set breakpoints, step, and inspect runtime state.

These are credible mechanisms, but adoption should follow observed local friction. Exact-text Edit already fails loudly on stale matches. Workbench's prior telemetry did not find a symbol-navigation bottleneck. Debugger control remains the most differentiated idea, but it still needs a real debugging workflow where ordinary command-line tools are the limiting factor.

## 10. Trust machinery is the autonomy limit

The practical ceiling on autonomy is set by sandboxing, permission scope, verification, attribution, spend limits, and kill switches rather than by model intelligence alone. The defensible norm remains: agents propose, tests and reviewers verify, humans merge. Workbench should continue using Claude Code or Codex for high-autonomy work against untrusted inputs because Pi's policy extensions are tool-call guardrails, not operating-system containment.

OpenAI's Windows sandbox illustrates why containment is a composition problem rather than a single switch. Its unelevated path combines a synthetic security identifier, access-control lists, write-restricted tokens, and explicit protection for repository metadata. Its elevated path uses separate local accounts for networked and offline work, restricted tokens, and firewall policy. The reusable design is to separate online and offline identities, grant only the workspace access each needs, and layer operating-system identity, filesystem, process, and network controls. No one Windows primitive supplies the whole boundary.

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

## 13. Code-first durable workflows

Vercel's Workflow SDK makes a strong case for expressing orchestration as ordinary program control flow rather than maintaining a separate visual or declarative directed acyclic graph. A compiler marks durable orchestration and side-effecting steps, while normal `await`, loops, branches, `try/catch`, and parallel promises remain the workflow definition. The backend supplies persistence, queuing, and replay rather than owning another copy of the business logic.

The transferable design criteria are:

- Workflow definitions are reviewed, typed source code when branching and state are substantial.
- Durable steps make side effects and retry boundaries explicit without duplicating control flow in configuration.
- In-flight runs stay pinned to the code version that created them; immutable deployment routing moves version compatibility out of application branches.
- Human input should use one composable wait/resume primitive rather than several overlapping signaling concepts.
- Runtime storage, queueing, and execution backends sit behind a narrow interface, but portability claims must be verified against each backend.

### Disposition

Adopt the design criteria, not Vercel Workflow SDK. Workbench has no durable workflow runtime to replace, and scheduled instances remain owned by the operating system, CI, or a private automation layer. If reusable automation mechanics earn a place here, start with ordinary code, explicit durable boundaries, and version-pinned runs rather than a visual graph or a second orchestration description.

Vercel's article is a first-party product argument. Its cleanest versioning result depends on Vercel retaining immutable deployments, the first-party Postgres backend did not yet provide the same routing, and the authors acknowledge that durable step calls still carry network and queue overhead.

Cloudflare Workflows V2 independently reinforces the mechanics: each step is durable and idempotent, successful steps are replayed rather than repeated after a failure, parallel branches are explicit, and step traces expose progress. This is useful corroboration, not a reason to add Cloudflare as another scheduler. The same requirement remains: business logic should stay in reviewed code while persistence, retries, and replay sit behind a narrow runtime boundary.

Sources: Pranay Prakash, [The best workflow engine is a programming language](https://vercel.com/blog/the-best-workflow-engine-is-a-programming-language), 2026-08-27; and [Cloudflare Workflows V2](https://developers.cloudflare.com/workflows/), 2026.

## 14. MCP composition without an aggregator by default

PulseMCP's advanced patterns identify the real Model Context Protocol value as cross-service composition and access from multiple client surfaces, not replacing one application's mature interface with chat. Their proposed progression is local server, remote multitenant server, installation links, and finally one authenticated aggregator to reduce an M-by-N client/server configuration problem to M-plus-N connections. They also recommend code execution, command-line composition, tool search, and response truncation to keep intermediate data and tool definitions out of model context.

The useful principles are:

- Adopt a connector for a cross-service job or missing capability, not merely to chat with one application.
- Prefer bounded search and action tools over exposing an entire API surface and all intermediate payloads to the model.
- Use browser or computer control as an escape hatch. Graduate a repeated predictable flow into a typed connector or script.
- Centralize declarative installation when many clients need the same servers, but keep authority narrow per session and per tool.
- Treat remote MCP servers, tunnels, aggregators, and browser-control servers as separate trust expansions that require authentication, tenant isolation, egress policy, and auditability.

### Disposition

Do not add an MCP aggregator. Workbench's registry and sync already centralize configuration across the supported harnesses while owned connectors preserve separate credentials, scopes, and tool contracts. There is not enough active M-by-N pressure to justify concentrating every credential and tool behind one runtime endpoint. The context-efficiency guidance reinforces the existing preference for small owned connectors, command-line interfaces, search, and truncation over broad always-on MCP schemas.

The article was originally published by PulseMCP, whose products and open-source examples benefit from broader MCP adoption. Its architecture is credible, but the security and operational costs of aggregation are underdeveloped relative to the convenience case.

Source: Adam Jones and Tadas Antanavicius, [Effective Patterns for Advanced MCP Usage](https://www.oreilly.com/radar/effective-patterns-for-advanced-mcp-usage/), 2026-08-26.

An MCP server should expose outcomes rather than mirror every REST endpoint. Keep one server focused on one job, prefer a small discoverable tool set, use flat typed arguments, return compact paginated results, and write errors that tell the agent how to recover. Service-prefixed action names reduce collisions when several servers are active. These are context-budget and reliability controls: orchestration that deterministic code can perform should not consume model turns, and a giant schema is not useful merely because it is complete.

Source: [Philipp Schmid's MCP server design guidance](https://www.philschmid.de/mcp-best-practices), 2026-01.

## 15. Passive retrieval can become code execution

Johann Rehberger demonstrated a targeted indirect prompt-injection chain against Claude Code Opus 5 Auto Mode. A website caused the preferred fetch tool to fail, the agent fell back to `curl`, followed a redirect to an archive, rejected the supplied binary, wrote its own Python decoder, and ran it inside the attacker-controlled extracted directory. Python module shadowing loaded a malicious `struct.py` during an apparently benign `base64` import. In small samples, the reported variants achieved their intended effects in three of five to four of five runs.

The important mechanism is not one poisoned filename. Goal pursuit converted a passive summary request into retrieval, extraction, code generation, and execution through individually plausible steps. A model-written replacement utility is not trusted when its imports resolve from attacker-controlled state. A permission classifier that judges one command at a time cannot enforce provenance across that chain.

### Disposition

- Keep external retrieval on dedicated read-only browser or connector tools. If they fail, stop rather than switching to a shell network client merely to complete a summary.
- Pi blocks `curl` and `wget` as a concrete tripwire, but this is not containment; other runtimes can still provide network access.
- Never execute an interpreter, build tool, decoder, or model-written helper from an untrusted download or extracted directory outside an operating-system sandbox.
- Use an explicit operating-system sandbox plus network egress restrictions for execution involving untrusted inputs. Auto approval and safety classifiers are not security boundaries.
- Treat archives, repositories, package contents, filenames, and working-directory import paths as executable attack surface, even when the visible task is read-only.

### Defense design if the gap becomes active

The right architecture is soft guidance plus hard containment, not a larger prompt-injection classifier. Rules can prevent common mistakes and identify suspicious transitions, but they cannot reliably decide whether sophisticated content is malicious. Deterministic policy should follow provenance and capability instead:

1. Mark browser, connector, archive, unfamiliar-repository, package, and automation output as untrusted ingress.
2. Keep source-reading sessions unable to act. Promote only a human-reviewed distillation into a fresh acting session.
3. When untrusted code must run, use a disposable worktree or copied workspace with no home directory, Keychain, SSH keys, agent credentials, authenticated browser profile, host process control, or durable Git authority.
4. Deny network egress by default while allowing loopback for application tests. If package installation or download is required, grant a narrow temporary route through a broker that records destination, redirects, content type, size, and hash.
5. Keep parent review and adoption outside the sandbox. The sandbox may produce a patch; it does not merge, commit, deploy, or publish.

High-signal tripwires are capability transitions rather than prose classification: read-only retrieval followed by shell networking; cross-origin or HTML-to-archive redirects; interpreter execution from an untrusted working directory; model-written helpers run immediately against untrusted files; module-shadowing filenames or package lifecycle hooks; nested-agent or detached-process creation; and new outbound destinations during local analysis.

### Current decision

Do not build this machinery yet. The present combination of source-only modes, dedicated retrieval tools, Pi tripwires, explicit sandboxed-harness fallback, disposable workers, and parent review is proportionate to observed use. Revisit only after a concrete workflow repeatedly requires untrusted execution and the existing sandboxed fallback is measurably too restrictive, too slow, or too easy to bypass. A future trial should begin with one sandboxed execution profile and provenance marker, not a universal taint engine, network broker, or attack classifier.

This is a motivated proof of concept with 15 reported trials across three variants, not a population-level attack-success estimate. The transferable conclusion is architectural: model behavior and per-command approval can reduce risk, but only isolation and egress control bound the consequence of a successful injection.

Sources: Johann Rehberger, [Breaking Claude Code Opus 5 Auto Mode](https://embracethered.com/blog/posts/2026/breaking-claude-code-opus-5-and-automode/), 2026-08-26; Jessica Lyons, [Researcher shows how Claude Code can be tricked simply by asking it to summarize a website](https://www.theregister.com/research/2026/08/28/researcher-shows-how-claude-code-can-be-tricked-simply-by-asking-it-to-summarize-a-website/5293372), 2026-08-28.

## 16. Role-based onboarding and teach-by-demonstration

Grok Bot packages a persistent cloud agent as named roles such as researcher, recruiter, or market analyst. The user can describe an outcome, choose a suggested role, or demonstrate a task in the agent's browser. The product converts a successful demonstration into a draft skill and can run that skill later as a routine. Desktop and mobile clients preserve access to the same background agent.

The transferable product pattern is a short progression:

1. Start from the user's job or outcome rather than asking them to design tools and prompts.
2. Let the user demonstrate an unfamiliar workflow instead of fully specifying it in prose.
3. Turn the demonstration into an inspectable draft skill.
4. Test the skill once before allowing it to become a recurring routine.
5. Keep the routine's progress, approvals, and handoffs visible across desktop and mobile.

This lowers the setup cost for non-technical users and teaches agent use through concrete work. Named roles also make delegation easier to understand, but they are interface boundaries rather than authority boundaries. Grok Bot's official documentation says all Bots for one user share one cloud computer, files, browser sessions, and credentials. Separate Bots therefore belong to one trust domain and must not imply isolation. Its model-based approval review can help triage prompts, but it is not a deterministic security boundary.

### Disposition

Adopt the onboarding sequence as a design reference, not the hosted credential model or a standing roster of named agents. If Workbench gains a repeated non-coding workflow, begin with an outcome-specific template and a demonstration-to-draft-skill flow. Require inspection and one successful supervised run before scheduling. Preserve explicit capability scope, deterministic policy, and least privilege underneath any friendly role metaphor.

The evidence is early. Official material establishes the interface and shared-runtime design. Early community reports broadly agree that setup is unusually approachable and that demonstrations and recurring monitoring are the distinctive features, but reports of execution quality are mixed. There is not enough independent head-to-head evidence to claim that Grok Bot produces better outcomes than Perplexity Computer. The supported conclusion is narrower: it is easier to start, not proven safer or more reliable to trust.

Reviewed 2026-08-30. Sources: [Grok Bot](https://x.ai/bot), [overview](https://docs.x.ai/grok-bot/overview), [skills, routines, and automations](https://docs.x.ai/grok-bot/skills-routines-and-automations), [approvals, security, and privacy](https://docs.x.ai/grok-bot/approvals-security-and-privacy), [FAQ](https://docs.x.ai/grok-bot/faq), [Perplexity Computer](https://www.perplexity.ai/products/computer), and early [Hacker News discussion](https://news.ycombinator.com/item?id=49261514).

## 17. Managed agent runtimes are converging

Anthropic Managed Agents, Google Managed Agents, LangChain Deep Agents Deploy, and OpenAI's hosted agent stack increasingly expose the same primitives: isolated execution, retained state, tools, background work, resumable environments, evaluation, observability, and credential handling. The category is becoming infrastructure rather than a unique product idea.

The practical selection criteria are therefore outside the feature checklist:

- where credentials are stored and how narrowly they can be injected
- whether outbound network access is denied, restricted, or open by default
- whether memory, evaluations, logs, and workflow definitions are exportable
- whether work can run behind the customer's boundary
- total task cost, including long reasoning traces and retries
- whether the runtime supports deterministic policy and human approval independently of model judgment

### Disposition

Do not add a second managed-agent runtime without a concrete workload that existing local execution, GitHub Actions, or a current hosted harness cannot satisfy. When that workload appears, compare the trust boundary, portability, and total completed-task cost before model branding. Google is the most important new watch because it is productizing the Antigravity-style harness through a general application programming interface; this does not create a present adoption need.

Sources: [Google Managed Agents](https://ai.google.dev/gemini-api/docs/agents), [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview), [Deep Agents Deploy](https://www.langchain.com/blog/deep-agents-deploy-an-open-alternative-to-claude-managed-agents), and [Anthropic Managed Agents](https://claude.com/blog/claude-managed-agents-memory).

## 18. Skills are operational packages, not prompt fragments

Anthropic's internal Claude Code practice reinforces the existing Workbench model: a useful skill is a folder that can contain instructions, scripts, references, data, and assets, with progressive disclosure controlling what enters context. The most valuable content is accumulated operational knowledge, especially edge cases and gotchas, rather than generic best practices. A skill description is a routing interface for the model, so it should state when the capability applies more precisely than it summarizes the content for a human.

Anthropic reports its clearest internal quality gains from verification skills. That supports a priority order for Workbench: package executable checks and proven runbooks before adding advisory prose; let deterministic policy live in hooks or code; use temporary on-demand hooks when a task needs stricter controls than the project default. Lightweight skill-local logs can help repeated workflows learn, but durable project facts still belong in the repository's canonical documentation.

Interactive HTML artifacts are useful when supervision benefits from direct manipulation: editing a plan, comparing layouts, annotating a proposal, or inspecting a generated visualization. Markdown remains the better durable format when diffability, search, and long-term maintenance matter. The artifact earns its complexity only when it lowers review cost or reveals state that prose cannot.

Sources: [Anthropic on internal skills](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills) and [Thariq Shihipar on interactive artifacts](https://www.lennysnewsletter.com/p/html-is-the-new-markdown-how-anthropic).
