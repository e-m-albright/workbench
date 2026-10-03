# Agent orchestration

Design bounded delegation, background work, durable execution, and recovery. Current Workbench configuration belongs in [its agent documentation](../../docs/agents/README.md).

## Advisor and monitor patterns

An advisor pattern lets a lower-cost executor ask a more capable model for help
when it encounters uncertainty. Evaluate the pair on completed tasks, recovery
turns, latency, and total cost. More model calls do not establish a benefit on
their own.

A monitor waits for a process or external condition to change and then wakes the
agent. This can reduce polling turns and keep background work bounded. Verify
which lifecycle events the harness actually exposes before depending on them.

The original August announcement notes reported a two-point multilingual
SWE-bench gain and about 11% lower cost for a Sonnet/Opus advisor pair, and
claimed that Claude Code monitoring required explicit prompting. Those notes
contain timestamps without an identifiable source. Treat these figures and
product details as unverified leads, not selection evidence.

## Bounded local delegation

Local delegation has two distinct forms:

- **Read-only finders** can safely run in parallel when their scopes are independent.
- **Mutating workers** require separate worktrees, explicit ownership, and parent review.

Workbench Pi implements the narrow mutating form through the model-callable `worker` tool: one child Pi, one isolated worktree, no commit or push, and parent-owned adoption. The model may delegate, review, and discard without per-use approval. `/worker` remains a manual entrypoint. This is deliberately not a standing agent roster, chain engine, or autonomous merge system. Expand it only when repeated use identifies a specific missing capability such as read-only fan-out or better progress reporting.

Philipp Schmid's four-pattern ladder is a useful complexity test: begin with one inline worker, add bounded fan-out only for independent work, add persistent agent pools only when repeated coordination needs durable identities and shared state, and use direct agent teams only when peer communication is itself necessary. Workbench intentionally stops at the first two levels. More autonomy is not progress if the coordination mechanism costs more than it returns.

Franck Verrot's "convergence engineering" is the matching control principle. The loop is only a mechanism; the real design object is an externally testable invariant that each pass moves toward, such as a green test suite, a reproduced browser state, or a review rubric with no surviving high-confidence findings. A loop without an acceptance condition can repeat, spend, and still drift. This reinforces Workbench's existing rule: give agents deterministic feedback and a bounded stop condition rather than asking them to keep improving an output abstractly.

## Background work, schedules, and durable objectives

Modern harnesses increasingly provide detached tasks, recurring prompts, event-triggered agents, and long-lived goals. These are different capabilities:

- **Process continuity** keeps a running shell or agent alive after disconnect.
- **Monitoring** wakes the agent when a condition changes instead of spending turns polling.
- **Scheduling** starts work at a future time or in response to an event.
- **Durable objectives** repeatedly reassess an open goal over a longer period.

Do not combine these into a homemade scheduler inside a coding harness. Use the operating system, CI, or an automation repository for scheduled instances. Use Paseo for agent process continuity and mobile control. Use a hosted harness when cloud execution is the required trust and availability boundary.

[Kiro's software factory account](https://kiro.dev/blog/software-factory-1000-prs/) describes a progression from one interactive session through multiple tabs, remembered and scheduled work, a queued pipeline, and a coordinator. Each stage answers a coordination bottleneck created by the prior one. Its reported 1,000 merged pull requests in a week measures throughput without a quality or rework denominator. Keep Workbench's bounded worker until measured waiting, review time, or recovery failures justify another stage.

## Cursor Automations patterns

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

## Durable workflows and replay

Vercel's Workflow SDK expresses orchestration as ordinary program control flow:
`await`, loops, branches, `try/catch`, and parallel promises. Durable step
boundaries let the runtime persist progress and reuse recorded results during
replay. Cloudflare Workflows is a second reference for explicit steps, parallel
branches, and execution traces. Neither removes the application's responsibility
for side-effect safety.

The transferable requirements are:

- Keep substantial workflow logic in reviewed, typed source.
- Identify side effects and retry boundaries explicitly. Make repeated execution
  safe with operation identifiers and source-side idempotency where available.
- Pin in-flight runs to a compatible code version.
- Use one composable wait-and-resume mechanism for human or external events.
- Bound retries, timeouts, and cancellation. Define compensation when a set of
  cross-system changes cannot be rolled back atomically.
- Record step inputs, outcomes, and current status.
- Verify backend portability, including deployment routing and replay behavior.

Vercel's article is a first-party product argument. Its versioning result depends
on retaining immutable deployments; at the cited review, its first-party
Postgres backend did not supply the same routing. Durable steps also introduce
network and queue overhead. These are design tradeoffs to test against the
actual workload.

[Pi Durable](https://earendil.com/posts/pi-durable/) is an experimental application
harness, separate from Pi's terminal coding agent. Its stored conversations,
checkpointed tasks, safe-versus-unsafe tool replay, multiple clients, and
replaceable execution environments make it a reference for long-lived agent
applications. **Watch, reviewed 2026-10-02:** evaluate only when recovery needs
exceed the existing job or workflow runtime, and test uncertain writes separately.

[Stateless MCP transport](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
and [AWS deployment guidance](https://aws.amazon.com/blogs/architecture/mcp-went-stateless-is-your-aws-mcp-server-deployment-well-architected/)
can simplify server deployment. Business operations still need state: an
interrupted external write requires an operation identifier, source read-back,
and an explicit unknown-outcome state before retry. The
[integration contract](integrations.md) owns the authority and reconciliation
requirements.

### Disposition

Workbench has no durable workflow runtime to replace. Scheduled instances remain
owned by the operating system, CI, or the private application that owns the work.
Adopt these design criteria when a concrete workload earns durable execution;
keep that runtime separate from the interactive coding harness.

Sources: Pranay Prakash,
[The best workflow engine is a programming language](https://vercel.com/blog/the-best-workflow-engine-is-a-programming-language),
2026-08-27; [Cloudflare Workflows](https://developers.cloudflare.com/workflows/).
