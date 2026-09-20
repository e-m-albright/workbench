# Working Files and Agent Artifacts

Use the project's existing ignored scratch or artifact directory. Workbench uses
`tmp/` for temporary work and `artifacts/` for generated deliverables. Check the
project's ignore rules before writing; a directory name alone does not keep a
file out of Git.

## What belongs where

| Material | Owner and lifetime |
|---|---|
| Provisional plan, research, debugging notes | Conversation or ignored scratch directory; remove when superseded |
| Approved implementation plan | Project's established plan location; retain while execution needs it |
| Settled architecture, decisions, operating instructions | Maintained project documentation; see [Project Memory and Decisions](project-memory.md) |
| Generated report, rendering, diagram | Project artifact directory; keep one canonical source |
| Cross-session continuation | [Handoff skill](../../agents/skills/handoff/SKILL.md) and its private queue |
| Raw conversations and private operational state | Their private owner; never a public repository |

Date a research snapshot and record its question, evidence, sources, conclusion,
and uncertainty. Name the exact files and verification results in an execution
plan. Update a plan when authorized scope changes; use Git history or the
project's approval record instead of accumulating competing version files.

## Deliverables

Keep agent-facing instructions and canonical maintained sources in Markdown.
For a longer owner-facing report, generate an HTML reading view from the same
source, with a useful table of contents and collapsible detail. Use the
[document-design skill](../../agents/skills/document-design/SKILL.md) and the
maintained [document templates](../../agents/templates/documents/README.md)
when they fit the job. Do not maintain duplicate prose in Markdown and HTML.

Link the final artifact and state what was verified. Separate observed evidence
from inference and leave unresolved decisions explicit. Copy paste-ready message
text to the clipboard only when that is the requested deliverable.

## Cleanup

After incorporating research or finishing a plan, remove obsolete scratch files
within the authorized task scope. Handoffs follow their skill's ready/consumed
lifecycle; do not replace that queue with repository-local conversation logs.
Keep durable decisions in their real documentation rather than an artifact index.
