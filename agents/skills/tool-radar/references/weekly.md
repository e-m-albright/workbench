# Weekly technology research spike

Use this mode for a broad industry pulse, a catch-up across tracked subjects, or
an explicitly requested weekly deep research issue. It extends Tool Radar's
bounded discovery workflow; it does not install tools or create a scheduler.

## Scope and ownership

State the research window, the reader's job, and what decision this should help.
Separate tools for doing the work from a market study of potential competitors.
Inspect the existing subject pages and watchlist before choosing search lanes.
Map all tracked pages, but distinguish a deep external review from an inventory
pass. An unexamined category is deferred, not unchanged.

Keep reusable technical conclusions in their existing playbook subjects. Keep
personal recommendations and provisional reports in ignored local artifacts or
the owning private application. A public site receives only an explicitly
approved public projection. Reuse an existing digest's acquisition, confinement,
credential and publishing contracts before creating another pipeline.

## Prepare the local run

In the Workbench checkout, inspect the helper's interface first:

```bash
uv run --locked python scripts/research.py --help
uv run --locked python scripts/research.py prepare --help
```

For a normal weekly run:

```bash
uv run --locked python scripts/research.py prepare --output artifacts/research/weekly
```

Use a new output directory each run; existing directories are rejected. The
helper defaults to UTC today and the preceding seven days. Use `--date` and
`--since` for a fixed catch-up window. It reads only local playbook Markdown,
includes substantive README pages, skips symlinks, and performs no network or
model requests. It writes four artifacts:

- `inventory.json` freezes page paths, titles, heading candidates, URLs and hashes,
  plus the watchlist baseline. Markdown parsing is intentionally lightweight;
  inspect the actual source for consequential interpretation.
- `coverage.json` owns the disposition of each inventoried page.
- `evidence.json` owns source identifiers, provenance and limitations.
- `report.md` is the canonical prose source for the reading view.

The helper lives at `scripts/research.py` in the Workbench repository, not the
deployed skill directory. This is an offline record-keeping utility, not an
unattended research agent.

## Research and synthesize

Choose independent lanes by professional job: agent engineering and verification;
systems, languages and deployment; research, learning, design and persuasion;
coordination and integrations. Check urgent deprecations and security changes
every run, rotate one deeper investigation, and reserve about one quarter of the
budget for topics outside the watchlist. Treat that allocation as a pilot policy,
not a measured optimum.

For an explicitly exhaustive landscape request, expand beyond a quick scan only
where the initial results cannot answer the question. Search serially with
high-signal queries. Shortlist before opening pages, prefer dated primary
sources, and collect counterevidence. Stop a lane when further retrieval is
unlikely to change its conclusion.

Separate these evidence roles in the prose:

- A release note establishes documented availability, not local value.
- A paper establishes what its authors tested, not universal generalization.
- A practitioner thread suggests a workflow or failure mode, not adoption rates.
- A search snippet is a discovery lead, not inspected repository source.
- A vendor comparison is interested evidence, even when technically detailed.

For Reddit or another community, sample different practitioner groups and retain
replies, disagreement, dates, concrete workflows, and commercial affiliations
when visible. Report sample size and selection limits. If a lane is blocked,
record the failed operation and finish unaffected work. Do not bypass challenges,
authentication or tool denials, or execute a downloaded helper to finish reading.
A mirror is weaker evidence and must be labeled as such.

For every consequential change, establish the previous baseline, dated new
evidence, implication, strongest counterargument, and exact next action. Separate
newly discovered products from newly launched products. Verify repository license,
maintenance, permissions and security before any trial; star totals do not prove
growth or quality. Keep the actionable repository shortlist to five even when the
broader category map is larger.

## Complete the evidence contract

Each `evidence.json` source needs:

- `id`: `S01` style, unique within the run.
- `title`, `url`, `kind`: nonempty title, HTTP(S) URL without credentials, and
  `primary`, `independent`, or `community`. Primary does not mean impartial.
- `published`: ISO date, or `null` when publication timing is unproven. For a
  rolling changelog, cite each relevant entry's date in the claim/prose.
- `retrieved`: ISO retrieval date, not later than the run's as-of date.
- `claim`, `limitation`: what the source supports and what it cannot establish.

Cite evidence as `[S01]` in `report.md`, with full source titles and URLs in its
source section. Each coverage row names its exact topic path, a note explaining
the scope, supporting source identifiers, and one final status:

- `researched`: fresh external evidence examined; specify any narrower scope.
- `reviewed`: local baseline or orientation assessed without a fresh full audit.
- `deferred`: follow-up needed; explain what remains unexamined.

Pending rows are incomplete. Do not use a coverage status to imply that every
vendor on a page received a new review. Do not manufacture a launch date for live
documentation or use a retrieval date as evidence of novelty.

## Deliver and verify

The briefing should contain a short decision path, a dated change chronology,
a category map, missing topics, skeptical interpretations, the five-repository
shortlist, at most three immediate experiments, and explicit evidence limits.
Allow a meaningful no-news result. Generate HTML from the canonical Markdown:

```bash
uv run --locked python scripts/research.py check artifacts/research/weekly
bash agents/templates/documents/render-reading.sh artifacts/research/weekly artifacts/research/weekly/report.md
```

The checker verifies records and references, not truth, citation entailment,
source independence, completeness, HTML safety or publishability. Rendered
reports require the normal document-design visual review. Treat the helper as
trusted local tooling, not an operating-system security boundary against a
concurrent hostile writer.

Record the actual model/provider and research date. Close by distinguishing
verified findings, recommendations, blocked lanes and implemented automation.
After at least three useful manual runs, evaluate deterministic candidate
collection through the existing owner. Schedule only after stable filters,
spend limits, partial-coverage handling and a no-op outcome are demonstrated.
Publishing remains separate from generation and needs exact authorization.
