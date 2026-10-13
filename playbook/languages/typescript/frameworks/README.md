# Full-Stack Web Application Frameworks

Use this map before choosing a TypeScript web framework. Framework quality, team familiarity, rendering model, deployment portability, and maintainer incentives matter more than benchmark wins.

For the surrounding platform competition, see [Vercel and Cloudflare Stack Watch](../../../systems/cloud-platforms.md). For ownership and effective control, see [Developer Tool Ownership](../../../engineering/vendor-ownership.md).

| Framework | Best fit | Ownership or influence | Current posture |
|---|---|---|---|
| **SvelteKit** | Full-stack interactive applications with a small runtime and concise component model | Open source with Vercel maintainer influence; deployment adapters support multiple hosts. | **Default.** Use Svelte 5 runes and a supported deployment target; Node LTS is the baseline. |
| **Next.js** | React applications that benefit from the largest full-stack React ecosystem and Vercel's native deployment path | Created and stewarded by Vercel. Open source, but many advanced behaviors and defaults align closely with Vercel infrastructure. | Avoid by default because React and platform complexity are real. Choose when the ecosystem or organization makes it decisive. |
| **Nuxt** | Full-stack Vue applications | NuxtLabs joined Vercel. Nuxt and Nitro remain open source with stated independent governance. Nitro targets several deployment platforms. | Inherited or Vue-centered choice, not a new default. |
| **React Router framework / Remix lineage** | Standards-oriented React applications, nested routing, loaders, and actions | Remix joined Shopify in 2022; framework development later converged into React Router. | Prefer over Next.js when React is required but Vercel coupling is not. Still carries React's complexity. |
| **TanStack Start** | Type-safe React or Solid applications assembled from TanStack Router, Query, and related libraries | Independent TanStack ecosystem with deployment adapters. | Watch. Strong composability and types; not relevant to the default Svelte stack yet. |
| **Astro** | Content sites with selective interactive islands rather than application-wide client JavaScript | Its company joined Cloudflare; the open-source framework deploys broadly. | **Default for content sites**, not complex application state. |
| **Solid / SolidStart** | Fine-grained reactive interfaces and full-stack applications expressed through JSX and functions | Open-source Solid ecosystem; SolidStart v2 uses Vite deployment integrations and supports a choice of routers. | **Leading alternative to Svelte/SvelteKit.** First comparative trial; [criteria and current architecture](solid.md). |
| **Qwik City** | Resumable applications optimized around minimal initial JavaScript | Qwik originated at Builder.io and remains open source. | Interesting performance model; ecosystem risk outweighs novelty for ordinary projects. |
| **Hono** | Small web application programming interfaces and applications across edge runtimes, including Cloudflare Workers | Independent open source with strong edge-runtime adoption. | Strong conditional choice for a small Workers or multi-runtime service, not a SvelteKit replacement by default. |

## Selection

1. Use **SvelteKit** for full-stack product applications.
2. Use **Astro** for content-first sites.
3. Use **Hono** for small edge-oriented application programming interfaces when a full application framework is unnecessary.
4. Use **Next.js** only when React or its ecosystem provides a concrete advantage large enough to accept Vercel gravity.
5. Use **Nuxt** only when Vue is already the ecosystem choice.
6. Evaluate **Solid/SolidStart first** when considering an alternative to Svelte/SvelteKit. Use a complete representative feature, not a synthetic rendering benchmark.
7. Keep TanStack Start and Qwik City as secondary candidates unless a concrete requirement changes the ranking.

The [runtime exploration](../runtimes.md) owns Node/pnpm, Bun, Deno, and Vite+ choices. Do not change the UI framework and runtime in the same comparison. Ownership sources: [Astro joining Cloudflare](https://blog.cloudflare.com/astro-joins-cloudflare/) and [SolidStart v2](https://docs.solidjs.com/solid-start/v2).

## Portability test

Before committing to a framework and host combination:

- Build and run it on a second supported adapter.
- Identify which cache, image, function, middleware, workflow, and observability behaviors are host-specific.
- Keep primary data outside a proprietary framework cache.
- Verify that preview and production configuration are source-controlled.
- Treat maintainer employment as influence, not proof of legal ownership or inevitable lock-in.
