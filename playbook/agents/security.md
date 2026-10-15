# Agent security

Keep untrusted content, execution, credentials, and consequential authority behind explicit boundaries. The [Workbench isolation contract](../../docs/security/isolation.md) owns the implemented local controls.

## Trust machinery is the autonomy limit

The practical ceiling on autonomy is set by sandboxing, permission scope, verification, attribution, spend limits, and kill switches. Use operating-system containment for untrusted execution, with explicit network and credential boundaries. A model's approval or a tool-call guardrail does not provide that containment. Workbench's current enforcement is specified in its [isolation contract](../../docs/security/isolation.md).

OpenAI's Windows sandbox illustrates why containment is a composition problem rather than a single switch. Its unelevated path combines a synthetic security identifier, access-control lists, write-restricted tokens, and explicit protection for repository metadata. Its elevated path uses separate local accounts for networked and offline work, restricted tokens, and firewall policy. The reusable design is to separate online and offline identities, grant only the workspace access each needs, and layer operating-system identity, filesystem, process, and network controls. No one Windows primitive supplies the whole boundary.

## Passive retrieval can become code execution

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

### Adoption boundary

Operating-system isolation and command-policy checks are already implemented in Workbench. Provenance tracking and brokered authority are additional mechanisms to evaluate only for a concrete workflow that exceeds that boundary. The [experiment record](../../docs/experiments.md) owns trial status. Start any such trial with one execution profile and measurable bypass cases; keep the reusable threat model here.

This is a motivated proof of concept with 15 reported trials across three variants, not a population-level attack-success estimate. The transferable conclusion is architectural: model behavior and per-command approval can reduce risk, but only isolation and egress control bound the consequence of a successful injection.

Sources: Johann Rehberger, [Breaking Claude Code Opus 5 Auto Mode](https://embracethered.com/blog/posts/2026/breaking-claude-code-opus-5-and-automode/), 2026-08-26; Jessica Lyons, [Researcher shows how Claude Code can be tricked simply by asking it to summarize a website](https://www.theregister.com/research/2026/08/28/researcher-shows-how-claude-code-can-be-tricked-simply-by-asking-it-to-summarize-a-website/5293372), 2026-08-28.

## Authority belongs outside generated code

[OpenAPPA](https://github.com/archestra-ai/OpenAPPA) is an information-flow policy reference: labels on untrusted material can constrain later tool actions at an enforcement point outside the model. Its [paper](https://arxiv.org/abs/2607.24625) reports project evaluations, not complete coverage of shell, browser, network, or side-channel effects. Compare it only for a bounded untrusted-content workflow, with independent bypass and fail-closed tests. [Meta Muse's design](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) uses a different external authority point, including credential surrogation and action review; the [control-plane landscape](assistants.md#persistent-personal-agents-to-monitor) tracks its product boundary.

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

Compare any deployment against those requirements explicitly. Workbench's [implemented boundary and accepted limits](../../docs/security/isolation.md) are separate from these stronger design criteria; local isolation alone does not establish brokered credentials or default-deny network access.

- **[OpenAPPA](https://github.com/archestra-ai/OpenAPPA)** -- **WATCH FOR UNTRUSTED-CONTENT POLICY.** Trial only when a bounded workflow needs information-flow restrictions at the tool boundary; independently test bypasses and fail-closed behavior. The [authority boundary](#authority-belongs-outside-generated-code) owns the mechanism and its limits.

## Hosted sandboxes and credential gateways

Reviewed 2026-10-14. These are candidates for specific gaps, not an active
deployment. The [TypeScript runtime exploration](../languages/typescript/runtimes.md)
owns Deno/Bun selection; choosing an execution service does not require choosing
the same vendor's application runtime.

### Why the existing coding sandbox is local

Workbench already wraps managed terminal agents and their children in a native
macOS boundary using the pinned Anthropic Sandbox Runtime. The
[isolation contract](../../docs/security/isolation.md) records the decision to
remove Lima's VM provisioning, duplicate guest tools, mounts, and login
management. It also states that editor, desktop, daemon, and direct-binary
routes do not inherit that promise automatically. This review reads the
documented contract; it does not independently verify a running session.

The [Sandcastle and cloud-only tombstones](../../docs/decisions/tombstones.md)
record the related judgment: remote execution must solve a demonstrated
unattended or untrusted-workflow need. The records inspected do not establish
a previous Claw Patrol or Deno Sandbox trial. Their absence is not evidence
that either product was tested and found inadequate.

A hosted environment would provide disposable execution away from the Mac,
but still needs repository transfer, toolchain images, agent authentication,
network rules, preview access, recovery, patch export, and cleanup. The existing
local path avoids those integration responsibilities for interactive work.
This is a workflow-fit judgment, not a claim that local isolation is stronger.

Two accepted local limits deserve explicit reconsideration: admitted provider
credentials are readable by the agent, and broad public HTTP/HTTPS egress means
readable repository data can leave the boundary. Local execution also shares
the host kernel and edits the live checkout. A VM and a credential gateway
address different parts of that exposure.

### Candidate roles

| Candidate | What it supplies | Selection |
| --- | --- | --- |
| [Deno Sandbox](https://docs.deno.com/sandbox/) | Hosted Linux microVMs, command execution, storage, network controls, and secret substitution; SDKs are usable from Node and Python as well as Deno | Architecture worth learning from. Do not make a new long-term dependency until its lifecycle after the Deploy announcement is clarified. |
| [Claw Patrol](https://deno.com/blog/clawpatrol) | External gateway with HTTP, SQL, and Kubernetes-aware rules, credential injection, and approval chains | First candidate to inspect when agents need controlled service access. It complements execution isolation; it does not provide the coding workspace. The announcement labels it alpha. |
| [E2B](https://e2b.dev/docs) and [Daytona](https://www.daytona.io/docs/en/) | Programmable environments for agent code execution | Compare for a disposable remote coding job. No local benchmark or product ranking has been established. |
| [Cloudflare Sandbox](https://developers.cloudflare.com/sandbox/) and [Vercel Sandbox](https://vercel.com/docs/sandbox) | Hosted sandbox services integrated with their respective platforms | Compare when an application already benefits from that platform; validate isolation and lifecycle rather than assuming all services use identical VM boundaries. |
| Existing CI or one disposable local VM | Execution with an established runner or a separately isolated machine | Include as the simpler baseline before building a service or another orchestrator. |

Deno's [acquisition announcement](https://deno.com/blog/cloudflare) gives Deploy
six months, but does not separately specify Sandbox or Claw Patrol's future.
Sandbox depends on Deploy according to its documentation. Treat that as an
unresolved dependency risk, not a separately announced Sandbox shutdown date.
The [Sandbox product page](https://deno.com/deploy/sandbox), rechecked
2026-10-14, explicitly describes Firecracker microVMs on Deploy, host allowlists,
and placeholder secrets substituted at the outbound proxy. These are vendor
claims, not independently verified guarantees; merely leaving this page online
does not resolve service continuity. Revisit only with an explicit Sandbox
support or migration commitment and a workflow needing remote isolation.

Claw Patrol routes agent traffic through a gateway that holds real credentials
and evaluates requests. To make it an enforceable boundary, the execution
environment must prevent direct credential access and alternate network routes.
Credential substitution alone does not prevent misuse of permitted operations.
Use least-privilege service accounts and server-side authorization; SQL parsing
and model judgment must not be the sole protection against destructive access.
Do not assume API-key injection supports existing subscription OAuth flows.

The [Claw Patrol announcement](https://deno.com/blog/clawpatrol), rechecked
2026-10-14, describes WireGuard/Tailscale routing, TLS termination, and HCL
rules over parsed protocol fields. That makes the gateway, its certificate
trust, and its administrative credentials part of the trusted boundary.
The supplied [repository](https://github.com/denoland/clawpatrol) could not be
read through the available browser policy; current implementation, releases,
and maintenance status remain unverified. The alpha label above is the
announcement's, not a fresh repository assessment. Revisit for one controlled
service only after source and maintainer review, then test alternate-route
bypasses, malformed protocol requests, approval failure, and audit redaction
with fake credentials. The Deploy announcement does not settle this separate
open-source project's future.

### Smallest useful trial

Trial only one missing capability at a time. Use a disposable coding workspace
for an unattended repository task, or a gateway with one read-only service for
an agent that needs remote data. Do not couple both to a new scheduler, agent
harness, memory system, or application-runtime migration.

Before a paid or external run, select an approved source boundary, authentication
route, spending limit, expiration, and output destination. Canary with a public
or synthetic repository, fake secrets, and one representative job. Verify denied
host access, denied egress, credential handling, cleanup, interruption recovery,
and patch retrieval. Confirm real keys stay out of process environments, files,
logs, and model context if credential isolation is the claimed benefit.

The result should be a patch and test evidence against a known base revision.
Keep review, adoption, and consequential external actions outside the worker.
Compare useful completed work, intervention, setup time, operating cost, and
recovery with the existing local or CI path. Expand only after the canary works.
Remove the experimental credentials, environment, and adapter if it adds more
work than the isolation or unattended execution benefit justifies.

The [experiment record](../../docs/experiments.md) owns activation and removal.
No infrastructure, credentials, or external execution is authorized merely by
recording this exploration.
