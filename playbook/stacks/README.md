# Stacks — curated technology taste

**Taste, not mandate.** These docs capture our current opinions on languages, tools, and frameworks so an AI agent (or human) can *consult them per-project to derive appropriate choices* — not so they get pushed verbatim into every repo. The field moves fast; treat these as a strong default to argue with, not a contract.

## How to use, per project

1. Open the language directory and read its `README.md` for **Selection** (pick / avoid / by phase) — most projects only need Phase 1.
2. Skim **Idioms** for how we write the language.
3. Pull **Code patterns** when you need a concrete starting point.
4. Check the language's `frameworks/` for the blessed framework choices.
5. Cross-reference [`../engineering-philosophy.md`](../engineering-philosophy.md) (universal principles) and relevant [recorded decisions](../../docs/decisions/).

## Languages

Start with the [programming-language landscape](languages.md) for the five-tier selection map. Each adopted language then has a directory with `README.md` for selection, idioms, and patterns and a `frameworks/` subdirectory.

- [**python/**](python/README.md) — + [ml.md](python/ml.md) (data/ML) · frameworks: [fastapi](python/frameworks/fastapi.md)
- [**typescript/**](typescript/README.md) — [full-stack framework landscape](typescript/frameworks/README.md) · adopted guides: [sveltekit](typescript/frameworks/sveltekit.md), [astro](typescript/frameworks/astro.md)
- [**golang/**](golang/README.md) — frameworks: [chi](golang/frameworks/chi.md)
- [**rust/**](rust/README.md) — frameworks: [axum](rust/frameworks/axum.md), [tauri](rust/frameworks/tauri.md)

## Cross-cutting

- [services.md](services.md) — hosting / db / auth / payments / queues / durable execution / realtime / observability picks (self-host-first)
- [vercel-cloudflare.md](vercel-cloudflare.md) — product-by-product watch of the converging Vercel and Cloudflare web and agent stacks
- [infrastructure.md](infrastructure.md) — Docker, IaC, dev-env tooling, observability topology + footguns, build discipline
- [security.md](security.md) — supply-chain & secrets (gitleaks, dependency auditing, secrets management)
- [data-stores.md](data-stores.md) — embedded/agent-written data stores: SQLite+DuckDB default, rejected "agent memory" engines, graduation triggers
