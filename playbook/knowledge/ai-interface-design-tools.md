# AI Interface Design Tools

Current as of 2026-08-28. This is an evaluation landscape, not an adopted-tool
list. Vendor quotas and beta terms change quickly; verify pricing before a trial.

## Decision

Use **design-first, blank-canvas tools** for visual-direction discovery. Use
**code-aware design tools** only after a direction wins. Use **app builders** to
make the winner interactive, not to decide what the product should look like.

Giving a coding agent an existing repository, screenshot, or component library
at the start strongly anchors it to the current information architecture and
component grammar. A useful zero-to-one trial supplies only the product brief,
representative synthetic data, required states, accessibility constraints, and
the emotional job of the interface.

## Recommended trial set

Run the same blind brief through several independent generators rather than
asking one tool for many nominal themes.

| Priority | Tool | Why it earns a trial | Free evaluation path |
|---|---|---|---|
| 1 | [UX Pilot](https://uxpilot.ai/) | Product-design workflow from brief or sketch through wireframes, four-look comparison, high-fidelity screens, flows, Figma, and code. Its explicit “four distinct looks” mode matches divergent exploration. | 80 daily credits; no card required. |
| 1 | [Flowstep](https://flowstep.ai/) | Infinite editable canvas, multi-screen generation, reference inputs, Figma copy, and React/TypeScript/Tailwind export. Design-first rather than an application host. | Free plan with limited messages, multi-screen work, and projects; no card required. |
| 1 | [Banani](https://www.banani.co/) | Editable multi-screen web/mobile prototypes from prompts or product requirements, manual token editing, Figma/code export, and MCP handoff. Built by a small design-focused team. | 12 monthly credits plus 3 daily credits; private projects; no card required. Figma/code export is paid, but MCP is available on all plans. |
| 1 | [Superdesign](https://superdesign.dev/) | Prompt-to-design exploration, a large remixable prompt library, quick natural-language iteration, code export, and an agent-oriented mode. Strong candidate for broad visual references and independent composition. | Free to start; no public quota table was found. |
| 1 | [Google Stitch](https://stitch.withgoogle.com/) | Fast web/mobile generation, easy edits, design ownership, and code export. Useful as an independent model family and for rapid breadth. | Public beta with “Try now”; Google does not publish a stable pricing table on the product page. |
| 1 | [Figma design agent](https://help.figma.com/hc/en-us/articles/37998629035799-Work-with-the-Figma-agent-in-design-files) | Editable zero-to-one layouts and remixing inside the canonical design canvas. Strongest choice when a human wants precise manual follow-through. | Available on all plans and free during beta, subject to monthly limits. Start in a blank file with no connected library. |
| 2 | [Paper](https://paper.design/) | Web-standards design canvas with read-write MCP, agents and humans sharing one surface, code/data connections, and an unusually generous collaboration model. | Free plan: unlimited viewers/editors, 100 MCP calls per week, limited image generation. |
| 2 | [pen.dev](https://www.pen.dev/) | Agent-driven vector canvas, open `.pen` format in Git, parallel screen generation, design kits, Figma copy/paste, and read-write MCP. Particularly interesting for reproducible design artifacts. | Currently free. For unbiased exploration, use a blank temporary project rather than an existing repository or brand kit. |
| 2 | [Magic Patterns](https://www.magicpatterns.com/) | Product-oriented prompt-to-UI concepts and interactive prototypes, closer to application design than site generation. | 100 monthly credits. |
| 2 | [Visily](https://www.visily.ai/) | Screens, components, diagrams, themes, prototypes, and low/high-fidelity switching. Useful for flows and structural breadth. | 300 AI credits per month and two editable boards. |
| 3 | [Uizard](https://uizard.io/) | Accessible prompt-to-mockup, screenshot, and wireframe workflows. Useful as another independent visual opinion, but the free allowance is too small for a tournament. | Three AI generations per month, two projects, up to five screens per project. |
| 3 | [Komposo](https://www.komposo.ai/) | Conversational editable design and multi-screen planning with Figma/code export on paid plans. More site- and reference-oriented than the first-priority tools. | Ten one-time credits and one project. |

### Suggested free sequence

1. Generate four directions in UX Pilot, Flowstep, Banani, Superdesign, and
   Stitch without references or current-product context.
2. Use Figma or Paper for human comparison, annotation, and recombination only
   after the independent results exist.
3. Expand the top three into one dense screen, one prose-heavy screen, one
   relationship/detail screen, and mobile.
4. Move only the winner into a code-aware design tool or app builder.

This sequence should yield more genuine diversity than one generator producing
100 variations from a shared hidden scaffold.

## Design-to-code bridges

These tools become more valuable after a visual thesis exists. They are poor
first judges of an existing product because their codebase and design-system
awareness deliberately preserves what is already there.

| Tool | Best job | Evaluation posture |
|---|---|---|
| [Subframe](https://www.subframe.com/) | Designer-first visual components that map predictably to production code, responsive canvases, prototypes, design systems, and MCP/skills. | Trial on a finalist. Free: one project, ten pages, two prototypes, limited AI. |
| [Polymet](https://polymet.ai/) | AI product designer with visual and code editors, Figma import/export, GitHub, package, and Storybook integration. | Watch/trial on a finalist; public pricing was not discoverable. Do not import an existing design system during divergent exploration. |
| [Onlook](https://www.onlook.com/) | Open-source visual editor directly over React code, with layers, chat, live preview, collaboration, and code as source of truth. | Strong implementation bridge, wrong first-stage discovery surface. Free when self-hosted. |
| [Tenor](https://tenor.design/) | Refines rough AI-built React against a visual reference, component by component, then returns working code. | Request-access watch. Its stated job is polish after a coding agent, not greenfield product direction. |
| [Layout](https://layout.design/) | Compiles an existing design system into context for coding agents. | Watch for design-system fidelity; intentionally not a zero-to-one ideation tool. |
| [Noon](https://noon.design/announcing-noon) | Early-access dual canvas that designs directly on production code; announced $44M funding in April 2026. | High-interest watch. Its code-native model may remove handoff, but no public hands-on or free evaluation path yet. |

## Code-first application builders

These tools optimize for a functioning application. They are useful for testing
interactions and responsive behavior after selection, but commonly converge on
familiar React, Tailwind, and component-library patterns when the visual brief
is weak.

| Tool | Free evaluation path | Use |
|---|---|---|
| [v0](https://v0.app/pricing) | $5 monthly credits and seven messages per day. | Best-known path from a selected concept to working React and visual edits. |
| [Bolt](https://bolt.new/pricing) | 300,000 tokens per day and one million per month. | Generous full-stack interactive prototype allowance. |
| [Lovable](https://lovable.dev/pricing) | Free grants; the pricing page does not state a fixed grant count. | Complete hosted application prototypes; design-system features are paid. |
| [Replit Agent](https://replit.com/pricing) | Free Starter access changes frequently and its pricing page may be bot-gated. Verify in-product. | Full application build and hosting, not independent visual discovery. |

Do not import the production repository into these tools until the structural
and visual direction is selected. Build a disposable synthetic prototype first.

## Site-first tools

[Relume](https://www.relume.ai/pricing), Framer, Webflow AI, and Dora are useful
for marketing sites, editorial sites, sitemaps, and landing-page composition.
Relume's free plan currently includes enough AI use for roughly one small site
per month. They are secondary choices for a dense repeated-work application
because their strongest priors are page publishing and conversion flows.

## Retired and misleading candidates

- [Motiff](https://www.motiff.com/) is discontinued; data export remains
  available only until 2026-10-31. Do not start a trial.
- Galileo AI is no longer a separate durable evaluation target; Google Stitch
  owns the relevant current product path.
- Screenshot cloning and design-system import are useful implementation
  features but actively harmful to an anti-anchoring exploration.
- A tool advertising code export is not necessarily a design tool. Judge
  whether it can create materially different grayscale structures before
  evaluating code quality.

## Anti-anchoring evaluation protocol

### Blind input

Provide:

- product purpose and recurring user jobs
- information types and representative synthetic content
- required dense, empty, waiting, overdue, expanded, error, and mobile states
- emotional qualities and unacceptable clichés
- accessibility and touch constraints

Withhold:

- current screenshots
- current repository and components
- current token values, fonts, and route layout
- named competitor interfaces
- an existing Figma library or brand kit

### Generation contract

Ask for four concepts that differ in all of these:

1. primary object and organizing metaphor
2. navigation model
3. overview/detail relationship
4. action representation
5. time representation
6. component anatomy
7. desktop composition
8. mobile composition

Require each concept to be delivered separately. If two concepts could share the
same grayscale wireframe, reject them as cosmetic variants.

### Scoring

Score each result from 1–5 on:

- structural distinctiveness
- hierarchy under realistic density
- long-session comfort
- product/domain fit
- recognizable identity in a cropped screenshot
- mobile survival without merely stacking desktop panels
- state coverage and accessibility
- feasibility without forcing the current implementation to survive

Do not score code quality until a direction clears the design round.

### Finalist expansion

For each finalist, request the same four archetypes:

- attention-focused daily surface
- dense operational queue
- long relationship or entity detail
- prose-heavy reference surface

A coherent design should express the same behavioral grammar across all four
without turning every data type into the same card.

## Research sources

Primary product and pricing pages were checked on 2026-08-28. Free allowances
are snapshots, not guarantees. The source links in the tables are the evidence;
re-check them immediately before spending evaluation time or connecting code.
