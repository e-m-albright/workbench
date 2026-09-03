# Vercel and Cloudflare Stack Watch

**Status:** Watch and selection reference. Neither vendor is a default suite to adopt wholesale.

**Last surveyed:** 2026-09-02. Recheck before a platform commitment or when a watched product reaches stability.

Vercel and Cloudflare are converging on the same prize from opposite directions. Vercel begins with frameworks, application authoring, and deployment experience. Cloudflare begins with the network, security boundary, globally distributed compute, and storage. Both now offer model gateways, durable execution, agent runtimes, observability, and increasingly complete local toolchains.

Ownership and effective-control relationships are maintained in [Developer Tool Ownership](../knowledge/developer-tool-ownership.md). This page owns selection guidance and product roles.

## Current posture

- Prefer **SvelteKit**, portable data stores, and explicit service boundaries over adopting either vendor as an inseparable suite.
- Prefer **Cloudflare** for edge-native workloads, global network primitives, low-egress object storage, stateful coordination, and portable infrastructure.
- Prefer **Vercel** when polished preview deployments, Next.js-native behavior, generative interface tooling, or its integrated AI application path creates measurable leverage.
- Adopt individual open-source tools on merit. Common ownership does not turn Vite, Vitest, SvelteKit, Nuxt, AI SDK, or Turborepo into a package deal.
- Test an exit path before relying on proprietary workflow state, observability history, model routing, or platform-specific caching.

## Vercel stack

| Category | Product | Use | Posture |
|---|---|---|---|
| Framework | **Next.js** | Full-stack React framework with routing, rendering, server functions, caching, and image handling. | Avoid by default because React and Vercel coupling add complexity. Use when its ecosystem is decisive. |
| Framework influence | **Svelte / SvelteKit** | Compiler-based user interfaces and the preferred full-stack web framework. | Adopted independently of Vercel. Creator Rich Harris works at Vercel, giving Vercel effective influence rather than legal ownership. |
| Framework company | **Nuxt / Nitro** | Full-stack Vue framework and portable server runtime. | NuxtLabs is part of Vercel; projects remain open source. Use only for an inherited or Vue-centered project. |
| Build | **Turborepo** | Monorepo task graph, incremental builds, and local or remote cache. | Conditional Phase 3 pick when a real monorepo needs it. Vercel-owned. |
| Components | **shadcn/ui and registry** | Copy-owned React components and a registry for distributing component source. | shadcn works on Vercel's AI team and co-created v0. Use the Svelte port for the current stack; mark the original project as effectively Vercel-influenced. |
| Components | **Tremor** | React dashboard and chart components. | Vercel-owned. Reference for dashboards; React-specific. |
| Authoring | **v0** | Natural-language and visual generation of interfaces and applications. | Strong prototype and React/Vercel authoring surface. Evaluate against design-first alternatives rather than treating generated output as architecture. |
| Model library | **AI SDK** | Provider-normalized model calls, streaming, structured output, tools, agent loops, user-interface hooks, and coding-harness adapters. | Default TypeScript model interface today. Works outside Vercel; ownership still creates ecosystem gravity. |
| Model gateway | **AI Gateway** | Unified hosted endpoint for model providers, retries, fallback, budgets, usage, and bring-your-own-key routing. | Strong when already on Vercel or AI SDK. Compare with OpenRouter and a self-hosted LiteLLM gateway before centralizing traffic. |
| Agent framework | **eve** | Filesystem-first durable backend agents. | Watch until a production agent needs its integrated Vercel runtime. |
| Durable execution | **Workflow Development Kit / Vercel Workflows** | Pause, retry, and resume TypeScript, JavaScript, and Python workflows. | Watch as a managed Temporal, DBOS, Inngest, or Trigger.dev competitor. Programming model is open; managed state is Vercel. |
| Isolated execution | **Sandbox** | Ephemeral compute for generated or untrusted code. | Evaluate for production agent execution when local containers are insufficient. |
| Compute | **Functions / Fluid compute** | Managed server-side execution for web and AI workloads. | Good application convenience; benchmark cost and runtime limits before scale. |
| Deployment | **Git deployments and previews** | Build every change and create reviewable preview environments. | Vercel's clearest durable advantage. Other hosts now imitate it. |
| Delivery | **Edge Network / content delivery network / domains** | Route, cache, secure, and serve applications globally. | Useful but not a reason alone to accept framework coupling. |
| Data | **Blob / Edge Config and marketplace integrations** | Object storage, globally read configuration, and connections to outside databases. | Use only when the application already accepts Vercel operational dependence. Prefer portable primary data stores. |
| Messaging | **Queues and Cron** | Delayed, asynchronous, and scheduled work. | Use for simple Vercel-local jobs; use the broader workflow decision table for durable work. |
| Feedback | **Observability, Web Analytics, Speed Insights** | Logs, traces, traffic, product usage, and real-user performance. | Convenient closed loop; preserve OpenTelemetry and export paths where possible. |
| Search | **Grep** | Search public code for examples and context. | Vercel-owned input to its coding and generation stack. Useful independently. |
| Analytics lineage | **Splitbee** | Product analytics capabilities folded into Vercel Analytics. | Ownership context, not a separate recommendation. |

## Cloudflare stack

| Category | Product | Use | Posture |
|---|---|---|---|
| Compute | **Workers** | Globally distributed serverless applications and application programming interfaces. | Preferred edge compute option. Avoid forcing long-running or memory-heavy work into it. |
| Compute | **Containers** | Container workloads integrated with Cloudflare's network. | Watch as the escape hatch for software that does not fit Workers. |
| Static and web | **Pages / Workers Builds** | Build and deploy web applications and static assets. | Strong SvelteKit and Astro deployment target; verify current adapter behavior. |
| Stateful compute | **Durable Objects** | Uniquely addressed state and coordination for rooms, sessions, real-time systems, and agents. | Distinctive Cloudflare advantage. Use only when the actor-like model fits. |
| Messaging | **Queues** | Asynchronous delivery and buffering. | Strong for Workers-local jobs. Not equivalent to durable multi-step execution. |
| Durable execution | **Workflows** | Retried and checkpointed multi-step work. | Watch and compare with DBOS, Temporal, Inngest, Trigger.dev, and Vercel Workflows. |
| Object storage | **R2** | S3-compatible objects without the usual egress pricing. | Preferred Cloudflare storage option and a credible general object-store alternative. |
| Relational data | **D1** | Managed SQLite-oriented database near Workers. | Conditional for Cloudflare-native, SQLite-shaped workloads. Prefer PostgreSQL for general systems. |
| Key-value data | **KV** | Globally distributed, read-heavy configuration and cached state. | Use for its consistency model, not as a general database. |
| Existing databases | **Hyperdrive** | Connection pooling and acceleration from Workers to PostgreSQL and compatible databases. | Useful when keeping the primary database portable outside Cloudflare. |
| Vector data | **Vectorize** | Managed vector index for retrieval and agent context. | Watch; avoid adding a dedicated vector store before PostgreSQL or existing search proves inadequate. |
| Analytics data | **Analytics Engine** | High-cardinality event ingestion and queries from Workers. | Platform-specific specialist. Keep canonical business data elsewhere. |
| Hosted inference | **Workers AI** | Run supported models on Cloudflare infrastructure. | Good bursty edge-adjacent inference; catalog breadth and hardware choice are constrained. |
| Model gateway | **Cloudflare AI Gateway** | Provider analytics, logging, caching, rate limits, retry, fallback, and routing. | Strong when applications already use Cloudflare. Compare OpenRouter and Vercel AI Gateway before centralizing model traffic. |
| Model platform | **Replicate** | Run catalog and custom open models. | Cloudflare-owned. Watch whether provider neutrality narrows as Workers AI integration deepens. |
| Agents | **Agents SDK / AI Search** | Stateful agent applications and managed retrieval over data. | Watch for Cloudflare-native products; not a reason to move an ordinary application. |
| Browser execution | **Browser Rendering** | Managed browser automation and page rendering near Workers. | Evaluate for production Cloudflare jobs; local Playwright remains the deterministic default. |
| Real-time | **PartyKit** | Collaborative and multiplayer application framework built around Durable Objects. | Cloudflare-owned specialist for real-time state. |
| Observability | **Baselime and Workers observability** | Logs, traces, and serverless debugging. | Convenient platform integration; preserve OpenTelemetry portability. |
| Developer interface | **Wrangler, workerd, Miniflare** | Deploy Workers, run the runtime, and emulate locally. | Required or useful when choosing Workers, not general replacements for the local language toolchain. |
| JavaScript toolchain | **Vite** | Development server and front-end build entrypoint. | Adopted for Vite frameworks. VoidZero is Cloudflare-owned. |
| Testing | **Vitest** | Vite-aware unit and component tests. | Adopted for Vite applications; pure Deno code keeps native tests. |
| Bundling | **Rolldown** | Rust-based Rollup-compatible bundler and Vite production foundation. | Use transitively through Vite; configure directly only for a demonstrated packaging need. |
| Compiler infrastructure | **Oxc** | JavaScript and TypeScript parser, resolver, transformer, minifier, linter, and formatter foundation. | Usually consumed through higher-level tools. |
| Linting | **Oxlint** | Fast linter with growing typed and ESLint-plugin compatibility. | Explicit watch candidate. Keep Biome today; reassess when rules or migration compatibility solve a real gap. |
| Formatting | **Oxfmt** | Fast Prettier-compatible formatter. | Watch while maturing; does not displace Biome today. |
| Unified toolchain | **Vite+** | Runtime, package, task, build, test, lint, format, and type-check command surface. | Watch while beta. It overlaps Deno, pnpm, Just, Biome, and repository checks. |
| Network and security | **DNS, content delivery, Tunnel, Access, WAF, Turnstile** | Delivery, private ingress, identity-aware access, application filtering, and bot protection. | Cloudflare's strongest cross-project platform layer. Adopt individual primitives when they solve a real boundary. |

## Model gateways: Vercel, Cloudflare, and OpenRouter

| Dimension | Vercel AI Gateway | Cloudflare AI Gateway | OpenRouter |
|---|---|---|---|
| Center of gravity | Vercel applications and AI SDK | Cloudflare applications and network controls | Vendor-neutral hosted model marketplace and router |
| Model breadth | Hundreds of models through one endpoint | Major hosted providers plus Workers AI and Replicate | More than 400 models from more than 80 providers as reported when Stripe announced its deal |
| Routing | Provider preferences, fallback, retries | Dynamic routing, fallback, retry, caching, and rate limits | Deep provider routing by price, speed, availability, context, data policy, and other preferences |
| Application library | Best paired with AI SDK | Provider-compatible application libraries and Workers tooling | Direct application programming interface, client software development kits, and an emerging agent software development kit |
| Portability | Gateway works outside Vercel, but integration is strongest inside its platform | Useful outside Workers, but operational integration is strongest on Cloudflare | Any language through an OpenAI-compatible interface; least tied to a deployment platform |
| Bring your own key | Supported | Supported for provider connections | The service primarily brokers model access; check current provider and enterprise options before assuming the same model |
| Observability | Usage, latency, spend, app attribution | Logs, analytics, token and cost metrics | Usage, provider performance, generation metadata, and routing visibility |
| Data controls | Provider and gateway controls, including documented training restrictions and retention options | Logging and caching require deliberate privacy configuration | Per-provider policy filters and enterprise regional routing; OpenRouter and the selected provider both sit in the data path |
| Ownership | Vercel | Cloudflare | Stripe agreement announced 2026-08-19; do not call completed without newer evidence |

**Current selection:** OpenRouter is the strongest broad hosted aggregator and routing marketplace. Vercel AI Gateway is highly competitive for an application already using AI SDK or Vercel and may produce the shortest integration path. Cloudflare AI Gateway is strongest when caching, rate controls, observability, and Workers integration matter. Use LiteLLM when self-hosting the gateway is worth the operational burden.

Price alone is unlikely to decide between Vercel and OpenRouter because both advertise provider-price pass-through in common paths. The meaningful differences are provider breadth, routing policy, deployment integration, data controls, and who receives all model traffic.

Stripe [agreed to acquire OpenRouter on 2026-08-19](https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter). The combination makes strategic sense: Stripe can optimize both payment revenue and model-token cost. It also means OpenRouter is no longer safely modeled as a durable independent neutral layer until the transaction and future product integration are clear.

## AI SDK: features and competitors

### What AI SDK offers

- One TypeScript interface across many model providers.
- Text generation and streaming.
- Structured object generation and schema validation.
- Tool definitions, typed tool context, tool calling, stopping conditions, and multi-step agent loops.
- Runtime context for state that should not live in prompts.
- Middleware and provider adapters.
- Framework hooks for chat and generative interfaces in React, Svelte, Vue, Angular, and Node-oriented applications.
- Streaming protocols and message models for client-server user interfaces.
- Harness adapters for established coding agents such as Claude Code, Codex, and Pi.
- Optional integration with Vercel AI Gateway, observability, templates, Sandbox, and deployment without requiring those services for the core library.

### Competitor map

| Competitor | Overlap | Read |
|---|---|---|
| **TanStack AI** | Multi-provider TypeScript calls, streaming, tools, agents, and framework hooks | Closest direct library competitor. More explicitly composable, uses the open AG-UI protocol, supports a broad framework matrix, and exposes more first-party persistence and resumability primitives. Younger ecosystem. Its comparison page is naturally written from TanStack's perspective. |
| **LangChain.js / LangGraph.js** | Providers, tools, retrieval, stateful agents, and workflows | Broader orchestration ecosystem and more explicit graphs or durable state. Heavier abstractions and more framework surface than needed for ordinary model-backed interfaces. |
| **Mastra** | TypeScript agents, workflows, memory, evaluation, observability, and deployment | Higher-level agent application framework. It can use or complement AI SDK rather than only replace it. Choose when production agent lifecycle is the problem. |
| **OpenRouter client and Agent SDKs** | Normalized providers and agent loops | Strong when model routing is already centralized through OpenRouter. More gateway-centered and less mature as a cross-framework user-interface layer. |
| **Cloudflare Agents SDK** | Tool loops, stateful agents, model access, and deployment | Compelling for Cloudflare-native agents; less neutral than AI SDK as an application library. |
| **assistant-ui** | Chat and agent user-interface components | Primarily a React interface layer. It commonly runs on top of AI SDK or LangGraph rather than replacing the model and tool layer. |
| **Direct provider software development kits** | Generation, streaming, structured output, and tools | Lowest abstraction and fastest access to provider-specific features, but creates direct model-vendor coupling. |
| **PydanticAI** | Typed providers, tools, agents, evaluation, and observability in Python | The strongest analogous choice for Python rather than a TypeScript competitor. |

**Current selection:** Keep AI SDK as the default TypeScript model interface because streaming user interfaces, Svelte support, provider adapters, tools, and structured output are packaged coherently. Evaluate TanStack AI when open wire protocols, deeper composition, resumability, or non-Vercel neutrality become decisive. Use Mastra or LangGraph only when the application truly needs a larger agent runtime.

## VoidZero migration watch

Biome remains the default formatter and linter for broad JavaScript and TypeScript projects. The VoidZero suite stays visible through explicit promotion triggers:

| Tool | Promotion trigger |
|---|---|
| **Oxlint** | Typed rules or ESLint-plugin compatibility catch important defects Biome cannot, or measured lint latency becomes material. |
| **Oxfmt** | Stable framework-file and Prettier compatibility exceed Biome's coverage without adding a second configuration burden. |
| **Rolldown** | A project needs custom bundler behavior or library packaging beyond Vite's transitive use. |
| **Oxc** | A maintained tool needs parser, transform, resolver, or minifier primitives directly. |
| **Vite+** | It reaches stable release and replaces several existing tools with less configuration while preserving Deno and deployment portability. |
| **Vite Task** | A monorepo requires caching and dependency scheduling beyond Just and native tasks. |

Do not run two permanent formatter or linter stacks merely to keep options open. A migration candidate earns a bounded comparison against real repository fixtures before adoption.

## Reassessment cues

- Before choosing a full-stack host for a new application.
- When Vercel Workflows, Cloudflare Workflows, or Vite+ reaches a materially different stability level.
- When an acquisition changes terms, telemetry, governance, or portability.
- When Biome misses a recurring defect or becomes a measured performance bottleneck.
- When model-gateway spend or reliability is large enough for routing policy to matter.
