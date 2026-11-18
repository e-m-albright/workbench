# Agent interfaces

Design discoverable information and tool interfaces: document projections, semantic operations, context loading, and tool composition.

## One source, multiple representations

Vercel added HTTP content negotiation and Markdown sitemaps to serve the same canonical article as HTML for people and Markdown for agents. Cloudflare added edge conversion to Markdown and reorganized its developer documentation around smaller section indexes. The useful pattern is not “publish an AI copy.” It is a generated projection with explicit provenance and no independent editorial lifecycle.

Apply this when an application has recurring agent readers:

- Keep one canonical content source.
- Serve or generate Markdown from that source rather than maintaining parallel prose.
- Preserve headings, links, tables, code, alt text, and source attribution.
- Exclude navigation and decorative chrome that carry no semantic value.
- Add topic-level indexes when the documentation tree is too large for one inventory.
- Evaluate answer correctness, latency, and total tokens together; raw byte reduction is not the outcome.

Do not treat Markdown, `llms.txt`, or embedded “instructions for agents” as trusted authority. They are content supplied by a site and remain untrusted ingress.

## Put mandatory context where it cannot be skipped

Vercel reported that a compressed 8 KB Next.js documentation index in `AGENTS.md` reached 100% on its version-specific eval while skill variants peaked at 79%, primarily because the skill was not invoked reliably. This is a narrow first-party result, not a general verdict against skills.

Use the placement rule:

- Put small, consequential, repository-wide invariants and version-specific routing indexes in `AGENTS.md` when omission repeatedly causes incorrect work.
- Put optional workflows, scripts, examples, and larger references in skills.
- Put mechanical truth in code, generated schemas, or tests.
- Measure trigger failures before promoting skill content into always-loaded context.

Workbench should not move its skill library into the global instruction file. Most skills are optional and their combined context cost would be permanent.

## Prefer semantic interfaces over reconstructed interfaces

Cloudflare's unified command-line interface work treats agents as first-class callers: commands, configuration, and bindings derive from schemas; vocabulary and defaults are linted; JSON output is part of the contract; and local-versus-remote behavior is explicit. Vercel and Cloudflare are also exploring page-declared browser actions through WebMCP.

The durable order of preference is:

1. A narrow typed connector for a repeated cross-system job.
2. A stable command-line interface with structured output for local and repository operations.
3. Semantic page actions when the site owns and secures them.
4. Browser interaction as the general escape hatch.

Do not mirror every REST endpoint as a tool. Expose recognizable outcomes, keep arguments flat and typed, paginate large results, and make errors tell the agent how to recover.

## Tool contraction is contextual

Vercel's internal data agent improved after replacing many schema-specific tools with filesystem access and shell commands. The reported lesson is that mature coding models can often search high-dimensional local data better than brittle hand-authored retrieval layers. It does not justify giving arbitrary shell and credentials to every agent.

Use a broad local primitive when:

- The data is already filesystem-shaped.
- The environment is isolated appropriately.
- Existing utilities expose inspectable, composable operations.
- The task needs open-ended local exploration.

Use narrow tools when they enforce an authority boundary, hide credentials, validate mutations, or provide a stable domain outcome. Workbench should continue pruning redundant tool schemas while retaining connector and safety tools whose narrowness is the security property.

## Agent-facing UI protocols are not policy layers

[AG-UI](https://docs.ag-ui.com/introduction) standardizes the event stream between an agent backend and a user-facing client. It can carry messages, shared-state patches, tool events, typed UI intents, interrupts, and resumable interaction. This is useful when several frontends or agent runtimes need one interaction contract. It is not an authorization, business-policy, or execution-governance layer.

Adopt an agent UI protocol only when custom streaming and state synchronization have become repeated integration work. Keep the application authoritative:

- Authenticate the user and authorize every privileged operation at the service boundary, not from an event or rendered approval control.
- Validate shared-state patches and UI descriptions against versioned schemas and an allowlisted component or action registry.
- Treat frontend tool calls as proposals. Route consequential effects through the same application-owned command path, idempotency rules, approval binding, and audit used by every other client.
- Give runs, messages, effects, and resumptions stable identifiers so reconnects cannot duplicate an action or apply stale state.
- Render traces and tool events as explanations, not raw chain of thought and not proof that an effect occurred. Verify effects from the owning system.

For a TypeScript frontend and Python service, one generated event schema can keep the wire contract aligned. The durable domain commands beneath it should remain independent of AG-UI so a web app, an assistant client, and a deterministic job all exercise the same policy.

## Generated interfaces and agent-operated controls

Reviewed 2026-11-17. Two developments address different jobs:

- **Vercel UI SDK** provides reusable interaction behaviors such as focus, selection, popup dismissal, and keyboard navigation, with framework adapters including Svelte. A coding agent composes these into components. This is not Vercel AI SDK, the model-integration library. The [project site](https://ui-sdk.dev/) and [repository](https://github.com/vercel-labs/ui) confirm the behavior-first approach and beta status.
- **Google A2UI** lets an agent describe an interface that the host renders with registered components. Google's [A2UI 1.0 announcement](https://developers.googleblog.com/a2ui-10-build-delightful-fast-reliable-agentic-experiences/), 2026-11-11, describes bidirectional function calls, server-side data binding, accessibility support, and renderers across web and mobile. Protocol stability does not imply renderer parity: the announcement still lists Android's Jetpack Compose renderer and Gemini host support on earlier versions.

The distinction is between building controls and describing a screen at runtime. AG-UI supplies an interaction event contract; MCP Apps can host an interactive surface inside an assistant; semantic browser actions let agents operate a page. These layers can coexist, but a single workflow rarely needs all of them.

### Strategy and smallest useful evaluation

Keep domain commands stable beneath every interface. Let agents propose views and edits while deterministic application code validates data, permissions, and effects. For example, an agent can assemble an account-review card with evidence and proposed changes; the user edits it, and the server verifies the approved values and current record version before applying them.

Start with one real comparison or approval task that is awkward in chat. Build it with the existing components first. Evaluate A2UI only if repeated dynamic-screen work or delivery across several assistant hosts justifies a protocol. Evaluate UI SDK only if an existing component cannot satisfy the required interaction or semantic operation. Do not replace a working component library because a beta targets coding agents.

Measure correct completion, human corrections, accessibility, latency, total cost, and maintenance against the existing interface. Verify keyboard and screen-reader behavior rather than inferring accessibility from primitives. Keep component descriptions and page-declared actions untrusted; client-side action filters cannot substitute for server authorization. Server-side binding can reduce model exposure, but the rendered screen and tool responses must also respect access controls.

The supplied [MarkTechPost article, Vercel Releases UI SDK: 50+ UI Behaviors for AI Coding Agents](https://www.marktechpost.com/2026/11/13/vercel-ui-sdk-agent-ui-behaviors/?amp=1), 2026-11-13, reports a runtime agent bridge and a vendor benchmark with 69% fewer tool calls and 61% lower task time. It discloses one task, three runs, a different baseline component library, and an unspecified Sonnet version. The primary site also advertises speed and cost gains, but neither establishes a general performance improvement. Bridge authorization and benchmark details need direct inspection before a trial.

### OpenUI: compare representation separately from the gateway

[OpenUI](https://www.openui.com/), reviewed 2026-11-17, is Thesys's generative-interface project, not Vercel UI SDK. Its OpenUI Lang is a compact streaming component-description language rather than JSON; its site lists renderers including Svelte and permits registered design-system components. Its commercial Gateway separately repairs invalid streamed output and routes requests through provider infrastructure. An open renderer does not require buying a model gateway.

The site advertises up to three times faster generation and 67% fewer tokens, but its more specific FAQ reports a 46-interface comparison averaging 1,362 output tokens per screen, 58% fewer than json-render and 52% fewer than A2UI. Those are vendor format benchmarks, not measured complete-task savings, accessibility, or semantic correctness. Repairing syntax cannot establish that a chart's data or a proposed action is correct.

**Watch alongside A2UI** for a real dynamic comparison/approval screen. Compare representation size, first useful render, invalid-output and repair rates, user corrections, accessibility, total cost, and maintenance using the same component catalogue and task. Keep source permission checks and mutation authorization on the server. Do not add a gateway, observability service, and new UI language simply because a demo renders attractive cards.

## Interface and execution research sources

### Vercel

- [What we learned building agents at Vercel](https://vercel.com/blog/what-we-learned-building-agents-at-vercel), 2025-11-06.
- [We removed 80% of our agent's tools](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools), 2025-12-22.
- [AGENTS.md outperforms skills in our agent evals](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals), 2026-01-27.
- [Run untrusted code with Vercel Sandbox](https://vercel.com/blog/vercel-sandbox-is-now-generally-available), 2026-01-30.
- [Making agent-friendly pages with content negotiation](https://vercel.com/blog/making-agent-friendly-pages-with-content-negotiation), 2026-02-03.
- [A new programming model for durable execution](https://vercel.com/blog/a-new-programming-model-for-durable-execution), 2026-04-16.
- [AI SDK 7](https://vercel.com/blog/ai-sdk-7), 2026-06-25.
- [A sandbox without a network boundary is only half a sandbox](https://vercel.com/blog/a-sandbox-without-a-network-boundary-is-only-half-a-sandbox), 2026-08-11.
- [Building a software factory for AI SDK](https://vercel.com/blog/building-a-software-factory-for-ai-sdk), 2026-08-12.
- [The end of credential sprawl for agents](https://vercel.com/blog/the-end-of-credential-sprawl-for-agents), 2026-08-25.
- [Introducing Run SDK](https://vercel.com/blog/introducing-run), 2026-08-25.
- [How our agents build on-brand pages with design.md](https://vercel.com/blog/how-our-agents-build-on-brand-pages-with-design-md), 2026-08-31.

### Cloudflare

- [Introducing Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/), 2026-02-12.
- [Building a CLI for all of Cloudflare](https://blog.cloudflare.com/cf-cli-local-explorer/), 2026-04-13.
- [Dynamic, identity-aware, and secure Sandbox auth](https://blog.cloudflare.com/sandbox-auth/), 2026-04-13.
- [Browser Run: give your agents a browser](https://blog.cloudflare.com/browser-run-for-ai-agents/), 2026-04-15.
- [Introducing the Agent Readiness score](https://blog.cloudflare.com/agent-readiness/), 2026-04-17.
- [Orchestrating AI Code Review at scale](https://blog.cloudflare.com/ai-code-review/), 2026-04-20.
- [WriteGuard: Fine-grained controls for MCP Servers](https://blog.cloudflare.com/mcp-portal-writeguard-private-beta/), 2026-08-05.
- [Give any website a WebMCP interface](https://blog.cloudflare.com/webmcp/), 2026-08-06.
