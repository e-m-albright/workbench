# Engineering Laws — decision heuristics

> Adages worth keeping *only where they change a decision we make*. A model already knows all of these from pretraining, so this is not a glossary — it is a map from **a decision you're about to make** to **the law that should bite** and **the move it implies**. The social laws at the bottom are calibration for judgment, not gates.

Cross-referenced by `playbook/engineering-philosophy.md` (quality bar), `agents/skills/planning/` (estimation, build-vs-buy), and `playbook/tools-to-evaluate.md` (adoption).

## When estimating

- **Ninety-ninety rule** (Cargill) — the first 90% of the code takes the first 90% of the time; the last 10% takes the *other* 90%. Happy-path CRUD is one sprint; the rollbacks, races, and edge cases are three. *Move*: estimate the tail explicitly. A plan whose estimate excludes error paths, migration, and deploy is already wrong — that is a `planning` Red Flag, not a detail.
- **Hofstadter's law** — it always takes longer than you expect, even when you account for Hofstadter's law. *Move*: padding does not save you; an undocumented legacy dependency will eat the buffer. Prefer decomposing into shippable increments over a padded big-bang estimate.

## When choosing build vs. buy / adopting tech

- **Sturgeon's law** — 90% of everything is crap; most new frameworks are a solution in search of a problem. *Move*: favor boring, established tech unless the new tool is a measurable, magnitude-level improvement. Route candidates through `playbook/tools-to-evaluate.md`.
- **Amara's law** — we overestimate a technology's impact in the short run and underestimate it in the long run. *Move*: this is the discipline behind our slow-to-adopt stance — reject the hype cycle without dismissing the decade-long shift. Re-evaluate rejected tech on a timer, not once.
- **Dunning-Kruger effect** — low competence in a domain reads from the inside as confidence. The engineer who proposes a custom consensus algorithm instead of etcd hasn't yet seen the failure modes. *Move*: match ambition to validated understanding; reach for the boring proven primitive before the bespoke distributed system (YAGNI + `planning` "is this already a service?").

## When maintaining code

- **Boy Scout rule** — leave the module better than you found it (rename the confusing variable, add the missing test) so debt never needs a blocking refactor sprint. Reinforces `engineering-philosophy.md` — surface the crack while you're in there.
- **Broken Window theory** — visible debt licenses more debt; a CI suite red for a week teaches the team the bar has dropped. *Move*: fix the first broken window fast. This is *why* our gates ratchet (`playbook/knowledge/engineering-gates.md`) — a green baseline is a social signal, not only a technical one.
- **Kernighan's law** — debugging is twice as hard as writing, so code as clever as you can write is, by definition, too clever for you to debug. *Move*: magic is technical debt. Prefer explicit, readable conditionals over a dense regex or nested ternary — you will meet it again at 2 a.m. Reinforces "convention over configuration over code."

## When scaling effort (people or agents)

- **Brooks's law** — adding people to a late project makes it later: onboarding cost plus non-linear communication overhead.
- **Ringelmann effect** — individual accountability falls as group size grows (social loafing). *For us*: this is the case for small, focused agent pods over large fan-out — a 15-way parallel sweep diffuses responsibility the same way a 15-person standup does. Favor few well-scoped subagents with clear ownership over a crowd of overlapping ones.

## For judgment, not action (social laws)

These explain behavior; they do not gate a decision. Keep them for calibration.

- **Hanlon's razor** — never attribute to malice what incompetence adequately explains. The platform team that dropped your DB version unannounced likely lacked a deprecation process, not a vendetta. Reach for the charitable, cheaper-to-verify explanation first.
- **Peter principle** — people in a hierarchy rise to their level of incompetence (the strong engineer promoted into a management role they're not suited for, and stuck there).
- **Dilbert principle** — the satirical corollary: the least-trusted get moved into roles where they can do the least damage to the actual work.
