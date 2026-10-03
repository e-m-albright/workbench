# Token Efficiency and Model Performance

> **Last reviewed:** 2026-07-21 - Refresh when new measured evidence or billing behavior emerges.

Reduce the total cost of correct work, not a local token proxy. An optimization
is useful only when it lowers billed cost or latency without reducing task
quality, increasing retries, or moving work into another token class.

## Core principles

1. **Measure the whole agent loop.** Prompt tokens, tool results, cache creation,
   cache reads, output, retries, and extra turns all affect cost.
2. **Estimate the reachable ceiling first.** Determine what fraction of the bill
   a proposed optimization can influence before building or buying it.
3. **Preserve quality.** Fewer tokens with worse task completion is not an
   efficiency win.
4. **Prefer structural reductions.** Remove irrelevant context, defer tools, and
   isolate research before compressing text the model may need.
5. **Treat self-reported savings as unverified.** A tool's counterfactual may not
   match provider truncation, caching, tokenization, or billing.

## Durable levers

### Keep stable instructions small

For each line in an always-loaded prompt or `AGENTS.md`, ask whether removing it
would cause a concrete recurring mistake. Remove general knowledge, duplication,
and preferences that rarely apply.

Stable prompt prefixes are more cache-friendly than frequently changing ones,
but cache behavior is provider-specific. Verify the actual billed token classes
rather than assuming a percentage.

### Load tools and references on demand

Tool schemas and reference documents consume context on every turn when loaded
eagerly. Keep skill descriptions sufficient for routing, then load detailed
references only when the task requires them.

### Select context instead of dumping it

- Search for relevant files before reading broad directories.
- Give implementation agents the narrow evidence they need.
- Delegate noisy, read-heavy research into isolated contexts and return a compact
  synthesis.
- Start a fresh session for unrelated work.
- Preserve critical decisions in a small canonical document rather than relying
  on a long transcript.

### Decompose by responsibility

| Pattern | Use when | Main benefit |
|---|---|---|
| Single pass | Scope is small and explicit | Lowest coordination overhead |
| Planner and worker | Ambiguity must be resolved before implementation | Expensive reasoning is concentrated |
| Fan-out research | Read-only questions are independent | Parallelism without write collisions |
| Writer and reviewer | Consequential output needs independent verification | Decorrelated error detection |

More agents are not automatically more efficient. Coordination, duplicated
search, merge conflicts, and repeated context can outweigh parallel speed.

### Route models by measured task class

Use the least expensive model that reliably meets the quality bar for a bounded
role. A stronger planner can sometimes reduce total worker spend by producing a
clearer decomposition, but planner price alone is not the metric: a weak plan can
multiply worker turns. Evaluate the complete run.

For a high-volume typed decision, compare [Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev), open [GLiClass](https://github.com/Knowledgator/GLiClass), ordinary structured model output, and deterministic rules on the same labelled cases. [Vercel's form-router example](https://vercel.com/kb/guide/jev-ai-sdk-form-router) shows a classifier with fallback. Measure calibration, abstention, tail latency, total cost, and downstream errors; a well-formed prediction cannot authorize an action or establish source truth. No evidence here establishes that one project copied the other, and a reported OpenAI Decisions API needs a public contract before comparison.

Effort controls also belong in a paired task benchmark. [Anthropic's effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort) makes medium the Opus 5.5 default and says supported per-message effort changes can preserve prompt caching, while a changed top-level setting may invalidate it. Verify the client request shape and actual cache charges before treating that as a general optimization.

## Evaluating token-saving claims

Use this ladder for tools such as prompt compressors, terse-output skills, shell
output filters, repository indexes, and context proxies.

### 1. Define the causal claim

Write down:

- the exact treatment
- which token classes or operations it can affect
- the expected mechanism
- the quality and compatibility risks
- the adoption threshold

Do not accept vague claims such as "saves context." Name the provider billing
metric expected to move.

### 2. Estimate the coverage ceiling for free

Replay representative transcripts and calculate:

- share of calls eligible for treatment
- share of tool-result bytes or tokens eligible
- share of total billed input represented by those results
- provider-side truncation already applied
- cache discounts that reduce the economic value of compression

If a tool touches 20% of tool output and tool output is 20% of billed input, even
perfect compression cannot save 60% of the bill.

### 3. Pre-register endpoints

Primary endpoints:

- paired per-task billed cost
- uncached input plus cache-creation tokens where applicable
- task quality or verifier score

Secondary diagnostics:

- cache reads
- output tokens
- turns and tool calls
- retries and recovery reads
- wall-clock latency
- treatment exposure
- compatibility or setup failures

### 4. Run paired trials

- Pin model, reasoning effort, harness, tool version, task input, and environment.
- Run the same task with and without the treatment.
- Exclude a task from both arms when either arm has an invalid trial, while
  reporting treatment-caused failures separately.
- Instrument whether the treatment actually activated.
- Use per-task paired deltas. Aggregate totals are vulnerable to outliers and
  long-context pricing thresholds.

### 5. Climb an evidence ladder

1. Transcript replay and ceiling estimate
2. One wiring run
3. Small smoke set at one attempt per task
4. The same smoke set with repeated attempts
5. Representative full benchmark
6. Replication across relevant reasoning efforts or models

Never make an adoption decision from one stochastic run. Report uncertainty and
use a paired non-parametric test when the sample supports it.

### 6. Audit the counterfactual

Compare the tool's dashboard with the provider bill. Check whether the tool:

- counts raw output the harness would already truncate
- estimates tokens with a character heuristic
- values cached and uncached tokens equally
- ignores context outside its interception point
- omits retries or extra turns induced by compression

## Research watch: SoL-Pi

[SoL-Pi: Scaling Auto-Research Loops for Efficient Agent Harnesses](https://nvlabs.github.io/SoL-Pi/) is an NVIDIA research lead captured on 2026-10-02. The supplied paper image identifies [arXiv 2609.20519](https://arxiv.org/abs/2609.20519). Public search located the NVlabs project page, but direct retrieval timed out; the full paper, code, ablations, and statistical claims have not been reviewed here. Do not install or fork from the social summary alone.

The supplied abstract reports automated searches over harness mechanisms across repository-derived and verifier-driven environments, retaining four mechanisms: **Action Fusion**, **Online Context Compact**, **ObservationPack**, and **Evidence-Preserving Reducer**. These concern action execution, in-run compaction, observation handling, and delegated reading respectively. On its reported 51-task EdgeBench evaluation, the authors claim 44.7-49.0% less token traffic and about one-third lower API cost relative to the baseline Pi harness. Those are attributed results, not local measurements or guaranteed savings under another provider's caching and pricing.

The displayed figure shows lower average scores for SoL-Pi than baseline Pi in both model comparisons. The authors' assertion of comparable performance therefore needs the actual tolerance, uncertainty, task mix, and per-task outcomes; it is not established by a cost chart. Estimated hourly savings depend on workload and throughput and should not become a budget forecast.

**Disposition:** retain as a high-interest mechanism study, not evidence that everyone should build a harness. Test individual mechanisms against the current implementation only after inspecting the primary paper and code. Apply the paired evaluation procedure above, including compaction evidence loss, extra recovery reads, source attribution, and whether fused actions preserve authorization and inspection boundaries. Never fuse a read and consequential write in a way that bypasses required approval.

## Evidence: Caveman and RTK

JetBrains evaluated both tools using paired SkillsBench runs on pinned Claude Code
configurations. These are vendor-authored studies of third-party tools, not an
independent academic benchmark, but their instrumentation and disclosed methods
are substantially stronger than README savings claims.

### Caveman

- Advertised output-token reduction: 65%.
- JetBrains measured reduction: 8.5%.
- Lesson: forcing terse output can reduce some output, but the advertised local
  reduction did not transfer proportionally to total agent cost.

Do not use a fixed "65%" estimate or claim that terse grammar inherently improves
accuracy. Evaluate concise-output instructions against the actual task and model.

### RTK

RTK rewrites eligible shell commands and compresses their output.

- Transcript replay found only about one third of Bash calls eligible and just
  under 20% of tool-result characters reachable, implying roughly a 3% ceiling
  on input-token savings under the tested workload.
- At low reasoning effort, JetBrains measured a median 7.6% cost increase
  (`p=0.004`), 13.8% more turns, and 14.3% more cache reads.
- At high reasoning effort, measured cost was effectively unchanged (`+0.1%`,
  `p=0.99`).
- Task quality was statistically indistinguishable in both arms.
- RTK reported 96.2 million tokens saved during the low-effort run while the
  measured bill increased. Its counterfactual counted raw output Claude Code
  would truncate and did not price cache behavior like the provider.

**Current decision:** do not adopt RTK. Revisit only if a materially different
harness makes shell output a much larger share of billed input and a paired test
shows end-to-end savings.

## Efficiency checklist

Before shipping an AI configuration or token optimization:

- [ ] The target billing metric and quality bar are explicit.
- [ ] A transcript replay estimates the reachable ceiling.
- [ ] Stable instructions contain no obvious duplication.
- [ ] Detailed tools and references load only when relevant.
- [ ] Research context is isolated when it would pollute implementation.
- [ ] The treatment is instrumented, not assumed.
- [ ] Evaluation uses paired tasks and more than one stochastic attempt.
- [ ] Provider bills are compared with tool-reported savings.
- [ ] Cache reads, turns, retries, latency, and quality are reported.
- [ ] Removal is clean if measured value does not clear the adoption threshold.

## Sources

- JetBrains AI, [Does Speaking to Agents Like Cavemen Really Save 65% of Tokens? We Test](https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/), July 2026.
- JetBrains AI, [Does "rtk" skill really cut agent tokens by 60-90%? We tested it](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/), July 2026.
- Levy et al., *Same Task, More Tokens*, ACL 2024.
- Liu et al., *Lost in the Middle*, TACL 2023.
- EASYTOOL, arXiv:2401.06201, 2024.

## Model routing for coding agents (2026-07 watch)

[Magpie](https://usemagpie.ai/) is a local multi-provider coding-agent interface to compare only when a supported credential path and a measurable routing gap exist. Do not infer that subscription credentials can be pooled safely through an unofficial proxy.

Distinguish **model selection** (choose a cheaper/capable model for the task) from **provider routing** (serve the same model through the cheapest/healthiest host). The latter is mature; the former remains difficult because prompt difficulty is an unreliable proxy for whether an agent loop will succeed. For the current flat-rate Codex subscription, the target is quota longevity, latency, and quality rather than a lower monthly bill.

**Native state:** Claude Code offers a narrow `opusplan` route (Opus for planning, Sonnet for execution), adaptive effort, and per-subagent model controls, but no general Cursor-style prompt router. Codex offers manual Faster/Power/Smarter controls and a fixed default (`gpt-5.6-sol` at medium effort), not prompt-aware automatic model selection. Pi intentionally ships no router; Workbench supplies explicit frontier and private routes. Its former local prompt classifier was removed because visible launcher intent is simpler and more predictable.

- **[pi-auto-router](https://pi.dev/packages/pi-auto-router)** / [source](https://github.com/danialranjha/pi-auto-router) (MIT; v0.2.2; 5 stars; ~154 monthly package downloads; last push Jun 2026) -- The closest drop-in answer for this stack. A Pi extension creates virtual routes over Claude, Codex, Gemini, OpenRouter, Ollama, and other configured targets; classifies prompts with zero-latency heuristics; tracks latency, feedback, budgets, circuit state, and subscription **Utilization Velocity Index**; and can fail over the same request before substantive output. It reads Pi OAuth/quota state, supports `openai-codex`, and has a shadow mode that logs decisions without changing routing. **Verdict: WATCH, with a plausible shadow-only trial.** The exact fit is unusually strong, but the trust surface is total, adoption is tiny, defaults drift quickly, and its heuristic classifier is not yet evidence that routed coding tasks finish more efficiently. Before trialing: source/security review, pin by hash/version, restrict routes to installed subscription models, pre-register quality/quota endpoints, and run shadow mode first.
- **[OpenRouter Auto Beta](https://openrouter.ai/docs/guides/routing/routers/auto-router)** (`openrouter/auto-beta`) -- Easiest pay-per-token option for Pi: classifies prompts into ~30 task types, ranks models using trailing community spend share, applies a 0-10 cost/quality dial, pins model/provider within a session for cache consistency, and charges no router premium beyond the selected model's normal OpenRouter price. Its published benchmark is vendor-reported and only partially coding-shaped. **Verdict: good API-funded experiment, irrelevant to making the existing Codex subscription cheaper.**
- **[LiteLLM Auto Router v2](https://docs.litellm.ai/docs/proxy/auto_routing)** (LiteLLM gateway: 54.7k stars; active Jul 2026; auto-router feature new in v1.94.x) -- Mature self-hosted gateway with a brand-new task router: heuristic, small-LLM, keyword/semantic, and adaptive Thompson-sampling modes plus session affinity. Strong reference architecture for measured routing, but it requires operating a proxy and API-key-funded model pool; it cannot magically pool first-party Claude/Codex subscription entitlements. **Verdict: watch the feature, do not add the gateway for a personal subscription workflow.**
- **[Claude Code Router](https://github.com/musistudio/claude-code-router)** (MIT; 36.2k stars; active Jul 2026) -- Mature local gateway/control plane spanning Claude Code, Codex, provider keys, Kimi Code subscription, retries, credential pools, protocol conversion, logs, and tools. It solves cross-provider plumbing more than reliable task difficulty, and overlaps the intentionally small Pi harness. **Verdict: ecosystem reference, not an adoption candidate.** Do not route first-party subscription OAuth through unofficial wrappers without explicit vendor support and a credential-path review.
- **[RouteLLM](https://github.com/lm-sys/RouteLLM)** (Apache-2.0; 5.3k stars; last push Aug 2024) -- Important research/evaluation framework for learned strong-vs-weak routing, but effectively dormant and aimed at API serving rather than coding-harness subscriptions. Keep as the benchmark-method reference, not software to install.
- **[CodeRouter](https://github.com/Code-Router/CodeRouter)** (MIT; 1 star; created May 2026) -- Claims intent-based routing, worktree execution, learning, and Claude Code/Codex integration, but currently has no adoption evidence and expands into another full orchestrator. **Verdict: ignore until independent usage and evaluation exist.**

**Decision rule:** do not adopt a router because it reports cheaper selected calls. Require paired task completion, retries/turns, prompt-cache behavior, quota consumption, latency, privacy outcomes, and verifier quality. A lower-tier miss that causes one recovery turn can erase the savings. Explicit frontier/private choice is the baseline; automatic routing must demonstrate enough repeated value to justify returning.

- **[LLMLingua](https://github.com/microsoft/LLMLingua)** -- Microsoft's LLM-based prompt-compression library. Compresses long contexts by an order of magnitude while preserving most task accuracy, via a small model that scores token importance. Evaluate when context cost or latency remains a bottleneck after selecting relevant input; measure task quality as well as compression.

- **[Headroom](https://github.com/headroomlabs-ai/headroom)** -- Local proxy/library/MCP layer that samples and deduplicates repetitive JSON/logs, uses an extractive ModernBERT compressor for prose, and keeps originals in a retrieval cache. **Evaluated 2026-07-22: WATCH; do not adopt globally.** The mechanism is real, but the 60-95% headline applies to favorable JSON/log payloads, not ordinary coding-agent traffic. Headroom's own [production telemetry](https://headroom-docs.vercel.app/docs/benchmarks) reports 4.8% median / 11.3% mean compression; its maintainer conceded a realistic 15-20% for coding agents in [#1843](https://github.com/headroomlabs-ai/headroom/issues/1843). One third-party [50-case benchmark](https://github.com/shreyassks/headroom-benchmarks) measured 42% input reduction on synthetic JSON-heavy support-ticket tasks, but did not score final-answer correctness; its small N=100 evals showed GSM8K -1pp, SQuAD exact match -5pp, and unchanged BFCL under a lenient scorer. More seriously, [#2085](https://github.com/headroomlabs-ai/headroom/issues/2085) measured a Claude Code prompt-cache collapse and ~2.5-3x provider-limit burn on v0.31.0; contributors reproduced it and shipped fixes in v0.32.0, but no independent post-fix A/B is published. "Reversible" means lossy prompt transformation plus separate local retrieval, not intrinsically lossless compression. Revisit only after a pinned project-local replay shows lower total billed cost (including cache writes/reads), unchanged task correctness, stable parallel-subagent behavior, and at least 15% net savings. Prefer filtering/pagination at the tool source and provider-native compaction first; explicitly disable Headroom telemetry in any trial.

## Claimed-vs-measured agentic improvements (roster)

Tools/skills marketed as cracking a real agent-efficiency problem (fewer tokens, faster runs, better code), tracked against independent or rigorous first-party measurement. Purpose: only build the stack up with what survives verification, not what markets well. Add an entry whenever a bold efficiency claim gets checked, win or lose.

- **[Ponytail](https://blog.jetbrains.com/ai/2026/07/ponytail-skill-claude-tested/)** (OSS Claude Code skill, MIT, v4.8.4) -- Runs a "does this need to exist / is it already available" decision ladder before code generation ("lazy senior developer" framing); explicitly leaves validation/error-handling/security/a11y untouched. **Claimed**: -54% code, -22% tokens, -20% cost, -27% time. **JetBrains measured** (80 paired tasks, Claude Code + Sonnet 5, Jul 2026): -15.4% code (not significant, p=0.088), **-10.3% cost (statistically solid, p=0.004)**, -11% time, no quality loss. **Verdict: partial survivor, not a null result** -- real effect, but 2-4x smaller than advertised and concentrated almost entirely on larger/over-engineerable tasks (near-zero on lean tasks); a contributor reportedly challenged the authors' own benchmark methodology afterward (InfoQ, Aug 2026). Treat vendor efficiency percentages as a ceiling, not an expectation -- JetBrains' harness-benchmarking spread (10-17 pts from scaffold alone, see the [harness evidence](../harnesses.md#evidence-update-minimum-viable-harness)) is the same discipline: verify the specific number against your own workload before trusting it into the stack.
- **Headroom** -- see full entry above (2026-07-22 evaluation): headline 60-95% compression is real only on favorable JSON/log payloads; own production telemetry shows 4.8% median / 11.3% mean on real traffic, and a v0.31.0 regression 2.5-3x'd provider-limit burn before a fix shipped. Filed here as the template case: self-reported headline number, independent measurement an order of magnitude lower, plus a live regression.
- **Starship prompt** -- see full entry above (2026-06-04 evaluation): not a token/cost claim, but same pattern -- feature set (contextual-safety modules) didn't match this environment's actual surface (no cloud CLIs installed, 0 kube contexts), so the marketed win evaporated on contact with real usage.
