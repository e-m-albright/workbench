# Performance tooling

Evaluate replacements against a measured runtime or development bottleneck and preserve application behavior.

## Optimize the user-visible completion path

Uber Eats' 2026 search rebuild is a useful performance method, not a reusable architecture. The team changed its primary metric from backend response time to above-the-fold completion, then removed low-value retrieval, reduced feature hydration, separated ranking data from presentation data, overlapped rendering, hedged selected requests, and reduced serialization and garbage-collection work. The reported 50% end-to-end improvement came from many measured changes rather than one rewrite.

Use the same sequence: measure the user-visible milestone, identify where work and waiting accumulate, remove work before making it faster, start independent work earlier, remove dependencies, and validate every change against the end-to-end metric. Local stage speedups do not count when they fail to improve the user's completion time or damage result quality.

Source: InfoQ, [Uber Eats Rebuilds Search Pipeline to Cut End-to-End Latency by 50%](https://www.infoq.com/news/2026/10/uber-eats-search-latency/), 2026-10-02; figures attributed there to Uber.

## Drop-in performance swaps

The recurring pattern: a native (usually Rust) reimplementation of a slow
interpreted tool behind the *same API*, adoptable by swapping an import or
binary. Already-committed swaps live in the stacks docs (ruff, uv, Biome/Oxlint,
fnm); candidates below are watch-only. Evaluation bar: API parity %, independent
(not self-reported) benchmarks, and out-of-beta status.

- **[rustwright](https://github.com/Skyvern-AI/rustwright)** (Skyvern AI, MIT) -- Playwright's API on a native Rust engine speaking CDP directly, eliminating the Node driver subprocess. Claims 2.55x faster / 70% less memory vs playwright-python -- self-reported, "not yet capped-CI evidence" by their own admission. ~96% sync-Python API coverage (515/536 methods); **explicitly early alpha**. Caveats: Chromium-only (Firefox/WebKit error out), Python async wraps the sync engine via threads (≤25 concurrent workflows), cross-origin iframe gaps. Verdict: legit team (Skyvern is the browser-agent company) and honestly-labeled claims, but not production-ready. Import-swap makes trialing cheap -- revisit at beta + independent benchmarks. Would slot under `browser-tooling` if adopted.
