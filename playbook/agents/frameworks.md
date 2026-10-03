# Agent application frameworks

Choose libraries and runtimes for an application that contains agents. Compare state ownership, execution, testing, and delivery interfaces against the application requirements.

## Agent frameworks -- build-your-own-agent SDKs (reviewed 2026-09-12)

For when we *build* an agent product rather than drive a coding harness. Language
fit is a first-order selection constraint: do not introduce TypeScript merely to
obtain orchestration that the Python or multi-language choices already provide.

**Current selection:** Mastra remains the strongest batteries-included TypeScript
candidate, but **Pydantic AI is now the preferred non-TypeScript canary and the
best fit for a Python-centered application**. LangGraph remains the escalation
path for explicit graph semantics. Microsoft Agent Framework is the serious
multi-language enterprise contender. Agno is the closest Python match to
Mastra's broad product surface, but earns a trial only when teams and operations
are needed together.

### Python front runners: Pydantic AI and Agno 3.0

The choice is primarily about where the framework boundary belongs. Pydantic AI
is a typed, composable library that fits into an application-owned architecture.
Agno is an integrated agent platform whose AgentOS owns more runtime and
operational concerns.

| Dimension | Pydantic AI | Agno 3.0 |
| --- | --- | --- |
| Best fit | An existing Python service that should retain its own architecture | A greenfield agent platform that needs an operations plane quickly |
| Core model | Typed agents, dependencies, tools, outputs, capabilities, and optional Harness packages | Agents, teams, workflows, AgentOS runtime, and Control Plane |
| Multi-agent | Subagents and typed graphs composed as needed | First-class coordinate, route, broadcast, and task team modes |
| Workflow and durability | Python control flow or Pydantic Graph; Temporal, DBOS, Prefect, Restate, and other durable engines | Native workflow steps, scheduler, durable queue, checkpoints, cancellation, and stream reconnection |
| State ownership | The application chooses storage and lifecycle boundaries | AgentOS schemas own sessions, runs, memory, knowledge, schedules, and evaluations |
| Operations | OpenTelemetry, Pydantic Evals, any compatible backend, and optional Logfire | Integrated metrics, tracing, evaluation, approvals, scheduling, role-based access control, and Control Plane |
| Interfaces | Python calls, command-line interface, web chat, realtime voice, AG-UI, Vercel streams, and experimental Agent Client Protocol | REST, server-sent events, WebSockets, Model Context Protocol, Agent-to-Agent protocol, AG-UI, Slack, Telegram, and WhatsApp |
| Testing | Strongest typing and validation boundary; offline test model | Integrated evaluation and runtime inspection, with more framework state to fixture |
| Lock-in | Lower; infrastructure remains replaceable | Higher; runtime data and operations adopt Agno concepts and migrations |
| Main risk | The rapidly expanding Harness surface is newer than the typed core | Platform breadth, breaking changes, and database migration burden |

Agno 3.0 is a credible production platform. Its release added per-user isolation,
normalized run storage, durable jobs, idempotency, bounded concurrency, large
result and media offloading, CodeMode for programmatic tool composition, and a
governed component catalogue. The same release also required a database
migration and made extensive breaking API changes, which demonstrates both its
new operational depth and its ownership cost.

**Decision rule:** default to Pydantic AI when agents are one capability inside a
Python application. Prefer Agno only when teams, durable jobs, schedules,
approvals, persistent multi-user state, several delivery interfaces, and an
operator console are requirements rather than attractive extras. For a serious
greenfield agent product, canary both on one representative vertical slice and
compare framework-specific code, interruption recovery, test setup, storage
migration burden, trace usefulness, approval handling, subsystem replacement,
and total completed-task cost. Sources: [Pydantic AI](https://pydantic.dev/docs/ai/),
[Pydantic capabilities](https://pydantic.dev/docs/ai/capabilities/overview/),
[AgentOS](https://docs.agno.com/agent-os/introduction), and
[Agno 3.0 release notes](https://github.com/agno-agi/agno/releases/tag/v3.0.0).

**TypeScript**

- **[Mastra](https://mastra.ai/)** -- **WATCH, still promising.** Agents, workflows, memory, evaluation, observability, deployment, Studio, and native Model Context Protocol support in one TypeScript platform. Its newer open-source [Factory](https://mastra.ai/factory) adds a configurable issue-to-pull-request board across GitHub, Linear, and Slack, with specialized agents and skills for intake, triage, planning, building, review, shared sessions, and team memory. Mastra's [1 minute 41 second demo](https://www.youtube.com/watch?v=wGtTga5SR_4) claims that its internal deployment produced more than a quarter of merged pull requests in its first three weeks; the description separately claims 25-35 percent of pull requests and 50-60 percent of closed issues. Those are vendor claims with no workload, quality, intervention, or rework denominator. The staged human-gated workflow is credible; the TypeScript-only runtime and Mastra Platform dependency for initial Factory authentication, database, and sandboxes are the main fit concerns. Trial only for a real TypeScript agent product, and require completed-task quality, intervention, spend, and portability evidence rather than pull-request share.
- **[Flue](https://flueframework.com/)** -- Pi-powered TypeScript framework for durable, addressable agents, persistent sessions, channels, and deployment adapters. The Workbench rejection and revisit condition live in [tombstones](../../docs/decisions/tombstones.md). Source overview: [Better Stack video](https://www.youtube.com/watch?v=n5cYS6KuyK8).

**Python and multi-language**

- **[Pydantic AI](https://pydantic.dev/docs/ai/)** (MIT; 19.9k GitHub stars as reviewed) -- **Preferred Python canary; now a direct Mastra competitor rather than merely a light agent loop.** The core provides typed providers, dependencies, tools, structured outputs, Model Context Protocol, evaluation, and OpenTelemetry. The newer Pydantic AI Harness composes memory, subagents, context management, filesystem and allowlisted shell access, planning, coding and research agents, an advisor, and on-demand capabilities. The same agent can run behind a web interface, command-line interface, realtime voice, or a durable queue. First-party and co-maintained integrations cover Temporal, DBOS, Prefect, and Restate, with other durable runtimes available. This is the strongest fit when Python, provider neutrality, testability, and application-owned deployment matter. Canary it before Mastra for a Python service; verify how much of the new Harness is stable versus freshly marketed surface.
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** -- Explicit graph-based stateful orchestration with durable checkpoints and maximum control, at the cost of the steepest abstraction and debugging burden. Use when cycles, resumability, branching state, and human interrupts are the actual domain model, not as the default agent loop.
- **[Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/)** (MIT; 13.5k GitHub stars as reviewed) -- The successor to AutoGen and Semantic Kernel now spans Python, .NET, and preview Go. It provides agents, a batteries-included Harness Agent, functional and graph workflows, sequential/concurrent/handoff/group orchestration, checkpointing, time travel, human approval, middleware, Model Context Protocol, OpenTelemetry, declarative YAML agents, a development interface, and Foundry hosting. This is a credible Mastra alternative when multi-language support or enterprise governance matters. The risk is Microsoft and Azure surface area, not missing capability.
- **[Agno 3.0](https://www.agno.com/products/sdk)** -- The closest Python analogue to Mastra's all-in-one posture: agents, teams, workflows, memory, knowledge, learning, guardrails, hooks, background work, evaluation, observability, scheduling, and FastAPI deployment through AgentOS. Its four team modes and six workflow step types are legible, but the broad platform is more opinionated than Pydantic AI. Evaluate when one product genuinely needs multi-agent teams and an operations plane; otherwise prefer the smaller typed core.
- **[Google Agent Development Kit](https://google.github.io/adk-docs/)** -- No longer accurately described as Python-only or GCP-only: current documentation spans Python, TypeScript, Go, Java, and Kotlin, with graph workflows, evaluation, deployment, and Gemini's multimodal tools. It remains optimized for Google's ecosystem even when model and deployment choices are flexible. Evaluate first for a Gemini-heavy voice, video, Maps, or managed-agent product, not as the neutral default.
- **[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)** -- Small Python and TypeScript agent loop with tools, handoffs, guardrails, sessions, tracing, voice, and Model Context Protocol. Prefer it when OpenAI-native capabilities are the reason for the application; Pydantic AI is the stronger neutral Python default.
- **[smolagents](https://github.com/huggingface/smolagents)** (Hugging Face) -- Code-first Python agents that write and execute Python instead of relying only on JSON tool calls. Fast setup, but not a Mastra-shaped production platform.
- **[AWS Strands Agents](https://strandsagents.com/)** -- AWS's model-driven SDK, Bedrock-native and OpenTelemetry-first. Consider for an AWS-centered deployment, not for framework neutrality.
- **[CrewAI](https://www.crewai.com/)** -- Role-based multi-agent crews. Its role metaphor remains approachable, but Pydantic AI, LangGraph, Agno, and Microsoft Agent Framework now offer stronger typed, durable, or operational foundations.

**Rust / Go** (crossed to production-viable in 2026)

- **[Rig](https://rig.rs/)** (Rust) -- Dominant Rust option, ~7.6k stars; 20+ providers, 10+ vector stores, OTel GenAI conventions, WASM, MCP. Real deployments (Cloudflare, Neon, Nethermind, St. Jude). Benchmarks claim ~5x memory reduction and 25-44% latency wins vs Python equivalents -- re-verify before citing.
- **[Eino](https://github.com/cloudwego/eino)** (Go) -- ByteDance CloudWeGo's component-based framework, 11k+ stars; LangChain-inspired but Go-idiomatic, built for massive-scale serving.
- **[Genkit Go](https://genkit.dev/)** (Go) -- Google's production-ready GenAI framework for Go; streaming, evals, tracing built in.
