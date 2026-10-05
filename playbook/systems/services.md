# Cloud Services Reference

**Philosophy**: Self-hosted first when practical. Managed services when self-hosting becomes a burden.

> **Note**: This is a menu, not a mandate. Most projects need only 2-3 services.
> A simple app needs hosting + database. Add services as requirements emerge.
>
> Vercel and Cloudflare now span several categories below. Use the dedicated [Vercel and Cloudflare stack watch](cloud-platforms.md) for their complete product roles, ownership ties, and cross-category selection guidance.

---

## Decision Framework

```
                    ┌─────────────────┐
                    │ Do you need it? │
                    └────────┬────────┘
                             │ yes
                    ┌────────▼────────┐
                    │ Can you         │
                    │ self-host it?   │
                    └────────┬────────┘
                      yes    │    no
                    ┌────────┴────────┐
                    ▼                 ▼
            ┌───────────┐    ┌───────────────┐
            │ Self-host │    │ Use managed   │
            │ (Railway, │    │ service       │
            │  Docker)  │    │               │
            └───────────┘    └───────────────┘
```

---

## Hosting

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **General** | Railway | Render | Railway: better DX, nixpacks. Render: cheaper for static. |
| **Edge/Static** | Cloudflare Pages | Vercel | Cloudflare: free tier, Workers. Vercel: Next.js native. |
| **Containers** | Fly.io | Railway | Fly.io: global edge, VMs. Railway: simpler PaaS. |

### When to Use What

- **Railway**: Default for most backend services. Great DX, easy scaling.
- **Cloudflare**: Static sites, edge functions, anything latency-sensitive.
- **Fly.io**: When you need VMs, global distribution, or SQLite (LiteFS).
- **Render**: Budget option, good for simple services.

---

## Infrastructure as Code

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **AWS + TypeScript** | SST | AWS CDK | SST: full-stack IaC in one `sst.config.ts`, Pulumi under the hood, fast local dev. CDK: lower level, use only for resources SST doesn't expose. |
| **Multi-Cloud** | Pulumi | Terraform / OpenTofu | Pulumi: real languages (TS/Python/Go). Terraform: industry standard (HCL), huge ecosystem. OpenTofu: OSS fork after HashiCorp license change. |

### When to Use What

- **SST**: Default for AWS + TypeScript. Defines Lambda, RDS, S3, queues, frontends in one config. Skip if you need multi-cloud.
- **Pulumi**: Multi-cloud or when SST doesn't cover your resource. More verbose but more flexible.
- **Terraform/OpenTofu**: Large infra teams, multi-cloud at scale. Overkill for solo devs on AWS.
- **AWS CDK**: SST is strictly better DX. Only use raw CDK for L3 constructs SST doesn't expose.

---

## Database

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Managed Postgres** | Supabase | Neon | Supabase: Postgres + auth + storage. Neon: pure Postgres, branching, scale-to-zero. |
| **Managed MySQL** | PlanetScale | — | Serverless MySQL on Vitess (YouTube's scaler). DB branching, non-blocking migrations. Killed free tier in 2024 ($39/mo min). |
| **Edge SQLite** | Turso | Cloudflare D1 | Turso: libSQL, replicas, cheap per-tenant isolation. D1: Cloudflare-native. |
| **Self-Hosted** | PostgreSQL on Railway | — | Just deploy a Postgres container. |

### When to Use What

- **Supabase**: Need Postgres + extras (auth, storage, realtime). Good free tier.
- **Neon**: Pure Postgres, need database branching for previews. Default "Postgres with nice devex."
- **PlanetScale**: Strong if you need MySQL or massive horizontal scale. Fewer ecosystem tools than Postgres.
- **Turso**: Edge-first, SQLite-compatible, global reads. Per-tenant DB isolation is cheap — good for multi-tenant SaaS with audit boundaries.

### Supabase Accelerators

| Tool | Purpose | Notes |
|------|---------|-------|
| **Basejump** | Multi-tenant SaaS | Pre-built RLS policies, team/org management, billing integration. Huge time saver. |

---

## NoSQL / Key-Value / Document

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **AWS Native KV** | DynamoDB | — | Single-digit ms at any scale. Pairs with Lambda/SST. Demands access-pattern-first design. |
| **Document DB** | MongoDB Atlas | — | Flexible JSON docs, aggregation pipeline, built-in full-text search. Less relevant if already using Postgres with JSONB. |
| **Cache + Queues** | Valkey / Upstash | Dragonfly | Valkey: Redis fork (self-hosted). Upstash: serverless Redis, per-request billing. Dragonfly: extreme perf. |

### When to Use What

- **DynamoDB**: Known, high-throughput access patterns (sessions, event logs, webhook state). Painful for flexible queries. Most solo devs should start with Postgres and migrate if they hit the wall.
- **MongoDB Atlas**: Variable-schema data, need full-text search without a separate service. Atlas Search is genuinely useful.
- **Valkey/Upstash**: Almost always needed alongside a primary DB for caching, rate limiting, pub/sub, sessions. Upstash pairs well with serverless (Railway/Vercel) — no persistent server to manage.

---

## Analytics (OLAP)

> **For heavy analytical queries.** Most apps don't need this—Postgres is fine for dashboards.

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **In-Process** | DuckDB | — | Query Postgres/Parquet with SQL. No server needed. Embeds in Python/Node/Rust. |
| **Managed** | Tinybird | ClickHouse Cloud | Tinybird: API-first, real-time. ClickHouse: raw power, millions of rows/sec ingest. |
| **Self-Hosted** | ClickHouse | — | Only for serious OLAP workloads at scale. |
| **Data Warehouse** | Snowflake | BigQuery | Snowflake: multi-cloud, excellent data sharing across orgs. BigQuery: GCP-native, pay-per-query, petabyte-scale. Both integrate with dbt. |

### When to Use What

- **DuckDB**: Default for analytics. Query your existing data without infrastructure.
- **Tinybird**: Real-time analytics APIs, user-facing dashboards, event streaming.
- **ClickHouse**: When DuckDB isn't fast enough (rare). Petabyte-scale analytics.

> **Note**: Most SaaS apps should start with Postgres + DuckDB. Add ClickHouse/Tinybird when you have millions of events and need sub-second queries. Snowflake or BigQuery may be needed when an application must integrate with an existing enterprise warehouse.

---

## Search

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Full-Text** | Meilisearch | Typesense | Meilisearch: easier setup. Typesense: more features. |
| **In-Browser** | Orama | Pagefind | Orama: full-featured. Pagefind: static site search. |

### Self-Hosting Meilisearch

```yaml
# docker-compose.yml
services:
  meilisearch:
    image: getmeili/meilisearch:v1.35
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
    volumes:
      - meilisearch_data:/meili_data
    ports:
      - "7700:7700"
```

> **Managed Option**: Meilisearch Cloud when self-hosting becomes a burden.

---

## Email

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Transactional** | Resend | Postmark | Resend: modern DX, React Email. Postmark: deliverability focus. |
| **Marketing** | — | — | Skip until you need it. Use Resend for basic emails. |

### Resend Example

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

await resend.emails.send({
  from: 'noreply@yourdomain.com',
  to: user.email,
  subject: 'Welcome!',
  react: <WelcomeEmail name={user.name} />,
});
```

---

## Authentication

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Self-Hosted** | Better Auth | — | Full-featured, TypeScript-first, active development. |
| **Managed** | Clerk | Auth0 | Clerk: modern DX. Auth0: enterprise features. |

### When to Use What

- **Better Auth**: Default. Self-hosted, full control, TypeScript-first, excellent SvelteKit integration.
- **Clerk**: When you don't want to manage auth infrastructure.
- **Clerk for delegated agents**: Clerk now supports OAuth-protected MCP servers through Client ID Metadata Documents or Dynamic Client Registration, consent and scopes, and authenticated Agent Task sessions that act on a user's behalf. This makes Clerk the stronger managed candidate when an application needs user-delegated agent access, not merely sign-in. Keep permissions narrow and inspect the session lifecycle before adopting; several AI-facing capabilities remain beta.

### Better Auth Setup

```typescript
// auth.ts
import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';

export const auth = betterAuth({
  database: drizzleAdapter(db, { provider: 'pg' }),
  emailAndPassword: { enabled: true },
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
  },
});
```

---

## Analytics

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Privacy-First** | Plausible Cloud | Umami (self-hosted) | Plausible is the managed default; Umami is the free, self-hosted option. |
| **Product Analytics** | PostHog | — | When you need feature flags, experiments, or session replay. |

### Plausible

Use Plausible Cloud by default for public websites that need traffic, campaign,
and conversion analytics. It provides a focused dashboard, custom events,
revenue attribution, Google Search Console integration, and EU-hosted,
cookieless data processing. Managed hosting is preferable here because web
analytics is supporting infrastructure, not a product capability worth
operating.

Use Umami instead when self-hosting or its free hosted tier is a project
constraint. Graduate to PostHog only when the product needs behavioral tooling
such as feature flags, experiments, or session replay.

---

## Caching

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Self-Hosted** | Valkey | Dragonfly | Valkey: Redis fork (post-license change). Dragonfly: faster. |
| **Managed** | Upstash | — | Serverless Redis. Pay per request. |

### When to Use What

- **Valkey**: Default for self-hosted. Drop-in Redis replacement.
- **Upstash**: Serverless, don't want to manage infrastructure.
- **Dragonfly**: Need extreme performance, drop-in Redis replacement.

---

## Queues / Event Streaming

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **AWS Native** | SQS / SNS | — | SQS: managed queue (pull). SNS: pub/sub (push). Both integrate with Lambda/SST natively. No ops. |
| **High-Throughput** | Kafka / Redpanda | — | Log-based streaming. Replay, fan-out, history retention. Redpanda: Kafka-compatible, faster, simpler ops. |
| **Serverless** | Upstash Kafka / QStash | — | Serverless Kafka + HTTP job queues. QStash: great for delayed jobs from serverless functions. |

### When to Use What

- **SQS/SNS**: Default if you're on AWS. SST wires them to Lambda trivially.
- **Kafka/Redpanda**: Real-time data feeds, event sourcing, audit logs at scale. Overkill for most early-stage apps.
- **QStash**: Underrated for webhook delivery and scheduled jobs from serverless (Railway/Vercel). No persistent server needed.

---

## Durable Execution / Workflows

> **For multi-step workflows that must survive a crash and resume from the last completed step** — strictly stronger than a queue (which only retries the whole job). The 2026 split is *library-on-Postgres* vs *server-you-operate*; for a Postgres-centric solo/small stack the former wins.

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Lightweight (library)** | DBOS | — | Postgres-only, runs *inside* your app process (Python/TS/Go). The "lightweight Temporal" — durability with zero new infra. Best default. |
| **Go background jobs** | River | asynq | Postgres-backed, transactional enqueue. A queue, not full durable execution. |
| **TS event-driven** | Inngest | Trigger.dev | Inngest: light self-host (single binary). Trigger.dev: more of a platform (registry + object storage). |
| **Heavy-duty** | Temporal | Restate (watch) | Cross-language, mission-critical scale. Temporal's cluster is a real operations burden; Restate aims for a lighter event-log-based runtime. Reach for either only when correctness at scale demands it. |
| **Platform-native** | Vercel Workflows / Cloudflare Workflows | — | Watch when the application already lives on that platform; compare portability and state export with DBOS, Inngest, and Temporal. |

### When to Use What

- **DBOS**: Default. A library, not a server — `pip install`/`npm i`, point at existing Postgres, decorate workflow/step functions. Matches the "Postgres as the only dependency" ethos. Free OSS core; only the ops console is paid.
- **Temporal**: When you genuinely need multi-DC, millions of concurrent workflows, or cross-service orchestration. Self-hosting the cluster is exactly the ops burden most projects should avoid; even Temporal concedes Cloud beats self-host economically below tens of millions of actions/month.
- **Plain Postgres + cron / Arq / River / QStash**: When the real need is "run on a schedule" or "a few retryable jobs." Durable execution only pays off once you have genuinely multi-step workflows with side effects you must not re-run.

[Restate's September 2026 funding announcement](https://restate.dev/blog/announcing-series-a) is market validation for durable execution, not product validation. Its useful claim is architectural: long-running agent work makes waits, retries, callbacks, partial failure, and duplicate side effects ordinary application concerns. Compare Restate when a real workflow needs those guarantees and its low-latency service or virtual-object model fits better than a Postgres library. Keep the business state machine, idempotency semantics, approvals, and unknown-outcome reconciliation in application-owned code. A $20 million Series A and vendor benchmarks do not displace the default progression from queue to DBOS to a heavier runtime.

---

## Realtime / Local-First Sync

> **For offline-first or live-multiplayer UIs.** A "solution looking for a problem" trap — don't adopt speculatively. Add only when there's a concrete offline/realtime requirement.

| Need | Pick | Notes |
|------|------|-------|
| Read-sync on your own Postgres | **ElectricSQL** | Postgres → client SQLite via declarative "shapes"; OSS, self-hostable. Best fit for a Postgres-centric SvelteKit shop. |
| Mobile/offline, production-tested | PowerSync | You own writes/conflict resolution via your API. |
| Collaborative text/rich-doc editing | Yjs | CRDT library — the right tool for collaborative editing, not structured-data sync. |
| General-purpose sync (watch) | Rocicorp Zero | Ambitious; still alpha — watch, don't build on yet. |

Convex / Liveblocks / PartyKit trade self-host-first for hosted DX — fine for speed, but a platform dependency.

---

## Payments

| Category | Primary Pick | Notes |
|----------|-------------|-------|
| **Payments** | Stripe | Industry standard. No real alternative at this level. |
| **Alternative** | LemonSqueezy | Merchant of record. Handles taxes for you. |

> **Note**: Use Stripe unless you specifically need merchant-of-record (LemonSqueezy handles sales tax/VAT).

---

## Observability

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Error Tracking** | Sentry | — | Industry standard. Excellent SDKs. |
| **Logs** | Grafana Cloud | Axiom | Grafana: full stack. Axiom: simpler, generous free tier. |
| **Tracing** | Jaeger | Grafana Tempo | Self-host Jaeger. Or use Grafana Tempo in Grafana Cloud. |

### Observability Tiers

```
Tier 1 (All Projects):
├── structlog / pino (logging)
└── Sentry (error tracking)

Tier 2 (2+ Services):
├── OpenTelemetry instrumentation
└── Basic metrics

Tier 3 (At Scale):
├── Jaeger / Grafana Tempo (tracing)
├── Grafana dashboards
└── Prometheus (metrics)
```

---

## Quick Reference: What to Use When

| Project Type | Services |
|-------------|----------|
| Simple API | Railway + Supabase + Sentry |
| + Auth | add Better Auth |
| + Email | add Resend |
| + Search | add Meilisearch (self-hosted) |
| + Caching/Queues | add Upstash (Redis + QStash) |
| SaaS Product | above + Stripe + Umami + PostHog |
| + AI Features | add Modal or pgvector |
| + IaC | SST (AWS) or Pulumi (multi-cloud) |
| At Scale | add Grafana Cloud + OpenTelemetry |
| + Analytics | add ClickHouse or Snowflake |
| + Event Streaming | add SQS/SNS (AWS) or Redpanda |
| Enterprise Data Integration | Snowflake or BigQuery + dbt |

---

## AI Infrastructure

> **For running ML models and AI workloads**, not for coding assistance.

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Serverless GPU** | Modal | Replicate | Modal: full control, Python-native. Replicate: pre-built models, API-first. |
| **Model Hosting** | Replicate | Baseten | Replicate: easy API. Baseten: more customization, self-hosted option. |

### When to Use What

- **Modal**: Default for custom AI workloads. Python-native, excellent DX, auto-scaling GPUs.
- **Replicate**: Running pre-trained models via API. Quick integration, no infra management.
- **Baseten**: Enterprise needs, self-hosted requirements.

### Modal Example

```python
import modal

app = modal.App("my-ai-service")


@app.function(gpu="A10G")
def run_inference(prompt: str) -> str:
    # Your model code here
    return result
```

> **Note**: For simple embeddings or completions, just use OpenAI/Anthropic APIs directly. Modal/Replicate are for custom models or heavy inference workloads.

---

## Vector Databases

> **For semantic search and RAG applications.** Most projects should start with pgvector.

| Category | Primary Pick | Alternative | Notes |
|----------|-------------|-------------|-------|
| **Postgres Extension** | pgvector | — | Add to existing Postgres. Good enough for most use cases. |
| **Managed Vector DB** | Pinecone | Weaviate Cloud | Pinecone: simple, fast. Weaviate: more features. |
| **Self-Hosted** | Qdrant | Milvus, Weaviate | Qdrant: best DX. Milvus: highest scale. |
| **Embedded** | LanceDB | Chroma | LanceDB: serverless, multimodal. Chroma: simpler. |
| **Library** | FAISS | — | Meta's similarity search. Embed in apps, not a full DB. |

### Decision Tree

```
How much vector data?
├── < 1M vectors → pgvector (in your existing Postgres)
├── 1M-100M vectors → Qdrant or Pinecone
└── > 100M vectors → Milvus or dedicated solution
```

### pgvector Setup (Supabase)

```sql
-- Enable the extension
create extension vector;

-- Add vector column
alter table documents add column embedding vector(1536);

-- Create index for fast similarity search
create index on documents using ivfflat (embedding vector_cosine_ops);
```

> **Recommendation**: Start with pgvector. Only move to dedicated vector DBs when you hit scale limits or need advanced features (hybrid search, filtering, etc.).

---

## Anti-Recommendations

| Service | Why to Avoid |
|---------|-------------|
| Firebase | Vendor lock-in, proprietary query language. |
| Heroku | Pricing, removed free tier, stagnant. |
| Auth0 | Complex, expensive, enterprise-focused. |
| Datadog/New Relic | Overkill for small teams, expensive. |
| AWS/GCP/Azure directly | Complexity overhead. Use Railway/Fly.io instead. |
| Vercel | Pricing traps, vendor lock-in, Next.js-centric. Use Railway or Cloudflare instead. |
| Next.js | Vercel-coupled, complexity creep. Use SvelteKit or Astro instead. |

## Cloud / Hosting Providers

Personal vibes-check on the current player set (2026-05). Opinions, not benchmarks — refine as we get hands-on. The maintained product-by-product comparison now lives in [`stacks/vercel-cloudflare.md`](cloud-platforms.md); keep these bullets as the broader provider shortlist rather than duplicating that inventory.

- **Cloudflare** -- Generally a strong platform that keeps getting better (Workers, D1, R2, Pages, Queues all maturing). Some questions on the team, but the product trajectory is solid.
- **Vercel** -- Probably still a decent solution for Next.js-native frontends. Terrible place to scale (pricing traps, vendor lock-in — already flagged in `playbook/systems/services.md` "When NOT to Use"). Some questions on the team. Very AI-forward / tech-forward, so they'll keep shipping interesting things.
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

## Scaling up — enterprise-level + good cost (2026-05 take)

Picking by stage and constraint, since "best" depends on what you're optimizing:

- **Best raw $/perf if you can self-manage:** Hetzner + Coolify (or Kamal for code-as-config). Brutal cost advantage; you own the ops burden. Good for serious scale if you have someone who likes infra.
- **Best PaaS DX without lock-in at scale:** Northflank BYOC into AWS or GCP. You get Railway-grade DX, but the underlying resources are your hyperscaler account — so you can negotiate enterprise commits, satisfy compliance, and exit if needed.
- **Best edge-native + flat pricing at scale:** Cloudflare. Workers + D1 + R2 + Queues + Durable Objects. Egress is free (huge), R2 has no egress fees vs S3, D1 has predictable per-request pricing. Weakness: long-running compute and big-RAM workloads are awkward.
- **Best if you must be on a hyperscaler:** AWS via SST (already the services.md default for TS). Pick AWS if compliance / partner ecosystem / enterprise sales demand it; otherwise the cost story is worse than the alternatives above.
- **Avoid for "serious scale":** Vercel (pricing traps), Railway (ceiling unclear, less BYOC story), Heroku (don't).

Rough mental model: **Hetzner+Coolify** for cost-floor self-host, **Northflank BYOC** for PaaS-DX-at-enterprise, **Cloudflare** for edge-native, **AWS+SST** for compliance/ecosystem reasons. Most serious shops end up running 2 of these.
