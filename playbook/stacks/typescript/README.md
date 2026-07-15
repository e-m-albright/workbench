# TypeScript

> Curated taste, not mandate — read this to derive per-project choices.

## Selection (pick / avoid / by phase)

Selection is *what* to reach for. Idioms below are *how* to use them. Detect the existing stack from project files before applying any of this — never switch package managers, linters, or frameworks in a project that already chose otherwise.

### Phase 1 — every project

| Category | Pick | Avoid (why) |
|----------|------|-------------|
| Runtime | **Deno** | Bun; Node.js remains the compatibility fallback |
| Lint + format | **Deno native** for pure Deno; **Biome** for broader projects | ESLint + Prettier unless inherited |
| Task runner | **Just / Deno tasks** | A second orchestration layer without a demonstrated need |
| Git hooks | **Lefthook** | Husky (slower, JS-based) |
| Styling | **Tailwind CSS v4** | CSS-in-JS (runtime cost), Sass (verbose) |

### Phase 2 — when needed

| Need | Pick | Avoid (why) |
|------|------|-------------|
| Full-stack app | **SvelteKit 2** | Next.js (React bloat, Vercel-coupled), Nuxt (Vue) |
| Content site | **Astro** | Gatsby (stagnant), Hugo (non-JS) |
| Vite build layer | **Vite 8** | Direct bundler configuration without a concrete need |
| UI components | **shadcn-svelte + Bits UI** | Chakra/MUI (React-only, heavy) |
| ORM | **Drizzle** | Prisma (heavy engine and slower iteration) |
| Database | **PostgreSQL** | SQLite (lacks concurrent writes) |
| Auth | **Better Auth** (Lucia for lightweight) | Auth0 (complex), NextAuth (React-only) |
| Forms | **Superforms + Zod** | Formik (React-only) |
| Validation | **Zod** | Yup (worse TS inference) |
| Data fetching | **TanStack Query** | SWR (React-only) |
| Charts | **LayerChart** | Recharts (React-only), Chart.js (limited) |
| i18n (SvelteKit) | **Paraglide JS 2.0** | i18next (runtime overhead) |
| Unit testing | **Deno test** for pure Deno; **Vitest** for Vite apps and components | Replacing Deno test merely for uniformity |
| E2E testing | **Playwright** (+ `@axe-core/playwright` for a11y) | Cypress (heavier) |
| LLM client | **Vercel AI SDK** (`ai` + `@ai-sdk/svelte`) | provider-locked SDKs — AI SDK is provider-agnostic with first-class streaming |
| Typed API contract | **SvelteKit remote functions** in-app; **oRPC** for external clients | tRPC (use only if you need it; oRPC also emits OpenAPI) |

### Phase 3 — at scale

| Need | Pick | Notes |
|------|------|-------|
| Desktop app | **Tauri** | Only when you need native distribution |
| Client analytics | **DuckDB-WASM** | Heavy client-side data processing |
| Observability | **OpenTelemetry** | When 2+ services call each other; OTLP export (browser + node SDKs) |
| Monorepo build | **Turborepo** | Simplest, Vercel-maintained. Over nx (plugin-heavy), moon (Rust-based) |
| Large-repo lint | **Oxlint**, when speed or type-aware rules materially help | It does not replace framework semantic checks |
| Published JS/TS library | **tsdown**, when declarations or multiple outputs are required | Adding a library packager to ordinary apps |
| Dead code | **Knip** | Finds unused exports, deps, files |
| Code health (advisory) | **fallow** | Knip-superset: complexity/CRAP, semantic dup, architecture-layer import enforcement, regression-gated. Optional deep tier |
| Supply chain | **deno audit** | See [security.md](../security.md) |
| Component dev | **Histoire** | Vite-native; lighter than Storybook |
| Docs site | **Starlight** (Astro) | Best docs DX in the ecosystem |

### Don't install

- **Prettier / ESLint** — Biome does both.
- **Bun** — retired from the owner environment; recognize its lockfiles only when auditing inherited repositories.
- **Vite+ as a blanket toolchain** — it duplicates Deno, fnm, Just, and project checks.
- **Oxfmt** — still beta; reassess after stable framework-file support.
- **Storybook** — Histoire is lighter and Vite-native.
- **Next.js** — Vercel-coupled, complexity creep.

### Version floors

Deno >=2.8, Vite >=8.0, Svelte >=5.0, SvelteKit >=2.0, Astro >=4.0, Tailwind >=4.0, Biome >=2.3.

## Idioms

### Runtime & package management

- **Deno** is the runtime, package manager, and default toolchain. Use Node via fnm only when a dependency or deployment target requires it.
- When Node is required, use **pnpm**. npm or Yarn remain inherited-project choices, not new defaults.
- Prefer `deno.json` + `deno.lock` for new projects. Deno can also consume an existing `package.json` and run its scripts with `deno task`.
- Detect the lockfile (`deno.lock`, `pnpm-lock.yaml`, …) and use the matching package manager in existing projects. A migration is an explicit project decision, never an incidental tool switch.
- **workerd** is the deployment runtime for Cloudflare Workers, not a local package-management or task-running competitor to Deno.

### Posture: thin frontend over polyglot backends

When the data/auth/jobs layer lives in backend services (Rust/Python/Go), the SvelteKit app is a **thin SSR proxy + session manager**, not a data owner: `hooks.server.ts` proxies `/api/*` to the backend, all loads are server-side (`+page.server.ts`), an httpOnly session cookie and an `X-Request-ID` ride every proxied request. In that posture, **Drizzle / Better Auth / Superforms / Paraglide may not live in the web tier at all** — the backend owns the schema, auth, and validation. The Phase-2 picks above assume full-stack-in-Svelte; drop the ones the backend already owns.

### Formatting & linting

- Prefer `deno fmt`, `deno lint`, and `deno test` when their native coverage is sufficient.
- Use **Biome** for broader JS/TS projects that need one stable formatter/linter across more file types. Don't introduce Prettier/ESLint alongside it.
- Keep **svelte-check** for Svelte semantics. Biome and Oxlint can inspect parts of `.svelte` files but do not own framework semantics.
- Consider **Oxlint** for large repositories where lint latency or type-aware rules are material. Its JavaScript-plugin support remains incomplete, so adopt it against demonstrated coverage rather than benchmark appeal.
- With no Biome config, fall back to whatever the repo already uses. Don't add new lint rules or config files without asking.

### Vite and the VoidZero toolchain

- **[Vite 8](https://vite.dev/blog/announcing-vite8) is adopted** for Vite-based frameworks. It already delivers Rolldown and Oxc transitively; applications should not configure either directly by default.
- **[Vitest](https://vitest.dev/guide/why.html) is adopted for Vite applications** because it shares Vite transforms, aliases, and plugins. Pure Deno libraries keep `deno test`.
- **[Rolldown 1.0](https://voidzero.dev/posts/announcing-rolldown-1-0) is conditional** for custom bundlers, unusual library packaging, or tooling that genuinely needs its Rollup-compatible API.
- **[tsdown](https://tsdown.dev/guide/) is conditional** for published Node/npm libraries needing declarations, multiple formats, source maps, minification, or executable packaging.
- **[Oxfmt](https://oxc.rs/blog/2026-02-24-oxfmt-beta) is watch-only** while beta. Its JS/TS compatibility and speed are promising, but it does not yet displace Deno native formatting or stable Biome coverage.
- **[Vite+](https://voidzero.dev/posts/announcing-vite-plus) is beta and watch-only**. It is credible for Node-centric Vite monorepos, but `vp env`, package installation, `vp run`, and `vp check` create a competing Node/package/task control plane. Revisit at 1.0 or when Deno integration becomes credible.
- **Vite Task is watch-only** until a monorepo demonstrates a need for its caching and dependency scheduling beyond Just and native project tasks.

[VoidZero joined Cloudflare on 2026-06-04](https://voidzero.dev/posts/voidzero-cloudflare). Vite, Vitest, Rolldown, Oxc, and Vite+ remain MIT-licensed under their existing project leadership. The acquisition improves funding durability while increasing ecosystem-concentration risk; adopt individual tools on merit rather than treating the suite as one endorsement.

### Types

- Prefer `type` for unions, intersections, and mapped types; `interface` for extendable shapes.
- Model state with **discriminated unions** — not `{ loading?: boolean; data?: T; error?: Error }`.
- Use `satisfies` for narrowing when it improves readability.
- Use `as const` for immutable arrays/objects.
- Use `??` (nullish coalescing) for defaults, not `||` — `||` swallows `''` and `0`.
- Never `any`. If you're tempted, the type design is wrong: use `unknown` and narrow.

### Code

- **Named exports** over default exports.
- Barrel files (`index.ts`) for re-exports only — no logic. Don't re-export types just for convenience; import from the source.
- **Zod** for all external-data validation.
- **`pino`** for logging — never `console.log` in production.
- Don't `try/catch` around code that can't throw — only wrap genuinely fallible operations. Never skip error handling on async work; unhandled rejections crash the process.
- Don't mutate props — derive new values.

### Styling

- **Tailwind CSS v4**. Class order: layout → spacing → sizing → colors → typography → effects.
- Extract repeated class sets into components with `cva` (class-variance-authority).

### Always

- Run the project check task before committing (`deno task check`).
- Handle loading and error states in UI components.

## Code patterns

### Discriminated union for async state

```typescript
type State<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };
```

### CVA component variants

```typescript
import { cva, type VariantProps } from 'class-variance-authority';

export const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        outline: 'border border-input hover:bg-accent',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;
```

### Drizzle schema as single source of truth

```typescript
import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// Auto-generate Zod schemas from the table — don't hand-maintain a parallel schema.
export const insertUserSchema = createInsertSchema(users);
export const selectUserSchema = createSelectSchema(users);
```

## Project layout

- One Drizzle table per file in `src/lib/server/db/schema/`.
- Generate Zod schemas from Drizzle tables (`drizzle-zod`) rather than maintaining both.
- Transactions: `await db.transaction(async (tx) => { ... })`.

## Exploring / watch

Not adopted — evaluation notes, argue before pulling in.

- **[Effect](https://effect.website) (effect.ts)** — a full functional effect-system + standard library for TypeScript (the `Effect<A, E, R>` type: typed success, **typed error channel**, and a dependency/context `R`). Ships schema, dependency injection, structured concurrency, retries/scheduling, resource safety, streams, observability. Think ZIO-for-TS. **Why it's interesting to us:** it directly targets pain points we already legislate by hand — typed errors instead of `try/catch` discipline, `Schema` overlapping **Zod**, discriminated-union state overlapping the **Effect** type, and built-in retry/concurrency/OTel overlapping our Phase-2/3 picks. **The tension:** it's a *paradigm*, not a drop-in — high learning curve, all-or-nothing gravity (code tends to become "Effect code"), and it cuts against our "simplicity over ceremony / fundamentals over frameworks" lean. **Evaluate when:** a service has genuinely complex error/concurrency/resource orchestration where the type-level guarantees earn their weight — not for thin SSR proxies or CRUD. Start with `@effect/schema` in isolation (as a Zod alternative) before adopting the runtime. Verify current API against effect.website — the ecosystem moves fast.
- **[TanStack](https://tanstack.com)** (Tanner Linsley's family) — headless, type-safe, framework-agnostic libraries. **Svelte-supported (Svelte 5 runes):** **Query** (server-state cache/mutations), **Table** + **Virtual** (headless data grids + virtualization), **Form** (headless form state), **DB** (reactive client store: collections, live queries, optimistic mutations). ⚠️ **Router and Start (the meta-framework) are React/Solid only — not Svelte.** **Fit to us:** in the thin-SSR-proxy posture, server state is loaded server-side so **Query** earns its keep mainly in client-heavy / realtime UIs; **Table + Virtual** are the strongest pulls (data grids are painful to hand-roll). Not a suite to adopt wholesale — reach for the individual library when the need is concrete.
- **The rest of the named ecosystem (quick classifier)** — you'll keep hearing these; the filter is *headless + framework-agnostic + solves a pain we actually have → evaluate; React-coupled → skip for our Svelte stack.*
  - *Validation:* **Zod** is the de-facto standard (our pick). **[Valibot](https://valibot.dev)** (tiny, tree-shakeable) and **[ArkType](https://arktype.io)** (fastest) are alternatives; the 2026 **[Standard Schema](https://standardschema.dev)** spec (from the Zod/Valibot/ArkType authors) makes them interchangeable — relevant since our tooling speaks Zod.
  - *Type-safe API:* **[tRPC](https://trpc.io)** (end-to-end types, no codegen) and **[Hono](https://hono.dev)** (edge web framework) — largely **N/A in our polyglot-backend posture**; only relevant when the backend is TypeScript.
  - *State machines:* **[XState](https://stately.ai/docs/xstate)** (framework-agnostic) for genuinely complex UI flows; zustand/jotai/valtio are React-world.

## Ask first

- Adding new dependencies.
- Changing database schema.
- Modifying auth flow.
- Deleting files.

## See also

- [frameworks/sveltekit.md](frameworks/sveltekit.md) — SvelteKit 2 + Svelte 5 patterns
- [frameworks/astro.md](frameworks/astro.md) — Astro content sites and islands
- [../../engineering-philosophy.md](../../engineering-philosophy.md) — universal code-health principles
