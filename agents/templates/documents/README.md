# Call-script HTML template

Use this template for call scripts, interview preparation, meeting run sheets, and rehearsal guides that a person will actively use during a conversation.

The design follows the Notes site directly:

- The same warm paper, raised surface, ink, rule, muted text, and blue accent tokens.
- Native interface typography with a restrained reading serif for the subtitle.
- Sharp ledger-style section rules rather than cards.
- A sticky table of contents on the right at desktop sizes.
- Collapsed sections that open only when selected.
- The same compact uppercase labels and square header controls.
- Matching light and dark themes.

Markdown remains the canonical source. The standalone HTML file is its generated reading view.

## Render a call script

From the Workbench repository:

```bash
just call-script-template
open artifacts/call-script-template/index.html
```

To render a different source file:

```bash
bash agents/templates/documents/render-examples.sh path/to/output path/to/call-script.md
```

The source is GitHub-flavored Markdown with Pandoc metadata. Second-level headings become collapsed sections and the generated table of contents remains on the right.

```yaml
---
title: Conversation run sheet
subtitle: What this conversation needs to accomplish.
updated: September 2026
status: Ready to rehearse
audience: Operating partner
---
```

Keep the title in metadata rather than repeating it as a first-level heading.

## Optional call-script components

The template styles ordinary Markdown without special markup. Raw HTML can add a small set of call-script-specific elements:

- `.prompt` for a question meant to be spoken.
- `.evidence` for supporting facts or a proof story.
- `.warning` for a boundary, risk, or statement to avoid.
- `.callout` for an important implication.
- `.status-row` with `.status-card` children for a compact opening frame.
- `.label` for a short uppercase component label.

Use these only when they improve retrieval during the conversation. The source must remain understandable as Markdown.

## Integrity rules

- Maintain one canonical Markdown source and regenerate the HTML after changes.
- Do not edit the generated HTML as a second copy.
- Keep every section collapsed by default.
- Keep the table of contents on the right on desktop.
- Keep the output standalone so it opens locally without a server or asset directory.
- Use a different interface for a different job rather than expanding this template into a general document application.
