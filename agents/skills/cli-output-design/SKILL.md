---
name: cli-output-design
description: Design readable CLI output. Use for "ugly table", wrapping, or terminal UX.
---

# CLI Output Design

Design terminal output as an information interface, not a database dump. Optimize the default view for the decision the user is making; preserve completeness behind focused detail modes.

## Start with the real surface

1. Run the command at representative widths, normally 80 and 120 columns.
2. Read the underlying row model and renderer. Separate data-shape problems from presentation problems.
3. State the primary scan question in one sentence. Examples: "What needs action first?" or "Which campaigns are moving, and what is the next gate?"
4. Identify the few fields needed to answer that question. Move provenance, identifiers, long bodies, and secondary metrics behind `--details`, `show`, or another focused projection.

Preserve a plain or machine-readable renderer when scripts depend on it. Rich terminal output is a human projection, not canonical state.

## Build a visual hierarchy

Use visual channels by semantic job:

- **Position:** Put the strongest sorting key at the far left. For action lists this is usually `p0`-`p4`, followed by the action. For portfolios it may be priority, status group, or stage.
- **Grouping:** Create one labeled divider per meaningful category or lifecycle group. Add vertical whitespace between groups instead of repeating the group value on every row.
- **Primary text:** Keep names, actions, and campaign titles neutral and readable. Bold selectively; do not color whole prose cells.
- **Metadata color:** Color compact semantic fields such as priority, posture, stage, due date, and evidence state. Reuse the application's semantic palette.
- **Emoji:** Use one recognizable emoji on group headings when it accelerates navigation. Emoji is a landmark, not a substitute for text or a decoration on every row.
- **Whitespace:** Prefer breathing room between sections and priority bands over boxes, separator noise, or dense punctuation.

Use plain colored `p0`-`p4` labels rather than colored-circle priority emoji. Color must reinforce text, never carry meaning alone.

## Control density and wrapping

- Keep the default table to roughly five conceptual columns. Merge related secondary values only when the result remains scannable.
- Give short enum and owner columns explicit widths with `no_wrap=True`.
- Let the main prose column absorb remaining width. Set a useful `min_width`; avoid allowing metadata columns to steal space from it.
- Do not place a sentence-like list of metrics in one narrow cell. Use compact labeled counts, a small pipeline, separate lines, or a detail block.
- Format dates for recognition and add relative urgency where it changes action. Keep raw ISO values available in details when needed.
- Avoid manual hard wrapping. Let Rich measure terminal width.
- At narrow widths, protect meaning before alignment: preserve priority, title, state, and the immediate next step; demote lesser metrics.

## Choose the right projection

Use one of these shapes deliberately:

- **Worklist:** priority, action, posture, due, context; category dividers; details reveal body and ID.
- **Portfolio:** priority, title, lifecycle/stage, compact progress signal, recent activity; details reveal next gate and identifiers.
- **Scoreboard:** grouped metric blocks or a narrow table when comparison matters more than prose.
- **Single-record view:** labeled sections or a tree, not a one-row mega-table.

Default output should answer the common question in seconds. `--details` should deepen the same hierarchy rather than switching to an unrelated layout. A `show <id>` command should remain the complete context reload.

## Implement with restraint

1. Reuse shared console, semantic styles, date helpers, and render primitives.
2. Keep data loading independent from rendering so tests can construct rows directly.
3. Add small renderer helpers when they encode a reusable semantic unit, such as a priority cell or evidence pipeline.
4. Prefer one active renderer. Remove superseded human-facing layouts rather than accumulating variants.
5. Keep output deterministic and accessible with `NO_COLOR`; avoid relying on ANSI assertions.

## Verify the interface

- Add focused tests for grouping, field presence, detail behavior, empty states, and filtering.
- Run formatter, linter, types, and the affected test suite.
- Inspect the real command at 80 and 120 columns, both default and detailed.
- Check long names, empty metrics, mixed statuses, and the densest owner/context values.
- Confirm that color, emoji, and whitespace improve scan order rather than merely making the output busier.

Finish by reporting the scan question the design now answers, the default/detail split, and the widths manually inspected.
