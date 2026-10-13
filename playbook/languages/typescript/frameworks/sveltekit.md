# SvelteKit

> Curated taste, not mandate — patterns for SvelteKit + Svelte 5 on Node LTS.

## Stack at a glance

```yaml
Framework:   SvelteKit + Svelte 5 (runes)
Runtime:     Node LTS (@sveltejs/adapter-node for a standalone server)
Packages:    pnpm (evaluate Vite+ for toolchain coordination)
Database:    Drizzle ORM + PostgreSQL
Auth:        Better Auth (or Lucia for lightweight)
Forms:       Superforms + Zod
Components:  shadcn-svelte + Bits UI
```

## Svelte 5 runes — not legacy syntax

Use runes, never the Svelte 4 reactive forms:

- `$state()` for reactive state — NOT bare `let x` reactivity.
- `$derived()` for computed values — NOT `$: x = ...`.
- `$effect()` for side effects — NOT `$: { ... }`.
- `$props()` for component props — NOT `export let`.
- `$bindable()` for two-way binding props.

```svelte
<script lang="ts">
  let count = $state(0);
  let doubled = $derived(count * 2);

  $effect(() => {
    console.log(count);
  });
</script>
```

### Typed props with `$props()`

```svelte
<script lang="ts">
  let {
    variant = 'default',
    disabled = false,
    class: className = '',
    children,
  }: {
    variant?: 'default' | 'outline';
    disabled?: boolean;
    class?: string;
    children?: import('svelte').Snippet;
  } = $props();
</script>
```

## Data loading

- `+page.server.ts` for data that needs auth or DB access; read auth off `locals`.
- `+page.ts` for public data or client-side fetching.
- Return plain objects from `load` — SvelteKit serializes them.

```typescript
// +page.server.ts
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, params }) => {
  const user = locals.user; // set in hooks
  const posts = await db.query.posts.findMany();
  return { posts, user };
};
```

## Form actions

Use Superforms + Zod for form handling with progressive enhancement.

```typescript
// +page.server.ts
import type { Actions } from './$types';
import { fail } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';

export const actions: Actions = {
  default: async ({ request }) => {
    const form = await superValidate(request, zod(schema));
    if (!form.valid) return fail(400, { form });
    // process...
    return { form };
  },
};
```

## Database (Drizzle)

- One table per file in `src/lib/server/db/schema/`.
- Use `drizzle-zod` to generate Zod schemas from tables — single source of truth.
- Transactions: `await db.transaction(async (tx) => { ... })`.

## Project layout

```
src/
├── lib/
│   ├── components/ui/   # shadcn-svelte components
│   ├── server/db/       # Drizzle schema + queries
│   ├── server/auth/     # Auth setup
│   └── utils/           # Shared utilities
└── routes/              # File-based routing
    ├── +layout.svelte
    ├── +page.svelte
    └── api/             # API routes (+server.ts)
```

## Commands

```bash
pnpm install               # Install declared dependencies
pnpm run dev               # Vite development server
pnpm run build             # Production build
pnpm run preview           # Preview production build
pnpm run check             # Svelte type check
pnpm run lint              # Project lint task
pnpm exec vitest run       # Unit and component tests
pnpm run db:generate       # Generate migration
pnpm run db:migrate        # Run migrations
pnpm run db:studio         # Open Drizzle Studio
```

## Critical / common mistakes

- **Tailwind plugin order:** `tailwindcss()` BEFORE `sveltekit()` in `vite.config`.
- **Production adapter:** use [`@sveltejs/adapter-node`](https://svelte.dev/docs/kit/adapter-node) for a standalone Node server, or the supported adapter for the chosen host. Build and run the artifact on the actual deployment runtime.
- Existing Deno projects keep their declared tasks and adapter until a deliberate migration. The [runtime exploration](../runtimes.md) explains the maintenance horizon and Bun evaluation; changing documentation does not migrate an application.
- Use `{@render children?.()}` with snippets — NOT `<slot>`.
- Use `onclick` (lowercase, no colon) — NOT `on:click`.

## Verified integration notes

These are version-specific observations, not permanent compatibility assumptions:

- **Biome 2.5.11 with Svelte 5:** enable `html.experimentalFullSupportEnabled` to parse templates fully; without it, imports used only in templates were falsely reported as unused. Recheck the option and diagnostics when upgrading Biome rather than suppressing unused-import checks.
- **Knip 6.38 with Deno 2.9 tasks:** tools invoked only through `deno.json` tasks were reported as unused dependencies. Keep narrowly documented `ignoreDependencies` entries for actual task executables, and declare native test entrypoints that discovery misses. Revisit exceptions when task discovery improves; do not suppress all development dependencies.
- **Playwright server isolation:** give browser tests dedicated frontend and backend ports, pass the same backend port to the frontend proxy, and set `reuseExistingServer: false` for both servers. An occupied port should fail visibly rather than silently testing an unrelated development process.

## See also

- [../README.md](../README.md) — TypeScript stack selection and idioms
- [solid.md](solid.md) — leading candidate alternative to Svelte/SvelteKit
- [astro.md](astro.md) — content sites and islands
- [../../../engineering-philosophy.md](../../../engineering/principles.md) — universal code-health principles
