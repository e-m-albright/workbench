# Agent integrations

Compare connectors, delegated identities, tool gateways, and application-owned business actions. This is architecture guidance and vendor research, not a selected deployment stack.

## MCP composition without an aggregator by default

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

## Gateway control when external AI clients call application tools

Treat Claude Desktop, ChatGPT, an IDE agent, and a custom agent as untrusted callers of the same capability plane. A client can help a user formulate an action, but it must not decide its own authority. Enforce controls in the MCP server, gateway, and downstream business service where every client path is covered:

1. Resolve the human, tenant, agent client, and execution separately. Prefer delegated user authority; never infer permission from possession of a server URL or tool name.
2. Publish only curated semantic operations. Newly discovered or generated tools remain disabled until an owner reviews the schema, description, data classification, and allowed callers.
3. Apply tool-level authorization, argument validation, rate and spend limits, response minimization, sensitive-data redaction, and network egress policy before returning data or dispatching an effect.
4. Bind a consequential approval to the exact actor, operation, arguments, target version, and expiration. Re-authorize delayed or retried execution.
5. Emit an audit record that joins request, policy decision, downstream effect, read-back, model/client identity when known, and override. Do not make prompt text or a model-based runtime review the only blocker.

[Uber's MCP Gateway design](https://www.uber.com/us/en/blog/designing-mcp-gateway/) is a scale reference, not a default blueprint. Its durable patterns are separating registry/control plane from proxy/data plane, deriving candidate tools from existing interface definitions, defaulting them off, retaining service-owner approval and rollback, and applying authorization and redaction in the execution path. Its incremental server/tool/schema discovery and response projection address context cost without presenting thousands of schemas to every model. The central gateway also concentrates credentials, policy mistakes, and availability risk; build it only after actual cross-client and cross-service pressure appears.

A small application should start with one owned MCP surface in front of existing domain commands and one policy enforcement point. Evaluate a cross-client governance product such as Runlayer when unmanaged clients, duplicate server configuration, or organization-wide audit are demonstrated problems. Evaluate an action gateway such as Arcade, Composio, or a cloud-native equivalent when delegated authorization and connector execution are the repeated problem. Neither category replaces domain validation, approval state, reconciliation, or source-system permission checks.

## Direct agent integrations and application-owned boundaries

Claude or ChatGPT can be an effective investigation and drafting interface over enterprise systems. Connectors and skills make a first supervised workflow cheap to explore: a user can retrieve permitted records, ask follow-up questions, and draft a resolution. The boundary changes when the workflow must decide which source is authoritative, carry a case across sessions, or write back to a system of record. Those decisions need application-owned rules and state that do not depend on one assistant's prompt or memory.

Both vendors now offer more than a personal chat client: organization-approved connectors, user or centrally managed authorization, and administrative tool controls are documented product surfaces. That establishes technical paths for enterprise rollout, not how widely companies actually deploy them or how well employees learn to use them. A deliberate rollout should assign workflow owners, start with a narrow group and read scope, provide examples and training, and measure useful completed tasks and errors. It should not assume that opening a connector catalogue makes employees competent operators. [ChatGPT connected apps](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt), [Claude connector setup](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities), and [Claude role permissions](https://support.claude.com/en/articles/13930458-set-up-role-based-permissions-on-enterprise-plans) describe the vendor controls.

For a cross-source reconciliation workflow, expose a small set of business operations to the assistant: fetch a normalized account view with source citations, list discrepancies, propose a resolution, request approval for an exact version, and commit or reconcile that version. The service behind those operations owns identity mapping, source precedence, field-level provenance, authorization, process versions, idempotency, audit records, and read-back of effects. It should return explicit states such as proposed, awaiting approval, confirmed, failed, and outcome unknown. A timeout after a write is an unknown outcome until the target system is checked; it is not permission to retry blindly. The assistant may investigate and compose, but a well-typed tool call is not itself authorization.

The smallest useful implementation is one vertical slice, not a general agent platform. Use a familiar service and storage layer with a few domain operations and deterministic scripts. Make the same API callable from Claude, ChatGPT, and the application's own interface if those entry points prove useful. Do not rebuild chat, a general workflow designer, or a model runtime for the initial slice. Integration vendors can handle OAuth, sync, and execution plumbing, but they cannot decide canonicality for the business.

This investment pays off when several users, workflows, or assistant vendors must share the same interpretation of records and the same write controls. A single exploratory, read-only task can remain a direct connector or skill. Once an action needs repeatable policy, approval, recovery, or audit, move that action behind the owning application rather than asking each assistant client to enforce it independently. The engineering cost of the service is real; there is no defensible universal multiplier relative to direct integration because entity matching, authorization, and write-back complexity vary by workflow.

For corporate or regulated data, assess the specific tenant configuration and contractual coverage before connecting a model provider to protected information. Keep least-privilege integration identities, source-side row and field restrictions, data minimization, retention controls, and audit independent of prompts. A business associate agreement, where required, does not replace application authorization or prove that every connector, subcontractor, log, and model feature is in scope. For sensitive writes, bind human approval to the exact action and version, execute through a scoped identity, and reconcile the result. These are design requirements to validate with the organization's security and legal owners, not claims that a particular vendor configuration is compliant.

Related reading: [integration candidates](#enterprise-integration-and-workflow-candidates-reviewed-2026-10-02) and [MCP security guidance](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices). Vendor capabilities and policies must be rechecked for any deployment decision.

## What a company can buy or own

| Layer | Job | Plausible options | Boundary to check |
| --- | --- | --- | --- |
| Assistant interface | Give employees a place to investigate and delegate | [Claude Cowork](https://claude.com/product/cowork), [ChatGPT Work and Workspace Agents](https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business) | Workspace enablement, connector scope, shared agents, approvals, usage visibility, and employee training |
| Cross-client governance | Curate approved MCP tools and skills, discover unmanaged access, apply central policy, and observe usage across clients | [Runlayer](https://www.runlayer.com/) | Coverage of each actual client and tool path, deterministic versus model-based enforcement, deployment boundary, and exportable audit |
| Connection infrastructure | Authorize accounts, refresh credentials, sync or expose source APIs | [Nango](https://nango.dev/), [Paragon](https://www.useparagon.com/), [Pipedream Connect](https://pipedream.com/connect) | Tenant and user identity, OAuth scopes, token custody, source rate limits, and data retention |
| Normalized APIs | Expose a common data model across supported software categories | [Merge](https://www.merge.dev/) | Coverage of custom fields, source semantics, sync lag, and escape hatches to the original API |
| Agent action gateway | Present curated tools and mediate execution | [Composio](https://docs.composio.dev/), [Arcade](https://docs.arcade.dev/); compare [Klavis](https://www.klavis.ai/) and [Metorial](https://metorial.com/) for hosted MCP needs | Per-user delegation, action-level policy, custom tools, tool result size, audit, retries, and deployment model |
| Enterprise integration platform | Run managed cross-system workflows and expose them as APIs or MCP tools | An existing integration platform, or [Workato MCP](https://docs.workato.com/mcp.html) where Workato is already in use | Whether its workflows preserve source provenance, human approval, and business transaction state |
| Cloud agent infrastructure | Host agents, gateways, credentials, policy, and observability | [Amazon Bedrock AgentCore Gateway and Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html); [OpenAI Agents API](https://openai.com/index/introducing-the-agents-api/) for a managed runtime | Cloud and model dependence, enforcement location, network egress, identity propagation, and exportability |
| Business control service | Decide canonical records, validate proposed changes, record approvals, and reconcile effects | A small application-owned service, possibly using the layers above | This domain logic must remain testable and enforceable outside a model prompt or vendor workflow definition |

The closest Composio versus Arcade comparison is the agent action gateway. Composio's documented strength is breadth: toolkits, hosted sessions, per-user authentication, triggers, and execution. Arcade emphasizes delegated authorization, a curated tool runtime, central governance, and audit. Both vendors' claims require a representative test. Nango, Paragon, and Pipedream Connect are adjacent connection products. Merge provides normalized APIs across supported software categories. Workato may already own the integration layer in a large company, in which case another gateway must justify a second credential and policy surface.

[AWS AgentCore Harness](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-harness-is-now-generally-available-go-from-idea-to-production-grade-agent-in-minutes/) is a managed-runtime comparison if hosted isolation or availability becomes a requirement. [Dify](https://dify.ai/) is a visual application-builder comparison if a supervised workflow needs an operator interface. Neither resolves source canonicality or application write semantics by itself.

Start selection with one workflow and one source-side identity model. Test a permitted read, a denied read, a proposed write, an approved write, and a timeout whose effect is initially unknown. Inspect the actual source permissions and audit trail after each call. Compare what the platform enforces with what remains in the business service. The important question is whether a platform removes repeated integration work without taking ownership of canonicality, authorization, or recovery away from the application.

## Agent identities, executions, and downstream authority

[Microsoft Entra Agent ID](https://learn.microsoft.com/en-us/entra/agent-id/how-to-plan-agent-identity-architecture) is an identity-governance option to evaluate, not proof that every downstream system accepts every agent token type. Distinguish an **agent identity blueprint** used to create/govern identities, a **logical agent identity** with an owner and assigned authority, and an **execution** using that identity. A blueprint is not a downstream permission group.

Concurrent replicas can share a logical identity only where supported authentication and common authority make that appropriate. Keep distinct run identifiers and source-request correlation; do not conflate shared authority with safely sharing mutable token caches or sessions. Separate identities when permissions, ownership, audit attribution, or independent revocation differ. Ordinary workload identities remain suitable for deterministic jobs.

An external source still validates the intended token audience/issuer, maps supported claims to its own identity, and applies its roles and grants. OAuth scopes are not interchangeable with database privileges. For example, documented [Snowflake Entra External OAuth](https://docs.snowflake.com/en/user-guide/oauth-azure) support does not itself establish Agent ID compatibility. Prove the exact flow before selecting it.

Revocation spans source grants, tokens, application/source sessions, caches, generated artifacts, and queued work. Set a measurable removal target, test existing as well as new sessions, and reauthorize delayed effects. Never substitute a stronger credential after a source denial. A named chatbot or messaging participant is not necessarily an independently governed security principal.

## Enterprise integration and workflow candidates (reviewed 2026-10-02)

These products solve different parts of an application-owned integration layer. None determines which source is canonical or whether a proposed business write is correct; those rules remain with the owning application. Compare the exact required operations and authority model, using the smallest representative proof that resolves uncertainty. A read-only application does not need to invent a write workflow to evaluate a vendor. Native maintained adapters are a baseline, not a mandatory first implementation; source count alone does not decide whether to buy.

| Candidate | Useful surface | Posture and revisit trigger |
| --- | --- | --- |
| [Nango](https://nango.dev/) | Connection lifecycle and authenticated proxy; broader sync, webhook, and tool capabilities depend on offering | **WATCH.** Evaluate when connection maintenance is a demonstrated burden. The [free self-hosting documentation](https://nango.dev/docs/guides/platform/free-self-hosting/configuration) previously described Auth and Proxy; verify current edition and license boundaries rather than assuming every capability is included or all self-hosting requires Enterprise. Self-hosting transfers operations to the adopter. |
| [Merge](https://www.merge.dev/) | Normalized unified APIs and agent-facing integration products | **WATCH.** Compare against direct APIs when several customers need the same category of SaaS system; test whether its common model preserves the fields and source semantics needed for reconciliation. |
| [Pipedream](https://pipedream.com/) | Hosted integrations and workflows; Connect for product integrations and Conduit for internal agent access | **WATCH.** Test only when managed connection breadth or enterprise access governance is the bottleneck; distinguish customer-facing embedded authorization from employee access to internal tools. |
| [Windmill](https://www.windmill.dev/) | Code-first scripts, workflow execution, schedules, and operator interfaces | **WATCH.** Evaluate when jobs need an operations surface beyond existing hosting. The [2026-10-14 comparison](#internal-software-and-workflow-platforms) covers its overlap with Retool and Quick Flows. DBOS is an application library, not the same product boundary. One runtime owns each workflow. |
| [Paragon](https://www.useparagon.com/) | Managed connections and [ActionKit](https://docs.useparagon.com/actionkit/overview) operations/triggers, alongside workflow products | **WATCH.** Potentially useful before workflows: supported source calls, connection lifecycle, and diagnostics can replace custom machinery. A Python backend can consume its API while retaining domain logic. Prove exact authentication, custom fields, denied/revoked access, connection binding, custody, pricing, and exit terms. Connector availability does not prove delegated identity or permission-preserving synchronization. |
| [Dify](https://dify.ai/) | Visual agent and workflow application builder | **REFERENCE.** Useful to compare build-versus-buy for a hosted AI workflow UI; no current need to move canonical data rules into its workflow definitions. |
| [Composio](https://docs.composio.dev/) | Agent-ready toolkits, per-user managed authentication, triggers, hosted MCP sessions, and execution | **WATCH.** Trial against Arcade on one read and one write with the same test users. Inspect tool schema quality, token custody, permission narrowing, audit, retries, and custom business actions. |
| [Arcade](https://docs.arcade.dev/) | Delegated agent authorization, tool execution, policy, and central tool governance | **WATCH.** Strong candidate when several agents or clients need the same user-scoped action gateway. Verify policy enforcement and audit at the actual execution boundary rather than relying on vendor positioning. |
| [Workato MCP](https://docs.workato.com/mcp.html) | Existing enterprise integration and orchestration platform with identity-aware MCP tools | **WATCH IF ALREADY DEPLOYED.** Reuse the company's established integration platform before adding another credential or workflow plane; test end-user identity propagation and action-level policy. |
| [Runlayer](https://www.runlayer.com/) | Cross-client agent catalogue, MCP gateway, identity policy, runtime review, and usage visibility | **WATCH FOR COMPANY-WIDE GOVERNANCE.** Compare when several teams use multiple assistant clients; verify coverage of tool paths and whether hard policy is independent of model review. |

**Closest alternatives to Composio and Arcade:** [Nango](https://nango.dev/) and [Pipedream Connect](https://pipedream.com/connect) cover managed connections; [Klavis](https://www.klavis.ai/) and [Metorial](https://metorial.com/) focus on hosted MCP infrastructure; [Amazon Bedrock AgentCore Gateway and Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html) provides an AWS-native gateway with external policy enforcement. These overlap only partially. Shortlist by the missing capability, not catalogue size. The [layer comparison](#what-a-company-can-buy-or-own) separates connection, action, policy, workflow, and business-state ownership.

## Enterprise governance and data-work candidates

Reviewed 2026-10-14 from the official pages linked below. These are **WATCH**
candidates, not tested deployments. Product descriptions are upstream claims;
this review does not establish permission preservation, compliance, benchmark
accuracy, or complete coverage of every client path. [Cerbos and WorkOS](../systems/authorization.md)
belong to the application authorization and identity layer, not this shortlist.

| Candidate | Current documented position | Why track it; exact evaluation trigger |
| --- | --- | --- |
| [Obot](https://obot.ai/) | MCP and model gateways, approved MCP/skill registries, hosted workloads, identity, and correlated audit. [Documentation](https://docs.obot.ai/) identifies version 0.26.0 and describes Sentry device management as beta. | Compare with Runlayer when an organization needs governance across multiple clients, not just configuration sync. Prove denied tool access, gateway bypass resistance, credential separation, and audit coverage on the actual clients. |
| [Credal](https://credal.ai/) | Curated enterprise context and MCP tools, agent building, registry, evaluations, policy, and cost attribution. Its [documentation](https://docs.credal.ai/) describes source-permission mirroring and cloud or on-prem deployment. | Compare with Obot/Runlayer when domain-specific context curation and evaluations matter alongside governance. Test revoked source access, bounded tool arguments, approval binding, and exportable audit. Shared instructions are not equivalent to deterministic enforcement. |
| [TextQL](https://textql.com/) | Ana reasons over an enterprise ontology, produces queries and data applications, and supports agents that write back. This is broader than a natural-language SQL frontend. [Deployment docs](https://docs.textql.com/core/admin/deployment-config) describe self-hosted Helm configuration, identity integration, tool availability, and context-review controls. | Evaluate when analysts repeatedly struggle with ambiguous enterprise schemas or metric definitions. Use a fixed set of known-answer questions, conflicting definitions, denied rows, and costly-query limits. Keep source writes disabled in the first trial. |
| [PromptQL](https://promptql.io/) | The current homepage emphasizes persistent multiplayer bots, shared dashboards/documents/sheets, isolated computers, and API/database tools, rather than only data querying. | Evaluate when a real collaborative workflow needs durable shared context and expert corrections. Compare with an existing employee assistant plus owned tools; test permissions, shared-output leakage, provenance, and corrections that survive subsequent runs. |

Obot's documented quickstart mounts the Docker socket. That gives its control
service consequential host authority; hosted workload isolation does not make
the control service unprivileged. Any trial belongs on a disposable evaluation
host, not a credential-rich workstation. Its open-source positioning and
edition descriptions do not substitute for reviewing exact component licenses,
feature limits, and the endpoint agent's privileges.

PromptQL's permission FAQ says each action borrows the requester's access, but
also explicitly says replies in a shared chat are visible to everyone in that
chat. Per-request source authorization therefore does not guarantee that every
reader is authorized to see a shared answer. Test with two users who have
different source permissions, including cached artifacts and later questions;
do not use sensitive data merely because source access is delegated. Its page
also describes beta invites. Confirm availability for the intended deployment.

TextQL's ontology accuracy improvements and Credal's accuracy/context savings
are vendor measurements without a benchmark reproduced here. Test against the
same questions, users, source snapshots, and cost budget before ranking them.
For TextQL self-hosting, the reviewed configuration recommends explicit
authentication enforcement for locked-down deployments and documents exceptions
for signed library-file links. Inspect artifact access as well as query access.

## Internal software and workflow platforms

Reviewed 2026-10-14. These products bundle an execution service with a building
and operations interface. They are not interchangeable with a durable-execution
library, nor does an attractive workflow editor establish transaction safety.

| Candidate | Documented useful surface | Posture and next action |
| --- | --- | --- |
| [Windmill](https://www.windmill.dev/) | Code-first scripts, workflows, approvals, schedules, data pipelines, and internal apps; cloud or self-hosting, CLI/Git collaboration, and React/Svelte app frontends. | **WATCH; first comparison for code-owned internal automation.** Trial when schedules and scripts need shared operations, approvals, and an operator UI. Compare with the existing service plus cron or [DBOS](../systems/services.md#durable-execution--workflows), including worker and edition costs. The vendor's speed claims were not benchmarked. |
| [Retool](https://docs.retool.com/) | Internal apps, AI-assisted and classic builders, agents, workflows, data sources, permissions, source control, and hosted/self-hosted deployment. The docs list self-hosted stable releases dated 2026-10-08. | **WATCH; interface-led alternative.** Compare with Windmill when building and maintaining operator screens is the repeated burden. Verify edition-specific permissions, source-control support, deployment rights, end-user costs, and portability before adopting. |
| [Amazon Quick Flows](https://aws.amazon.com/quick/flows/) | Natural-language workflow creation and sharing within Amazon Quick, connected data/actions, browser interactions, and conversational refinement. | **WATCH IF QUICK IS ALREADY RELEVANT.** Evaluate one low-risk employee workflow in an authorized tenant. Confirm region, connectors, user licensing, execution identity, action approval, and recovery instead of treating AWS availability as proof of fit. |

AWS's [administration guide](https://docs.aws.amazon.com/quick/latest/userguide/managing-quick-flows.html)
describes feature enablement, ownership/sharing controls, and administrative
approval before sharing flows. Approval to share a workflow is not evidence of
approval for each consequential action it later performs. Browser interactions
also require a separate check of identity, allowed destinations, and read-back.

For all three, run one synthetic workflow with a human approval, interruption,
retry, denied source access, and a write whose result initially times out.
Inspect whether restart duplicates effects, whether approval binds the exact
arguments, and whether rollback changes code only or also repairs external
state. Choose one runtime to own the workflow. Retain business validation,
idempotency, and unknown-outcome reconciliation in application-owned code.
Do not add a second scheduler or move canonical records merely to test a UI.

This is an initial official-documentation review. Component licenses, security
advisories, full release histories, independent benchmarks, and negotiated
pricing remain adoption-review work; no vendor has passed that gate here.
