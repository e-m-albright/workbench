# Developer Tool Ownership Landscape

Developer tooling is consolidating into vertically integrated platforms that want to own the path from writing code through review, deployment, observability, model evaluation, and production infrastructure.

**Snapshot:** September 2, 2026. “Owned” means a completed acquisition. An announced agreement, team hire, license, investment, sponsorship, and open-source stewardship are different relationships even when they create effective influence. Product roles and selection guidance for the most contested web stack live in the [Vercel and Cloudflare stack watch](../stacks/vercel-cloudflare.md).

## Practical posture

- Do not abandon a good tool merely because its parent changed. Evaluate behavior, governance, release quality, telemetry, pricing, portability, and export.
- Continue using Astral's **uv** and **Ruff**. Pin versions, retain reproducible configuration, and watch whether OpenAI changes governance or ties them to Codex. A speculative migration would cost more than it protects today.
- Explore **Promptfoo** as a portable evaluation and adversarial-testing layer, but confirm that non-OpenAI models remain first-class after the proposed acquisition.
- Treat common ownership across editor, agent, review, deployment, and telemetry as correlated risk.
- An open-source license preserves fork rights. It does not guarantee neutral staffing, governance, defaults, hosting, or roadmap priorities.

## Control map

| Parent | Developer estate | Read |
|---|---|---|
| **Microsoft** | GitHub, npm, Copilot, Actions, Codespaces, Visual Studio, Visual Studio Code, TypeScript, .NET, Azure | The deepest established vertical stack: language, editor, packages, source, review, continuous integration, security, agent, and cloud. |
| **Stripe** | Payments and billing platform; agreement to acquire **OpenRouter** announced 2026-08-19 | Stripe is joining payment optimization with model and token routing. Treat OpenRouter as transaction-pending rather than independently owned or already Stripe-owned. |
| **SpaceX** | **Cursor / Anysphere**, acquired August 14, 2026; Cursor previously added Supermaven, Graphite, and other coding or review capabilities | Cursor is no longer a top-level independent owner. Treat Cursor and its subsidiaries as part of the wider SpaceX control group. |
| **Anthropic** | Claude Code, Bun, Vercept, Stainless, Claude models and application programming interface | Coding agent plus JavaScript runtime, computer use, software development kit generation, and Model Context Protocol tooling. |
| **OpenAI** | Codex, Rockset, Statsig, and proposed acquisitions of Promptfoo, Astral, and Ona | Coding agent plus retrieval, experimentation, AI security, Python tooling, and persistent agent environments. |
| **Cloudflare** | Workers platform, PartyKit, Baselime, Replicate, VoidZero, and Human Native | Edge compute plus JavaScript tooling, observability, stateful applications, and AI model execution. |
| **Vercel** | Next.js, Turborepo, NuxtLabs, Grep, Tremor, Splitbee, v0, AI SDK, AI Gateway, Workflow, and platform infrastructure; employs Svelte creator Rich Harris | Owns or strongly influences much of the preferred web-development path from framework to deployment and durable agents. |
| **CoreWeave** | Graphics-processing-unit cloud and Weights & Biases | Infrastructure moved upward into experiment tracking, evaluation, and model operations. |
| **Cognition** | Devin and Windsurf product assets after the Windsurf transaction | Autonomous coding agent plus integrated development environment. Windsurf's earlier Google license and leadership move complicate the lineage. |
| **Atlassian** | Jira, Confluence, Bitbucket, Compass, Loom, DX, and The Browser Company transactions | Planning and collaboration are converging with engineering intelligence and agent-oriented browsing. |
| **IBM** | Red Hat, OpenShift, Ansible, and HashiCorp's Terraform, Vault, Consul, and Nomad | Linux, hybrid cloud, infrastructure as code, secrets, and scheduling under one parent. |
| **Cisco** | Splunk and Isovalent, including Cilium and Tetragon stewardship | Networking, security, observability, and cloud-native networking. |
| **Databricks** | MosaicML, Tabular, Neon, and the lakehouse platform | Model training, table formats, databases, and data infrastructure. |
| **NVIDIA** | CUDA, networking, Run:ai, Bright Computing, Excelero, Deci, Brev.dev, Shoreline.io, OctoAI assets, the reported Gretel transaction, and related investments | More acquisitive than it first appears, but focused on making accelerated computing easier to consume rather than owning every application. |
| **Google / Alphabet** | Android Studio, Go, Dart, Flutter, Angular, Bazel, TensorFlow, JAX, Kubernetes lineage, Firebase, Cloud Run, Colab, Kaggle, Gemini Code Assist, Jules, and Firebase Studio | Google mostly builds and distributes developer infrastructure directly. Its recent Windsurf move used licensing and hiring rather than buying the surviving product. |
| **Datadog** | Application and infrastructure observability, Metaplane, Eppo | Operational telemetry expanded into data quality and product experimentation. |
| **Hugging Face** | Hub, models, datasets, Spaces, inference, and XetHub storage | Model distribution plus the storage substrate beneath it. |
| **Docker** | Docker Desktop, Hub, Compose, Build Cloud, Testcontainers, model tooling, and agent sandboxes | The local container boundary is becoming an agent execution and governance surface. |
| **GitLab** | Source, review, continuous integration, security, planning, registry, deployment controls, and Duo agents | The notable integrated alternative built mainly as one product rather than assembled in the current acquisition wave. |

## Cursor is now under SpaceX

The earlier map was wrong. SpaceX and Anysphere entered a merger agreement on June 16, 2026, and SpaceX's August 14, 2026 filing reports completion. Cursor should therefore be represented as:

```text
SpaceX
└── Cursor / Anysphere
    ├── Cursor editor and agents
    ├── Supermaven capabilities
    └── Graphite review workflow
```

That changes the risk model. Cursor is now attached to a much larger private industrial and AI group rather than financed as an independent developer-tool company. The immediate product may remain excellent; the strategic dependency, governance, and data boundary are different.

Sources: [SpaceX acquisition filing](https://app.edgar.tools/filing/1181412/0001628280-26-056945) and [Reuters deal report](https://www.reuters.com/legal/transactional/spacex-buy-anysphere-60-billion-2026-06-16/).

## Stripe and OpenRouter

Stripe [agreed to acquire OpenRouter on 2026-08-19](https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter). The announcement described more than 400 models from more than 80 providers and positioned model routing as the cost side of the same economic infrastructure Stripe already supplies for revenue. This is strategically coherent, but the transaction should remain labeled as an agreement until completion is verified.

OpenRouter's value depends on being a credible multi-model neutral layer. Watch whether routing remains driven by user-selected price, performance, availability, and data policies rather than Stripe bundling; whether non-Stripe billing remains practical; and whether all model traffic becomes part of a broader financial and application telemetry profile. The direct comparison with Vercel and Cloudflare is maintained in the [stack watch](../stacks/vercel-cloudflare.md#model-gateways-vercel-cloudflare-and-openrouter).

## Vercel

### What Vercel effectively controls

Vercel does not legally own every open-source project associated with it. It does own the commercial platform, created and stewards Next.js, acquired several tool companies, and employs influential maintainers.

Rich Harris, Svelte's creator, [joined Vercel in 2021](https://vercel.com/blog/vercel-welcomes-rich-harris-creator-of-svelte) to work on Svelte full time. Vercel's announcement says Svelte remains independently governed. Formally, that is not ownership. Practically, employing the principal author creates substantial influence and deserves an **effective-control** marker in this map.

The creator known as **shadcn** also [identifies himself as a design engineer on Vercel's AI team](https://shadcn.com/), created shadcn/ui and its registry, and co-created v0. Vercel does not thereby own every copy of shadcn/ui code, but it employs the principal creator and connects the project, registry, and v0 through one team. Mark shadcn/ui as Vercel-influenced.

NuxtLabs [joined Vercel in 2025](https://vercel.com/blog/nuxtlabs-joins-vercel). Nuxt and Nitro were promised continued MIT licensing, public roadmaps, and independent governance. Again, legal portability and practical sponsor influence coexist.

### Toolset and use of each part

| Tool or platform | Use |
|---|---|
| **Next.js** | Full-stack React framework. Handles routing, rendering, server functions, caching, image optimization, and application structure. Vercel is its native commercial deployment platform. |
| **Svelte and SvelteKit influence** | Svelte is a compiler-based user-interface framework; SvelteKit is its application framework. Vercel employs Rich Harris but does not formally own the projects. |
| **shadcn/ui and registry** | Copy-owned React components and code distribution. Vercel employs shadcn on its AI team; he also co-created v0. This is effective influence, not simple ownership of downstream component copies. |
| **Nuxt and Nitro** | Nuxt is the full-stack Vue framework. Nitro is its portable server runtime and also supports other frameworks. NuxtLabs is part of Vercel. |
| **Turborepo** | Monorepo task runner, dependency graph, incremental builds, and local or remote build caching. Useful when several packages or applications share one repository. |
| **Vercel platform** | Git-triggered builds, preview deployments, production deployment, content delivery network, domains, functions, firewall, logs, analytics, and observability. Its core advantage is reducing web deployment operations. |
| **Vercel Functions and Fluid compute** | Run server-side functions without managing servers. Fluid compute pools work more efficiently than a simple one-request-per-instance model and targets bursty web and AI workloads. |
| **v0** | Generates and iterates on user interfaces and applications from natural-language or visual input. It is an authoring and prototyping surface that feeds Vercel deployment. |
| **AI SDK** | Open-source TypeScript toolkit for model calls, streaming user interfaces, tool calling, structured output, and agents across React, Next.js, Vue, Svelte, and Node.js. It reduces direct dependence on any one model application programming interface. |
| **AI Gateway** | One endpoint for many model providers with routing, retries, budgets, usage monitoring, and bring-your-own-key support. It centralizes model procurement and telemetry. |
| **Workflow Development Kit and Vercel Workflows** | Durable functions that pause, retry, persist progress, and survive process restarts. This occupies the Temporal, Inngest, and Trigger.dev category. The programming model is open source; the managed control plane is Vercel. |
| **eve** | Filesystem-first framework for durable backend AI agents, connected to Workflow, Sandbox, and model routing. |
| **Sandbox** | Ephemeral isolated compute for running generated or untrusted code. Important for coding agents and evaluation. |
| **Grep** | Public code search across repositories. Useful for finding implementation examples and supplying code context to AI systems. |
| **Tremor** | React dashboard and chart components. Useful directly and as component material for v0. |
| **Splitbee lineage** | Product and web analytics capabilities integrated into Vercel Analytics. |
| **Observability, Web Analytics, and Speed Insights** | Runtime logs, traces, traffic, product usage, and real-user performance. This closes the feedback loop after deployment. |

### Read

Vercel is assembling the most opinionated **web application factory**: framework and components, generated interface, build graph, preview, production runtime, model access, durable work, and feedback. The experience can be exceptionally coherent. The corresponding risk is architectural gravity: each individually portable abstraction works best when the next layer is also Vercel.

Use Vercel when that coherence materially speeds a web product. Keep the repository, data, model interface, and workflow state exportable, and periodically prove that the application can run somewhere else.

References: [Vercel documentation](https://vercel.com/docs), [AI SDK](https://vercel.com/docs/ai-sdk), [AI Gateway](https://vercel.com/docs/ai-gateway), and [Vercel Workflows](https://vercel.com/docs/workflows).

## Cloudflare

### Toolset and use of each part

| Tool or platform | Use |
|---|---|
| **Workers** | Globally distributed serverless JavaScript, TypeScript, Python, Rust-generated WebAssembly, and other web workloads. Best for latency-sensitive services close to users. |
| **Containers** | Container workloads integrated with Cloudflare's network for software that does not fit the Workers runtime. |
| **Durable Objects** | Stateful, uniquely addressed compute units for coordination, real-time applications, rooms, sessions, and agent state. |
| **Queues and Workflows** | Asynchronous messaging and durable multi-step execution. Workflows compete with other orchestration products while remaining integrated with Workers. |
| **R2** | Object storage with a strong egress-cost pitch and S3-compatible interfaces. |
| **D1** | Managed SQLite-oriented database for Workers applications. |
| **KV** | Globally distributed key-value data optimized for read-heavy configuration and cached state. |
| **Hyperdrive** | Connection pooling and acceleration between Workers and existing databases. |
| **Workers AI** | Hosted model inference on Cloudflare infrastructure. |
| **AI Gateway** | Model request routing, observability, caching, rate limits, and controls across providers. |
| **Agents and Vectorize** | Agent runtime patterns and vector storage for retrieval and stateful AI applications. |
| **Replicate** | Catalog and execution platform for open and custom AI models. It expands Cloudflare beyond its original Workers AI catalog. |
| **PartyKit** | Framework for multiplayer, collaborative, and real-time applications, built around Durable Objects. |
| **Baselime** | Serverless observability and OpenTelemetry-oriented debugging. |
| **VoidZero** | Company and team behind the modern JavaScript toolchain described below. |
| **Network, security, domains, and content delivery** | Domain name system, content delivery network, traffic filtering, zero-trust access, bot controls, and application protection. This is Cloudflare's durable distribution advantage. |

### VoidZero and the JavaScript toolchain

Cloudflare [acquired VoidZero in June 2026](https://cloudflare.net/news/news-details/2026/Cloudflare-Acquires-VoidZero-to-Build-the-Future-of-the-AI-Native-Web/default.aspx). The projects remain open source and MIT-licensed.

| VoidZero tool | Use |
|---|---|
| **Vite** | Development server and front-end build entrypoint. |
| **Vitest** | Vite-aware unit test runner with Jest-style ergonomics. |
| **Rolldown** | Rust-based Rollup-compatible bundler and Vite's production bundling foundation. |
| **Oxc** | Rust-based JavaScript and TypeScript parser, resolver, transformer, minifier, linter, and formatter foundation. |
| **Oxlint** | Fast JavaScript and TypeScript linter built on Oxc. |
| **Oxfmt** | Fast formatter intended to cover the Prettier role. |
| **Vite+** | Unified command surface combining runtime and package management with Vite, Vitest, Rolldown, tsdown, Oxlint, Oxfmt, type checking, and task running. |

### Read

Cloudflare is assembling a more infrastructural **web and agent operating layer**. Vercel begins with the application framework and developer experience; Cloudflare begins with the network, security boundary, globally distributed runtime, storage, and state. VoidZero lets Cloudflare move upstream into the local toolchain.

Cloudflare is the more attractive strategic substrate when portability, global primitives, protocol-level infrastructure, and avoiding framework lock-in matter. Vercel is usually more cohesive when the product is a conventional web application and the team wants one polished golden path.

Reference: [Cloudflare developer platform](https://developers.cloudflare.com/).

## Oxlint versus Biome

Yes, **Oxlint is part of the VoidZero family**. More precisely, Oxlint is built on Oxc, and Oxc, Oxlint, Oxfmt, Vite, Vitest, Rolldown, and Vite+ are stewarded by VoidZero under Cloudflare.

| Dimension | Oxlint | Biome |
|---|---|---|
| Primary job | Linter | Integrated formatter and linter, with parser and related tooling |
| Implementation | Rust through Oxc | Rust |
| Migration target | Primarily ESLint | Primarily ESLint plus Prettier |
| ESLint compatibility | Strong emphasis on familiar rules and running ESLint-compatible plugins | Reimplements supported rules; it is not a general ESLint plugin host |
| Type-aware linting | Uses TypeScript tooling and Oxc infrastructure for typed rules | Supports type-informed capabilities but has historically emphasized self-contained analysis |
| Formatting | Separate **Oxfmt** tool; Vite+ bundles both | Formatter is a first-class part of the same `biome` command and configuration |
| Language breadth | Focused on JavaScript and TypeScript tooling | JavaScript, TypeScript, JSX, JSON, CSS, GraphQL, and additional supported web formats, with maturity varying by language |
| Governance | VoidZero, now Cloudflare | Community project driven primarily by volunteers; Vercel has funded specific type-inference work but does not own it |
| Best fit | A repository that wants maximum lint speed, close ESLint migration, plugin compatibility, or the Vite+/Oxc stack | A repository that wants one independent formatter-and-linter replacement with a single configuration and broad web-file coverage |

**Current preference:** keep Biome where its formatter and linter already provide adequate coverage. Evaluate Oxlint when ESLint compatibility, typed lint performance, or Vite+ integration solves a measured problem. Do not switch merely because Oxlint is newer or faster. If Oxfmt and Oxlint together become materially more compatible than Biome without adding configuration complexity, reassess.

References: [Oxlint documentation](https://oxc.rs/docs/guide/usage/linter.html), [Biome formatter](https://biomejs.dev/formatter/), and [Biome linter](https://biomejs.dev/linter/).

## Why NVIDIA has not acquired everything

The premise is partly wrong: NVIDIA has bought many targeted complements. Recent moves include Run:ai for graphics-processing-unit scheduling, Bright Computing for cluster management, Excelero for storage, Deci for inference optimization, Brev.dev for development environments, Shoreline.io for cloud operations, and OctoAI assets for model serving. Reporting also described a Gretel transaction for synthetic data, but NVIDIA did not provide the same clear first-party announcement used for Run:ai, so treat that item as reported rather than independently confirmed here. Mellanox remains the major earlier acquisition that gave NVIDIA networking as well as compute.

NVIDIA nevertheless has reasons not to own the whole developer stack:

1. **Neutrality sells chips.** NVIDIA benefits when every cloud, model laboratory, framework, and application standardizes on CUDA and its hardware. Competing with all of those customers at the application layer could weaken that position.
2. **The bottleneck is already valuable.** Control of accelerators, CUDA, networking, and optimized libraries captures enormous value without the lower margins and support burden of every end-user product.
3. **Investment and integration can be cheaper than ownership.** Capital, engineering support, preferred access, and software certification can align a company without integrating it.
4. **Acquisitions invite regulatory and channel conflict.** NVIDIA already faces competition, export-control, and antitrust scrutiny. Buying major model or cloud platforms would intensify it.
5. **Application markets turn quickly.** NVIDIA prefers capabilities that increase graphics-processing-unit utilization across many winners: scheduling, networking, inference, synthetic data, and cluster operations.

The useful model is not “NVIDIA is strangely inactive.” It is “NVIDIA acquires bottleneck-adjacent infrastructure and invests broadly so that many application winners increase NVIDIA demand.”

Reference: [NVIDIA's Run:ai announcement](https://blogs.nvidia.com/blog/runai/).

## Where Google fits

Google is a major developer-tool owner, but much of the estate was built internally or acquired earlier rather than assembled in the latest visible wave.

### Existing control points

- **Languages and frameworks:** Go, Dart, Flutter, Angular.
- **Machine learning:** TensorFlow, JAX, Colab, Kaggle, Vertex AI, and Gemini application programming interfaces.
- **Build and infrastructure:** Bazel, Kubernetes lineage, Cloud Run, Google Kubernetes Engine, Cloud Build, Artifact Registry, and Cloud Workstations.
- **Application development:** Firebase, Android Studio, Firebase Studio, Gemini Code Assist, and Jules.
- **Cloud data and operations:** BigQuery, Spanner, AlloyDB, Looker, Apigee, and cloud observability and security products.

### Why the acquisition list looks quieter

1. Google already owns operating systems, browsers, cloud infrastructure, model infrastructure, languages, frameworks, and global distribution. It can build a tool and place it in Android Studio, Chrome, Firebase, Google Cloud, or Gemini without buying an audience.
2. Recent deals often use **nonexclusive technology licenses plus team hiring** rather than full acquisition. Windsurf is the important example: Google hired key leaders and licensed technology, while Cognition acquired the surviving Windsurf product and business.
3. Alphabet faces intense antitrust scrutiny, making large horizontal developer-platform acquisitions harder.
4. Google's recurring weakness is not lack of assets. It is product coherence and sustained commitment across overlapping assets.

### Current read

Google may be the most undercounted developer platform because no single product presents the whole estate. Microsoft has GitHub, Vercel has a coherent web factory, and Cloudflare has a coherent network platform. Google's tools are distributed across Android, Firebase, Google Cloud, DeepMind, and open-source projects.

The key watch item is whether Gemini Code Assist, Jules, Firebase Studio, Vertex AI, and Google's cloud runtime become one understandable agent-development path. If they do, Google does not need many acquisitions. If they remain fragmented, licensing talent from companies such as Windsurf will not solve the product problem.

## Ownership and influence labels

Use these distinctions when maintaining the landscape:

1. **Completed acquisition:** the parent owns the company or assets.
2. **Definitive agreement:** intent is announced, but closing may remain conditional.
3. **License and team hire:** the buyer receives technology rights and people, but may not own the product.
4. **Employment and sponsorship:** practical influence without project ownership.
5. **Open-source stewardship:** maintainers and roadmap influence can move even when the license and fork rights remain unchanged.

Vercel and Svelte demonstrate why the fourth category matters. SpaceX and Cursor demonstrate why the first category must update the top-level map.

## Watch list

1. Keep using uv and Ruff; monitor Astral's governance under OpenAI rather than reacting preemptively.
2. Run a bounded Promptfoo evaluation trial after its OpenAI transaction status and model neutrality become clear.
3. Watch whether SpaceX changes Cursor's product direction, data practices, model procurement, or enterprise posture.
4. Watch whether Cloudflare's ownership changes Vite, Vitest, Oxlint, Oxfmt, or Vite+ defaults toward Workers.
5. Watch whether Vercel Workflows remains operationally portable beyond its open-source programming model.
6. Watch whether Svelte and Nuxt governance remain meaningfully independent despite maintainer employment and company ownership.
7. Watch whether Weights & Biases preserves cross-cloud neutrality under CoreWeave.
8. Watch whether Google turns its scattered developer estate into one coherent Gemini-centered platform.
9. Watch whether OpenRouter preserves broad provider neutrality, data-policy routing, and deployment independence if Stripe's acquisition closes.

## Caveats

Company announcements emphasize user benefit and may omit staff departures, integration failures, commercial tension, or changed roadmaps. A signed transaction may not have closed. Open source reduces some exit risk but does not remove data, trademark, governance, or hosted-service dependence. The relevant question is not only who owns a tool, but which technical, economic, data, and governance exits remain available.
