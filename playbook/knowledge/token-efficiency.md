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
