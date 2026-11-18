# Engineering playbook

Reusable judgment, technology comparisons, and research live with their subject.
This includes software-engineering and AI discoveries and technical learning.
Private client applications, relationships, commitments, and personal reference
lists stay with their private owner. Keep reusable evidence here and link to it
from private applications rather than maintaining competing technical syntheses.
Browse the directories or search their filenames; there is no document register.
Keep original reading links beside the conclusions they support, with the source
title, review date, and a short reason to revisit. Mark a particularly useful
source **Read in full** in its subject page. A synthesis is not a replacement
for the source; do not create a separate bookmark queue or duplicate summary.

- [Agents](agents/README.md): models, harnesses, orchestration, tools, integration,
  memory, evaluation, and the authority of agents.
- [Engineering](engineering/README.md): design decisions, verification, review,
  documentation, builds, and developer workflows.
- [Languages](languages/README.md): language selection, idioms, libraries, and
  framework guides.
- [Systems](systems/README.md): application services, data, infrastructure,
  security, hosting, and workstation tools.
- [Product](product/README.md): discovery, visual design, and user interfaces.

## A connected map of the stack

Classify a new product by the responsibility it takes over, not by its use of “AI-native.” One vendor can span several rows, and an application can buy one layer without adopting the rest of its platform.

| Responsibility | Question and owning subject |
| --- | --- |
| Models | Who generates or classifies an answer, at what quality, latency, and cost? [Model choices](agents/models/providers.md) |
| Harness and coordination | Who maintains context, chooses tools, limits a run, and recovers work? [Harnesses](agents/harnesses.md), [orchestration](agents/orchestration.md) |
| Execution and hosting | Where does code run? Distinguish a local container engine such as Kiri, fleet orchestration such as Kubernetes, and application hosting. [Infrastructure](systems/infrastructure.md), [services](systems/services.md) |
| Tools and connections | How does the application reach existing systems and perform typed operations? [Integrations](agents/integrations.md), [browser engines and controls](agents/browser.md) |
| Identity and authority | Who is acting, what may they access, and where is that decision enforced? [Authorization](systems/authorization.md), [agent security](agents/security.md) |
| Records and meaning | What is authoritative, and what does an entity mean for this decision? [Data stores](systems/data-stores.md), [retrieval](systems/retrieval.md) |
| Human interaction | How do people inspect, approve, correct, and use the result? [Agent interfaces](agents/interfaces.md), [product interfaces](product/interfaces.md) |
| Verification and operation | What shows the result is correct, and how are failure and recovery observed? [Verification](engineering/verification.md), [evaluation](agents/evaluation.md) |

A CRM with agents owns business records and workflows; an identity service or container runtime does not become its substitute by adding an agent API. AWS Emulator supplies a test environment, not permission assurance. A browser engine and its automation interface are different choices. Cheap implementation can shift effort toward definitions, independent checks, integration maintenance, and safe operations without eliminating them. Private venture reasoning should ask which valuable outcome a buyer will pay for and which responsibilities repeat across customers; it belongs with its private owner, linked to these technical comparisons.

## Research lifecycle

[The watchlist](watchlist.md) holds questions and revisit triggers. The linked
subject pages own the comparisons and evidence. Update an existing topic when
new research changes its conclusion; a candidate becoming adopted does not need
a new research location. Keep evidence dates and uncertainty with the claim.

Workbench's current configuration and decisions belong in [docs](../docs/README.md).
Executable agent workflows belong in [skills](../agents/skills/), reusable prompt
artifacts in [prompts](../agents/prompts/README.md), and portable health examples
in [health](../health/README.md). Private records and temporary research stay with
their owning project or in ignored scratch space.
