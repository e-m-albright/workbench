# Security — supply-chain & secrets

> Curated taste, not mandate — read this to derive per-project choices.

The cheapest, highest-leverage engineering discipline most projects skip. Three layers: **don't commit secrets**, **don't ship known-vulnerable dependencies**, **keep dependencies current**. All of the defaults below are OSS, self-hostable, and free in CI for small/public repos. Bias: self-host-first, one tool over many, gate the delta not the backlog.

## Selection (pick / avoid)

| Concern | Pick | Avoid / notes |
|---------|------|---------------|
| Secret scanning | **gitleaks** | TruffleHog (heavier; its edge is live-credential *verification* — add in CI only if you need it) |
| Dependency vulns (cross-language) | **OSV-Scanner** (Google) | running every per-language auditor when one tool covers them all |
| Dependency vulns (Go, reachability) | **govulncheck** | keep alongside OSV-Scanner — it does call-graph reachability OSV doesn't |
| Dependency vulns (Rust) | **cargo-deny** (advisories + licenses + bans + sources) | cargo-audit alone (cargo-deny is a superset) |
| Dependency vulns (Python) | **pip-audit** | — |
| Dependency vulns (JS/TS) | **deno audit** / `pnpm audit --audit-level=high` for existing pnpm projects | — |
| Automated dependency updates | **Renovate** | Dependabot is fine and zero-ops *if* you're GitHub-only |
| Malicious-package detection | **Socket** (free GitHub App) | the one SaaS exception — catches typosquat/install-script exfil that CVE scanners miss |
| Secrets at runtime | **Infisical** (or Doppler / SOPS+age) | `.env` files as the source of truth; plaintext secrets in any tracked file |
| SBOM | skip as a solo default | generate on demand (Trivy/syft) only when a consumer requires attestation |

## The disciplines

### Secrets never live in files

`.env` holds **non-secret local config only**; real secrets come from a manager (Infisical/Doppler) overlaid at runtime. `.env.example` carries placeholder **names only**, never values. This makes "did we leak a secret" a structural non-question rather than a vigilance task.

- **gitleaks** runs both as a Lefthook pre-commit hook and a CI job (with `fetch-depth: 0` so the diff is deterministic across rebases).
- **Pin the gitleaks version.** Its action's stock version has historically ignored `[[allowlists]]` array-of-tables syntax, silently turning every documented exemption into a no-op. Version-dependent behavior must be pinned.
- Allowlist **surgically**: each exemption pairs a path glob *and* a content regex *and* a comment explaining why it's safe — so a rule rename or a genuinely new finding still surfaces.

### Provisioning ≠ rotation

Rotating an existing secret has a hot fallback (the old value stays valid during rollover). Provisioning a **brand-new** auth path (e.g. a new service-to-service key) does not — it's a hard failure until the secret exists in every consuming path. So a PR that introduces a new auth path should block on a provisioning checklist (mint → stage in every consumer → verify sync → deploy → end-to-end smoke that expects a 200), not merely on the code merging — otherwise a key that's defined-but-never-provisioned passes review and fails only when first traffic hits it.

### One audit command per language, pinned ignores

Wire a uniform `audit-<lang>` recipe per stack, aggregated under one `just audit` (or `just ci audits`), running only on lockfile change (cheap):

```
cargo deny check advisories && cargo deny check licenses   # Rust
uv run pip-audit                                           # Python
deno audit                                                 # JS/TS
govulncheck ./...                                          # Go
osv-scanner --lockfile=...                                 # cross-language gate
```

When an advisory is genuinely unavoidable, **pin the ignore with a written justification and a removal condition** (cargo-deny's `[advisories.ignore]`, pip-audit's `--ignore-vuln`). An un-annotated ignore is debt with no shelf life.

### Pin third-party CI Actions by commit SHA, not tag

GitHub Action tags are mutable and have been force-pushed to malware in real supply-chain attacks (the `trivy-action` compromise, March 2026). Pin every third-party Action by full commit SHA; let Renovate/Dependabot bump the SHA with a changelog in the PR. Treat bumps to anything touching **transport or security defaults** (auth libs, OTEL, the HTTP stack, an MCP server lib) as manual-review — a semver-silent default change there can be a breaking change discovered only via prod errors.

### Treat agent workspaces as active content

An OS sandbox can correctly confine an agent and still lose the security
boundary later. Files the agent writes may be interpreted by trusted host tools
outside the sandbox: editor tasks, agent hooks, Git configuration, Python
interpreter discovery, package scripts, build tools, or privileged local daemons.
Prompt injection in a README, issue, dependency, or diff can therefore become
host execution without a direct syscall escape.

Practical rules:

- Treat changes to `.claude`, `.vscode`, Git metadata, hooks, task files, package
  scripts, virtual environments, and tool configuration as executable changes.
  Review them before opening the project in a privileged editor or starting a new
  agent session.
- Do not rely on path denylists. Git metadata can live outside `.git`, and new
  executable configuration surfaces appear faster than filename lists evolve.
- Validate command semantics and arguments, not only the executable name. A
  nominally read-only command can invoke helpers or configuration that executes
  code.
- Keep agents away from Docker sockets and other privileged local daemons unless
  the task explicitly requires them. Access to a root-equivalent daemon defeats
  filesystem containment.
- Use an ephemeral clone, VM, or container for untrusted repositories and
  untrusted issue or dependency content. Do not grant broad unsandboxed retries
  merely because a command is incompatible with the sandbox.
- Review the artifacts an agent leaves behind, not only its process behavior.
  The important boundary is what trusted host software will execute next.

This class is commonly called a **configuration-based sandbox escape**. The 2026
reports affected Cursor, Codex, Gemini CLI, Antigravity, and earlier Claude Code
flows. Most named vendor issues were patched, but the architectural lesson is
broader than those versions.

Sources: [BleepingComputer summary](https://www.bleepingcomputer.com/news/security/cursor-codex-gemini-cli-antigravity-hit-by-sandbox-escapes/), [Pillar Security's Week of Sandbox Escapes](https://www.pillar.security/blog/the-week-of-sandbox-escapes), and [Cymulate's configuration-based sandbox escape research](https://cymulate.com/blog/the-race-to-ship-ai-tools-left-security-behind-part-1-sandbox-escape/), July 2026.

**Workbench posture:** Pi, Claude Code, and Codex use a shared restricted/unrestricted launch wrapper. Restricted is the default and applies an outer Seatbelt policy. Unrestricted omits that outer sandbox and permits harness edits while native approval rules remain active. Pi selects hosted or local inference separately. Verify the actual launch path and denied operations; this is not an NDA-compliance guarantee. No VM is deployed. The [launch matrix](../../docs/agents/pi/README.md#launch-modes-and-permission-guardrails) owns the current commands and limits.

## Quick reference: adopt in this order

1. **gitleaks** (pre-commit + CI) — blocks the single worst mistake; ~5-minute setup.
2. **One cross-language vuln gate** — OSV-Scanner, plus `govulncheck` if you ship Go seriously; `cargo-deny`/`pip-audit`/`deno audit` per-stack if you prefer native tools.
3. **Renovate** (or Dependabot if GitHub-only) — most vulns are fixed simply by staying patched.
4. **Secrets via a manager**, `.env.example` names-only — the structural fix.
5. **+1 if you touch npm/PyPI/crates often:** the free **Socket** GitHub App.

**Skip as a solo dev:** routine SBOM generation, TruffleHog verification mode, any paid security-scanner tier — those are compliance/enterprise concerns.

## See also

- [infrastructure.md](infrastructure.md) — CI gate structure, secrets sync, build discipline
- [Verification](../engineering/verification.md) — how these gates compose with code-health ratchets
- [../engineering-philosophy.md](../engineering/principles.md) — universal code-health principles

## Security / Static Analysis

- **[Semgrep](https://semgrep.dev)** -- Pattern-based SAST/SCA/secrets platform unifying static analysis with AI reasoning to detect IDORs, broken authz, and other logic-level vulnerabilities. Lightweight grep-like custom rule syntax plus reachability analysis (vendor claims 98% false-positive reduction). OSS Community Edition (free, self-hostable) plus SaaS AppSec Platform. Evaluate when you want fast SAST/secrets coverage with custom rules in CI without standing up a heavy platform.
- **[SonarQube](https://www.sonarsource.com/products/sonarqube/)** -- Code quality and security analysis covering 40+ languages with bug/vulnerability/code-smell detection. Quality Gates enforce deployment standards; SonarLint feeds the same rules into the IDE. Community Build OSS; Team plan ~$32/mo; Enterprise custom. Evaluate when you want enterprise-grade quality gates and broad language coverage across IDE + CI, especially for AI-generated code review.

## Static analysis

- **[Oxc and Oxlint](https://oxc.rs/docs/guide/what-is-oxc.html)** — **KEEP ON CONDITIONAL WATCH, not as an AI checker.** Oxc is a shared Rust compiler-tooling foundation; Oxlint 1.85.0 adds the relevant product surface through type-aware checks and ESLint-compatible JavaScript plugins. That plugin path can host focused agent-facing policies such as `@shadcn/lint`, but speed alone does not justify running a second linter beside Biome. Evaluate when a concrete typed rule or compatible plugin catches a demonstrated defect that Biome cannot, or measured lint latency becomes material. Preserve framework semantic checks either way.
- **[alint](https://github.com/moeru-ai/alint)** — **WATCH THE MODEL-BACKED SEMANTIC-LINT CATEGORY; do not gate CI yet (reviewed 2026-09-24).** This early MIT project turns model or tool-using-agent judgments into ESLint-shaped diagnostics, supports local OpenAI-compatible providers, dirty-file runs, cached results, and a cache-only language server. The category could encode contextual policies that syntax tools cannot express, but it is probabilistic review packaged as lint: findings can drift with the model and prompt, hosted use exposes code and incurs token cost, and upstream says its APIs may change. It currently duplicates Workbench's advisory review and adversarial-assessment paths. Trial only after the same semantic defect recurs at least three times and a bounded corpus can measure precision, recall, stability, latency, and cost; keep findings advisory until evidence supports one narrow gate.
- **[anti-slop](https://github.com/dmmulroy/anti-slop)** -- A deliberately opinionated set of local Oxlint JavaScript-plugin rules for patterns such as chained assertions, widening known values to `unknown`, unparsed boundary values, module mocking, and unexplained type assertions. The useful thesis is already adopted: deterministic checks should enforce mechanically expressible policy instead of asking an agent instruction file to remember it. Do **not** vendor the complete ruleset into the current Biome projects: it adds a second linter plus owned plugin source, performs only same-file ESTree analysis rather than TypeScript type analysis, and several taste rules such as banning ad hoc `typeof` checks are broader than the demonstrated problem. Mine individual rules only after a recurring defect supplies a fixture and false-positive test. The first plausible candidates are chained assertions and widen-then-assert; the existing suppression ratchet remains the cheaper general guard. Source discussion: [Better Stack video](https://www.youtube.com/watch?v=mmrSYvYKD9g).

## Tamper-evident audit logging (2026-08 research spike)

For "prove person X accessed data Y" product features (HIPAA-credible access trails). Key insight: the crypto structure is cheap -- nearly all the security comes from anchoring periodic checkpoints *outside* the operator's control (customer-held, RFC 3161 timestamp authority, public transparency log, or object-locked storage in a separate account). Cryptographic proof is never regulator-required (HIPAA/SOC 2 are technology-neutral); it is a differentiator and a forensics asset. Recommendation ladder: (1) MVP ~1 week -- hash-chained INSERT-only Postgres/SQLite table + signed nightly checkpoints to S3 Object Lock compliance mode in a separate account (+ pgaudit for out-of-band DBA access); (2) customer-verifiable -- Merkle tree via Tessera, checkpoints published to customers and anchored to public Rekor; (3) auditor-grade -- witnessed per-tenant logs, only when HITRUST/contract demands it. Full survey with regulation citations lives in the private notes wiki (`audit-logging`).

- **[Tessera](https://github.com/transparency-dev/tessera)** -- Trillian's successor for verifiable append-only logs (tile-based, Certificate-Transparency lineage). GA v1.0.x, very active (as of 2026-08). Embeddable Go library, backends from POSIX files to S3/Aurora/Spanner. The OSS pick when inclusion/consistency proofs become a product feature. (Trillian v1 itself: maintenance mode, don't start new logs on it.)
- **[Sigstore Rekor v2](https://github.com/sigstore/rekor-tiles)** -- Public signature-transparency log, rebuilt on Tessera, GA (as of 2026-08). Pattern worth stealing even outside supply-chain: anchor your own log's checkpoint hashes into the public instance as free, operator-independent existence proofs (hashes only -- never sensitive payloads).
- **[immudb](https://github.com/codenotary/immudb)** -- Immutable KV/SQL DB with built-in Merkle proofs + client-side verification. Alive (v1.11.x, 2026) but single-vendor with historically gappy cadence; proofs-without-building-them, risky as a sole system of record.
- **[pgaudit](https://github.com/pgaudit/pgaudit)** -- Postgres session/object audit to the server log; actively maintained per PG major. Complement to an app-level audit table (it catches out-of-band DBA access; the app table carries business meaning). Available on RDS/Aurora/Cloud SQL.
- **Retired/risky**: AWS QLDB shut down 2025-07-31 (AWS's own migration guidance is trigger-based hash chaining on Aurora PostgreSQL); Pangea Secure Audit Log acquired by CrowdStrike (roadmap risk); Azure SQL Ledger is the best managed option iff already on Azure/MSSQL.
