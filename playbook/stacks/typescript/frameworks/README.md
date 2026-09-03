# Full-Stack Web Application Frameworks

Use this map before choosing a TypeScript web framework. Framework quality, team familiarity, rendering model, deployment portability, and maintainer incentives matter more than benchmark wins.

For the surrounding platform competition, see [Vercel and Cloudflare Stack Watch](../../vercel-cloudflare.md). For ownership and effective control, see [Developer Tool Ownership](../../../knowledge/developer-tool-ownership.md).

| Framework | Best fit | Ownership or influence | Current posture |
|---|---|---|---|
| **SvelteKit** | Full-stack interactive applications with a small runtime and concise component model | Independent open source. Creator Rich Harris works at Vercel, giving Vercel substantial practical influence. Deploys to Vercel, Cloudflare, Deno, Node, and other adapters. | **Default.** Use Svelte 5 runes and keep the deployment adapter replaceable. |
| **Next.js** | React applications that benefit from the largest full-stack React ecosystem and Vercel's native deployment path | Created and stewarded by Vercel. Open source, but many advanced behaviors and defaults align closely with Vercel infrastructure. | Avoid by default because React and platform complexity are real. Choose when the ecosystem or organization makes it decisive. |
| **Nuxt** | Full-stack Vue applications | NuxtLabs joined Vercel. Nuxt and Nitro remain open source with stated independent governance. Nitro targets several deployment platforms. | Inherited or Vue-centered choice, not a new default. |
| **React Router framework / Remix lineage** | Standards-oriented React applications, nested routing, loaders, and actions | Remix joined Shopify in 2022; framework development later converged into React Router. | Prefer over Next.js when React is required but Vercel coupling is not. Still carries React's complexity. |
| **TanStack Start** | Type-safe React or Solid applications assembled from TanStack Router, Query, and related libraries | Independent TanStack ecosystem with deployment adapters. | Watch. Strong composability and types; not relevant to the default Svelte stack yet. |
| **Astro** | Content sites with selective interactive islands rather than application-wide client JavaScript | Independent company and open-source project; deploys broadly, including Vercel and Cloudflare. | **Default for content sites**, not complex application state. |
| **SolidStart** | Fine-grained reactive full-stack applications in the Solid ecosystem | Independent open source with smaller ecosystem and deployment adapters. | Watch or use for an existing Solid team. |
| **Qwik City** | Resumable applications optimized around minimal initial JavaScript | Qwik originated at Builder.io and remains open source. | Interesting performance model; ecosystem risk outweighs novelty for ordinary projects. |
| **Hono** | Small web application programming interfaces and applications across edge runtimes, including Cloudflare Workers | Independent open source with strong edge-runtime adoption. | Strong conditional choice for a small Workers or multi-runtime service, not a SvelteKit replacement by default. |

## Selection

1. Use **SvelteKit** for full-stack product applications.
2. Use **Astro** for content-first sites.
3. Use **Hono** for small edge-oriented application programming interfaces when a full application framework is unnecessary.
4. Use **Next.js** only when React or its ecosystem provides a concrete advantage large enough to accept Vercel gravity.
5. Use **Nuxt** only when Vue is already the ecosystem choice.
6. Keep TanStack Start, SolidStart, and Qwik City on watch rather than creating exploratory production dependencies.

## Portability test

Before committing to a framework and host combination:

- Build and run it on a second supported adapter.
- Identify which cache, image, function, middleware, workflow, and observability behaviors are host-specific.
- Keep primary data outside a proprietary framework cache.
- Verify that preview and production configuration are source-controlled.
- Treat maintainer employment as influence, not proof of legal ownership or inevitable lock-in.
