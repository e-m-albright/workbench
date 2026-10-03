# Data Stores — embedded, agent-written, and "agent memory" engines

> **Taste, not mandate** — see [`README.md`](../languages/README.md). **Last surveyed:** 2026-07-26.
> Revisit cue: a named capability gap the default stack cannot serve, or a
> step-change in a tracked engine.

Survey context: choosing the structured data layer for an agent-written
personal knowledge system — concurrent agent writers, git-reviewable history,
entity/edge graph queries, full-text and vector search, decades-long
durability expectations. The conclusions generalize to most single-host,
agent-written stores.

## Default pick

**SQLite as the system of record, DuckDB as the query lens.** One file, two
engines — SQLite for transactional writes (multi-process safe via WAL), DuckDB
attached read-only for analytics and ad-hoc SQL. A deterministic text dump
committed via pre-commit hook keeps every agent write reviewable as a git diff.

The [supplied DuckDB first-impressions video](https://www.youtube.com/watch?v=KJao6oq9MKM) describes its embedded, columnar, file-querying design. It adds no new adoption decision: use DuckDB for analytical reads over files and data frames, and keep concurrent application writes in the transactional source.

## Guiding principles

- **Storage engines don't do "agent memory."** Across every "database for
  agents" product examined, entity extraction, temporal fact management, and
  enrichment are ALWAYS application-layer LLM pipelines over a conventional
  store (Graphiti over Neo4j/FalkorDB, Mem0's pipeline with its own SQLite
  truth list, Cognee over SQLite+LanceDB+Kuzu files, Neo4j's agent-memory
  labs) — never a storage-engine property. The era's two loudest "built for
  agents" engine launches (Turso, Tiger Agentic Postgres) are pitches for
  SQLite files and Postgres respectively.
- **Steal the ideas, not the engines.** Graphiti-style bitemporal edge columns
  (`valid_at` / `invalid_at`, supersede-never-delete; arXiv 2501.13956) deliver
  "what did we believe when" without adopting XTDB.
- **A lifelong personal dataset outlives seed-stage vendors.** Hosted memory
  SaaS (Zep/Mem0 platform, Supermemory, Honcho) is the definitional vendor
  risk for data you intend to keep for decades.
- **Adoption requires a written capability case** — a named gap the incumbent
  stack cannot serve, not novelty.

## Catalog — evaluated and rejected (2026-07-26)

Revisit any of these only with a written capability case.

| Engine | Category | Why rejected | Revisit trigger |
|---|---|---|---|
| **SurrealDB** | multi-model | Embedded mode measured 15–60x slower than SQLite (June 2026 community benchmark); SurrealQL + BSL license lock-in; "agent memory" positioning is storage features plus marketing, not extraction | A capability gap SQLite genuinely can't cover |
| **Gel** (ex-EdgeDB) | graph-relational | Server weight class for an embedded, single-host use case; strong schema/query language but wrong deployment shape | Same |
| **Kuzu** | embedded graph | Abandoned upstream 2025-10 after the Apple acqui-hire; forks (Bighorn, Ladybug) have no consolidated steward — the embedded-graph category currently has **no viable option** | A fork consolidates a real steward *and* traversal becomes the primary interrogation mode |
| **Dolt** | versioned SQL | Row-level branch/merge is compelling, but a committed deterministic SQL dump already covers reviewability at current write volume | Data PRs at high agent write volume |
| **XTDB** | bitemporal | Bitemporality covered more cheaply by Graphiti-style `valid_at`/`invalid_at` edge columns in SQLite | Historical truth and conflicting sources becoming the heart of the data model |
| **Parquet** | columnar format | Immutable analytics format, wrong for a mutable store | — |
| **DuckDB (as store)** | OLAP | Single-writer file locking loses to concurrent agent sessions; superb as the read lens, wrong as the record | — |
| **Hosted memory SaaS** (Zep, Mem0, Supermemory, Honcho) | SaaS | Lifelong personal graph on seed-stage SaaS = definitional vendor risk | — |

## Catalog — adopted or in play

| Tech | Role | Notes |
|---|---|---|
| **SQLite** | system of record | Typed columns for closed vocabularies, JSON columns for flex attributes, FTS5 over prose, edges as relation tables, WAL for multi-process safety |
| **DuckDB** | query lens | Attaches/reads the SQLite data for recipes and ad-hoc analytics |
| **sqlite-vec** | embeddings | v0.1.9 stable 2026-03. Single-maintainer risk accepted because the vector index is derived and regenerable |
| **LanceDB** | embeddings fallback | If volume ever outgrows brute-force KNN |
| **Cognee** | optional experiment | Run its LLM extraction over a corpus and diff its graph against curated edges; output imports into SQLite; never canonical (its default graph store is orphaned Kuzu) |
| **Graphiti** (pattern only) | bitemporal edges | The idea import, not the product — see guiding principles |

## When the workhorses win — and when they don't

- **SQLite** is the default for a single-host, file-shaped, agent-written
  store: zero ops, git-adjacent, embeddable everywhere, FTS5 + sqlite-vec
  cover search. Its CHECK constraints being immutable means vocabulary changes
  are schema-version migrations — plan for that.
- **Postgres + pgvector** is the named graduation target: adopt when semantic
  retrieval or concurrent *remote* access outgrows SQLite. Not before.
- **An embedded graph engine** earns a place only if traversal becomes the
  primary interrogation mode — and today the category has no well-stewarded
  candidate anyway (see Kuzu row).
- **The exotic capabilities** (bitemporality, versioned branches, multi-model)
  are each individually replicable on the workhorses at current scale:
  bitemporal columns, dump-diffs, JSON columns. The specialist engines start
  paying rent only when one of those capabilities becomes the *center* of the
  workload rather than a feature.

## Open questions / to-do (tracked)

- [ ] **Cognee extraction experiment** — cheap, optional: diff its extracted
      graph against hand-curated edges to measure what LLM extraction adds.
- [ ] **Embedded-graph category re-check** — does any Kuzu fork (Bighorn,
      Ladybug) consolidate a steward? Quarterly glance, no action otherwise.
- [ ] **Re-verify churny facts** before any adoption decision: SurrealDB
      embedded benchmarks, Gel licensing/positioning, sqlite-vec maintenance
      cadence. All fast-moving.

*Fast-moving category — re-verify before committing to anything.*

## Data

- **[DuckDB WebAssembly](https://www.infoq.com/news/2026/01/duckdb-iceberg-browser-s3/)** -- Query Iceberg datasets in the browser.
- **[Turso](https://thenewstack.io/why-we-created-turso-a-rust-based-rewrite-of-sqlite/)** -- Rust rewrite of SQLite. Edge-native.
- **[MotherDuck semantic layer for DuckDB](https://motherduck.com/blog/semantic-layer-duckdb-tutorial/)** -- Semantic layer tutorial.
- **[Pandera](https://github.com/unionai-oss/pandera)** -- Declarative schema validation for dataframes (pandas, Polars, PySpark, Modin, Dask). Pydantic-style `DataFrameModel` class API plus statistical hypothesis checks. The right default for validating ETL boundaries and the contract between untrusted input and downstream analytics. Catches schema drift at the boundary instead of through defensive code in pipeline logic.
- **[Polars Cloud](https://cloud.pola.rs/)** -- Managed serverless Polars compute. Same Polars API runs on a laptop or scales across distributed clusters; pay-per-second, no idle charges. AWS now, GCP/Azure planned. Worth tracking when a pandas/Polars pipeline outgrows a single machine but a full Spark cluster is overkill.
- **[TigerBeetle](https://tigerbeetle.com/)** -- Purpose-built double-entry accounting database (Zig): accounts + transfers as fixed 128-byte immutable records, ~1M transfers/sec, strict serializability, Viewstamped Replication, famously rigorous deterministic simulation testing ("VOPR"). Evaluate only if ever moving actual money at volume -- it is not a general database (no SQL, no arbitrary tables) and its immutability is operational, not cryptographic, so it is **not** an audit-log substrate (evaluated 2026-08: for "prove person X accessed data Y", a hash-chained table + external anchoring wins; see the audit-logging cluster below). The deterministic-simulation testing culture is worth studying regardless.

## Specialist data layer (when to pick over a full provider's DB)

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
