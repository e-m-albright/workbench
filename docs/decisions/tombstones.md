# Tombstones

Tombstones record evaluated tools and approaches that should remain absent from
the active workbench. They prevent accidental reintroduction and repeated
evaluation. Reconsider one only when its stated trigger becomes true.

This file covers only decisions with no code off-switch. Retirements that code
enforces live with their enforcement: `RETIRED_SUBAGENTS` / `RETIRED_SKILLS` in
`src/workbench/core.py` and the `_*_disabled` entries in
`agents/shared/mcp-servers.json`, each carrying its own reason.

| Capability | Status | Reason | Revisit when |
|---|---|---|---|
| Gemini tooling | Retired | Google agent tooling is not currently worth another first-class integration | The product materially leads Claude or Codex on a recurring workflow |
| Batteries-included Pi fork or distribution | Rejected | Upstream Pi plus a small managed extension set now provides durable value; migrating to an Oh My Pi-style bundle would trade away legibility and add overlapping runtimes, memory, browser, subagent, and collaboration machinery | Multiple independently validated needs require coordinated core changes that upstream extensions cannot provide |
| Cursor agent integration | Retired | The Cursor IDE and its agent control plane did not earn their overlap with Zed, Claude Code, and Codex | Cursor becomes a regular primary coding environment again |
| Hermes coding parity | Rejected | Hermes is better evaluated as an automation runtime than as another coding-agent target | Its coding workflow becomes independently valuable |
| Hermes automation runtime | Rejected | Evaluated 2026-07-21: the always-on value (competitive polling, outreach batching, repo watchdogs) is better served by tight in-house scheduled jobs; phone chat is Tailscale to an interactive session; self-writing skills and memory remain too haphazard to trust | An always-on capability emerges that scheduled jobs plus interactive sessions cannot replicate, with a credible security story |
| Cross-vendor capability matrix | Retired | Expensive to maintain and previously drifted from installed behavior | A concrete portability regression cannot be caught by deployment checks |
| Agent usage telemetry | Retired | Incomplete observations produced misleading conclusions | Vendor APIs expose complete, stable usage evidence |
| Historical machine snapshots | Retired | Past-live versus current-live diffs do not establish drift from desired state | A forensic use case appears that live reconciliation cannot answer |
| Impeccable skill suite | Retired | Strong design ideas, but its mandatory context files, preflight gates, command suite, and runtime overlap with the smaller repo-owned frontend-design skill | A recurring design workflow proves the lighter skill cannot express a needed capability |
| Globally installed stack skills | Retired | Framework, database, and SaaS instructions consumed every session's skill metadata despite being relevant only in some repositories | A skill proves useful across most repositories rather than one stack |
| Global Cloudflare skill bundle | Retired | Eleven official retrieval-first skills exceeded the needs of occasional Workers, Pages, and email-routing work and had no managed update path | Repeated Cloudflare work proves project context and current official docs insufficient |
| Global `find-skills` skill | Retired | Occasional discovery did not justify permanent session metadata or a dedicated external-install pathway | On-demand skill discovery becomes a repeated need |
| Generic verify/format agent hooks | Retired | Project-native task runners and hook systems own formatting and verification; global agent hooks duplicated them and produced surprising cross-project behavior | A vendor exposes a narrowly scoped hook event that cannot call the project's own gate |
| Generic notification agent hook | Retired | Terminal activity titles and the managed status line cover progress without another interrupting shell hook | Long unattended runs make missed completions a recurring, measurable problem |
| Pi Fast-mode control | Rejected | The Codex subscription route does not expose authoritative state and priority service changes usage economics; thinking level is not Fast mode | Pi exposes reliable provider-route state and the owner explicitly wants the cost tradeoff |
| Custom Pi transcript viewport | Rejected | Pi has no supported scrollback viewport API, and duplicating the transcript renderer would depend on private TUI internals | Terminal-native navigation fails a controlled test and Pi exposes a public viewport API |
| Permanent Pi subagent fleet | Rejected | A roster and parallel writers add coordination and trust cost while explicit consult covers independent review | Bounded delegation repeatedly saves time, with worktree isolation and parent-owned verification |
| Universal ceremony gates (Superpowers-style) | Rejected | Firing a mandatory brainstorm→plan→review pipeline on every task burns tokens on ceremony a one-line fix does not need; discipline gates on complexity, not existence | Selective gating demonstrably lets consequential changes ship unplanned |
| Standalone wrapper CLI (GSD-style) | Rejected | Owning the execution environment for programmatic context management means maintaining a second harness that trails vendor releases; native skills plus fresh subagent contexts cover context rot | Vendor harnesses stop exposing enough context control for a recurring workflow |
| Large agent rosters (OMC-style) | Rejected | Dozens of installed specialists create Oh-My-Zsh syndrome: easy to install everything, hard to know what is active; a small subagent set with obvious triggers stays legible | A recurring task class needs a specialist the small roster genuinely cannot express |
| Numeric code-shape rules as always-on prose | Rejected | Max-line and helper-count limits in global instructions are advice an agent may or may not weigh; they belong in deterministic project gates (linters, ratchets) | A shape regression recurs that no project-native gate can encode |
