# TanStack and AI Application Libraries

TanStack is an umbrella for independent TypeScript libraries, not one framework and not a suite to install wholesale. Most packages are headless: they provide behavior and state while the application keeps control of markup and styling.

## Plain-language model

Think of a web application as a workshop:

- **TanStack Query** keeps fetched server data fresh and avoids asking for the same data repeatedly.
- **TanStack Table** supplies the sorting, filtering, grouping, and pagination logic for a data grid, but does not choose how the table looks.
- **TanStack Virtual** renders only the visible part of a huge list.
- **TanStack Form** coordinates fields, validation, submission, and errors in a complex form.
- **TanStack Router** maps addresses to screens with strong TypeScript guarantees.
- **TanStack Start** combines Router with server rendering and server functions to make a full React or Solid application framework.
- **TanStack DB** keeps reactive client-side collections synchronized and supports optimistic writes.
- **TanStack AI** gives an application one interface for model providers, streaming, tools, and agent interactions.

The shared name signals a design style and maintainer ecosystem. It does not mean an application should use every package.

## Choose by problem

| Problem | TanStack option | Start simpler with | Main alternatives | Current posture |
|---|---|---|---|---|
| Remote data caching, refetching, and mutations | **Query** | SvelteKit server loads or remote functions and ordinary `fetch` | SWR, Apollo Client, urql, Relay | Adopt when client-side synchronization, retries, invalidation, or optimistic mutations have become real application concerns. |
| Complex sortable and filterable data grids | **Table** | Semantic HTML tables and local derived state | AG Grid, Handsontable, Grid.js | Strong conditional choice. Headless control is valuable once table behavior is genuinely complex. |
| Very long lists, grids, logs, or chat histories | **Virtual** | Render the complete collection | Framework-specific virtual-list packages, React Virtuoso | Add only after profiling shows rendering or scrolling cost. |
| Complex form state and validation | **Form** | Native forms; Superforms plus Zod in SvelteKit | Felte, React Hook Form, Formik | Conditional. Keep Superforms as the SvelteKit default unless framework-neutral client form state solves a demonstrated problem. |
| Reactive local collections, live queries, and optimistic writes | **DB** | Framework state plus explicit application programming interface calls | Dexie, RxDB, LiveStore, PowerSync, ElectricSQL | Watch. Sync architecture and conflict behavior matter more than the client query syntax. |
| Small framework-neutral client state | **Store** | Svelte runes or stores | Zustand, Redux Toolkit, XState | Usually unnecessary in Svelte. Use XState instead when the actual problem is a complex state machine. |
| Type-safe single-page application routing | **Router** | The selected framework's router | React Router, Vue Router, framework-native routing | React and Solid only. Do not add a second router to SvelteKit or Astro. |
| Full-stack React or Solid application | **Start** | SvelteKit for applications; Astro for content sites | Next.js, React Router framework, Nuxt, SolidStart | Watch. It is not relevant to the default Svelte stack. See the [framework map](frameworks/README.md). |
| Provider-neutral model calls and streaming interfaces | **AI** | A direct provider software development kit for one small integration | Vercel AI SDK, LangChain or LangGraph, Mastra | Closest direct alternative to AI SDK. Evaluate for open protocols, composition, persistence, or resumability; do not migrate for brand consistency. |
| Charts with application-owned presentation | **Charts** | CSS, SVG, or a small purpose-built visualization | LayerChart, Apache ECharts, D3, Chart.js | Watch and compare against the chart types, accessibility, and Svelte support actually required. |
| Debouncing, throttling, rate limiting, queues, and batching | **Pacer** | A small local helper | Lodash utilities, `p-limit`, `p-queue`, Bottleneck | Conditional. Useful when cancellation, observable pending state, or several pacing strategies justify a dependency. |
| Keyboard shortcuts | **Hotkeys** | A local `keydown` handler | hotkeys-js, Mousetrap, framework-specific actions | Conditional for shortcut-heavy applications. Keep ordinary pages dependency-free. |
| JavaScript package maintenance | **Config** and related tooling | Existing repository tasks and configuration | Changesets, tsdown, Biome, Vitest, release scripts | Do not adopt as a second toolchain. Evaluate only for a published package family with repeated maintenance work. |

TanStack also publishes narrower or newer packages such as Markdown, Highlight, Devtools, CLI, and Intent. Treat these as individual candidates. Their existence does not change the current stack until a project has the problem they solve and they outperform the existing choice.

## Where AI SDK-style tools fit

“AI tooling” covers several different layers that are easy to confuse:

| Layer | Plain-language job | Examples |
|---|---|---|
| Provider software development kit | Talks directly to one model company | Anthropic, OpenAI, or Google client libraries |
| Model application library | Gives application code a common interface for generation, streams, structured output, and tools | **Vercel AI SDK**, **TanStack AI** |
| Agent runtime | Coordinates longer-lived state, workflows, memory, or graphs | Mastra, LangGraph |
| User-interface layer | Renders chat and agent interactions | AI SDK framework hooks, assistant-ui |
| Gateway | Routes model traffic, applies policy, and records usage | Vercel AI Gateway, Cloudflare AI Gateway, OpenRouter, LiteLLM |

These layers can complement each other. A gateway does not replace application code, and a chat component does not replace a model client. Keep the detailed and more volatile competitor assessment in the [Vercel and Cloudflare stack watch](../vercel-cloudflare.md#ai-sdk-features-and-competitors).

## Adoption rule

Start with framework-native data loading, forms, routing, and state. Add one TanStack library only when its specific problem has become difficult enough to name and test. Typical triggers are:

- repeated cache invalidation or background refresh logic;
- a data grid with substantial sorting, filtering, grouping, or selection behavior;
- measured rendering problems from thousands of rows;
- complex client forms that outgrow the framework-native path;
- offline or realtime collections with optimistic synchronization;
- multi-provider model streaming, tool calls, or resumable agent interactions.

Do not replace working SvelteKit, Astro, or AI SDK code merely to make the dependency list look consistent.

## References

- [TanStack libraries](https://tanstack.com/)
- [TanStack Query](https://tanstack.com/query/latest/docs/framework/svelte/overview)
- [TanStack DB](https://tanstack.com/db/latest/docs/overview)
- [TanStack Form](https://tanstack.com/form/latest/docs/overview)
- [TanStack Router](https://tanstack.com/router/latest/docs/framework/react/overview)
- [TanStack Start](https://tanstack.com/start/latest/docs/framework/react/overview)
- [TanStack Virtual](https://tanstack.com/virtual/latest/docs/introduction)
- [TanStack AI](https://tanstack.com/ai/latest)
- [TanStack Pacer](https://tanstack.com/pacer/latest/docs/overview)
