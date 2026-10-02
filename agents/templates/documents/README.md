# Document HTML templates

Markdown remains canonical. These templates generate standalone HTML reading views for two distinct jobs:

- `reading.html` presents reports, briefs, research, and other long-form documents with a decision path and an audit path.
- `call-script.html` supports call scripts, interview preparation, meeting run sheets, and rehearsal guides used during a live conversation.

## Reading template

The reading template provides a restrained long-form foundation rather than a fixed report composition. It includes a responsive table of contents, readable prose measure, full-width evidence tables, light and dark color schemes, accessible horizontal table overflow, and print handling that opens disclosure sections without changing their saved screen state.

Install Pandoc, then render the maintained neutral example:

```bash
just reading-template
open artifacts/reading-template/index.html
```

To render another Markdown source:

```bash
bash agents/templates/documents/render-reading.sh path/to/output path/to/report.md
```

Use Pandoc metadata for the document frame:

```yaml
---
title: Service renewal decision
subtitle: The recommendation and evidence in one reading view.
updated: September 2026
audience: Technical executive
lang: en
---
```

The source may use ordinary Markdown tables and raw HTML `details` elements. Keep material-specific hierarchy and evidence geometry in the source; do not turn this foundation into a universal report schema.

## Call-script template

Use this template for conversation material that must be quickly retrieved while speaking. The design follows the Notes site directly:

- The same warm paper, raised surface, ink, rule, muted text, and blue accent tokens.
- Native interface typography with a restrained reading serif for the subtitle.
- Sharp ledger-style section rules rather than cards.
- A sticky table of contents on the right at desktop sizes.
- Collapsed sections that open only when selected.
- The same compact uppercase labels and square header controls.
- Matching light and dark themes.

The standalone HTML file is a generated view of the canonical Markdown.

### Render a call script

Install Pandoc, then run from the Workbench repository:

```bash
just call-script-template
open artifacts/call-script-template/index.html
```

`just check-documents` renders the maintained example into a temporary directory
and verifies that Pandoc produced standalone HTML. The full `just check` gate and
CI both include this smoke test.

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

### Optional call-script components

The template styles ordinary Markdown without special markup. Raw HTML can add a small set of call-script-specific elements:

- `.prompt` for a question meant to be spoken.
- `.evidence` for supporting facts or a proof story.
- `.warning` for a boundary, risk, or statement to avoid.
- `.callout` for an important implication.
- `.status-row` with `.status-card` children for a compact opening frame.
- `.label` for a short uppercase component label.

Use these only when they improve retrieval during the conversation. The source must remain understandable as Markdown.

## Shared integrity rules

- Maintain one canonical Markdown source and regenerate the HTML after changes.
- Do not edit the generated HTML as a second copy.
- In call scripts, keep every section collapsed by default and the table of contents on the right on desktop.
- Keep each output standalone so it opens locally without a server or asset directory.
- Use a different interface for a different job rather than expanding either template into a general document application.
