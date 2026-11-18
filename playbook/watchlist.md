# Technology watchlist

This queue records unresolved decisions and the event that would make another
review useful. Comparisons, sources, and dated findings live in their subject
pages. A listed product is not an adopted dependency. This is an on-demand queue;
it does not imply a scheduled monitoring service.

## Agents

| Question or candidates | Revisit when | Evidence and comparison |
| --- | --- | --- |
| Docker Agent | Repeated agent setup or distribution work merits comparison with an application-owned framework | [Declarative packaging](agents/frameworks.md#declarative-agent-packaging) |
| gVisor | A Linux execution service needs disposable agent sandboxes or measured density gains; test compatibility, containment, egress, and host resource limits against containers and microVMs | [Application-kernel isolation](agents/security.md#gvisor-linux-application-kernel-isolation) |
| Strands Box and Dogwood | A concrete execution path needs non-bypassable operation-level policy; verify preview compatibility and policy completeness | [Semantic policy](agents/security.md#strands-box-containment-with-semantic-policy) |
| Notion shared context and skill distribution | Multiple assistant hosts need reviewed shared guidance; verify revision delivery, permission behavior, and revocation | [Shared context](agents/memory.md#shared-context-and-portable-skills) |
| Composio, Arcade, Klavis, Metorial | Several assistant clients need the same delegated tool access | [Integrations](agents/integrations.md) |
| Nango, Paragon, Pipedream Connect, Merge | Connection maintenance or source normalization becomes repeated application work | [Integration candidates](agents/integrations.md#enterprise-integration-and-workflow-candidates-reviewed-2026-10-02) |
| Workato, Runlayer, AgentCore | An organization needs centralized integration, policy, or hosted execution | [Control-plane layers](agents/integrations.md#what-a-company-can-buy-or-own) |
| Obot, Credal | Multiple employee clients need governed tools, source-permission enforcement, or curated context with measurable evaluations | [Governance and data candidates](agents/integrations.md#enterprise-governance-and-data-work-candidates) |
| Attio | An existing CRM workflow needs governed account context and actions; compare native agents before building, and test privacy, permissions, approvals, recovery, and export | [CRM as an agent surface](agents/integrations.md#attio-the-crm-is-becoming-an-agent-execution-surface) |
| TextQL, PromptQL | Ambiguous enterprise data or collaborative analysis warrants a fixed-question benchmark; verify shared-output permissions | [Data-work comparison](agents/integrations.md#enterprise-governance-and-data-work-candidates) |
| Windmill, Retool, Amazon Quick Flows | A real internal workflow needs an operator interface or shared operations beyond the existing service; compare Quick Flows only in a suitable tenant | [Workflow platforms](agents/integrations.md#internal-software-and-workflow-platforms) |
| Delta | Shared coding review loses decisions, and shipped safeguards or a verified external boundary can constrain execution | [Delta safety and trial criteria](agents/harnesses.md#delta-collaborative-coding-workspace) |
| Muse, Grok Bot, Dots, Lefos | Credential isolation, memory correction, action recovery, or enterprise controls materially change | [Persistent assistants](agents/assistants.md) |
| OpenAPPA | A bounded workflow needs policy over actions influenced by untrusted content | [Agent security](agents/security.md) |
| OpenClaw Enterprise | A bounded unattended workflow needs a separate control plane; verify release maturity, brokered credentials, revocation, and containment before trial | [Persistent-agent controls and full reading source](agents/security.md#persistent-agents-need-an-external-control-plane) |
| A2UI, OpenUI, and Vercel UI SDK | A real comparison or approval task needs generated screens, multiple assistant hosts, or an interaction missing from existing components; benchmark representation, renderer, and gateway separately | [Interface roles and evaluation](agents/interfaces.md#generated-interfaces-and-agent-operated-controls) |
| Claw Patrol and credential gateways | A concrete agent task needs service access without exposing reusable credentials; verify non-bypassable routing and authentication compatibility | [Sandbox and gateway exploration](agents/security.md#hosted-sandboxes-and-credential-gateways) |
| Deno Sandbox, E2B, Daytona, Cloudflare Sandbox, Vercel Sandbox | Unattended or untrusted coding work outgrows local isolation; clarify Deno Sandbox's lifecycle before adoption | [Sandbox roles and trial](agents/security.md#hosted-sandboxes-and-credential-gateways) |
| Jev, Decider, GLiClass, documented OpenAI decision APIs | Typed decision volume makes measured latency, calibration, or cost material | [Model efficiency](agents/models/efficiency.md) |
| Pi Durable, Kiro, Mastra Factory | A real workflow needs durable execution or repeatedly stalls on coordination | [Orchestration](agents/orchestration.md), [application frameworks](agents/frameworks.md) |
| Pydantic AI, Agno, LangGraph, Microsoft Agent Framework, Strands | An application needs agents with specific state, recovery, and operator requirements | [Framework comparison](agents/frameworks.md) |
| Factory Droid | A recurring supported-harness gap or measured context/cache bottleneck justifies a paired comparison; reuse individual mechanisms before switching runtime | [Factory direction and boundaries](agents/harnesses.md#factory-optimize-the-loop-before-replacing-the-harness) |
| OpenHarness, Open Interpreter, OpenHands, OpenCode | A capability gap appears in the supported coding harnesses | [Harnesses](agents/harnesses.md) |
| Warp Agent CLI and Factories | A concrete coding-harness gap or unattended engineering workflow earns comparison; no factory adoption without measured value | [Warp direction](systems/workstations.md#terminal-stack) |
| Magpie, pi-auto-router, OpenRouter, LiteLLM | A supported route can improve completed-task cost or latency without losing quality | [Routing evidence](agents/models/efficiency.md) |
| Hindsight, Recall, OpenWiki, Graphify | Documented continuity or retrieval failures persist | [Memory](agents/memory.md) |
| Serena, ast-grep, Mindwalk | Symbol navigation or structural edits become a measured bottleneck | [Code intelligence](agents/code-intelligence.md) |
| Browserbase, Browser Use, Stagehand | A recurring browser workflow outgrows local browser tools | [Browser tooling](agents/browser.md) |
| Cloudflare Kitesurf | Public JavaScript extraction makes browser resources or cloud concurrency a measured constraint, or persistent-session support materially improves; no adoption now | [Engine trade-offs and trial criteria](agents/browser.md#kitesurf-watch-not-adopted) |
| VoiceInk, Handy, OpenWhispr | A concrete dictation or conversational workflow merits a local trial | [Voice interfaces](agents/voice.md) |
| New models and managed agent APIs | A release changes capability, privacy, portability, or an execution boundary | [Providers](agents/models/providers.md), [inference](agents/models/inference.md), [platforms](agents/platforms.md) |

## Engineering

| Question or candidates | Revisit when | Evidence and comparison |
| --- | --- | --- |
| Agent-run verification and Cursor Rollouts | The same manual correction recurs or a release needs change-specific monitoring | [Verification](engineering/verification.md) |
| CodeRabbit, Entire Trails, and other review tools | Human review becomes the bottleneck and a bounded evaluation can measure useful findings; changing forge needs a separate hosting justification | [Code review](engineering/review.md) |
| AI-assisted formal verification | One consequential invariant or dependency has a precise specification and a reproducible proof-checking path at an acceptable cost | [Proof scope and assumptions](engineering/verification.md#formal-verification-stronger-claims-need-narrower-specifications) |
| Archify and Whiteboard | A substantial architecture or specification change needs AI-led explanation grounded in source; compare understanding, omissions, and upkeep against Git and Mermaid | [Code understanding and visualization](engineering/review.md#change-comprehension-and-visualization) |
| Depot, Blacksmith, Buildkite and CI alternatives | Runner cost, build latency, or hardware requirements are measured constraints | [Builds](engineering/builds.md) |
| Ziggity | Recurring manual staging or diff-review friction warrants comparison with the existing editor, CLI, and Lazygit; verify history-rewrite and private-diff boundaries | [Terminal Git interface](engineering/version-control.md#ziggity-a-terminal-interface-not-a-git-replacement) |
| Git hosting and forge alternatives | Hosting or concurrent agent traffic creates a concrete limit | [Version control](engineering/version-control.md) |
| Performance replacements | Profiling identifies the component a proposed replacement would improve | [Performance tooling](engineering/performance.md) |
| OpenSpec and spec-kit | The existing planning workflow repeatedly loses requirements or acceptance criteria | [Project documentation](engineering/documentation.md) |
| Ownership changes across developer vendors | Control, licensing, data handling, or portability changes | [Vendor ownership](engineering/vendor-ownership.md) |
| Bun ecosystem | A release removes meaningful tools, configuration, or recurring work; require matching-version checker parity and representative compatibility checks before adoption | [Bun watch criteria](languages/typescript/runtimes.md#bun-watch-criteria), [releases](https://bun.com/blog) |
| Deno ecosystem and maintained successors | Integrated tooling removes meaningful work and a credible ongoing release and security-response commitment resolves the maintenance concern | [Deno watch criteria](languages/typescript/runtimes.md#deno-watch-criteria), [releases](https://github.com/denoland/deno/releases) |
| Node + Vite+, Nub | Demonstrated configuration or tool removal while retaining framework coverage | [Runtime consolidation](languages/typescript/runtimes.md) |
| Topcoat | A new Rust application could remove a separate frontend build and API layer; verify experimental API stability, authentication, jobs, migrations, and deployment with one complete feature | [Rust framework watch](languages/rust/README.md#topcoat-full-stack-web-framework-watch) |
| Solid / SolidStart | A complete interactive feature can test authoring clarity and operational fit; first alternative to Svelte/SvelteKit | [Framework comparison](languages/typescript/frameworks/solid.md) |

## Systems and product

| Question or candidates | Revisit when | Evidence and comparison |
| --- | --- | --- |
| Render, Railway, Northflank, Hetzner and deployment tools | Workload, residency, operations capacity, or measured hosting cost changes | [Services](systems/services.md) |
| Kiri | Docker Desktop/OrbStack resource use becomes measured friction or Kiri resolves a concrete compatibility gap; test representative Compose workflows without migrating real data | [Local container-runtime assessment](systems/infrastructure.md#local-container-runtimes-kiri-watch) |
| AWS Emulator | A real AWS-dependent workflow needs fast local feedback; pin a release, inspect fidelity gaps, and retain real-AWS security tests | [Emulator limits and trial](systems/infrastructure.md#aws-emulator-local-api-behavior-not-aws-security), [factory mechanism](engineering/verification.md#aws-emulator-a-factory-with-a-reference-implementation) |
| OpenTofu, Pulumi, Crossplane, Kubernetes | The current deployment model cannot satisfy a named requirement | [Infrastructure as code](systems/infrastructure-as-code.md) |
| Database and analytical engines | Concurrency, query shape, scale, or recovery requirements exceed the current store | [Data stores](systems/data-stores.md) |
| DBOS, Temporal, Restate, Prefect | An application needs durable progress, or Python pipelines need shared scheduling and operations; test recovery and external-write idempotency | [Workflow selection](systems/services.md#durable-execution--workflows), [Prefect comparison](systems/services.md#prefect-comparison-reviewed-2026-10-15) |
| Vercel AI SDK, TanStack AI | A concrete provider/runtime capability gap or measured advantage justifies revisiting the selected TypeScript model library | [AI SDK beyond UI](systems/cloud-platforms.md#beyond-the-user-interface) |
| Cerbos, WorkOS | Cross-service policy, delegated agent identity, browser-only authentication, or internal-app governance exceeds existing controls; verify each product's availability and authority boundary | [Identity and authorization](systems/authorization.md), [WorkOS direction](systems/authorization.md#workos-from-sign-in-apis-toward-governed-agent-access) |
| Semgrep, SonarQube and supply-chain tools | A specific security detection or audit gap justifies another gate | [Systems security](systems/security.md) |
| Embeddings and LangExtract | A retrieval or extraction benchmark demonstrates value over existing parsing and search | [Retrieval](systems/retrieval.md) |
| Nix, nix-darwin, Home Manager; NixOS for Linux | Recurring dependency mismatches, exact-version recovery, or several Macs justify stronger reproducibility; a concrete Linux host need justifies NixOS | [Declarative host and development environments](systems/workstations.md#declarative-host-and-development-environments) |
| Terminal, editor, capture and remote-access candidates | Recurring host friction earns a change in the host repository | [Workstations](systems/workstations.md) |
| Raycast launcher and AI direction | A specific desktop interaction remains unmet; no additional desktop agent, memory store, or scheduler by default | [Raycast direction](systems/workstations.md#terminal-stack) |
| Anatomy | One mechanism needs an interactive explanation that outperforms prose or a small diagram; verify the behavioral model and bound generation spend | [Interactive explanation](product/design-tools.md#anatomy-interactive-explanation-not-evidence-of-physical-truth) |
| Moda and other visual design tools | A concrete artifact needs a comparative design trial | [Design tools](product/design-tools.md) |
| Storybook, component systems and content tools | Interface complexity or repeated visual defects justify their maintenance | [Product interfaces](product/interfaces.md) |
| shadcn/ui, shadcn-svelte, Bits UI, Melt UI | A concrete component or markup requirement exceeds the existing shadcn-svelte/Bits UI selection; verify the target Svelte version | [Component layers](product/interfaces.md#component-systems-and-primitives) |
| Shadcn Space, Radix UI by WorkOS, Base UI | A real React surface warrants reusable blocks or primitives; keep React examples as references rather than direct Svelte dependencies | [Component comparison](product/interfaces.md#component-systems-and-primitives) |
| Svelte MapLibre GL | An interactive choropleth or other geographic question warrants a map; validate data joins, aggregation, licensing, and accessible alternatives | [Geographic maps](product/interfaces.md#geographic-maps-and-choropleths) |
| Gemini avatar | Its product contents become directly reviewable | [Design-tool evidence](product/design-tools.md) |

Supplied video summaries remain attributed in the owning topics. The source
links for [Pi](https://www.youtube.com/watch?v=SxuQs9GGYbk),
[verification loops](https://www.youtube.com/watch?v=mQZB0l-rhxE),
[Opus prompting](https://www.youtube.com/watch?v=vsGwx28z4jk),
[automated research](https://www.youtube.com/watch?v=R9momwXV9w4), and
[DuckDB](https://www.youtube.com/watch?v=KJao6oq9MKM) remain available for transcript
follow-up; a supplied summary is not a verified transcript.
