---
name: document-design
description: Design reports, briefs, benchmarks, and HTML reading views. Use for "make this a report", "turn this into HTML", document polish, or evidence-heavy pages. SKIP product UI and decks.
---

# Document Design

Design a document around what its reader must understand, decide, or do. Shape the argument and the reading interface together instead of decorating source-order prose.

Use `presentation-design` for decks and pitches. Use `frontend-design` for repeated product interfaces and marketing sites. Use the call-script template for conversation run sheets and rehearsal guides rather than creating another shell.

## Frame the reader's job

Before choosing a layout, establish:

1. Who opens the document, and in what context?
2. What should they understand, decide, or do next?
3. What is the strongest supported answer?
4. Which evidence earns that answer?
5. Which uncertainty or caveat could change it?

Preserve supplied facts, formulas, units, periods, populations, qualifiers, privacy constraints, and sources before improving style. Distinguish observation, derivation, projection, recommendation, and causation. Ask one grouped set of questions only when an unknown could materially change meaning; otherwise label or omit it and proceed.

Order the document by reader need rather than source order. Support two reading speeds:

- **Decision path:** title, headings, decisive values, captions, and conclusion communicate the answer quickly.
- **Audit path:** exact tables, assumptions, methodology, caveats, and sources preserve the record.

Every section must answer a new reader question. Combine repetitions and give each important claim one primary evidence home.

## Choose composition before components

Name the obvious template suggested by the document category, then reject it unless the material earns it. When structure is uncertain, compare two materially different compositions before coding. Change hierarchy, density, evidence placement, and reading order rather than palette alone.

Treat evidence geometry as the visible relationship among the claim, comparison basis, chronology, uncertainty, and supporting detail. Choose that relationship before selecting components:

- Use aligned position or length for magnitude and rank.
- Use horizontal order for change over time.
- Use a boundary or range for thresholds.
- Use connection and sequence for process or dependency.
- Use aligned rows for qualitative comparison.
- Use tables for precise lookup and prose for one conclusion.

Make the first viewport establish the document's identity, reader question, strongest answer, and decisive evidence. Give important tables, comparisons, diagrams, and interactive evidence the width they need instead of constraining them to prose measure.

## Reuse mechanics without forcing a template

Read the host project's design tokens, components, build tooling, accessibility patterns, print rules, and representative shipped artifacts during convergence. Reuse the relevant vocabulary instead of inventing parallel typography, spacing, colors, controls, or document behavior. When no host project exists, use semantic HTML, restrained system typography, readable measures, and the smallest CSS and JavaScript needed for the document's job.

Preserve supplied tables semantically: keep every material row, column, value, unit, qualifier, and relationship unless the user authorizes a transformation. The visual form may change to improve lookup or responsive behavior, but the evidence may not silently disappear or change meaning.

Keep judgment in this skill or a project-local design document. Keep repeatable mechanics in CSS, templates, or components. Keep objective failures in deterministic checks. A project-specific decision belongs in the project that owns the surface.

Maintain one canonical prose source when generating HTML. For conversation material, use `agents/templates/documents/call-script.html` through its documented renderer. Add another reusable template only after a distinct document job recurs and needs different retrieval or interaction behavior.

## Write for trust

Use concrete claims and active verbs. Define unfamiliar terms once in plain language. Keep exact technical vocabulary in the audit path. Simplify language without broadening the claim.

Use visual emphasis in proportion to evidence. Prefer typography, alignment, spacing, and evidence geometry before cards, borders, icons, color, or motion. Empty space must amplify something; it must not conceal missing content or an underfilled grid.

Name and reject these generated-document reflexes during review:

- A generic centered hero followed by a card grid.
- Repeated metric boxes where one comparison would be clearer.
- Cards nested inside cards or borders compensating for weak hierarchy.
- Decorative gradients, glows, glass, blobs, textures, or ornamental shadows.
- Pills, icon tiles, and all-caps labels used as decoration.
- Tiny muted prose or arbitrary type sizes used to make density fit.
- A narrow table floating inside a wide evidence section.
- Charts without a shared scale, direct labels, or a reader question.
- Identical section silhouettes for unrelated questions.
- Repeated recommendation, rationale, summary, and conclusion blocks saying the same thing.

Avoiding those defaults must not produce a sterile universal template. Give each document one evidence-bearing organizing move specific to its material.

## Verify the artifact

Render the actual output at its reading viewport. Inspect desktop and mobile, light and dark when supported, and print when printing is part of the job.

Review in this order:

1. The first viewport communicates the question, supported answer, and evidence.
2. Headings and captions carry a coherent decision path.
3. Facts, qualifiers, units, sources, and caveats survive unchanged.
4. Each section advances the reader's job without equal-weight repetition.
5. Tables, charts, and comparisons use honest geometry and available width.
6. Typography, baselines, gutters, and spacing establish stable hierarchy.
7. Responsive reflow preserves readable text, controls, and evidence without page overflow.
8. Semantics, keyboard access, focus, contrast, labels, and text alternatives are sound.

Fix the highest-impact systemic defect, render again, and stop when no known material issue remains. Promote a repeated subjective correction into guidance, a repeated mechanic into a primitive, and an objective regression into a test.

## Evaluation

When changing this skill or shared document mechanics, use the frozen scenarios in `evals/evals.json`. Save the baseline first, keep model, inputs, viewport, and first-attempt policy fixed, then compare blindly. Record the model, skill version, screenshots, and reviewer corrections. Treat model judgment as advisory; a person owns the visual decision.

## Sources

- Informed by Vercel's [design.md evaluation loop](https://vercel.com/blog/how-our-agents-build-on-brand-pages-with-design-md) and [public design guidance](https://vercel.com/design.md), reviewed 2026-09-02. The workflow and examples were generalized for Workbench rather than copied as a brand system.
