# Remote agent execution

Reviewed 2026-11-21. Research only: no provider, runtime, gateway, or client is
adopted by this comparison. Evaluate one bounded workflow when remote availability
or isolation becomes useful; do not build an agent platform in advance.

## Separate the responsibilities

| Responsibility | Candidates | Boundary |
| --- | --- | --- |
| Session access and continuity | [Paseo](https://paseo.sh/), [Herdr](https://herdr.dev/), [HAPI](https://hapi.run/), Rex | Reconnection, status, conversation or terminal access. These do not inherently enforce credentials, network policy, or deployment authority. Rex's current remote capabilities were not verified. |
| Governed tools and automation | [Runlayer](https://docs.runlayer.com/platform-agents) | Connector selection, identities, policy, approvals, audit, and hosted agents. Check coverage of external harness calls and shell networking. |
| Credential brokering | [Infisical Agent Vault](https://infisical.com/platform/agent-vault) | Scoped sessions and a proxy that attaches credentials outside the worker. Preview; enforce routing so the worker cannot bypass it. |
| Disposable Linux execution | [Cloudflare Sandbox](https://developers.cloudflare.com/sandbox/concepts/), [Daytona](https://www.daytona.com/pricing), [E2B](https://e2b.dev/pricing), existing CI | Validate persistence, runtime limits, egress controls, harness compatibility, patch export, recovery, and cleanup. |
| Conventional machine | [Hetzner](https://www.hetzner.com/cloud/), [DigitalOcean](https://www.digitalocean.com/pricing/droplets), [Lightsail](https://aws.amazon.com/lightsail/pricing/), existing cloud compute | Ordinary Linux administration and private networking; the operator owns containment and maintenance. |

Herdr documents SSH/Tailscale machine access and server-side processes that
survive client closure, not server reboot. HAPI documents a VPS-capable hub,
web/mobile clients, and Claude Code, Codex, and Pi integrations. Its
[support matrix](https://hapi.run/docs/guide/agents) lists Pi as remote-only and
always auto-approved. Its [peer tools](https://hapi.run/docs/guide/how-it-works)
can inspect, message, and spawn sessions; disable unnecessary cross-session
access rather than treating the shared hub as an isolation boundary.

Runlayer's hosted runtime documentation describes AgentCore microVM sessions
or Kubernetes sandboxes backed by gVisor/Kata, depending on deployment. It also
states that public egress is allowed by default. Runs are short-lived and
interactive terminal programs requiring a TTY are unsupported. Its product is
broader than an MCP gateway, but not a drop-in remote terminal for every harness.

Infisical's [pricing](https://infisical.com/pricing.md) lists 5,000 brokered
requests monthly free, then $1 per 10,000. Agent Vault is distinct from its
secret manager and deprecated earlier proxy products. A secret manager or
command-scoped environment injection can still expose the real secret to the
executed command; brokered credentials address a different risk.

## Execution boundaries

Ordinary containers share the host kernel. [gVisor](https://gvisor.dev/docs/architecture_guide/intro/)
implements Linux interfaces in a restricted userspace application kernel;
`runsc` integrates with container tooling. Kata Containers and Firecracker use
guest-kernel VM boundaries. Bubblewrap and nsjail use Linux process isolation;
V8/WebAssembly isolates fit bounded computation rather than arbitrary Linux
programs. Compare compatibility and overhead instead of treating these as
interchangeable security levels.

Keep the following outside the worker's writable environment:

- Policy, launch configuration, credential issuance, revocation, and spending limits.
- Canonical application state, deployment authority, and independent recovery copies.
- Personal home directories, authenticated browser profiles, SSH agents, and host Docker sockets.

Use repository-scoped [GitHub App installation access](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation),
with the App private key outside workers. Branch rules and protected deployment
environments constrain effects that token repository scope alone does not.
Bind approval, tests, and publication to the exact adopted revision.

Deny unnecessary egress, private-network routes, metadata credentials, and
alternate DNS paths. A proxy environment variable is not network enforcement.
An agent can abuse permitted operations without stealing a credential; readable
source can leave through model requests, issue comments, or other allowed
channels. Typed methods, minimal inputs, and deterministic server-side policy
remain necessary. Scanners and independent reviews reduce vulnerable changes;
they do not prove generated code is safe.

## Cloudflare: managed compute, not a conventional VPS

[Containers](https://developers.cloudflare.com/containers/) run Linux images
inside Firecracker microVMs and are controlled by Workers/Durable Objects.
[Dynamic Workers](https://developers.cloudflare.com/sandbox/concepts/) instead
run generated JavaScript against methods supplied by trusted code; set
`globalOutbound` to `null` when no independent network access is needed.
Neither environment should inherit durable application credentials by default.

The [container lifecycle](https://developers.cloudflare.com/containers/concepts/architecture/)
is not permanent-machine semantics. Disk is ephemeral by default; snapshots
are immutable point-in-time copies, not a continuously durable database volume.
Do not place canonical SQLite on disposable disk or assume an object-storage
FUSE mount supplies SQLite's required filesystem semantics. A stateful Python
application needs a separately designed durable store and recovery path.
Workers/D1 can reduce idle hosting cost but require application adaptation;
D1 is not a filesystem-mounted SQLite replacement.

[Container pricing](https://developers.cloudflare.com/containers/platform/pricing/)
requires the $5/month Workers Paid account plan. Included monthly usage is
25 GiB-hours memory, 375 vCPU-minutes, and 200 GB-hours disk. Additional rates
are $0.009/GiB-hour memory, $0.072/active-vCPU-hour, and $0.000252/GB-hour disk.
Memory/disk are provisioned capacity while running; CPU is active usage.
Worker, Durable Object, storage, observability, and network charges can be
additional. Existing account allowances are shared, not free per application.

For illustration, a basic 1 GiB/4 GB instance running 730 hours costs about
$12/month including the account subscription and subtracting the listed
memory/disk allowances, before CPU and other services. A 4 GiB/8 GB instance
is about $32.50 on the same basis. Sleeping between visits can reduce cost;
reliable state recovery must come first. These are calculations, not workload
measurements or quotations.

[Workers](https://developers.cloudflare.com/workers/platform/pricing/) and
[D1](https://developers.cloudflare.com/d1/platform/pricing/) have free tiers,
so a compatible low-traffic application can fit at $0. This does not establish
that an existing filesystem-backed application can be moved unchanged for free.
Private hosting must preserve authentication on every route, including APIs,
previews, assets, and origin paths. An identity-aware HTTPS gateway is a different
contract from a tailnet-only application; do not silently replace one with the other.

## Conventional and managed alternatives

Checked published Linux general-purpose Lightsail IPv4 bundles: 2 GB/2 vCPU
$12/month, 4 GB/2 vCPU $24, 8 GB/2 vCPU $44, 16 GB/4 vCPU $84. DigitalOcean Basic
lists 8 GiB/4 vCPU $48 and 16 GiB/8 vCPU $96. These are not equivalent CPU
performance guarantees; region, availability, snapshots, taxes, and overages
need checking. Hetzner remains a value candidate without a verified comparable
regional quote in this review. Existing-cloud compute can avoid another vendor.

Daytona documents usage billing and stopped/paused lifecycle; E2B documents
Hobby sessions up to one hour and Pro at $150/month plus usage with sessions up
to 24 hours. Neither pricing page establishes complete workflow fit or isolation
quality. Compare one public or synthetic task before paid expansion.

## Revisit criteria

First decide whether the need is durable application availability, cross-device
session access, governed personal automation, or disposable coding execution.
Keep durable services and coding workers separate. Preserve one canonical store
rather than synchronizing a live database between machines.

A useful future trial must complete a representative task while denying secret
reads, policy modification, direct network bypass, unrelated service access,
protected-branch pushes, cross-session access, and deletion of recovery copies.
Measure intervention, reconnect/resume behavior, total cost, and recovery. Keep
local device integrations separate from remote application hosting. See
[agent security](security.md) for the threat model and
[decision models](models/efficiency.md#typed-decision-models) for classification
and research-routing candidates. No trial is scheduled by this document.
