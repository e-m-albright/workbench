# Active Experiments

Temporary harness changes live here so a trial cannot quietly become permanent.
Each experiment must name a review trigger and a complete removal path.

## Proposed, not active

- **Pi phone Web UI over Tailscale:** tracked in the private Work queue. Trial an audited existing package before building a client. Any trial needs its own dated entry here when it begins.
- **Conversational Pi coordinator:** test whether a voice-first foreground Pi can remain responsive while isolated child Pi jobs work asynchronously, then proactively summarize completions at safe conversational boundaries. Candidate speech transport: Hugging Face `speech-to-speech` on Apple Silicon, with cloud STT/TTS retained as a measured fallback if local latency or voice quality misses the bar. This is not active: first write a dated experiment entry with staged success criteria (local barge-in smoke; one Pi SDK/RPC session; non-blocking worktree worker; completion-event narration), privacy/cost boundaries, and complete removal steps. Do not begin by building an always-on assistant, durable memory, staff-persona framework, or queue mutation layer.
