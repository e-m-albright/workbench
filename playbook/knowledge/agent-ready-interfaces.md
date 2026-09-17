# Agent-Ready Interfaces

> **Last reviewed:** 2026-09-02. This review covers relevant Cloudflare and Vercel work published from November 2025 through early September 2026. Product adoption and performance figures are vendor-reported unless independently reproduced.

Cloudflare and Vercel are converging on the same architectural claim: agents work better when systems expose compact semantic interfaces, narrow authority, isolated execution, and versioned feedback rather than asking a model to reconstruct intent from a human interface. Workbench should adopt those interface properties without adopting either vendor as another control plane.

## Current disposition

| Pattern | Workbench posture | Reason |
| --- | --- | --- |
| Markdown projection from canonical web content | Adopt per project when an agent-read use case exists | Reduces conversion and context waste without creating a second source of truth |
| Small topic indexes and machine-readable sitemaps | Adopt for large documentation surfaces | Improves discovery without one oversized inventory |
| Stable, machine-readable command-line interfaces | Keep and sharpen | Already the preferred cross-repository contract |
| Always-loaded indexes for mandatory version-specific facts | Use selectively | Better recall can justify the context cost when omission predictably breaks work |
| Skills for optional workflows and supporting assets | Keep | Progressive disclosure remains appropriate when routing is reliable enough |
| Browser live view, diagnostics, recording, and human handoff | Treat as production-browser criteria | Local Agent Browser plus Playwright already covers the current need |
| WebMCP and page-declared actions | Watch | Promising semantics, immature authority and compatibility boundaries |
| Ephemeral sandboxes with snapshots | Use through an existing sandboxed harness when needed | No recurring workload justifies another managed runtime |
| Default-deny egress and brokered credentials | Adopt as requirements for any future untrusted-execution trial | Filesystem isolation alone does not bound network consequences |
| Server-side write policy and human-versus-agent attribution | Adopt for mutating connectors | Client prompts and skills are not authority boundaries |
| Durable workflows expressed as ordinary code | Keep as design criterion | Avoids a second graph or orchestration language |
| Autonomous software factory | Reject for current scale | Human attention and issue volume do not justify the control plane |

## 1. One source, multiple representations

Vercel added HTTP content negotiation and Markdown sitemaps to serve the same canonical article as HTML for people and Markdown for agents. Cloudflare added edge conversion to Markdown and reorganized its developer documentation around smaller section indexes. The useful pattern is not “publish an AI copy.” It is a generated projection with explicit provenance and no independent editorial lifecycle.

Apply this when an application has recurring agent readers:

- Keep one canonical content source.
- Serve or generate Markdown from that source rather than maintaining parallel prose.
- Preserve headings, links, tables, code, alt text, and source attribution.
- Exclude navigation and decorative chrome that carry no semantic value.
- Add topic-level indexes when the documentation tree is too large for one inventory.
- Evaluate answer correctness, latency, and total tokens together; raw byte reduction is not the outcome.

Do not treat Markdown, `llms.txt`, or embedded “instructions for agents” as trusted authority. They are content supplied by a site and remain untrusted ingress.

## 2. Put mandatory context where it cannot be skipped

Vercel reported that a compressed 8 KB Next.js documentation index in `AGENTS.md` reached 100% on its version-specific eval while skill variants peaked at 79%, primarily because the skill was not invoked reliably. This is a narrow first-party result, not a general verdict against skills.

Use the placement rule:

- Put small, consequential, repository-wide invariants and version-specific routing indexes in `AGENTS.md` when omission repeatedly causes incorrect work.
- Put optional workflows, scripts, examples, and larger references in skills.
- Put mechanical truth in code, generated schemas, or tests.
- Measure trigger failures before promoting skill content into always-loaded context.

Workbench should not move its skill library into the global instruction file. Most skills are optional and their combined context cost would be permanent.

## 3. Prefer semantic interfaces over reconstructed interfaces

Cloudflare's unified command-line interface work treats agents as first-class callers: commands, configuration, and bindings derive from schemas; vocabulary and defaults are linted; JSON output is part of the contract; and local-versus-remote behavior is explicit. Vercel and Cloudflare are also exploring page-declared browser actions through WebMCP.

The durable order of preference is:

1. A narrow typed connector for a repeated cross-system job.
2. A stable command-line interface with structured output for local and repository operations.
3. Semantic page actions when the site owns and secures them.
4. Browser interaction as the general escape hatch.

Do not mirror every REST endpoint as a tool. Expose recognizable outcomes, keep arguments flat and typed, paginate large results, and make errors tell the agent how to recover.

## 4. Authority belongs outside generated code

Recent Cloudflare and Vercel work independently separates untrusted execution from credentials and consequential tools:

- Cloudflare routes sandbox egress through a trusted outbound worker that can inject credentials, restrict destinations, log requests, and reduce permissions during a run.
- Vercel Connect exchanges stored provider credentials for task-scoped runtime tokens.
- Vercel Run executes generated JavaScript or TypeScript without direct Node.js or network access and exposes only named host functions.
- Cloudflare WriteGuard classifies and blocks high-risk Model Context Protocol calls before tool handlers run while recording both the human identity and agent session.

The resulting requirements are stronger than “put secrets in a vault”:

- Untrusted code never receives a reusable provider credential.
- Egress is default-deny and accounts for DNS, redirects, proxies, loopback, metadata services, and alternate address forms.
- A trusted broker injects short-lived authority only for the exact destination and operation.
- Critical mutations require deterministic server-side policy or human confirmation before the handler executes.
- Audit events distinguish a person's direct action from an agent acting under that person.
- Permissions can narrow after setup or discovery completes.

Workbench's read-only connectors, confirmed writes, protected credential paths, and parent-owned worker adoption already follow the small local version. A future sandbox experiment should add operating-system isolation and brokered egress rather than expanding regular-expression command policy.

## 5. Durable execution is a replay contract

Vercel Workflows and Cloudflare Workflows both express long-running coordination as ordinary code with durable step boundaries. The infrastructure records an event history, replays completed steps instead of repeating side effects, resumes after interruption, and exposes traces. Vercel also pins in-flight runs to the code version that started them.

If Workbench or a private layer gains a real durable workflow, require:

- Reviewed source code as the workflow definition.
- Explicit idempotent side-effect boundaries.
- Version-pinned in-flight runs.
- One composable wait-and-resume mechanism for human or external events.
- Bounded retries, timeouts, cancellation, and atomic rollback where possible.
- Traceable step inputs, outcomes, and current status.

Do not build a scheduler or workflow engine into Pi. The operating system, continuous integration, or a private automation owner remains the correct runtime until a concrete workload outgrows it.

## 6. Evaluation and observability must follow the artifact

Vercel's design guidance, agent software factory, Run SDK, and AI SDK telemetry all preserve the configuration that produced an output. Cloudflare's code-review system similarly emphasizes local and continuous-integration parity, structured findings, bounded retries, and observable human overrides.

For stochastic work, retain:

- Input, model, reasoning level, harness version, guidance version, and tool policy.
- First-attempt output and any reroll or recovery reason.
- Deterministic check results separately from model or human judgment.
- Screenshots, traces, or recordings when behavior is visual or interactive.
- Human corrections attached to the exact run that caused them.
- A safe no-op outcome; automation should not invent work to justify a run.

Promote repeated judgment into guidance, repeated mechanics into reusable code, and objective failures into deterministic checks. Keep model grades advisory.

## 7. Tool contraction is contextual

Vercel's internal data agent improved after replacing many schema-specific tools with filesystem access and shell commands. The reported lesson is that mature coding models can often search high-dimensional local data better than brittle hand-authored retrieval layers. It does not justify giving arbitrary shell and credentials to every agent.

Use a broad local primitive when:

- The data is already filesystem-shaped.
- The environment is isolated appropriately.
- Existing utilities expose inspectable, composable operations.
- The task needs open-ended local exploration.

Use narrow tools when they enforce an authority boundary, hide credentials, validate mutations, or provide a stable domain outcome. Workbench should continue pruning redundant tool schemas while retaining connector and safety tools whose narrowness is the security property.

## 8. What not to add

- Do not adopt Vercel or Cloudflare as a second managed agent runtime without a workload requiring hosted isolation or availability.
- Do not add an always-on browser or Model Context Protocol server merely because semantic browser actions are emerging.
- Do not build a software factory for a personal repository portfolio. Borrow its risk tiers, observability, and no-op semantics instead.
- Do not expose private applications to crawlers solely for agent readiness. Generate local or authenticated Markdown projections where useful.
- Do not accept vendor efficiency percentages without a paired local benchmark and quality endpoint.

## Sources

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
