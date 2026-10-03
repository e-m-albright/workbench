# Persistent assistants

Compare persistent personal agents, recurring work, memory, and human supervision across assistant products.

## Role-based onboarding and teach-by-demonstration

Grok Bot packages a persistent cloud agent as named roles such as researcher, recruiter, or market analyst. The user can describe an outcome, choose a suggested role, or demonstrate a task in the agent's browser. The product converts a successful demonstration into a draft skill and can run that skill later as a routine. Desktop and mobile clients preserve access to the same background agent.

The transferable product pattern is a short progression:

1. Start from the user's job or outcome rather than asking them to design tools and prompts.
2. Let the user demonstrate an unfamiliar workflow instead of fully specifying it in prose.
3. Turn the demonstration into an inspectable draft skill.
4. Test the skill once before allowing it to become a recurring routine.
5. Keep the routine's progress, approvals, and handoffs visible across desktop and mobile.

This lowers the setup cost for non-technical users and teaches agent use through concrete work. Named roles also make delegation easier to understand, but they are interface boundaries rather than authority boundaries. Grok Bot's official documentation says all Bots for one user share one cloud computer, files, browser sessions, and credentials. Separate Bots therefore belong to one trust domain and must not imply isolation. Its model-based approval review can help triage prompts, but it is not a deterministic security boundary.

### Disposition

Adopt the onboarding sequence as a design reference, not the hosted credential model or a standing roster of named agents. If Workbench gains a repeated non-coding workflow, begin with an outcome-specific template and a demonstration-to-draft-skill flow. Require inspection and one successful supervised run before scheduling. Preserve explicit capability scope, deterministic policy, and least privilege underneath any friendly role metaphor.

The evidence is early. Official material establishes the interface and shared-runtime design. Early community reports broadly agree that setup is unusually approachable and that demonstrations and recurring monitoring are the distinctive features, but reports of execution quality are mixed. There is not enough independent head-to-head evidence to claim that Grok Bot produces better outcomes than Perplexity Computer. The supported conclusion is narrower: it is easier to start, not proven safer or more reliable to trust.

Reviewed 2026-08-30. Sources: [Grok Bot](https://x.ai/bot), [overview](https://docs.x.ai/grok-bot/overview), [skills, routines, and automations](https://docs.x.ai/grok-bot/skills-routines-and-automations), [approvals, security, and privacy](https://docs.x.ai/grok-bot/approvals-security-and-privacy), [FAQ](https://docs.x.ai/grok-bot/faq), [Perplexity Computer](https://www.perplexity.ai/products/computer), and early [Hacker News discussion](https://news.ycombinator.com/item?id=49261514).

## Persistent personal agents to monitor

[Lefos](https://earendil.com/posts/announcing-pi-and-lefos/) is an adjacent email-first assistant in public alpha. Its durable channel and collaborative correspondence are worth watching alongside dedicated agent computers. The cited first-party announcement does not establish every integration or communication channel claimed in secondary summaries; verify those before comparing permissions.

| Product | Published mechanism | Open question for a serious deployment |
| --- | --- | --- |
| [Meta Muse](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) | Dedicated cloud computer; separate credential service and privileged connector workers; Sentinel mediates connector actions and network egress; credential surrogation keeps real tokens outside the agent runtime | How completely the boundary covers new connectors, browser behavior, and recovery from mistaken actions; Meta presents this as its design, not an independent security audit |
| [Grok Bot](https://x.ai/news/designing-grok-bot) | Persistent named Bots with a cloud computer, memory, routines, and visible transcripts | [Security documentation](https://docs.x.ai/grok-bot/security) says a user's Bots share files and browser sessions; examine default network policy, action-review coverage, routine retention, and separation between roles and actual authority |
| [OpenAI Dots](https://help.openai.com/en/articles/20001529-dots-privacy-security-and-safety-faqs) | Persistent context, existing plugin connections, proactive research, action rules, auto-review, and activity view | Plugin permissions span Dots, ChatGPT, Work, and Codex; individual dot memories cannot currently be inspected or edited; verify action coverage, revocation, retention, and whether review is backed by deterministic enforcement |

Monitor these products for five concrete changes: stronger credential isolation; action approval bound to exact parameters and version; a recoverable state machine for uncertain effects; visible, correctable memory and complete run history; and enterprise controls that narrow agent authority below the user's full source permissions. Benchmark a complete recurring task, including correction and cleanup, rather than counting successful demos or autonomous turns. Muse's separated permission authority is an architecture reference; Grok Bot's routine transcript is a usability reference; Dots shows the importance of permission and memory lifecycle across a broader product suite.

The same scrutiny applies to corporate and regulated use. Vendor approvals and model review can help users supervise work, but application-owned credentials, source-side restrictions, durable audit, and read-back remain necessary for consequential writes. Contractual coverage and feature eligibility need validation for the exact workspace and connector configuration before protected data is connected.

- **[Lefos](https://earendil.com/posts/announcing-pi-and-lefos/)** -- **WATCH (reviewed 2026-10-02).** Earendil's email-first collaborative assistant is a reference for open-channel interaction and gradually earned authority. The first-party announcement establishes public alpha and email collaboration; additional claims in a supplied summary about Telegram or integrations remain unverified. Revisit when a recurring communication workflow needs shared human-agent correspondence and its credential, approval, and retention model can be inspected.

## Personal AI assistants / always-on agents (2026-07 watch)

A distinct category from coding harnesses and agent SDKs: persistent assistants
that live in your messaging channels, hold cross-session memory, and act on your
behalf. Same skepticism applies as Tier-3 harnesses (they hide a lot, and the
self-hosted ones are a standing security surface — broad machine access + inbound
messages from many channels). Watch, not adopt, until one earns trust.

- **[OpenClaw](https://openclaw.ai/)** -- The viral one (200k+ GitHub stars). Local-first OSS personal agent by Peter Steinberger (PSPDFKit), BYOK, 24 messaging channels (WhatsApp/Telegram/Slack/iMessage/Signal/...), community plugin ecosystem, writes its own skills. Governance moved to a 7-person steering committee after Steinberger joined OpenAI (early 2026). Biggest open question for us: the attack surface of an autonomous agent bridged to every inbox.
- **[Hermes Agent](https://hermes-agent.org/)** -- Self-hosted personal agent with persistent memory, messaging gateways, and multiple execution backends. Both the coding and automation decisions are settled in [tombstones](../../docs/decisions/tombstones.md); use their revisit conditions rather than treating this as an active trial.
- **[Town](https://www.town.com/)** -- Proprietary, email-native EA: you get an `@town.com` address and delegate like to a human assistant (inbox, calendar, Slack, docs). Founded by ex-Plaid CTO + ex-Google applied-AI lead; $55M Series A from a16z/Forerunner (Jun 2026). The polished rent-don't-own pole of this category.
- **[Poke](https://poke.com/)** (The Interaction Company) -- Messaging-native agent: no app, you text it (iMessage/SMS/Telegram/WhatsApp) and it acts on email/calendar/files -- drafts replies, reschedules, books travel. Launched Mar 2026; $300M valuation (Spark/General Catalyst); first third-party AI agent approved on Apple's Messages for Business (Jun 2026). Town's competitor with texting instead of email as the interface.
- **[Lindy](https://www.lindy.ai/)** -- Cloud "AI employee" -- proactive email management, scheduling, business workflow automation. The no-code/business-buyer pole; less interesting to us than the self-hosted options but a category anchor.
- **[Claude](https://claude.com/blog/cowork-is-now-claude)** (Anthropic; Cowork consolidated into Claude) / **Perplexity Computer** -- The frontier-lab managed takes: autonomous desktop work and cloud agent grounded in live web research respectively. Anthropic's September 2026 consolidation and its separate [Claude Docs](https://support.claude.com/en/articles/16923645-get-started-with-claude-docs) surface are strategically notable: the general Claude product is absorbing agentic work and document creation instead of keeping Cowork as a separate destination. Track whether this removes the need for a standalone personal-work agent, but do not mirror broad consumer surfaces in Workbench without a recurring coding or private-workflow gap and an acceptable data boundary.
