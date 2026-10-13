# Solid and SolidStart

Reviewed 2026-10-10. **Solid/SolidStart is the leading candidate alternative to
Svelte/SvelteKit.** SvelteKit remains the default. This ranking gives Solid the
first comparative trial; it is not a migration mandate or a completed benchmark.

## Why it deserves the first trial

Solid exposes reactive state through functions such as createSignal and composes
UI through JSX. Component initialization generally runs once; tracked reactive
computations update their dependents. This can suit interfaces whose behavior is
easier to describe as explicit functions and reactive relationships.

Svelte also supports granular reactive updates. Its compiler-supported runes
and HTML-like templates offer a different expression of similar goals. A switch
should improve clarity, interaction design, or demonstrated performance rather
than assume that only Solid has fine-grained reactivity.

| Concern | Svelte/SvelteKit | Solid/SolidStart |
| --- | --- | --- |
| Authoring preference | Templates, scoped styles, and runes | JSX, functions, signals, and explicit reactive composition |
| Reactive pitfalls | Compiler rules and boundaries when passing state | Reading accessors outside tracking scopes and losing reactive property access |
| Existing investment | Established default and application patterns | New component, integration, deployment, and debugging patterns to validate |
| Framework selection | One established application framework | SolidStart v2 with a choice of router and deployment integration |
| Adoption test | Keep if the complete feature remains clearer | Promote only where the complete feature demonstrates a durable advantage |

JSX resemblance does not make React components or React's execution assumptions
portable to Solid. Verify required UI libraries before treating it as a drop-in
ecosystem replacement. For a browser-only feature, Solid with Vite can be enough;
SolidStart earns its role when routing and server behavior are needed.

Sources: [Solid reactivity](https://docs.solidjs.com/concepts/intro-to-reactivity)
and [Svelte state](https://svelte.dev/docs/svelte/$state).

## Current SolidStart architecture

The [v2 overview](https://docs.solidjs.com/solid-start/v2) describes SolidStart v2
on Solid v1 and Vite 8+, using Vite's Environment API. Deployment integrations
include Nitro v3 and Cloudflare and Netlify Vite plugins. It supports Solid
Router v1 and TanStack Solid Router v1. Do not equate the framework's major
version with the UI library's version or repeat older tooling assessments
without checking the selected release.

This architecture offers deployment choices, but adapters and plugins do not
prove portability of storage, caching, authentication, or hosted services.
Switching UI frameworks also does not remove shared Vite ecosystem sponsorship.

## Proposed comparison

Use one editable table or multi-pane live workspace with realistic state.
Keep runtime, package manager, data source, and visual requirements constant.
Include server rendering if the product needs it, route navigation, authenticated
reads and mutations, loading and error recovery, keyboard access, and browser
tests. Reuse ordinary business logic without inventing a portability framework.

Evaluate readability after completion, reactive mistakes found during testing,
library gaps, client JavaScript, interaction responsiveness, debugging effort,
and deployment configuration. Use the same data volume and device conditions.
Do not substitute a counter or synthetic rendering benchmark for the feature.

The initial trial is a bounded feature implementation. An application migration
would replace templates and framework boundaries and therefore has much greater
scope than the [runtime/package-manager comparison](../runtimes.md).
Retain SvelteKit unless the complete result justifies that surface area.
If Solid wins, adopt it first in one suitable new project; do not maintain two
implementations of a production feature indefinitely.
