# Tools to Evaluate

Bookmarked tools and services worth investigating.

> **Graduated into `playbook/stacks/` (2026-06):** several categories that were "evaluate" now have committed picks. Supply-chain & secrets → [`stacks/security.md`](stacks/security.md) (gitleaks, OSV-Scanner, cargo-deny/pip-audit/govulncheck, Renovate, Socket). Durable execution & realtime sync → [`stacks/services.md`](stacks/services.md) (DBOS, Temporal, River, Inngest; ElectricSQL). Eval-in-CI → [`knowledge/ai-tools.md`](knowledge/ai-tools.md) (promptfoo, pydantic-evals, DeepEval alongside Langfuse/Logfire). Test/perf tooling → language READMEs (cargo-nextest, insta, Polyfactory, schemathesis, mutmut, CodSpeed). Dev-env → [`stacks/infrastructure.md`](stacks/infrastructure.md) (mise, Caddy, Bruno, Hurl, git-cliff, Mermaid). The enforcement layer (ratchets, CI structure, affectedness) → [`knowledge/engineering-gates.md`](knowledge/engineering-gates.md). Items below remain genuinely unadopted / watch-only.

## Security / Static Analysis

- **[Semgrep](https://semgrep.dev)** -- Pattern-based SAST/SCA/secrets platform unifying static analysis with AI reasoning to detect IDORs, broken authz, and other logic-level vulnerabilities. Lightweight grep-like custom rule syntax plus reachability analysis (vendor claims 98% false-positive reduction). OSS Community Edition (free, self-hostable) plus SaaS AppSec Platform. Evaluate when you want fast SAST/secrets coverage with custom rules in CI without standing up a heavy platform.
- **[SonarQube](https://www.sonarsource.com/products/sonarqube/)** -- Code quality and security analysis covering 40+ languages with bug/vulnerability/code-smell detection. Quality Gates enforce deployment standards; SonarLint feeds the same rules into the IDE. Community Build OSS; Team plan ~$32/mo; Enterprise custom. Evaluate when you want enterprise-grade quality gates and broad language coverage across IDE + CI, especially for AI-generated code review.

## CI / CD

- **Blacksmith vs Depot** -- both are drop-in replacements for GitHub Actions runners with ~2-10x speed/cost claims. **Blacksmith** ([blacksmith.sh](https://blacksmith.sh)) leans bare-metal gaming-CPU hardware + Docker layer cache on NVMe; 60-75% cost reduction vs GHA; 3,000 free minutes/month. **Depot** ([depot.dev](https://depot.dev)) has a wider product surface (remote BuildKit, distributed cache, programmable CI engine, Build API) and per-second billing; claims 10x faster workflows / 40x faster Docker builds. **Recommendation**: try Depot first (broader surface, mature cache story); benchmark Blacksmith for raw runner speed on Docker-heavy pipelines.
- **[Depot](https://depot.dev)** -- Remote Docker builder + GHA runners + distributed remote cache + programmable CI engine. Claims ~30% faster CPUs and 10x networking on runners; per-second billing; unrestricted concurrency. Evaluate when Docker builds or GHA runtime are the bottleneck.
- **GitHub Actions paid runners** ([github.com/features/actions](https://github.com/features/actions)) -- Baseline. Free on public repos; private repos billed per-minute by runner class. macOS and large runners are the cost driver that motivates Depot/Blacksmith/Namespace.
- **[CircleCI](https://circleci.com)** -- Mature CI/CD now branding as "autonomous validation" with test intelligence and rollback pipelines. Chunk Agent claims 97% faster test runs; MCP server for AI-driven failure diagnosis. Freemium credit-based pricing; cloud/hybrid/on-prem. Startup program offers up to $20k credits. Evaluate for large team / complex matrix needing strong test parallelization.
- **[Semaphore](https://semaphoreci.com)** -- Cloud CI/CD positioned explicitly on speed -- vendor benchmarks claim 94% faster than GHA at ~$0.04/job vs GHA's ~$0.06. OSS Community Edition (self-hostable) plus pay-as-you-go cloud. Evaluate for performance-sensitive pipelines where managed beats self-hosted.
- **[Buildkite](https://buildkite.com)** -- Hybrid model: SaaS control plane, BYO agents. **Yes, you can use a local machine as a runner** -- that's the core model. Agents run anywhere (laptop, server, K8s, GPU, on-prem). Per-user pricing on self-hosted agents (not per-minute). Hosted Mac/Linux agents are an add-on. Evaluate when you need SaaS orchestration over specific hardware (GPUs, secured networks, your own laptop).

### Build Infra

- **[Docker BuildKit](https://github.com/moby/buildkit)** -- Modern Moby builder backend; concurrent, cache-efficient, Dockerfile-agnostic. Default since Docker Engine 23.0. Powers Depot, Blacksmith, Namespace under the hood. Worth understanding directly when tuning cache strategy or going rootless.
- **[Docker buildx](https://docs.docker.com/build/buildkit/)** -- Docker CLI plugin exposing BuildKit features; the `docker buildx` command. First-class multi-arch builds (`linux/amd64` + `linux/arm64` in one command) and remote builder connections. Bundled with Docker Desktop.
- **[Namespace](https://namespace.so)** -- Developer infra: fast GHA/GitLab runner replacements + isolated cloud Devboxes + remote caching for Docker/Bazel/Turbo/Nix. Sub-second (~900ms) instance boot. Broader cache coverage than Depot (Bazel/Turbo/Nix in addition to Docker) plus Devboxes for AI coding agents. Evaluate if you want CI acceleration plus on-demand cloud workspaces for agents.

## Git Hosting

- **[Codeberg](https://codeberg.org)** -- Non-profit git hosting (Codeberg e.V., Berlin) on the OSS Forgejo platform. Community-governed, EU-hosted, no tracking/ads/data sale. Built-in CI and Pages. Free (donations / membership). Evaluate for hosting OSS outside big tech or for EU data residency with a non-commercial ethos.
- **[GitLab](https://about.gitlab.com)** -- Single-platform DevSecOps: git + CI/CD + planning + integrated SAST/SCA/secrets/DAST + AI agents (GitLab Duo). OSS Community Edition (self-hosted) plus SaaS at gitlab.com. Premium/Ultimate paid tiers; Ultimate adds the security suite. Evaluate when you want a one-vendor full stack with strong self-hosted story or built-in security/compliance reporting.
- **[Sourcehut](https://sr.ht)** -- Minimalist OSS forge by Drew DeVault: git/Mercurial, mailing lists, issue tracking, CI, wikis, chat -- email-driven workflows. No JavaScript required, no tracking, no AI features; patches via `git send-email`. Paid subscription supports the project; still public alpha. Evaluate for maximum data portability and terminal/email-native workflow.

## Code Review

- **[CodeRabbit](https://coderabbit.ai)** -- AI PR review with 40+ linter/security-scanner integrations plus IDE + CLI review modes. Codegraph-based codebase understanding; learns from natural-language feedback. SaaS per-seat; SOC 2 Type II, zero data retention. 15k+ customers. Evaluate for broad-coverage AI review with high configurability via YAML.
- **[Greptile](https://www.greptile.com)** -- (User likely meant this; "Reptile" is not a code-review tool.) AI code-review agent that builds a graph index of the codebase and runs parallel agents to review PRs with full repo context. Benchmarks claim it flags more critical bugs than major competitors. Used by Stripe, Amazon. **Confirm: is Greptile what you meant by "Reptile"?**
- **[Graphite](https://graphite.com)** -- Code-review platform built around **stacked PRs** (no other vendor really competes here) plus Diamond AI review and a stack-aware merge queue. CLI + VS Code extension. Per-seat paid tiers. Evaluate if the team hits review bottlenecks on large PRs and you want to adopt stacked-diff workflow.
- **[Cursor BugBot](https://cursor.com/bugbot)** -- Cursor's AI PR-review bot, tuned for high signal-to-noise on logic bugs (not style); vendor claims >50% of flags get fixed pre-merge; strong on AI-generated code. Customizable via BugBot Rules. Evaluate if already in Cursor's ecosystem.
- **[Claude Code Review (GitHub Action)](https://github.com/anthropics/claude-code-action)** -- Anthropic's official Action that runs Claude Code on PRs to post inline comments on logic, security, edge cases, regressions. Same engine as local Claude Code; fleet of specialized agents; `/security-review` slash command; severity-tagged but non-blocking. Install via `/install-github-app` from Claude Code. **Announcement**: [claude.com/blog/code-review](https://claude.com/blog/code-review) -- internally raised substantive PR comments from 16% to 54%. Pay Anthropic API + CI minutes.
- **[Macroscope](https://macroscope.com)** -- AI code review + engineering-intelligence platform (PR bug detection, commit/status summaries, Slack/GitHub agent for engineering Q&A). AST-based graph analysis (not embeddings); learns from accepted vs rejected comments; explicitly does not train on user code. Usage-based pricing ($0.05/KB review, $0.05/commit status). **Caveat**: user-reported "exact strength for Python/TypeScript/Go" is **not corroborated by the homepage** -- no published language list. Confirm via demo before evaluating on that basis.

> **Strategic consideration**: an alternative to picking one is a **homegrown AI review scaffold** -- Claude Code Action + strict static checkers (Ruff, mypy, ESLint, golangci-lint, Semgrep) that emit graded reports and block CI. Custom rubric, no per-seat lock-in, lives in your repo. Worth a spike before committing to a SaaS code-review vendor for 12+ months.

### Additional AI code review entries

- **[Qodo](https://qodo.ai)** (formerly CodiumAI) -- Enterprise pick for large monorepos. Built on the OSS [PR-Agent](https://github.com/qodo-ai/pr-agent). monday.com prevents 800+ issues/month at 73.8% suggestion-acceptance. Configurable rule system, indexes many repos. PR-Agent is self-hostable for air-gapped/private deploys.
- **[GitHub Copilot Code Review](https://github.blog/changelog/copilot-code-review/)** -- Native, zero-setup, included with Copilot subscription. GA April 2025, 1M users in first month. The "if you already pay for Copilot, turn it on" option.
- **[CodeAnt AI](https://www.codeant.ai/)** -- Line-by-line review + security scanning + DORA tracking. 30+ languages.
- **[Panto AI](https://panto.ai/)** -- DevSecOps flavor: secrets + dependency + IaC + code review in one workflow. Compliance-heavy environments.
- **[Sourcegraph Cody](https://sourcegraph.com/cody)** -- Code-aware Q&A and review hints across very large codebases. Pair with, not replace, dedicated PR reviewers.
- **[Augment Code](https://www.augmentcode.com/)** -- VC-darling for enterprise monorepos; indexes hundreds of services. Evaluate for very large polyglot codebases.
- **[Codacy](https://www.codacy.com/)** -- Predominantly rule-based with AI layered on. Multi-language quality gates.
- **[Snyk Code](https://snyk.io/product/snyk-code/) / [Semgrep](https://semgrep.dev)** -- Security-specialized scanners (Semgrep already tracked under Security/Static Analysis). Run alongside, not instead of, an AI reviewer.
- **[Qodana (JetBrains)](https://www.jetbrains.com/qodana/)** -- IDE/CI parity for JetBrains shops.
- **[GitLab Duo](https://about.gitlab.com/gitlab-duo/)** -- GitLab-native review. Solid if you're on GitLab.
- **Devlo / Atlassian Rovo** -- Newer entrants inside Bitbucket/Jira ecosystems.

## Web / Frontend

- **[AI interface design tools](knowledge/ai-interface-design-tools.md)** -- Current design-first generators, editable canvases, code-aware bridges, app builders, free evaluation paths, and an anti-anchoring trial protocol. The present first-round set is UX Pilot, Flowstep, Banani, Superdesign, Google Stitch, and the Figma design agent; Paper, pen.dev, and Magic Patterns are the strongest second-round canvases. Re-check the dated landscape before a trial rather than copying its volatile pricing into this watchlist.
- **[Zero (Rocicorp)](https://zero.rocicorp.dev/)** -- General-purpose sync engine for local-first apps. Instant local reads + server reconciliation; optimistic mutations with built-in conflict resolution. Pitch: "absurdly fast" UI because data is already on-device. Worth evaluating for any product where perceived latency dominates (especially LLM-backed UIs where the model call is slow). See Scott Tolinski's video ([YouTube](https://www.youtube.com/watch?v=aV6aM3R74AQ)) for the practitioner take.
- **[Storybook](https://storybook.js.org/)** -- Component workshop / dev environment for UI components in isolation. The de facto standard for design-system documentation, visual regression testing, and component-level interaction testing. Evaluate when component count crosses ~30 and review-by-screenshot becomes a bottleneck. Pairs naturally with Chromatic for visual diffing.
- **[Framer Motion](https://www.framer.com/motion/)** -- React animation library with a declarative API (`motion.div` + `animate` / `initial` / `exit` props). The mainstream choice for "we need animations beyond CSS transitions but don't want to wire up GSAP." Strong gesture support (drag, pan, hover) and layout animations. Evaluate for any UI where motion telegraphs state changes (loading, success, list reorder).
- **[Base UI](https://base-ui.com/)** -- Unstyled, accessible React component primitives from the team behind Radix UI and Material UI. Headless: you bring the styles. Successor / sibling to Radix Primitives. Evaluate when building a custom design system and want correctness (a11y, keyboard, focus management) without inheriting visual opinion. Likely default over Radix for new projects in 2026.
- **[TanStack](https://tanstack.com)** -- Type-safe data fetching, routing, forms. Evaluate for replacing ad-hoc React data layer.
- **[Vite+](https://voidzero.dev/posts/announcing-vite-plus-beta)** -- Beta unified Node/Vite toolchain. Technically credible, but overlaps Deno, fnm, Just, Biome, and framework checks; reconsider at 1.0 or for a genuinely Node-centric Vite monorepo.
- **[Vite Task](https://viteplus.dev/guide/run)** -- Interesting automatic input tracking, caching, and dependency ordering, currently coupled to the Vite+ control plane. Watch until a real monorepo need exceeds Just.
- **[Oxfmt](https://oxc.rs/blog/2026-02-24-oxfmt-beta)** -- Fast Prettier-compatible formatter, still beta. Keep Deno native formatting and Biome as defaults.
- **[Leptos](https://leptos.dev)** -- Rust full-stack web framework. Evaluate for Rust-heavy teams.
- **[Dioxus](https://dioxuslabs.com/)** -- Rust full-stack crossplatform app framework (web, desktop, mobile). Alternative to Leptos; evaluate when a single Rust codebase needs to ship to multiple platforms.
- **Enhance** -- Backend-first web framework. Read: [How To Build an App With Enhance](https://thenewstack.io/how-to-build-an-app-with-enhance-a-backend-first-framework/).
- **[Astryx](https://astryx.atmeta.com/)** (Meta, beta 2026) -- OSS design system: React + StyleX, 160+ accessible themeable components, dark mode, CLI scaffolding + theme generation. Grown internally at Meta for 8 years; claims 13k+ apps. The notable part for us: **"agent ready" is a first-class pitch** -- agent-oriented docs plus an MCP server, i.e. a design system built to be *consumed by coding agents*, not just humans. Tension: React-coupled, so per our classifier it's a skip for the Svelte stack -- evaluate for any React surface, and **study it as the reference pattern for agent-ready component docs/MCP regardless of framework**.

## Managed browser automation and portal integrations

These are application-layer platforms for turning legacy healthcare portals into reliable workflows or APIs, not general replacements for the local Playwright plus Agent Browser stack. Track them as category references when a product must operate authenticated, API-less systems at production scale.

- **[Asteroid](https://asteroid.ai/)** -- Managed integration platform for EHRs, payer portals, registries, and desktop applications, with a catalogue of existing healthcare connectors and human oversight for difficult runs. Its current positioning is HIPAA-compliant healthcare integration rather than horizontal browser infrastructure. **Verdict: watch as the managed API-over-legacy-portals option.** Evaluate when regulated portal coverage, credential handling, and operational review would otherwise require building an internal browser-automation service.
- **[CloudCruise](https://cloudcruise.com/)** / [Run API](https://docs.cloudcruise.com/run-api/start-a-run) -- Managed healthcare browser automation with an agent-assisted workflow builder, reusable parameterized scripts, self-healing execution, webhooks, delegated authenticated users, and dry runs. **Verdict: watch as the workflow-runtime option.** Evaluate when a product needs repeatable payer or EHR workflows behind an API and compare its generated-script maintainability and failure recovery directly with deterministic Playwright.

**Decision rule:** do not add either to the standing coding-agent stack. For generic cloud-browser infrastructure, compare Browserbase, Anchor, Kernel, and Steel; for local exploration and regression coverage, keep Agent Browser and Playwright. Revisit Asteroid or CloudCruise only for a concrete legacy-portal integration workload where managed authentication, compliance, and run operations justify a vendor dependency.

## Drop-in performance swaps

The recurring pattern: a native (usually Rust) reimplementation of a slow
interpreted tool behind the *same API*, adoptable by swapping an import or
binary. Already-committed swaps live in the stacks docs (ruff, uv, Biome/Oxlint,
fnm); candidates below are watch-only. Evaluation bar: API parity %, independent
(not self-reported) benchmarks, and out-of-beta status.

- **[rustwright](https://github.com/Skyvern-AI/rustwright)** (Skyvern AI, MIT) -- Playwright's API on a native Rust engine speaking CDP directly, eliminating the Node driver subprocess. Claims 2.55x faster / 70% less memory vs playwright-python -- self-reported, "not yet capped-CI evidence" by their own admission. ~96% sync-Python API coverage (515/536 methods); **explicitly early alpha**. Caveats: Chromium-only (Firefox/WebKit error out), Python async wraps the sync engine via threads (≤25 concurrent workflows), cross-origin iframe gaps. Verdict: legit team (Skyvern is the browser-agent company) and honestly-labeled claims, but not production-ready. Import-swap makes trialing cheap -- revisit at beta + independent benchmarks. Would slot under `browser-tooling` if adopted.

## CMS / Content

- **[EmDash CMS (Cloudflare)](https://www.producthunt.com/products/emdash-cms)** -- TypeScript CMS positioned as WordPress alternative. On our platform already.
- **[Payload CMS on Cloudflare Workers](https://blog.cloudflare.com/payload-cms-workers/)** -- Full-fledged CMS running entirely on Cloudflare's stack.
- **[MarkdownCMS](https://markdowncms.netlify.app/)** + **[waynesutton/markdown-site](https://github.com/waynesutton/markdown-site)** -- Lightweight markdown-driven sites.

## CLI Libraries

- **[Ink](https://github.com/vadimdemedes/ink)** -- React renderer for terminal UIs by Vadim Demedes; uses Yoga flexbox so you write CLIs with the same component model as the web. **Battle-tested**: powers Claude Code, GitHub Copilot CLI, Gemini CLI, Wrangler, Shopify CLI, Prisma. OSS (MIT), 38.4k stars. Evaluate for any non-trivial Node/TS CLI with interactive UI. Maintainer policy: fully AI-generated PRs are rejected.

## Terminal Stack

> Host installation state is owned by the dotfiles package manifest. This section records evaluation posture, including installed tools that may now be retirement candidates.

- **[Warp](https://www.warp.dev/)** -- Terminal explicitly designed for **multi-agent dev**. Supports Codex, OpenCode, Gemini CLI as first-class threads with vertical tabs, configurable per-agent metadata (branch, worktree, PR), unified notification center. Send inline comments/snippets/files directly to a running agent session. Evaluate when juggling multiple Claude Code instances across worktrees becomes painful in plain Ghostty.
- **[Yazelix](https://github.com/luccahuguet/yazelix)** -- Reproducible terminal IDE bundling **Yazi + Zellij + Helix** with an AI-aware layout. No longer an aspiration: the Zellij layer has not earned regular use, so adding a larger terminal-IDE bundle would compound the wrong surface.
- **[Zellij](https://zellij.dev/)** -- **Retired 2026-08-26.** Its web client, layouts, multiplayer attachment, and serialized resurrection were not used. Paseo owns agent continuity and the phone experience; there is no remaining phone-shell requirement.
- **tmux** -- **Retired 2026-08-26.** Do not introduce a terminal multiplexer without a demonstrated local process-continuity need. It is not part of the Paseo mobile path.
- **[Atuin](https://atuin.sh/)** -- Command history in SQLite with full-screen fuzzy search on the up-arrow + cross-machine sync. Evaluate as a `Ctrl-R` upgrade.
- **[Lazygit](https://github.com/jesseduffield/lazygit)** -- TUI for git, faster than CLI for hunk staging, rebasing, diffs. **Especially valuable alongside AI agents** -- file-level diff view gives precise control over every AI-touched line before committing.
- **[Lazydocker](https://github.com/jesseduffield/lazydocker)** -- Same TUI pattern for containers.
- **[Btop](https://github.com/aristocratos/btop)** -- Prettier, faster htop replacement.
- **[eza](https://eza.rocks/)** -- `ls` with git status, icons, tree mode. Successor to `exa`.
- **[bat](https://github.com/sharkdp/bat)** -- `cat` with syntax highlighting + git markers; doubles as a pager for other tools (`--pager`).
- **[delta](https://github.com/dandavison/delta)** -- Git's diff viewer rewritten: side-by-side, syntax highlighting, proper word-level highlights.
- **[difftastic](https://difftastic.wilfred.me.uk/)** -- **Structural (AST-based) diffs** that ignore reformatting noise. Devastating once you try it on a refactor PR.
- **[Starship](https://starship.rs/)** -- Fast cross-shell prompt surfacing git, k8s context, exec time, language versions. Cross-platform.

> **Starship — EVALUATED 2026-06-04, WATCH (not adopting).** Hands-on trial: installed, built a config mirroring the hand-rolled `amuse` zsh theme *exactly*, then a "personality" config (language/tool versions, `❯`, ops modules). Verdict: marginal value for this workflow. The features that justify the dependency are contextual-safety modules that stay **dark** here — no `aws`/`gcloud`/`terraform` installed, **0** kube contexts, **1** SSH host. Language versions are low-signal when you don't juggle toolchains, and the daily prompt is near-identical to what's already hand-rolled in `shell/amuse.zsh-theme`. Async git is the only real engine win and a decently big polyglot work repo didn't hitch. **Revisit if** the workflow shifts to multi-cluster / multi-account ops (`⎈ context`, `☁ aws-profile` are genuine prod-safety wins) or many remote shells (hostname-on-SSH). **Spin-off win banked regardless:** the A/B drove real `amuse` upgrades — richer git (ahead/behind, staged/unstaged/untracked counts), command duration, exit codes, and worktree / `cc:` profile context. Uninstalled; trial configs removed.
- **[sesh](https://github.com/joshmedeski/sesh)** -- **Rejected with the tmux retirement.** A picker around a multiplexer has no job when the underlying multiplexer has no job. Revisit only if tmux first earns a concrete local continuity workflow.
- **[fish](https://fishshell.com/)** -- Shell with sane defaults + autosuggestions without a plugin manager. Alternative to zsh+plugins.

## Editors / Terminals

- **[Zed editor](https://zed.dev)** -- Modern editor written in Rust, GPU-accelerated rendering. Open-sourced Jan 2024. Positions as a native-performance alternative to Cursor/VS Code -- the tradeoff is a smaller extension ecosystem (no VS Code Marketplace). Built-in real-time collaborative editing ("channels") and an agentic AI edit mode. Worth a side-by-side with Cursor specifically for Python work given recent LSP investment; less compelling if our Cursor extension setup is load-bearing. Python, Markdown, LSP-first. Reading: [Making Python in Zed Fun](https://zed.dev/blog/making-python-in-zed-fun), [Settings UI rebuild](https://zed.dev/blog/settings-ui).
- **[Ghostty 1.3.0](https://www.xda-developers.com/ghostty-13-terminal-makes-finding-your-previous-commands-a-ton-easier/)** -- Modern terminal. Improved previous-command search.

## Runtimes / Languages

- **[Pyodide](https://thenewstack.io/run-real-python-in-browsers-with-pyodide-and-webassembly/)** -- Real Python in the browser via WebAssembly.
- **[Python 3.14 Lazy Annotations](https://realpython.com/python-annotations/)** -- New deferred-evaluation annotations behavior. Check impact on our typing patterns.
- **[Zig](https://ziglang.org)** -- Systems language positioned between Rust (safety-first, borrow checker) and C (minimal, unsafe): no hidden control flow, no hidden allocations, explicit memory management without a borrow checker. Excellent cross-compilation -- `zig cc` works as a drop-in C cross-compiler even if you never write Zig. Smaller ecosystem than Rust; language still pre-1.0 and evolving. Worth exploring for performance-critical tooling where Rust's safety discipline feels like overhead, or as a gentler C-replacement for embedded/systems work.
- **[uvloop](https://github.com/MagicStack/uvloop)** -- Drop-in replacement for the default Python `asyncio` event loop, built on libuv. Roughly 2-4x faster on typical async workloads; one-line install (`import uvloop; uvloop.install()`). The right default for any Python service that's I/O-bound (HTTP clients, WebSocket servers, LLM call fanout). Already a transitive dep of uv/uvicorn-fast-path. See also [[Knowledge/Software-Engineering/Architecture-Patterns]] for why this fits the 12-factor "stateless processes" tier.
- **[Granian](https://github.com/emmett-framework/granian)** -- Rust-based PSGI/ASGI/WSGI HTTP server for Python. Alternative to uvicorn/gunicorn with lower overhead and built-in support for HTTP/1, HTTP/2, and WebSockets. Evaluate as the production runner for FastAPI services where uvicorn's overhead becomes measurable (see the FastAPI vs Fiber benchmark -- Granian narrows the gap with Go). Drop-in for most ASGI apps.

## Data

- **[DuckDB WebAssembly](https://www.infoq.com/news/2026/01/duckdb-iceberg-browser-s3/)** -- Query Iceberg datasets in the browser.
- **[Turso](https://thenewstack.io/why-we-created-turso-a-rust-based-rewrite-of-sqlite/)** -- Rust rewrite of SQLite. Edge-native.
- **[MotherDuck semantic layer for DuckDB](https://motherduck.com/blog/semantic-layer-duckdb-tutorial/)** -- Semantic layer tutorial.
- **[Pandera](https://github.com/unionai-oss/pandera)** -- Declarative schema validation for dataframes (pandas, Polars, PySpark, Modin, Dask). Pydantic-style `DataFrameModel` class API plus statistical hypothesis checks. The right default for validating ETL boundaries and the contract between untrusted input and downstream analytics. Catches schema drift at the boundary instead of through defensive code in pipeline logic.
- **[Polars Cloud](https://cloud.pola.rs/)** -- Managed serverless Polars compute. Same Polars API runs on a laptop or scales across distributed clusters; pay-per-second, no idle charges. AWS now, GCP/Azure planned. Worth tracking when a pandas/Polars pipeline outgrows a single machine but a full Spark cluster is overkill.
- **[TigerBeetle](https://tigerbeetle.com/)** -- Purpose-built double-entry accounting database (Zig): accounts + transfers as fixed 128-byte immutable records, ~1M transfers/sec, strict serializability, Viewstamped Replication, famously rigorous deterministic simulation testing ("VOPR"). Evaluate only if ever moving actual money at volume -- it is not a general database (no SQL, no arbitrary tables) and its immutability is operational, not cryptographic, so it is **not** an audit-log substrate (evaluated 2026-08: for "prove person X accessed data Y", a hash-chained table + external anchoring wins; see the audit-logging cluster below). The deterministic-simulation testing culture is worth studying regardless.

### Tamper-evident audit logging (2026-08 research spike)

For "prove person X accessed data Y" product features (HIPAA-credible access trails). Key insight: the crypto structure is cheap -- nearly all the security comes from anchoring periodic checkpoints *outside* the operator's control (customer-held, RFC 3161 timestamp authority, public transparency log, or object-locked storage in a separate account). Cryptographic proof is never regulator-required (HIPAA/SOC 2 are technology-neutral); it is a differentiator and a forensics asset. Recommendation ladder: (1) MVP ~1 week -- hash-chained INSERT-only Postgres/SQLite table + signed nightly checkpoints to S3 Object Lock compliance mode in a separate account (+ pgaudit for out-of-band DBA access); (2) customer-verifiable -- Merkle tree via Tessera, checkpoints published to customers and anchored to public Rekor; (3) auditor-grade -- witnessed per-tenant logs, only when HITRUST/contract demands it. Full survey with regulation citations lives in the private notes wiki (`audit-logging`).

- **[Tessera](https://github.com/transparency-dev/tessera)** -- Trillian's successor for verifiable append-only logs (tile-based, Certificate-Transparency lineage). GA v1.0.x, very active (as of 2026-08). Embeddable Go library, backends from POSIX files to S3/Aurora/Spanner. The OSS pick when inclusion/consistency proofs become a product feature. (Trillian v1 itself: maintenance mode, don't start new logs on it.)
- **[Sigstore Rekor v2](https://github.com/sigstore/rekor-tiles)** -- Public signature-transparency log, rebuilt on Tessera, GA (as of 2026-08). Pattern worth stealing even outside supply-chain: anchor your own log's checkpoint hashes into the public instance as free, operator-independent existence proofs (hashes only -- never sensitive payloads).
- **[immudb](https://github.com/codenotary/immudb)** -- Immutable KV/SQL DB with built-in Merkle proofs + client-side verification. Alive (v1.11.x, 2026) but single-vendor with historically gappy cadence; proofs-without-building-them, risky as a sole system of record.
- **[pgaudit](https://github.com/pgaudit/pgaudit)** -- Postgres session/object audit to the server log; actively maintained per PG major. Complement to an app-level audit table (it catches out-of-band DBA access; the app table carries business meaning). Available on RDS/Aurora/Cloud SQL.
- **Retired/risky**: AWS QLDB shut down 2025-07-31 (AWS's own migration guidance is trigger-based hash chaining on Aurora PostgreSQL); Pangea Secure Audit Log acquired by CrowdStrike (roadmap risk); Azure SQL Ledger is the best managed option iff already on Azure/MSSQL.

## Infra / DevOps

- **[OpenTelemetry "Demystifying OpenTelemetry" guide](https://www.infoq.com/news/2026/02/opentelemetry-observability/)** -- New OTel intro guide worth skimming before our next observability rollout.

## Kubernetes / GitOps

> Not currently using Kubernetes. Evaluate as a group when a project outgrows Fly/Railway/Cloudflare Workers or needs multi-region orchestration beyond what PaaS offers. These tools travel together -- adopt as a set if at all.

- **ArgoCD** -- GitOps continuous delivery for Kubernetes. Declarative, git-driven deployments reconciled from a repo. Evaluate against **Flux** (lighter, CNCF-graduated) and **Rancher Fleet** (multi-cluster focus).
- **Helm** -- De facto package manager for Kubernetes ("apt for k8s"). Charts templatize manifests. Widely used but criticized for Go-template complexity; watch **Kustomize** (overlays, no templating) and **Kluctl** as alternatives depending on preference for templating vs. patching.
- **[Fly Kubernetes](https://fly.io/docs/kubernetes/)** -- Managed k8s on Fly's edge network. Lower ops burden than EKS/GKE. Compelling if we outgrow Fly Machines but want to stay on Fly.
- **kubectl / k9s** -- Canonical CLIs. `kubectl` is the control-plane client; `k9s` is a TUI dashboard. Install via Homebrew when k8s becomes real -- not before.
- **Consider also**: **Tilt** / **Skaffold** (inner dev loop), **cert-manager** (TLS automation), **external-secrets** (pulls secrets from Vault/AWS/etc. into k8s).

## AI / Dev Workflow

- **[OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/main/docs/workflows.md)** -- Spec-driven dev workflow (Fission-AI). See also: [[Knowledge/Software-Engineering/Spec-Driven-Development]].
- **[Open-WebUI Open Terminal](https://github.com/open-webui/open-terminal?ref=console.dev)** -- Terminal from the Open-WebUI project.
- **[Microsoft FARA](https://github.com/microsoft/fara)** -- Microsoft agentic framework. Check positioning vs. Semantic Kernel / AutoGen.
- **[Browserbase](https://www.browserbase.com/)** -- Managed headless-browser infrastructure built for AI agents. Run Playwright/Puppeteer at scale without provisioning Chromium yourself; includes session recording, stealth/anti-bot handling, and proxy management. Evaluate for any agent workflow that needs to drive a real browser (form filling, scraping, web-based tool use). Likely cheaper and more reliable than rolling our own browser pool.
- **[Sandcastle](https://github.com/mattpocock/sandcastle)** -- TypeScript library for orchestrating "AFK" (away-from-keyboard) coding agents in isolated sandboxes. Workflow: front-load context via a grilling session with the human, then delegate execution to a sandboxed environment where the agent runs tests and fixes bugs autonomously. Pairs with vertical-slice TDD and markdown Kanban boards as agent state. Worth evaluating once we have a workflow that hits the "I trust this agent to run for an hour unattended" bar. See [Matt Pocock's video](https://www.youtube.com/watch?v=E5-QK3CDVQM).

### Model routing for coding agents (2026-07 watch)

Distinguish **model selection** (choose a cheaper/capable model for the task) from **provider routing** (serve the same model through the cheapest/healthiest host). The latter is mature; the former remains difficult because prompt difficulty is an unreliable proxy for whether an agent loop will succeed. For the current flat-rate Codex subscription, the target is quota longevity, latency, and quality rather than a lower monthly bill.

**Native state:** Claude Code offers a narrow `opusplan` route (Opus for planning, Sonnet for execution), adaptive effort, and per-subagent model controls, but no general Cursor-style prompt router. Codex offers manual Faster/Power/Smarter controls and a fixed default (`gpt-5.6-sol` at medium effort), not prompt-aware automatic model selection. Pi intentionally ships no router; Workbench now supplies explicit frontier/private/auto modes, a local classifier, fail-closed behavior, and sticky private sessions.

- **[pi-auto-router](https://pi.dev/packages/pi-auto-router)** / [source](https://github.com/danialranjha/pi-auto-router) (MIT; v0.2.2; 5 stars; ~154 monthly package downloads; last push Jun 2026) -- The closest drop-in answer for this stack. A Pi extension creates virtual routes over Claude, Codex, Gemini, OpenRouter, Ollama, and other configured targets; classifies prompts with zero-latency heuristics; tracks latency, feedback, budgets, circuit state, and subscription **Utilization Velocity Index**; and can fail over the same request before substantive output. It reads Pi OAuth/quota state, supports `openai-codex`, and has a shadow mode that logs decisions without changing routing. **Verdict: WATCH, with a plausible shadow-only trial.** The exact fit is unusually strong, but the trust surface is total, adoption is tiny, defaults drift quickly, and its heuristic classifier is not yet evidence that routed coding tasks finish more efficiently. Before trialing: source/security review, pin by hash/version, restrict routes to installed subscription models, pre-register quality/quota endpoints, and run shadow mode first.
- **[OpenRouter Auto Beta](https://openrouter.ai/docs/guides/routing/routers/auto-router)** (`openrouter/auto-beta`) -- Easiest pay-per-token option for Pi: classifies prompts into ~30 task types, ranks models using trailing community spend share, applies a 0-10 cost/quality dial, pins model/provider within a session for cache consistency, and charges no router premium beyond the selected model's normal OpenRouter price. Its published benchmark is vendor-reported and only partially coding-shaped. **Verdict: good API-funded experiment, irrelevant to making the existing Codex subscription cheaper.**
- **[LiteLLM Auto Router v2](https://docs.litellm.ai/docs/proxy/auto_routing)** (LiteLLM gateway: 54.7k stars; active Jul 2026; auto-router feature new in v1.94.x) -- Mature self-hosted gateway with a brand-new task router: heuristic, small-LLM, keyword/semantic, and adaptive Thompson-sampling modes plus session affinity. Strong reference architecture for measured routing, but it requires operating a proxy and API-key-funded model pool; it cannot magically pool first-party Claude/Codex subscription entitlements. **Verdict: watch the feature, do not add the gateway for a personal subscription workflow.**
- **[Claude Code Router](https://github.com/musistudio/claude-code-router)** (MIT; 36.2k stars; active Jul 2026) -- Mature local gateway/control plane spanning Claude Code, Codex, provider keys, Kimi Code subscription, retries, credential pools, protocol conversion, logs, and tools. It solves cross-provider plumbing more than reliable task difficulty, and overlaps the intentionally small Pi harness. **Verdict: ecosystem reference, not an adoption candidate.** Do not route first-party subscription OAuth through unofficial wrappers without explicit vendor support and a credential-path review.
- **[RouteLLM](https://github.com/lm-sys/RouteLLM)** (Apache-2.0; 5.3k stars; last push Aug 2024) -- Important research/evaluation framework for learned strong-vs-weak routing, but effectively dormant and aimed at API serving rather than coding-harness subscriptions. Keep as the benchmark-method reference, not software to install.
- **[CodeRouter](https://github.com/Code-Router/CodeRouter)** (MIT; 1 star; created May 2026) -- Claims intent-based routing, worktree execution, learning, and Claude Code/Codex integration, but currently has no adoption evidence and expands into another full orchestrator. **Verdict: ignore until independent usage and evaluation exist.**

**Decision rule:** do not adopt a router because it reports cheaper selected calls. Require paired task completion, retries/turns, prompt-cache behavior, quota consumption, latency, privacy outcomes, and verifier quality. A lower-tier miss that causes one recovery turn can erase the savings. Explicit frontier/private choice remains the baseline while Workbench's auto mode is evaluated; an external router must beat that smaller owned policy layer before adoption.

### Voice input and conversational agents (2026-07 watch)

**Baseline:** TypeWhisper remains the installed macOS dictation tool and is working well; this is a watchlist, not a migration queue. Prefer local, open-source options. Stars and activity below are a 2026-07-25 snapshot, not quality scores.

**System dictation**

- **[Awesome Voice Typing](https://github.com/primaprashant/awesome-voice-typing)** (MIT; 162 stars; active Jul 2026) -- Maintained cross-platform directory of open-source dictation tools, including TypeWhisper. Use it as the category index before adding another candidate here; its rankings are discovery guidance, not comparative testing.
- **[Handy](https://github.com/cjpais/Handy)** (MIT; macOS/Windows/Linux; 27.5k stars; active Jul 2026) -- The strongest FOSS general-purpose alternative: offline Whisper.cpp/Parakeet dictation, push-to-talk, transcript history/dictionary, signed releases, CLI remote control, and by far the largest community here. Contrary to the earlier “raw transcript only” description, it now has configurable post-processing prompts and OpenAI-compatible/Apple Intelligence providers plus a separate post-processing hotkey. The genuine advantages over TypeWhisper are cross-platform parity, model portability, a Raycast integration, and a much larger contributor base; TypeWhisper has its own Homebrew tap, fits the current native-Mac workflow, and exposes the local CLI/API needed for automation. Evaluate only if TypeWhisper becomes unreliable, its smaller project becomes a maintenance risk, or one of those integrations becomes load-bearing.
- **[VoiceInk](https://github.com/Beingpax/VoiceInk)** (GPLv3; macOS; 5.7k stars; active Jul 2026) -- Native Apple-Silicon dictation with per-app tuning, custom dictionary, WhisperKit/BYOK engines, and an optional AI-polish layer. Source builds are free; the signed convenience binary is paid. Most interesting feature comparison for TypeWhisper, but not a current replacement need.
- **[OpenWhispr](https://github.com/OpenWhispr/openwhispr)** (MIT; macOS/Windows/Linux; 4.9k stars; active Jul 2026) -- Cross-platform local Whisper/Parakeet plus optional BYOK cloud providers, custom dictionary, and filler-word cleanup. Track as the flexible hybrid option, not as a reason to replace a satisfactory local setup.
- **[VoiceTypr](https://github.com/moinulmoin/voicetypr)** (AGPLv3; macOS/Windows; 609 stars; active Jul 2026) -- Local Tauri/Whisper dictation; source is open while distributed binaries require a one-time license. Strong network copyleft matters only if distributing a modified service; ordinary local use or an unpublished fork is not a problem.
- **[nerd-dictation](https://github.com/ideasman42/nerd-dictation)** (GPLv3; Linux; 1.9k stars; last push Oct 2025) / **[Speech Note](https://github.com/mkiol/dsnote)** (MPL-2.0; Linux; 1.6k stars; active Jul 2026) -- Linux-only local dictation. Keep as portability references; neither supplies the polished macOS workflow being used today.
- **[Buzz](https://github.com/chidiwilliams/buzz)** (MIT; macOS/Windows/Linux; 20.4k stars; active Jul 2026) -- Mature local microphone/file transcription UI, but text stays in Buzz rather than flowing into the active application. Track for batch media transcription, not system dictation.

- **[LLMLingua](https://github.com/microsoft/LLMLingua)** -- Microsoft's LLM-based prompt-compression library. Compresses long contexts by an order of magnitude while preserving most task accuracy, via a small model that scores token importance. Pairs with [[Knowledge/LLMs-and-AI/Context-Engineering]]: high-leverage when prompts are bumping the cost/latency budget and reranking alone isn't enough.
- **[Headroom](https://github.com/headroomlabs-ai/headroom)** -- Local proxy/library/MCP layer that samples and deduplicates repetitive JSON/logs, uses an extractive ModernBERT compressor for prose, and keeps originals in a retrieval cache. **Evaluated 2026-07-22: WATCH; do not adopt globally.** The mechanism is real, but the 60-95% headline applies to favorable JSON/log payloads, not ordinary coding-agent traffic. Headroom's own [production telemetry](https://headroom-docs.vercel.app/docs/benchmarks) reports 4.8% median / 11.3% mean compression; its maintainer conceded a realistic 15-20% for coding agents in [#1843](https://github.com/headroomlabs-ai/headroom/issues/1843). One third-party [50-case benchmark](https://github.com/shreyassks/headroom-benchmarks) measured 42% input reduction on synthetic JSON-heavy support-ticket tasks, but did not score final-answer correctness; its small N=100 evals showed GSM8K -1pp, SQuAD exact match -5pp, and unchanged BFCL under a lenient scorer. More seriously, [#2085](https://github.com/headroomlabs-ai/headroom/issues/2085) measured a Claude Code prompt-cache collapse and ~2.5-3x provider-limit burn on v0.31.0; contributors reproduced it and shipped fixes in v0.32.0, but no independent post-fix A/B is published. "Reversible" means lossy prompt transformation plus separate local retrieval, not intrinsically lossless compression. Revisit only after a pinned project-local replay shows lower total billed cost (including cache writes/reads), unchanged task correctness, stable parallel-subagent behavior, and at least 15% net savings. Prefer filtering/pagination at the tool source and provider-native compaction first; explicitly disable Headroom telemetry in any trial.
- **[Vercel AI SDK](https://ai-sdk.dev)** -- TypeScript framework providing a unified interface across 100+ LLMs / 16+ providers for text, image, speech, video, tools, and structured output. Provider-agnostic (swap OpenAI/Anthropic/Google with a one-line change); first-class streaming primitives for React/Next/Vue/Svelte/Node. OSS (Apache 2.0), 13M weekly downloads, 24.2k stars. Default for any TS-based product needing LLM calls with streaming without provider lock-in. Cookbook example -- [Natural Language Postgres](https://ai-sdk.dev/cookbook/guides/natural-language-postgres) (NL-to-SQL with GPT-4o + Zod + auto-charting).
- **[OpenWiki](https://www.langchain.com/blog/openwiki-0-2-adds-okf-support)** -- LangChain's OSS CLI that generates and maintains a wiki for a codebase and keeps it synced as code changes, built for coding-agent consumption. 0.2 (2026-07) adds **OKF (Open Knowledge Format)** -- a Google Cloud-proposed standard for knowledge wikis (YAML front matter with tags/categories, `index.md` summaries, `logs.md` changelogs) so agents can do cheap deterministic tag lookups instead of open-ended search. Inspired by **DeepWiki** (Cognition's hosted talk-to-a-repo docs, Devin-powered) and Karpathy's LLM-wiki concept. For our small hand-curated repos, AGENTS.md + this playbook already fill the role; evaluate when dropping agents into a large unfamiliar codebase. Watch OKF itself as the possible standard for agent-readable docs.
- **[spec-kit](https://github.com/github/spec-kit)** -- GitHub's OSS toolkit for spec-driven development. Slash commands (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`) walk an AI agent from intent through implementation. Works across 30+ agents (Copilot, Claude, Gemini, etc.). **Compare against** the `planning` skill before adopting -- significant overlap; pick one discipline.
- **[Jules (Google)](https://jules.google)** -- Async coding agent (Gemini-powered) that clones your repo into a Google Cloud VM and works in the background, returning a PR. Fire-and-forget execution model; concurrent task support; "Jules Tools" CLI for scripting. Three tiers: free, Google AI Pro, Google AI Ultra (multi-agent). Evaluate as an alternative to Codex Cloud / Claude Code background tasks for backlog churn (deps bumps, test writing, small features).
- **[Claude in Chrome (beta)](https://code.claude.com/docs/en/chrome)** -- Anthropic's official Chrome extension + `claude --chrome` / `/chrome` slash command for browser automation: live debugging, design verification, form filling, data extraction, authenticated-app interaction. Requires Chrome/Edge, extension v1.0.36+, Claude Code v2.0.73+, direct Anthropic plan. **Anthropic-specific alternative to Agent Browser or Playwright MCP** for browser-tied workflows.
- **[everything-claude-code (affaan-m)](https://github.com/affaan-m/everything-claude-code)** -- "Harness performance system" bundling 60+ agents, 228+ skills, rules, hooks, and MCP configurations for Claude Code, Cursor, OpenCode, etc. Installable as Claude Code plugin or manually. **Mine for patterns** before adopting wholesale -- the agents/skills are uneven quality and the bundle is large.
- **[awesome-agent-skills (VoltAgent)](https://github.com/VoltAgent/awesome-agent-skills)** -- Curated index of 1,100+ agent skills from official teams (Anthropic, Google, Vercel, Stripe) and community contributors. Targets Claude Code, Codex, Gemini CLI, Cursor. Browse before writing a new skill from scratch.
- **[AgentHub (jamesrochabrun)](https://github.com/jamesrochabrun/AgentHub)** -- **Rejected for the current workflow.** Its SwiftUI monitoring, parallel terminal execution, diffs, worktrees, and GitHub surface optimize a fleet control plane. Paseo plus one parent and bounded delegation is deliberately smaller. Revisit only if measured cross-session coordination friction, rather than raw concurrency, becomes the limiting problem.
- **[Anthropic Academy (Skilljar)](https://anthropic.skilljar.com/)** -- Anthropic's official training portal with 20+ courses on Claude tools, API, MCP, agent skills, and AI fluency. Skim for non-obvious capabilities -- this is "how Anthropic wants you to use Claude," authoritative.

### Agent frameworks -- build-your-own-agent SDKs (2026-07 survey)

For when we *build* an agent product rather than drive a coding harness. Weighted
picks in bold; the rest catalogued so we don't re-derive the field.

**TypeScript**

- **[Mastra](https://mastra.ai/)** -- Agents, workflows, memory, evals, observability; from the Gatsby team, YC W25. Hit 1.0 in Jan 2026; ~22k stars, 300k+ weekly npm downloads; still shipping fast (Jul 2026 "Goals": durable objectives for long-running agents with LLM-judged evals). **Weighted pick: default for any TS agent build.** Composes with, rather than replaces, the Vercel AI SDK (which stays the lower-level provider layer). Caveat: no SOC 2 as of early 2026. Native MCP support.

**Python**

- **[Pydantic AI](https://ai.pydantic.dev/)** -- **Weighted pick: closest in spirit to Mastra** -- type-safe, model-agnostic, testing built in, deliberately light orchestration. Native MCP. Multi-agent orchestration still maturing.
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** -- Explicit graph-based stateful orchestration; maximum control, steepest learning curve. The "serious production workflow" default per most 2026 surveys. Native MCP. Reach for it only when the workflow genuinely needs durable multi-step state.
- **[Agno](https://agno.com/)** -- Batteries-included agent *platform* (build/run/monitor, multi-agent teams). Opinionated; closer to Mastra's full-stack ambition than Pydantic AI.
- **[Google ADK](https://google.github.io/adk-docs/)** -- Gemini/GCP-native; strongest for multimodal (video/voice/image) agents. Only if committed to GCP. MCP via adapters.
- **[OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)** -- Model-driven loop with built-in tracing; tight integration with OpenAI hosted tools but works with 100+ models. Native MCP.
- **[smolagents](https://github.com/huggingface/smolagents)** (Hugging Face) -- Code-first: agents write and execute Python instead of JSON tool calls. Fastest setup for a single-agent loop; no native MCP.
- **[AWS Strands Agents](https://strandsagents.com/)** -- AWS's model-driven SDK, Bedrock-native, OTel-first (X-Ray/CloudWatch). Same "give the model tools and get out of the way" stance as smolagents. Native MCP.
- **[CrewAI](https://www.crewai.com/)** -- Role-based multi-agent crews. Popular but MCP only via shims; surveys increasingly rank it behind LangGraph/Pydantic AI for production.

**.NET / Java-shaped enterprises**

- **[Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/)** -- AutoGen + Semantic Kernel merged into one .NET + Python SDK; 1.0 GA 2026-04. The Azure-enterprise default; note as the answer to "what happened to AutoGen/SK".

**Rust / Go** (crossed to production-viable in 2026)

- **[Rig](https://rig.rs/)** (Rust) -- Dominant Rust option, ~7.6k stars; 20+ providers, 10+ vector stores, OTel GenAI conventions, WASM, MCP. Real deployments (Cloudflare, Neon, Nethermind, St. Jude). Benchmarks claim ~5x memory reduction and 25-44% latency wins vs Python equivalents -- re-verify before citing.
- **[Eino](https://github.com/cloudwego/eino)** (Go) -- ByteDance CloudWeGo's component-based framework, 11k+ stars; LangChain-inspired but Go-idiomatic, built for massive-scale serving.
- **[Genkit Go](https://genkit.dev/)** (Go) -- Google's production-ready GenAI framework for Go; streaming, evals, tracing built in.

### Personal AI assistants / always-on agents (2026-07 watch)

A distinct category from coding harnesses and agent SDKs: persistent assistants
that live in your messaging channels, hold cross-session memory, and act on your
behalf. Same skepticism applies as Tier-3 harnesses (they hide a lot, and the
self-hosted ones are a standing security surface — broad machine access + inbound
messages from many channels). Watch, not adopt, until one earns trust.

- **[OpenClaw](https://openclaw.ai/)** -- The viral one (200k+ GitHub stars). Local-first OSS personal agent by Peter Steinberger (PSPDFKit), BYOK, 24 messaging channels (WhatsApp/Telegram/Slack/iMessage/Signal/...), community plugin ecosystem, writes its own skills. Governance moved to a 7-person steering committee after Steinberger joined OpenAI (early 2026). Biggest open question for us: the attack surface of an autonomous agent bridged to every inbox.
- **[Hermes Agent](https://hermes-agent.org/)** (Nous Research, Feb 2026) -- OSS self-improving personal agent on your own infra. Three-layer memory (skills / conversational / user model), 20+ messaging platforms via one gateway, 40+ tools, 6 terminal backends (local→Docker→SSH→Modal), multi-provider LLM + browser automation as of v0.18 (Jul 2026). The "own your assistant" analog of our Pi bet -- philosophically closest to us. **Verdict (2026-07-21, tombstoned): out.** The legitimate always-on use cases (competitive polling, outreach batching, repo health watchdogs) are being covered by our own scheduled jobs; messaging-gateway chat is replicable with Tailscale into an interactive session; auto-generated skills/memory are too haphazard to trust. See `docs/decisions/tombstones.md`.
- **[Town](https://www.town.com/)** -- Proprietary, email-native EA: you get an `@town.com` address and delegate like to a human assistant (inbox, calendar, Slack, docs). Founded by ex-Plaid CTO + ex-Google applied-AI lead; $55M Series A from a16z/Forerunner (Jun 2026). The polished rent-don't-own pole of this category.
- **[Poke](https://poke.com/)** (The Interaction Company) -- Messaging-native agent: no app, you text it (iMessage/SMS/Telegram/WhatsApp) and it acts on email/calendar/files -- drafts replies, reschedules, books travel. Launched Mar 2026; $300M valuation (Spark/General Catalyst); first third-party AI agent approved on Apple's Messages for Business (Jun 2026). Town's competitor with texting instead of email as the interface.
- **[Lindy](https://www.lindy.ai/)** -- Cloud "AI employee" -- proactive email management, scheduling, business workflow automation. The no-code/business-buyer pole; less interesting to us than the self-hosted options but a category anchor.
- **Claude Cowork** (Anthropic) / **Perplexity Computer** -- The frontier-lab managed takes: autonomous desktop work and cloud agent grounded in live web research respectively. Track as the "the platform does it for you" endgame that squeezes the independents above.

### Structural code search/edit tools for agents (2026-08 research spike)

Evaluated whether ast-grep and similar structural (AST-aware) search/rewrite tools, plus LSP-backed navigation tools, are worth adopting for Claude Code / Codex / Pi beyond ripgrep.

- **[ast-grep](https://ast-grep.github.io/)** (`sg`) -- Rust/tree-sitter CLI matching and rewriting code via language-shaped patterns (`foo($A, $B)`) instead of regex; ignores formatting/comments/strings that trip up `rg`. **Verdict: install the CLI opportunistically, skip the MCP layer.** Value is real but narrow and low-frequency: for targeted single-file edits an agent with `rg`+`Edit` already does fine, so marginal value is near zero there. The genuine win is bulk structural rewrites (rename a signature and fix N call sites with reordered/added args across dozens+ of sites) -- one rewrite rule vs. N error-prone manual edits, and it won't false-positive inside docstrings/strings. The official `ast-grep/ast-grep-mcp` repo self-describes as **"experimental"** (~450 stars, thin activity) -- not something to depend on. For a mid-sized mostly-Python personal codebase, this scenario comes up a handful of times a year, not daily.
- **[Serena](https://github.com/oraios/serena)** -- LSP-backed MCP server (wraps pyright/gopls/rust-analyzer/etc.) giving agents real go-to-definition/find-references/symbol-level edits. 28k+ stars, actively released, more institutional backing than ast-grep-mcp. **Why MCP and not a CLI**: LSP servers are long-lived processes that index the whole project once and serve many queries fast; a CLI invoked per-query would either re-spawn/re-index every call (slow) or need its own persistent daemon -- which is just an MCP server with extra steps. Real setup friction: indexing `node_modules`-scale junk without ignore-path config makes startup "painfully slow" per Serena's own docs. **Measured value is thin and mixed, not proven**: Serena's own claims (99% fewer tokens, 8-12 steps to one call) are self-reported and uncited. The one independent benchmark found (ManoMano, Feb 2026, 36k-line/381-class Java payment service): for a read-only lookup task, Serena cost **~4x more tokens and took 60% longer** than plain grep-based Claude Code -- a net loss; for deep multi-file refactor/write tasks they judged it necessary but published no comparable hard numbers. No SWE-bench-style or reproducible benchmark isolating Serena's contribution exists. **Verdict: skip for now.** Plausible mechanism (ground-truth symbol refs beat grep's text-pattern guessing as refactor complexity rises), but the only real external measurement shows a net cost on ordinary lookups. Revisit only if doing heavier multi-file structural refactor work where symbol-accurate edits start to matter.
- Comparables surveyed and passed on: **Semgrep** (security/SAST-flavored, already tracked above, overkill for refactor tasks), **Comby** (text-pattern not true AST -- fails on Python's indentation sensitivity), **GritQL** (more expressive logic-DSL, steeper learning curve, Biome-coupled). ripgrep + `fd` remain the converged standard and need no change.

### Claimed-vs-measured agentic improvements (roster)

Tools/skills marketed as cracking a real agent-efficiency problem (fewer tokens, faster runs, better code), tracked against independent or rigorous first-party measurement. Purpose: only build the stack up with what survives verification, not what markets well. Add an entry whenever a bold efficiency claim gets checked, win or lose.

- **[Ponytail](https://blog.jetbrains.com/ai/2026/07/ponytail-skill-claude-tested/)** (OSS Claude Code skill, MIT, v4.8.4) -- Runs a "does this need to exist / is it already available" decision ladder before code generation ("lazy senior developer" framing); explicitly leaves validation/error-handling/security/a11y untouched. **Claimed**: -54% code, -22% tokens, -20% cost, -27% time. **JetBrains measured** (80 paired tasks, Claude Code + Sonnet 5, Jul 2026): -15.4% code (not significant, p=0.088), **-10.3% cost (statistically solid, p=0.004)**, -11% time, no quality loss. **Verdict: partial survivor, not a null result** -- real effect, but 2-4x smaller than advertised and concentrated almost entirely on larger/over-engineerable tasks (near-zero on lean tasks); a contributor reportedly challenged the authors' own benchmark methodology afterward (InfoQ, Aug 2026). Treat vendor efficiency percentages as a ceiling, not an expectation -- JetBrains' harness-benchmarking spread (10-17 pts from scaffold alone, see the "AI Tooling Research Notes" section above) is the same discipline: verify the specific number against your own workload before trusting it into the stack.
- **Headroom** -- see full entry above (2026-07-22 evaluation): headline 60-95% compression is real only on favorable JSON/log payloads; own production telemetry shows 4.8% median / 11.3% mean on real traffic, and a v0.31.0 regression 2.5-3x'd provider-limit burn before a fix shipped. Filed here as the template case: self-reported headline number, independent measurement an order of magnitude lower, plus a live regression.
- **Starship prompt** -- see full entry above (2026-06-04 evaluation): not a token/cost claim, but same pattern -- feature set (contextual-safety modules) didn't match this environment's actual surface (no cloud CLIs installed, 0 kube contexts), so the marketed win evaporated on contact with real usage.

### AI coding agents -- alternatives to evaluate against Claude Code / Codex / Cursor

> User research note (2026-04-30): "read on OpenHands; OpenCode; Aider meh against Claude Code / Codex / Cursor"

- **[OpenHands](https://github.com/All-Hands-AI/OpenHands)** (formerly OpenDevin) -- OSS autonomous coding agent that runs in a sandboxed Docker environment. Multi-model, supports Anthropic / OpenAI / local. Worth comparing for the "fully autonomous agent in a sandbox" workflow.
- **[OpenCode](https://github.com/opencode-ai/opencode)** -- OSS terminal coding agent. Lightweight, BYO API key. Compare against Aider for cost-control / provider-flexibility use cases.
- **[Aider](https://aider.chat/)** -- Veteran OSS terminal coding agent. User flagged "meh" in 2026-04 notes -- worth confirming whether the gap to Claude Code / Codex has actually closed or remained.
- **[Codex CLI](https://github.com/openai/codex)** (the actual CLI, distinct from Claude Code / Cursor) -- OpenAI's official terminal coding agent. The cross-model pairing pattern: write with Claude Code, review with Codex (or reverse).

### Observability / Analytics

- **[PostHog](https://posthog.com/)** -- Product analytics + session replay + feature flags + A/B + LLM observability all in one. User note (2026-04): "PostHog wiki has tips" -- worth a skim for both feature-flag patterns and the LLM observability dashboards. OSS self-hostable; cloud also offered.

- **[ChatGPT Atlas (OpenAI)](https://chatgpt.com/atlas)** -- OpenAI's AI-native browser (launched late 2025). ChatGPT is the default address bar / sidebar / agent on every page; reads what's on screen and can take actions (form fill, navigation, multi-tab workflows) inside an authenticated browser session. Mentioned in Garry Tan's "20x Company" video as part of the toolchain that lets tiny teams operate at scale. Compare against **Claude in Chrome** (already tracked) -- Atlas is a *whole browser*, Claude in Chrome is an *extension on top of Chrome*. The browser-as-product positioning makes Atlas more aggressive about agent context (sees everything) and more concerning for privacy boundaries. Worth evaluating side-by-side if browser automation is core.

### Research and comparison sources

The maintained benchmark catalogue and selection sequence live in
[open-model-inference.md](knowledge/open-model-inference.md). Keep only integration
indexes here: [deepseek-ai/awesome-deepseek-agent](https://github.com/deepseek-ai/awesome-deepseek-agent)
is DeepSeek's official list of compatible agent frameworks.

### Open-model inference

Current model families, local runtimes, routers, managed inference hosts, and
serverless GPU platforms are ranked in
[open-model-inference.md](knowledge/open-model-inference.md). Keep candidate tools
here only when they still need an adoption decision; do not duplicate volatile
prices or model rankings.

## Workbench Watch Items (2026-08)

Sync-simplifying upgrades the improvement hunt confirmed are not ready yet;
re-check occasionally.

- **`uv audit`** ([astral.sh/blog/uv-audit](https://astral.sh/blog/uv-audit), 2026-06-08) -- uv-native pip-audit replacement; would delete the pip-audit dev-dependency tree. Explicitly preview/unstable as of June 2026 — adopt when stabilized.
- **Claude Code native AGENTS.md** ([anthropics/claude-code#34235](https://github.com/anthropics/claude-code/issues/34235)) -- open enhancement, no roadmap. Landing would let `workbench sync` drop the CLAUDE.md translation surface.
- **Exa hosted MCP** ([docs.exa.ai/reference/exa-mcp](https://docs.exa.ai/reference/exa-mcp)) -- remote Streamable HTTP endpoint at `mcp.exa.ai/mcp` could replace the stdio server and the stamp-time key-baking workaround; evaluate the auth tradeoff (OAuth vs key-in-URL) before switching.
- **Pi Packages** ([extensions docs](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)) -- npm/git distribution for Pi extensions/skills/themes. The real-file deployment remains the deliberate choice for owned, drift-checked config; revisit if extension count grows.

## AI Stack Rankings (personal, 2026-05)

> Historical hands-on ordering, not benchmarks or active support policy. Some entries remain useful as evaluation notes.

### Model access

The historical May ranking has been superseded. The current local model, runtime,
router, managed-host, and serverless-GPU decisions live in
[open-model-inference.md](knowledge/open-model-inference.md). Closed frontier access
remains a separate subscription and API decision rather than part of the
open-model ranking.

### Harnesses

**Proprietary CLIs / apps** — 1. **Claude Code / Claude Desktop**. 2. **Codex CLI / Codex Desktop**. 3. **Gemini CLI** (no desktop; lagging on model quality).

**Model-variety IDEs** — **Zed** wins heavily (model range + vibe) ≫ **Cursor** (undeniably great; lingering personal aversion).

**Model-variety CLIs** — **OpenCode** leads on mindshare / feature parity, but the *whole concept* is undercut while proprietary CLIs subsidize inference via subscription. Then **Crush**. **Goose** ranks lowest of those tried (see niche below). **Pi** TBD.

**Overall daily-driver feel** — 1. (tie) **Zed** (flexible; shows code, not just an agent REPL) and **Pi** (pi.dev — surprisingly delightful: ultra-light terminal agent, ~1k-token system prompt, hackable, mid-session provider swap). 2. **Claude Code / Codex CLI / Cursor (+Cursor CLI)**. 3. **Gemini CLI**. 4. **OpenCode**. 5. **Crush** (cute, but the glamorous TUI is both nice and way too much — "just build an IDE if you're going to be so heavy"). 6. **Goose** (lowest of tools tried — see below). opencode/crush both fine, just too heavy for a daily driver vs a real IDE.

> **Pi's adopted niche:** primary terminal-native interactive loop for subscription, local oMLX, and BYO-key provider-hopping with a consistent transparent surface. Workbench now deploys and drift-checks Pi as a first-class target; Codex and Claude Code remain specialist fallbacks.

> **Warp** (warp.dev) — WATCH, not yet tried. Different direction: an AI-native *terminal* built for multi-agent dev (Codex/OpenCode/Gemini as first-class threads, per-agent worktree/branch/PR metadata, unified notifications). Solid-feeling, ambitious product; a plausible "great solution" — deferred while exploring Zed. Revisit if juggling many agent sessions outgrows Zed + Ghostty.

> **Goose (Block → Linux Foundation/AAIF) — WATCH, no use today.** Targeted niche is **autonomous execution / headless automation** ("Recipes" — fire-and-let-it-work, install/run/edit/test), *not* the interactive, watch-every-tool transparency this setup values. First hands-on was poor: the CLI is deliberately plain (no rich TUI, no message queue), shows little with no extensions enabled, and a 4B local model can't tool-call reliably. Revisit only if a headless/scheduled automation need appears — then try Goose **Desktop** + the Developer extension + a frontier model, not the bare CLI.

## AI Tooling Research Notes (2026-05)

Findings from a deep research pass (2026-05-25). Sources at the end. Treat dollar figures and limits as accurate-as-of-late-May-2026 but volatile. We'll revisit harness benchmarking as the field matures.

### Subscription vs API access — who lets you spend a subscription in an agnostic tool

The frontier field has **bifurcated**: Western incumbents wall their subsidized subscriptions into first-party clients; challengers (Chinese labs, Cerebras, OpenAI-via-partners) compete by *welcoming* third-party tools.

| Provider | Subsidized sub exists? | Usable in 3rd-party tools (Pi / OpenCode / Zed-ACP)? | Notes |
|---|---|---|---|
| **Anthropic** | Yes (Max) | ❌ **Banned** (Jan/Feb 2026) — first-party Claude Code / claude.ai only | API key (metered) everywhere else. Confirmed via ToS + error strings. |
| **Google Gemini** | Yes | ❌ Banned; **individual CLI/IDE tiers retire Jun 18 2026** → Antigravity | As/more restrictive than Anthropic. Vertex API key for 3rd-party. |
| **OpenAI / Codex** | Yes (ChatGPT Plus/Pro) | ✅ **Officially sanctioned** (Zed native + ACP, OpenCode) — personal use | The permissive Western outlier. Zed markets this. |
| **GitHub Copilot** | Yes | ✅ Official in OpenCode (Jan 2026) | Flat today → usage-credits Jun 1 2026. |
| **Zhipu GLM** | Yes — **Coding Plan $18/mo** | ✅ Explicitly supports Claude Code/OpenCode/Cline/Cursor/Crush/Goose | The anti-Anthropic. GLM-5.1 ≈94.6% of Opus 4.6 on their eval. |
| **Alibaba Qwen** | Yes — Coding Plan ~$50/mo | ✅ via subscription endpoint+key (free OAuth ended Apr 15 2026) | Pivoted from free-OAuth to sub-key-into-tools. |
| **Cerebras Code** | Yes — $50/$200/mo | ✅ any tool, via **API key** (flat-rate hybrid) | Qwen3-Coder ~2000 t/s, no weekly limits. Best "flat + everywhere" for OSS coding. |
| **xAI Grok** | Yes (SuperGrok) | ◑ official in OpenCode; Grok Build CLI wants $99 or API credits | Mixed, leans tolerant. |
| **Moonshot Kimi** | Yes — coding plans ($39–$199) | ◑ OpenAI-compatible endpoint; subscription-passthrough ToS **gray/unverified** | Has its own Kimi Code CLI. |
| **DeepSeek** | No sub (API only) | n/a — bring cheap API key | V4-Flash ~$0.14/$0.28 per M. |
| **Mistral** | Le Chat Pro (no API) | n/a — metered API only | Consumer sub explicitly excludes API. |

**Takeaways:** Anthropic isn't unique — it's the leading edge of a Western lockdown (Google is equally/more restrictive). For our barbell: **local oMLX** or, if we ever want a subscription inside an agnostic tool, **GLM Coding Plan / Cerebras / Copilot / ChatGPT** are the sanctioned paths. **Anthropic Max stays first-party** (Claude Code / Zed-ACP). Pi → Anthropic = pay-per-token API, *not* the Max subscription.

### Harness benchmarking — the scaffold moves a fixed model 10–17 points

The harness (tool/scaffold) is now benchmarked **separately** from the model, and the effect is large:

- **Terminal-Bench 2.0** reports `agent+model` pairs. Same **Opus 4.7** scores **90.2%** (top harness) vs **80.2%** (a lower one) — ~10-pt spread from scaffold alone; GPT-5.5 swings ~17 pts. **Claude Code itself ranks ~51st** there.
- **LangChain** documented **+13.7 pts on one model** by changing only the harness. **SWE-Effi** (academic) and the **Aider polyglot** (edit-format efficiency) corroborate.
- **"Cursor > Claude Code on Opus 4.7"**: true on **one** published benchmark (Endor Labs: Cursor 91.1% vs Claude Code 87.2% functional) — narrow security-CVE dataset, ~4 pts. **Directionally real, not a general law.**
- **Pi**: credible-but-**unbenchmarked** (no clean published number; not on the current board). Its thesis (minimal prompt + frontier model) is plausible, not proven.
- **Zed-ACP is NOT guaranteed 1:1 with native Claude Code** — it wraps the Claude *Agent SDK*, which defaults to a *minimal* system prompt (omits Claude Code's coding guidelines) unless the `claude_code` preset is set, and shipped with plan mode / slash commands missing. So hardest work may still be marginally better in the native CLI.
- **What drives the gap:** edit/diff-format fit (#1 — models are RL'd on a specific tool surface), context management/compaction, verification-before-exit loops, reasoning-budget routing, loop detection, prompt size/structure ("model-harness fit").

> **Don't pick daily tools off the Terminal-Bench leaderboard.** The top entries (`vix`, `Capy`, `Droid`, `WOZCODE`, `Terminus 2`) are mostly **benchmark-tuned / research / competitive harness submissions** — scaffolds optimized to pass 89 terminal tasks, not consumer products with good DX. `Terminus` is the benchmark's own minimal *reference* agent. High leaderboard ≠ good daily driver; it measures scaffold-on-benchmark, not real-world ergonomics. Use it to confirm "harness matters," not to choose tools.

### Scheduling / automation portability

There is **no fully-managed vendor-agnostic agent cron.** Choices: (a) **vendor cloud** = zero ops, lock-in [Claude Routines, Codex Cloud, Cursor Automations, Jules]; or (b) **self-host a scheduler that invokes a headless agent CLI** = agnostic, you own the box.

- **Zed**: no scheduler/routines (interactive editor; hooks are editor-event-only, don't fire for agent tasks).
- **Pi**: no built-in scheduler *either*, but has the headless surfaces (`pi -p`, `--mode rpc`, SDK) to be driven by **cron / GitHub Actions / a VPS** — the agnostic path. `0 9 * * * cd /repo && pi --tools read,grep,find,ls,edit -p "$(cat nightly.md)"`.
- **Goose** has a real built-in `goose schedule` (cron) if a batteries-included open option is wanted.
- **Cursor Automations review (2026-08-26):** the useful capabilities are scheduled and repository-event triggers, template-distributed workflow definitions, declared tool scopes, reruns when pull requests change, confidence-gated mutation, explicit safe no-op outcomes, adversarial treatment of trigger content, and a small workflow-specific deduplication ledger. The public critical-bug template uses persistent `MEMORIES.md` only for open or rejected findings; reviewer workflows can reassess prior decisions as pull requests change. **Verdict:** mine these patterns, do not adopt Cursor or build a scheduler into Pi. Put recurring instances in GitHub Actions or the private automation layer. Keep model risk ratings advisory; do not copy automatic low-risk approval. The full research record and primary sources are in [Agent Capability Patterns](knowledge/agent-capability-patterns.md#12-cursor-automations-patterns).
- **Bottom line:** Zed + Pi *can* do scheduled runs — via Pi headless + your own trigger. The price of agnostic is hosting the runner.

### Research sources (2026-05-25)

- Subscriptions: [Anthropic OAuth ban (Register)](https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/) · [Zed × ChatGPT sub](https://zed.dev/blog/chatgpt-subscription-in-zed) · [GLM Coding Plan](https://z.ai/subscribe) · [Copilot → OpenCode](https://github.blog/changelog/2026-01-16-github-copilot-now-supports-opencode/) · [Cerebras Code](https://www.cerebras.ai/blog/introducing-cerebras-code) · [Qwen free-tier shutdown](https://decrypt.co/364501/alibaba-shuts-down-free-tier-qwen-code)
- Harness benchmarking: [Terminal-Bench 2.0](https://www.tbench.ai/leaderboard/terminal-bench/2.0) · [Terminal-Bench paper](https://arxiv.org/abs/2601.11868) · [SWE-Effi](https://arxiv.org/abs/2509.09853) · [Aider edit-format leaderboard](https://aider.chat/docs/leaderboards/edit.html) · [LangChain harness engineering](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering) · [Endor Labs (Opus 4.7)](https://www.endorlabs.com/learn/claude-opus-4-7-sets-new-records-in-the-endor-labs-agent-security-league) · [Zed Claude Code via ACP](https://zed.dev/blog/claude-code-via-acp)
- Scheduling: [Claude Routines](https://claude.com/blog/introducing-routines-in-claude-code) · [Codex Automations](https://developers.openai.com/codex/app/automations) · [Cursor Automations](https://cursor.com/docs/cloud-agent/automations) · [Jules scheduled tasks](https://jules.google/docs/scheduled-tasks/) · [Goose scheduler](https://block.github.io/goose/docs/guides/recipes/recipe-reference/)
- Pi/Zed setup: [pi.dev](https://pi.dev/) · [earendil-works/pi](https://github.com/earendil-works/pi) · [awesome-pi-agent](https://github.com/qualisero/awesome-pi-agent) · [pi-superpowers-plus](https://github.com/coctostan/pi-superpowers-plus) · [Zed external agents](https://zed.dev/docs/ai/external-agents) · [agentskills.io](https://agentskills.io)

## Cloud / Hosting Providers

Personal vibes-check on the current player set (2026-05). Opinions, not benchmarks — refine as we get hands-on.

- **Cloudflare** -- Generally a strong platform that keeps getting better (Workers, D1, R2, Pages, Queues all maturing). Some questions on the team, but the product trajectory is solid.
- **Vercel** -- Probably still a decent solution for Next.js-native frontends. Terrible place to scale (pricing traps, vendor lock-in — already flagged in `playbook/stacks/services.md` "When NOT to Use"). Some questions on the team. Very AI-forward / tech-forward, so they'll keep shipping interesting things.
- **Render** -- Dark horse. Worth a real evaluation: product quality, principles/values, pricing structure. Currently filed as "budget option for simple services" in services.md but probably deserves more attention.
- **Railway** -- Seems pretty good. Possibly a little too dumbed down — TBD whether that's a feature or a ceiling. Pricing structure matters; worth scrutinizing same as Render.
- **Supabase** -- Not really a full cloud provider — they're Postgres-plus-extras (auth, storage, realtime, edge functions). Useful piece of a stack, not a primary host.
- **Google Cloud** -- Downgrade. Multiple outages recently. Reliability story is worse than the marketing suggests.
- **AWS** -- Just works, but blows in a lot of ways (UX, cost surprises, sprawl). Pick-your-poison among hyperscalers.
- **Azure** -- Same energy as AWS. Pick-your-poison.
- **Hetzner** -- The "self-rolling" option. Cheap EU bare-metal / VPS. Pair with Coolify / Dokploy / Kamal if going self-hosted PaaS. Worth a real look if cost matters or we want sovereignty from US hyperscalers.
- **Netlify** -- Curious about it but suspect they may be too small / too narrowly Jamstack to be a primary host. Worth a quick read on where they actually win vs Cloudflare Pages and Vercel.
- **Heroku** -- Hard no. Not evaluating.
- **Fly.io** -- Already in services.md as the "containers / global edge" pick. Keep on the list; reassess if pricing or reliability shifts.

- **Fly.io** -- Currently in use. Pricing is fine; probably overspending a touch right now and worth a right-sizing pass (check machine sizes, suspended-vs-stopped, Postgres tier). Already in `services.md` as the containers/global-edge pick. Reassess if pricing or reliability shifts.
- **DigitalOcean** -- App Platform sits Render-adjacent (PaaS for web services); Droplets sit Hetzner-adjacent but pricier (~2–3× per vCPU/GB). Managed Postgres / Spaces / K8s are solid mid-market. Good middle ground when you've outgrown Railway/Render but don't want to live in AWS.
- **Scaleway** -- French hyperscaler-lite. Bare metal, managed K8s (Kapsule), serverless containers/functions, managed Postgres. EU sovereignty story; pricing competitive with Hetzner on bare metal. Evaluate if EU data residency matters or as a hyperscaler-light alternative to AWS.
- **OVHcloud** -- Larger / older EU player. Strong on bare metal and dedicated GPU. Console UX is rougher than Scaleway. Evaluate mainly for GPU rental or heavy bare-metal needs at EU prices.
- **Coolify / Dokploy / Kamal** -- The self-host PaaS layer that sits on top of Hetzner / DO Droplets / any VPS. **Coolify** = open-source Heroku/Vercel clone, web UI, broadest feature set. **Dokploy** = leaner Coolify alternative, more modern stack. **Kamal** (37signals/Basecamp) = CLI-only, deploys Docker containers to any SSH-able host; intentionally minimal. Pick Coolify for breadth, Dokploy if Coolify feels bloated, Kamal if you want code-as-config and no web UI. All three pair naturally with Hetzner for ~5–10× cost reduction vs Railway/Render at small-to-mid scale.
- **Northflank** -- Kubernetes-native PaaS that hides the K8s. Build, deploy, autoscale services, jobs, databases, GPUs in one platform. BYOC mode (run on your own AWS/GCP/Azure account) is the killer feature: PaaS DX without vendor lock-in, and you can negotiate hyperscaler commits. Pricing roughly Railway-level on their cloud; on BYOC you pay hyperscaler costs + a margin. Strongest candidate when you outgrow Railway but want to stay off raw K8s.
- **Porter** -- Similar shape to Northflank: PaaS-on-top-of-K8s, BYOC-first (deploys into your AWS/GCP). Heroku-style git push deploys. More opinionated than Northflank, smaller surface. Evaluate head-to-head with Northflank if BYOC K8s is the goal.

### Scaling up — enterprise-level + good cost (2026-05 take)

Picking by stage and constraint, since "best" depends on what you're optimizing:

- **Best raw $/perf if you can self-manage:** Hetzner + Coolify (or Kamal for code-as-config). Brutal cost advantage; you own the ops burden. Good for serious scale if you have someone who likes infra.
- **Best PaaS DX without lock-in at scale:** Northflank BYOC into AWS or GCP. You get Railway-grade DX, but the underlying resources are your hyperscaler account — so you can negotiate enterprise commits, satisfy compliance, and exit if needed.
- **Best edge-native + flat pricing at scale:** Cloudflare. Workers + D1 + R2 + Queues + Durable Objects. Egress is free (huge), R2 has no egress fees vs S3, D1 has predictable per-request pricing. Weakness: long-running compute and big-RAM workloads are awkward.
- **Best if you must be on a hyperscaler:** AWS via SST (already the services.md default for TS). Pick AWS if compliance / partner ecosystem / enterprise sales demand it; otherwise the cost story is worse than the alternatives above.
- **Avoid for "serious scale":** Vercel (pricing traps), Railway (ceiling unclear, less BYOC story), Heroku (don't).

Rough mental model: **Hetzner+Coolify** for cost-floor self-host, **Northflank BYOC** for PaaS-DX-at-enterprise, **Cloudflare** for edge-native, **AWS+SST** for compliance/ecosystem reasons. Most serious shops end up running 2 of these.

### Specialist data layer (when to pick over a full provider's DB)

The question of "PlanetScale vs Neon vs Turso vs Cloudflare D1 vs Supabase Postgres vs Fly Postgres" comes down to **workload shape**, not vendor preference:

- **[PlanetScale](https://planetscale.com)** -- MySQL (Vitess) with horizontal sharding, branching, and online schema changes. Removed their free tier in 2024 (~$39/mo entry), so this is a "we're serious about MySQL at scale" pick now. Best when you need MySQL specifically, true horizontal sharding, or zero-downtime schema migrations on a hot table. Overkill for most apps.
- **[Neon](https://neon.tech)** -- Serverless Postgres with branching and scale-to-zero. Free tier exists; paid starts ~$19/mo. Storage and compute billed separately, which makes per-tenant / per-PR-branch usage cheap. Best when you want real Postgres with dev/preview branching, infrequent workloads, or many small databases. The "Vercel-Postgres" backend used to be Neon under the hood.
- **[Turso](https://turso.tech)** -- libSQL (SQLite fork) with multi-region replicas, per-database isolation, scale-to-zero. Free tier generous; paid scales with row reads / storage. Best for edge-read-heavy workloads, per-tenant isolated databases (multi-tenant SaaS where each customer = one DB), or anything where sub-10ms reads at the edge matter more than complex SQL. Weak on heavy writes and complex joins.
- **Cloudflare D1** -- Cloudflare's managed SQLite. Tight integration with Workers; included generously in the Workers paid plan ($5/mo). Per-request and per-row-read pricing, cheap at small-to-mid scale. Best when you're already all-in on Cloudflare and the data fits SQLite semantics. Weaker tooling and ecosystem than Turso (no libSQL extensions, fewer ORMs) but the integration story with Workers/Pages is unbeatable.
- **Supabase Postgres** -- Real Postgres + auth + storage + realtime + edge functions in one product. Pick when you want a batteries-included BaaS, not when you want a focused database. Pricing reasonable up to ~$25/mo Pro; scales linearly past that.
- **Fly Postgres** -- Just Postgres on Fly machines. Cheap, you-manage-it. Fine for app-and-DB-on-same-platform but no autoscale or branching magic.

**Decision rule of thumb:**
- Need MySQL at scale or zero-downtime migrations → PlanetScale
- Need Postgres with branching / preview envs / scale-to-zero → Neon
- Need per-tenant isolated DBs or edge reads → Turso
- Already on Cloudflare and data is SQLite-shaped → D1
- Want a full BaaS, not just a DB → Supabase
- Already on Fly, just need Postgres → Fly Postgres
- On AWS for compliance → RDS / Aurora Serverless v2 (boring, expensive, works)

Open questions to chase next round: Render pricing + principles, Railway scaling ceiling, Hetzner + Coolify/Dokploy stack, Netlify's real niche in 2026, Northflank BYOC pricing on AWS vs raw EKS, Fly right-sizing pass.

## Home / Personal

- **[Scrypted](https://github.com/koush/scrypted)** -- Home automation platform. Evaluate as a HomeKit / NVR alternative.

## Reference Reading

- **[Building a CLI for all of Cloudflare](https://blog.cloudflare.com/cf-cli-local-explorer/)** -- How Cloudflare approached building a unified CLI. Useful if we ever build a CLI across services.

## Other

- **Project Glasswing** -- Amazon's rumored internal AI agent framework. Track for potential public release or competitive implications.

## Remote Access

### Cross-harness mobile agent control

The requirement is to start or continue Pi, Claude Code, and Codex sessions from a phone with a uniformly readable transcript and usable approvals.

- **Paseo over Tailscale** is the adopted and sole phone surface. The daemon runs locally, binds to the tailnet interface, and keeps the relay disabled.
- **Zellij web, tmux, Mosh, and Mission Control** are retired. The owner does not need terminal connectivity from the phone, and a second continuity or presentation path only adds code and operations.
- **The private Notes web surface** may also use Tailscale, but remains a separate productivity application rather than an agent-session transport.

**Current recommendation (2026-08-26):** keep the mobile stack to Paseo plus Tailscale. If Paseo fails a concrete workflow, evaluate existing cross-harness clients before building; Pi-only web interfaces do not meet the requirement.

### BitBang (watch)

[BitBang CLI](https://github.com/richlegrand/bitbang-cli) is an interesting
**ad-hoc access** option, not part of the installed stack. As of 2026-08-04, its
single Go binary can expose a shell, a bounded file tree, or an HTTP proxy through
a capability URL. A browser is enough on the connecting side; WebRTC usually
provides a direct path through NAT, with encrypted TURN relay fallback. It needs
no account, inbound port, VPN, or preinstalled client. A six-digit, verbally
verified pairing flow can save credentials for later CLI connections.

The security design is thoughtful: the URL fragment holds the access secret and
is not sent to the signaling server; endpoint identity and DTLS fingerprints are
verified independently; and the server or TURN relay should see metadata and
ciphertext, not payloads. The important limits are:

- The URL is a bearer capability. The default `bitbang serve` grants shell,
  files, and proxy access, so a leaked URL has a large blast radius; use a
  capability-specific subcommand, optional PIN, and ephemeral identity instead.
- Browser clients still trust JavaScript delivered by the signaling server. The
  installed CLI avoids that code-delivery boundary, or the server can be
  self-hosted.
- This is a young, pre-1.0 project. The latest release was `0.4.7`, published
  2026-07-31; only the latest release is supported, the macOS binaries are not
  notarized, and the security policy says the project has a very small team.
- It does not serve the current workflow. The owner does not need phone terminal access; Paseo over Tailscale already owns agent continuity and mobile control.

**Disposition:** out for daily phone access. Re-evaluate only for a concrete temporary shell-sharing need. If trialed, use a non-sensitive test account, pin a release, inspect the installer, and serve only the narrow capability required.

Primary sources: [CLI documentation](https://github.com/richlegrand/bitbang-cli),
[trustless-signaling design](https://github.com/richlegrand/bitbang/blob/main/trustless-signaling.md),
[security policy](https://github.com/richlegrand/bitbang-cli/blob/main/SECURITY.md),
and [v0.4.7 release](https://github.com/richlegrand/bitbang-cli/releases/tag/0.4.7).

