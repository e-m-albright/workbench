# AI Code Review — Landscape & Workflow Tactics

> **Last reviewed**: 2026-07. Fast-moving vendor segment — re-verify claims before committing to a tool.

> **Epistemic note**: The vendor numbers cited below (precision percentages, "X% more PRs/dev," "Y% acceptance rate") are **vendor self-reported** unless otherwise marked. They come from marketing pages or company blog posts — not independent benchmarks. Cross-reference before betting on any single number. The workflow tactics (small PRs, stacked PRs, cross-model review) have stronger empirical backing.

> Claimed industry-level stats (also worth scrutinizing): AI shifts review burden onto humans — PRs ~18% larger, incidents/PR up ~24%, change-failure rate up ~30% with adoption. These come from a single Addy Osmani Substack post citing multiple studies; the magnitudes are directional, not gospel.

## The Dedicated AI PR Reviewers

Numbers below are **vendor-reported** unless flagged otherwise. Use the "Distinctive" column as positioning, not as truth.

| Tool | Distinctive (mostly vendor framing) | Best For |
|---|---|---|
| **CodeRabbit** | Most-deployed PR-comment reviewer; AST + SAST + LLM hybrid; *46% real-bug accuracy (vendor-reported)* | Easiest setup; criticized as noisiest in some independent benchmarks |
| **Bugbot (Cursor)** | Spawns cloud agents to test and propose fix commits; *35%+ of fixes merge directly (vendor-reported)* | Teams already in Cursor; $40/user/mo on top |
| **Greptile** | Full-repository graph index; parallel agents with full repo context | Monorepos / "this change ripples in ways the diff doesn't show" |
| **Graphite Agent** | Pairs AI review with stacked PRs + merge queue; *<3% unhelpful-comment rate (vendor)*. Shopify: *33% more PRs/dev (vendor case study)*; Asana: *7h/week saved (vendor case study)* | Teams adopting stacked-diff workflow |
| **Macroscope** | "Precision over volume" — *98% precision, comment volume -22%, nitpicks -64% Py / -80% TS (vendor v3 benchmarks)* | Teams burned by noisy bots; reddit sentiment unusually warm |
| **Qodo** (formerly CodiumAI) | Built on OSS PR-Agent; configurable rule system, indexes many repos. *monday.com prevents 800+ issues/month at 73.8% acceptance (vendor case study)* | Large monorepos / enterprise |
| **GitHub Copilot Code Review** | Zero-setup, native, included with Copilot. *1M users in first month post-GA (vendor)* | "If you already pay for Copilot, turn it on" |
| **Claude Code Review** | Multi-agent: specialized agents analyze diff in parallel -> verification pass -> severity-ranked inline comments. *Internally: substantive PR comments 16% -> 54% (Anthropic-reported)* | Anthropic's own; uses same Claude Code engine |
| **Codex PR review** | Not formally branded but widely used; clean PR diffs from sandboxed task model | Community pattern: Claude Code writes the feature, Codex reviews |
| **CodeAnt AI** | Line-by-line review + security + DORA tracking; 30+ languages | Want review + metrics in one tool |
| **Panto AI** | DevSecOps flavor: secrets, dependency, IaC, code review in one workflow | Compliance-heavy environments |
| **GitLab Duo** | GitLab-native | Already on GitLab; not really a destination tool otherwise |
| **Augment Code** | VC-darling for enterprise monorepos; indexes hundreds of services | Very large polyglot codebases |
| **Devlo / Atlassian Rovo** | Newer entrants inside Bitbucket/Jira ecosystems | Atlassian-heavy teams |

## Adjacent Tools (Pair With, Not Instead Of)

- **Sourcegraph Cody** — code-aware Q&A and review hints across very large codebases.
- **Codacy** — predominantly rule-based with AI layered on. Multi-language quality gates.
- **SonarQube** — not AI. Deterministic baseline most teams pair with an AI reviewer.
- **Snyk Code / Semgrep** — security-specialized scanners. Run alongside, not instead.
- **Qodana (JetBrains)** — IDE/CI parity for JetBrains shops.
- **PR-Agent (OSS)** — the engine Qodo is built on. Self-hostable for air-gapped/private deploys.

## The Tactics That Move the Needle More Than the Tool

The strongest finding across every comparison: **the workflow matters more than the tool.** Same reviewer is signal on a 150-line diff and noise on a 1,000-line one.

1. **Make PRs small.** Target 200-400 lines. Research shows 30-40% cycle-time improvements for PRs under 500 lines; diminishing returns above.
2. **Adopt stacked PRs.** Single highest-leverage workflow change. Teams using stacked PRs ship 20% more code with 8% smaller median PR size; ~10h/week saved waiting to merge. Tools: Graphite, GitHub's new `gh-stack`, ghstack (Meta), git-town, spr, Sapling.
3. **Different model writes vs reviews.** Asking the model that produced the bug to find the bug is structurally weak. Dominant 2026 pattern: **Claude Code writes -> Codex reviews** (or vice versa).
4. **Layer deterministic + probabilistic.** Lint + SAST (SonarQube, Semgrep, Ruff, mypy, ESLint, golangci-lint) for deterministic checks. AI reviewer for logic, intent, edge cases. Both, not either.
5. **Multi-agent review (parallel specialists).** Anthropic's Claude Code Review, Qodo, Greptile all do this. Separate agents for security, performance, correctness, style -> dedupe -> rank. Better than one generalist.
6. **Verification / false-positive filter step.** Don't post raw model output. Second pass: "is this finding actually correct given the surrounding code?" Macroscope's precision and Claude Code Review's quality both depend on this.
7. **Scope repository review invariants.** Put only consequential, non-obvious checks in `AGENTS.md`: state the invariant and safe path, locate service-specific guidance in the nearest nested file, and test one violation, one valid exception, and one unrelated change. Keep mechanical formatting in CI. OpenAI reports materially better custom-finding recall from this pattern, but the evaluation is first-party and should not be treated as a universal effect size.
8. **Risk-tiered review.** Dependabot version bump != agent-generated auth refactor. Auto-merge low risk; human sign-off on high risk.
9. **Standard PR template that captures AI involvement.** Addy Osmani's pattern: What/why (1-2 sentences), proof it works (tests, manual steps, screenshots/logs), risk + AI role (which parts were AI-generated), review focus (1-2 areas for human input).
10. **Generate tests as part of the review.** Have the AI reviewer write the test that would have caught the bug — turns review into regression prevention.
11. **Ad-hoc pre-push review.** Before opening a PR, paste the diff into Claude/GPT/Gemini for a 30-second sanity check. Costs nothing.
12. **Hard line on human accountability.** AI is first pass. **A human owns the merge.** Across every serious analysis, the same point.

## The Convergent Stack (What Most Serious Teams End Up With)

Three layers, not one tool:

1. **Deterministic linter/SAST**: SonarQube, Semgrep, or language-native (Ruff/mypy, ESLint, golangci-lint, clippy).
2. **AI reviewer**: CodeRabbit, Bugbot, Macroscope, or Graphite Agent. Pick one based on team's primary pain (noise tolerance, monorepo, stacked workflow, etc.).
3. **Cross-model second opinion**: Claude Code writes -> Codex reviews (or reverse).

Plus **stacked PRs** as the workflow scaffolding that makes all three work better.

That combination is more effective than any single "best" tool.

## The Homegrown Alternative

Worth a spike before committing to a SaaS code-review vendor for 12+ months:

- **Claude Code GitHub Action** (anthropics/claude-code-action) as the AI review engine.
- **Strict static checkers** (Ruff + mypy + ESLint + golangci-lint + Semgrep) emit graded reports.
- **Custom rubric** — the things this team cares about (e.g., "is the new endpoint authenticated?", "does this DB write have a transaction boundary?").
- **CI gates** that block merge on red findings, comment on yellow.

Lives in your repo, no per-seat lock-in, evolves with the codebase. Tradeoff: you maintain the rubric and the prompts. Pay-off: zero vendor risk.

## Caveats / Where This Could Be Wrong

- **Every "X% better" number in this page is vendor-reported.** Independent reviewer benchmarks (e.g., from BugLab, public eval suites) tell a noisier story. Treat vendor numbers as upper bounds, not expectations.
- **"CodeRabbit is the noisiest" is itself contested.** Independent comparisons cited in one source; CodeRabbit users routinely report different experiences. Tool configuration matters enormously.
- **The "different model writes vs reviews" tactic is community wisdom, not measured.** It's plausible and there are good theoretical reasons, but the magnitude of improvement is anecdotal.
- **"Stacked PRs ship 20% more code"** — one Graphite case study generalization. Real benefit varies enormously with team size, codebase, and existing workflow.
- **The 18% / 24% / 30% industry stats** come from one Addy Osmani Substack roll-up of multiple sources. Directional truth; not survey-grade.
- **The Claude Code Review section is built on Anthropic's own announcement** — they have every incentive to report well. Independent comparison data is still thin in mid-2026.

## Key Takeaways

- Code review is the most contested AI tool segment in 2026. There is no single "best" — the right answer depends on noise tolerance, codebase shape, and workflow.
- **Workflow > tool**: small PRs, stacked PRs, different model writes/reviews, layered deterministic+probabilistic.
- The convergent stack: deterministic linter + AI reviewer + cross-model second opinion + stacked PRs.
- A homegrown scaffold (Claude Code Action + strict checkers + custom rubric + CI gates) is a defensible alternative to picking one SaaS.
- Hard rule: a human owns the merge.

## Resources

- [Bringing Code Review to Claude Code (Anthropic)](https://claude.com/blog/code-review)
- [Custom Code Review rules for Codex (OpenAI)](https://developers.openai.com/blog/custom-code-review-rules-for-codex)
- [CodeRabbit](https://coderabbit.ai) / [Bugbot](https://cursor.com/bugbot) / [Greptile](https://greptile.com) / [Graphite](https://graphite.com) / [Macroscope](https://macroscope.com) / [Qodo](https://qodo.ai)
- Addy Osmani's Substack (industry stats roll-up): https://addyosmani.substack.com/
- See also: [`../tools-to-evaluate.md`](../tools-to-evaluate.md) for watch-only tools.
