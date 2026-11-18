# Performance tooling

Evaluate replacements against a measured runtime or development bottleneck and preserve application behavior.

## Optimize the user-visible completion path

Uber Eats' 2026 search rebuild is a useful performance method, not a reusable architecture. The team changed its primary metric from backend response time to above-the-fold completion, then removed low-value retrieval, reduced feature hydration, separated ranking data from presentation data, overlapped rendering, hedged selected requests, and reduced serialization and garbage-collection work. The reported 50% end-to-end improvement came from many measured changes rather than one rewrite.

Use the same sequence: measure the user-visible milestone, identify where work and waiting accumulate, remove work before making it faster, start independent work earlier, remove dependencies, and validate every change against the end-to-end metric. Local stage speedups do not count when they fail to improve the user's completion time or damage result quality.

Source: InfoQ, [Uber Eats Rebuilds Search Pipeline to Cut End-to-End Latency by 50%](https://www.infoq.com/news/2026/10/uber-eats-search-latency/), 2026-10-02; figures attributed there to Uber.

## Agent-led performance work on an existing codebase

**Read in full:** Google, [Optimizing a 200,000-line Python codebase overnight with Gemini 4 Argon](https://developers.googleblog.com/optimizing-a-200000-line-python-codebase-overnight-with-gemini-4-argon/), 2026-10-13, reviewed 2026-11-17. The supplied [InfoQ account](https://www.infoq.com/news/2026/10/google-argon-optimizes-adk/), 2026-10-24, is a useful summary, but the primary source exposes important limits.

Google reports six proposals from an 11-hour ADK optimization run and two shipped changes: filter session events before copying them, and defer heavy imports while preserving public attributes and mock compatibility. The agent measured before editing, received repository-specific instructions after an initial attempt, and ran 16,892 public tests. Maintainers still found 25 internal test failures from import changes; the fix preserved patchable attributes. Passing a public suite did not establish full compatibility.

The reported 40% reduction concerns long-session preparation in the in-memory store, not database-backed stores or total inference time. A maintainer-written holdout withheld from the agent used instant model/tool substitutes to isolate framework overhead, with byte-identical model requests and medians of 6–12 runs. Its 158-turn benchmark fell from 65.6 to 56.1 seconds. Imports improved 21%, but new-process time to the first model request stayed flat, 3.07 to 3.09 seconds, because the deferred work returned on the first turn.

The four rejected ideas are especially reusable warnings: a weak-reference cache could return stale data after memory-address reuse; a telemetry fast path depended on a private library attribute; a history-format rewrite worsened readability without holdout improvement; and an event index added state for synthetic-only gains. Do not accept caches, indexes, private-API shortcuts, or rewrites merely because one microbenchmark improves.

For a local trial, choose one measured slow path, hold public behavior and model inputs fixed, create a holdout workload before optimization, and request a patch with benchmarks, regression tests, and rejected alternatives. Keep runtime and spending bounded, isolate execution, and retain human adoption review. Do not introduce an overnight optimization scheduler without repeated useful attended results.

## Uber: production migration versus synthetic benchmark

Two primary engineering posts reviewed 2026-11-17 provide a broader optimization lesson:

- [Velox at Uber: Rebuilding Presto's Execution Engine for Speed and Scale](https://www.uber.com/us/en/blog/velox-at-uber/), 2026-11-10, reports phased migration, correctness comparisons, production-traffic shadowing, fallback routing, and extensive native-process operational work. Its four-day matched-capacity study reports 2.4 times faster average queries and 3.06 times lower CPU use on eligible traffic. Eligibility selection, queueing, and success rates remain part of the comparison, not details to discard.
- [Making Every Core Count: In Pursuit Of Faster Apache Spark Jobs at Uber](https://www.uber.com/us/en/blog/uber-benchmarking-quanton/), 2026-11-05, distinguishes shipped Gluten/Velox changes from a synthetic Quanton write-path evaluation. Its 5.5/4.7 times steady-state speedups exclude metadata-compaction rounds; some stages stayed flat or became slower, and scaling comparisons had only two measured commits per configuration. These are not fleet-wide savings or a reason to add Spark here.

The transferable method is to compare identical work and capacity, preserve correctness and fallback, account for maintenance and excluded phases, and separate production evidence from synthetic opportunity. Faster native execution is valuable only when the full operational cost justifies a second implementation and toolchain.

## Drop-in performance swaps

The recurring pattern: a native (usually Rust) reimplementation of a slow
interpreted tool behind the *same API*, adoptable by swapping an import or
binary. Already-committed swaps live in the stacks docs (ruff, uv, Biome/Oxlint,
fnm); candidates below are watch-only. Evaluation bar: API parity %, independent
(not self-reported) benchmarks, and out-of-beta status.

- **[rustwright](https://github.com/Skyvern-AI/rustwright)** (Skyvern AI, MIT) -- Playwright's API on a native Rust engine speaking CDP directly, eliminating the Node driver subprocess. Claims 2.55x faster / 70% less memory vs playwright-python -- self-reported, "not yet capped-CI evidence" by their own admission. ~96% sync-Python API coverage (515/536 methods); **explicitly early alpha**. Caveats: Chromium-only (Firefox/WebKit error out), Python async wraps the sync engine via threads (≤25 concurrent workflows), cross-origin iframe gaps. Verdict: legit team (Skyvern is the browser-agent company) and honestly-labeled claims, but not production-ready. Import-swap makes trialing cheap -- revisit at beta + independent benchmarks. Would slot under `browser-tooling` if adopted.

## Why a fast query can still finish late

ClickHouse's [32 millisecond latency investigation](https://clickhouse.com/blog/chasing-32ms-tail-latency-clickhouse) separates time to the first result from time to the protocol's end-of-stream marker. In its reproduced customer case, an idle connection's reduced congestion window and many small metadata writes forced an additional network round trip. The congestion window limits unacknowledged data; `TCP_NODELAY` disables the kernel's usual small-write batching, but does not eliminate that limit.

ClickHouse reports that batching the final metadata writes removed the extra delay in its reproduction (reviewed October 17, 2026). The practical diagnostic is to measure first result and full completion separately, reproduce idle periods and network delay, and inspect packet boundaries before assuming query execution is slow.

This is one team's demonstrated failure mechanism, not a universal explanation for latency. Batching must preserve time-sensitive progress messages; each application write does not always become exactly one packet.
