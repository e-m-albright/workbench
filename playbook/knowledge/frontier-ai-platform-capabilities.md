# Frontier AI platform capabilities

Last reviewed: 2026-09-12

This document tracks the developer-platform capabilities exposed by OpenAI,
Anthropic, and Google. It inventories product primitives rather than every API
method, model name, quota, or user-interface feature. Model selection, privacy,
and subscription portability remain in [Frontier Coding Model Providers](frontier-model-providers.md).
Reusable orchestration lessons remain in [Agent Capability Patterns](agent-capability-patterns.md).

All capability descriptions below come from provider documentation. A listed
feature is evidence that the provider exposes it, not evidence that it is mature,
safe, economical, or better than an application-owned alternative. Preview and
beta labels matter.

## Current conclusion

The three providers are converging on the same base platform:

- a stateful model API with streaming and background execution
- built-in retrieval, code execution, computer use, and external tools
- managed agent sessions with sandboxes, retained state, and observability
- context caching or compaction for long-running work
- multimodal input, structured output, evaluation, and governance controls

The meaningful differences are now in integration shape and trust boundaries:

- **OpenAI has the broadest end-to-end application platform.** It spans direct
  model calls, a managed Codex harness, multi-agent orchestration, browser voice
  over WebRTC, application widgets, plugins, workspace agents, evals,
  fine-tuning, and enterprise deployment controls.
- **Anthropic has the clearest composable agent primitives and capability
  disclosure.** Its feature matrix explicitly identifies platform availability
  and Zero Data Retention eligibility. Advisor calls, programmatic tool calling,
  tool search, progressive-disclosure skills, and a choice among Messages, the
  Agent SDK, and Managed Agents are the notable design patterns.
- **Google has the broadest native modality surface.** Gemini covers text,
  images, audio, video, music, live vision, transcription, translation, maps,
  robotics, and managed agents. Its newer Interactions API improves platform
  coherence, but current gaps and storage defaults require deliberate handling.

Do not select a provider by feature count. Keep ordinary model calls, tools,
state, and evaluation behind application-owned contracts. Use a provider-specific
feature only when its distinct value pays for the portability, retention, and
operational cost.

## Capability map

| Area | OpenAI | Anthropic | Google Gemini |
| --- | --- | --- | --- |
| Primary model interface | Responses API | Messages API | Interactions API; `generateContent` is legacy but supported |
| Application-owned agent loop | Agents SDK | Claude Agent SDK | Google Agent Development Kit and Antigravity SDK |
| Managed agent runtime | Agents API with the Codex harness | Managed Agents | Gemini Managed Agents with Antigravity and Deep Research |
| Native multi-agent | Responses and Agents API multi-agent, beta | Agent SDK subagents; managed orchestration primitives | Framework or custom-agent orchestration; managed agents do not advertise an equivalent first-class multi-agent switch |
| Hosted execution | OpenAI-hosted sandbox plus self-hosted and partner environments | Anthropic-hosted or self-hosted environment | Google-hosted Linux sandbox |
| Built-in current-information tools | Web search, file search, connectors | Web search and web fetch | Google Search, Google Maps, URL context, and file search |
| Tool-scale controls | Programmatic tool calling, tool search, namespaces, remote MCP | Programmatic tool calling, tool search, fine-grained streaming, remote MCP connector beta | Combined built-in tools and function calling; remote MCP for Gemini 3 is documented as coming soon |
| Browser and computer control | Computer use through a supplied environment | Browser use and computer use through client-side environments | Computer use plus agentic vision and robotics surfaces |
| Realtime interaction | WebRTC and WebSocket voice, transcription, translation, SIP | No native realtime voice platform in the reviewed Claude API surface | WebSocket Live API for audio, image, and text input with audio output; partner WebRTC integrations |
| Media generation | Images, speech, custom voices, and Sora video | Text output; vision and PDF understanding, but no native image, audio, or video generation in the reviewed API surface | Images, video, music, speech, transcription, and translation |
| Long-running state | Conversations, background Responses, durable agent sessions, compaction, webhooks | Client-managed Messages; resumable Agent SDK sessions; stateful Managed Agents; compaction beta | Stored Interactions, `previous_interaction_id`, background execution, and managed-agent environments |
| Evaluation and optimization | Datasets, graders, trace grading, agent evals, prompt optimizer, external-model evals, multiple fine-tuning methods | Evaluation tooling, prompt tooling, batch processing, and model steering; no public fine-tuning surface in the reviewed capability index | Logs and datasets, prompt tools, batch, caching, flex and priority inference; safety and tuning surfaces are less unified in the Gemini API docs |
| Enterprise controls | Projects, service accounts, role-based access control, spend and rate controls, workload identity, Mutual TLS, IP controls, Private Link, Terraform | Workspaces, Admin API, usage and cost API, Compliance API, data residency, per-feature retention matrix | Projects, billing and rate limits, OAuth, logs, safety settings, regional availability, Google Cloud distribution |

## OpenAI inventory

### Core model and media

- Responses API for text, reasoning, vision, structured outputs, streaming, and
  conversation state.
- Server-sent event streaming, WebSocket mode, mid-turn steering, asynchronous
  tool calls, background mode, webhooks, and standalone or server-side
  compaction.
- Image understanding, image generation and editing, file inputs, PDF and
  document workflows, speech-to-text, text-to-speech, custom voices, live
  transcription, live translation, and Sora video generation.
- Embeddings and vector retrieval.
- Batch, flex, fast, and ordinary processing tiers; token counting, predicted
  outputs, prompt caching diagnostics, latency guidance, and spend controls.

### Tools and retrieval

- Application functions with structured arguments.
- Programmatic Tool Calling, which lets model-written programs invoke an
  allowlisted tool subset without returning every intermediate step to the model
  context.
- Tool search and namespaces for deferring large tool surfaces until needed.
- Hosted web search, file search, vector stores, Code Interpreter, hosted shell,
  local shell, Apply Patch, computer use, and image generation.
- Remote Model Context Protocol servers, provider-maintained connectors, and a
  secure outbound tunnel for private Model Context Protocol servers.
- Reusable skills for shell and agent environments.

### Agent surfaces

OpenAI exposes four different abstraction levels:

1. **Responses API:** application-owned control with optional hosted tools,
   conversation state, and beta multi-agent orchestration.
2. **Agents SDK:** a code-first loop with agents, handoffs, agents-as-tools,
   guardrails, approvals, tracing, and sandbox integrations.
3. **Agents API:** an OpenAI-managed Codex harness with durable sessions,
   context compaction, recovery, events, webhooks, artifacts, tracing, hosted or
   self-hosted environments, Model Context Protocol tools, plugins, credential
   vaults, and beta multi-agent orchestration.
4. **Agent Builder and ChatKit:** visual workflow composition that can export to
   code, plus an embeddable chat interface and widgets.

Multi-agent gives each subagent a separate context and lets the root create,
message, wait for, interrupt, and combine subagent work. OpenAI explicitly
recommends it for independent workstreams and warns against it for ordered work,
small tasks, shared mutable state, or work dominated by one slow external call.
It is beta and can materially increase token use.

Agents can use OpenAI-hosted sandboxes, self-hosted compute, or documented
partners including Cloudflare, Daytona, DigitalOcean, E2B, Modal, Runloop,
Vercel, Blaxel, and Oracle Cloud Infrastructure. OpenAI's security guidance says
agent-generated code can access every file, credential, and network route made
available to its environment. It recommends isolated workloads, outbound
allowlists, a restricted executor key, and credential brokers that inject
third-party secrets only into approved requests.

### Voice and realtime

- The Realtime API provides low-latency speech-to-speech conversations, barge-in,
  turn detection, transcripts, tools, handoffs, and guardrails.
- Browsers connect directly over WebRTC with an ephemeral credential or through
  a trusted server that exchanges the Session Description Protocol offer.
  Servers can use WebSockets. Telephony can use Session Initiation Protocol or
  an audio bridge.
- GPT-Live separates a fast conversational frontend from a more capable
  Responses backend. A data channel carries transcripts, events, session
  updates, and delegated work while media travels on WebRTC tracks.
- Server-side controls keep private instructions and tool execution off the
  browser. The browser never receives the project API key.

The important design is not voice synthesis by itself. It is the split between a
low-latency conversational model and a slower backend agent, with explicit event
and authority boundaries between them.

### Evaluation, tuning, and operations

- Datasets, graders, evaluation runs, agent trace grading, external-model evals,
  prompt generation, and prompt optimization.
- Supervised fine-tuning, direct preference optimization, reinforcement
  fine-tuning, and vision fine-tuning.
- Moderation, safety classifiers, safety identifiers, misalignment monitoring,
  cybersecurity checks, human approvals, and content provenance for generated
  media.
- Admin APIs, projects, service accounts, custom roles, role-based access
  control, rate and spend limits, IP allowlists, Mutual TLS, Private Link,
  workload identity federation, and a Terraform provider.

### Adjacent product surfaces

OpenAI's developer site also exposes capabilities outside the core model API:

- ChatGPT plugins made from skills, Model Context Protocol servers, optional UI,
  authentication, review, and publication. The docs include a migration path for
  packaging a Claude Code plugin for OpenAI.
- Workspace Agents API for triggering published ChatGPT workspace agents from
  backend systems.
- GPT Actions, Codex developer tools, an Ads API, and Agentic Commerce protocols
  for catalogues, checkout, and delegated payments.

These product surfaces are distribution channels, not neutral infrastructure.
Use them only when reaching ChatGPT users or OpenAI-managed workspaces is itself
the requirement.

## Anthropic inventory

### Core model capabilities

- Messages API with streaming and application-managed conversation state.
- Text generation, image understanding, PDF understanding, citations, search
  result blocks, structured JSON output, and strict tool inputs.
- Context windows up to one million tokens on supported models.
- Thinking, adaptive thinking, and effort controls.
- Batch processing at a documented 50 percent discount.
- Server-side fallback between models and fallback credits are beta.
- Per-request data residency controls on supported first-party platforms.

### Tools

Anthropic divides tools by execution owner.

**Server-side:** web search, web fetch, sandboxed code execution, and a beta
Advisor tool that lets a faster executor consult a higher-intelligence model
mid-generation.

**Client-side:** custom functions, Bash, browser use, computer use, memory, and
text editing. The application owns the actual execution boundary.

**Tool infrastructure:** programmatic tool calling from code-execution
containers, dynamic tool search across large catalogues, fine-grained parameter
streaming, a beta remote Model Context Protocol connector, and Agent Skills with
progressive disclosure. The tool-search and programmatic-calling combination is
particularly relevant when a workflow has hundreds of tools or many dependent
calls: it reduces schema and intermediate-result pressure on model context.

### Agent surfaces

Anthropic also exposes four levels:

1. **Messages API and client SDKs:** direct model access with an
   application-owned tool loop.
2. **Claude Agent SDK:** the Claude Code loop embedded in Python or TypeScript,
   including file and shell tools, hooks, subagents, Model Context Protocol,
   permissions, resumable and forkable sessions, skills, commands, memory, and
   plugins.
3. **Managed Agents:** beta hosted or self-hosted environments with stateful
   sessions, persistent event history, tools, Model Context Protocol servers,
   skills, streaming, and permission policy.
4. **Claude Code:** the interactive coding product rather than an application
   runtime.

Managed Agents distinguishes `always_allow`, `always_ask`, and model-evaluated
`auto` permission policies. The prebuilt agent toolset defaults to
`always_allow`; Model Context Protocol toolsets default to `always_ask`.
Model-evaluated approval is useful triage, not a deterministic security boundary.

### Context, files, evaluation, and governance

- Server-side compaction and context editing are beta.
- Automatic prompt caching, explicit five-minute and one-hour cache windows, and
  token counting are generally available on the first-party API.
- Files API supports reusable PDF, image, and text assets but is not eligible for
  Zero Data Retention.
- Agent Skills, code execution, programmatic tool calling, and several managed
  features also require retention. Anthropic's feature overview publishes a
  per-feature Zero Data Retention matrix rather than applying one blanket claim.
- Workspaces, key administration, usage and cost APIs, Admin API, Compliance API,
  evaluation guidance, guardrails, and cloud distribution through Amazon
  Bedrock, Google Cloud, and Microsoft Foundry round out the platform.

Anthropic currently has the clearest documentation of which capability breaks a
Zero Data Retention posture. That is a design advantage for regulated or
privileged workflows even when another provider has more features.

## Google Gemini inventory

### Core and generated modalities

- Text, image, audio, video, and document understanding; long context, thinking,
  thought signatures, structured outputs, and function calling.
- Native image generation and editing through Nano Banana and Imagen, video
  generation through Veo and Gemini Omni, music generation through Lyria,
  speech generation, transcription, translation, and embeddings.
- Robotics capabilities include spatial reasoning, agentic vision, task
  orchestration, streaming control, and video understanding.

Google has the broadest native media and physical-world surface of the three.
That matters for products built around live video, robotics, generated media, or
Google Maps. It does not make Gemini the automatic choice for an ordinary text
agent.

### Interactions API

The Interactions API became generally available and Google's recommended default
for new Gemini projects in June 2026. It unifies direct model and specialized
agent calls, supports observable execution steps, optional server-side state,
streaming, and background execution, and is where Google says new model, tool,
and agent features will launch.

Important current boundaries:

- Interactions are stored by default. Paid projects retain them for 55 days and
  free projects for one day unless configured otherwise.
- `store=false` disables server-side continuation through
  `previous_interaction_id` and is incompatible with background execution.
- Remote Model Context Protocol is not yet supported for Gemini 3.
- Batch, automatic Python function calling, explicit caching, and custom safety
  settings remain on the legacy `generateContent` API rather than Interactions.
- Mixing models in one conversation requires modality compatibility between
  outputs and subsequent inputs.

This is a consequential migration boundary, not a cosmetic endpoint rename.
Applications must choose among retained state, background work, and stateless
privacy, and may need both APIs until feature parity closes.

### Tools and agents

- Google Search, Google Maps, code execution, URL context, computer use, file
  search, and custom function calling.
- Batch processing, webhooks, flex inference, priority inference, context
  caching, token counting, file storage, streaming, and background execution.
- Gemini Managed Agents are in public preview. The Antigravity agent runs code,
  manages files, and browses the web in a Google-hosted Ubuntu sandbox. Deep
  Research handles multi-step research. Agents can be extended with
  instructions, skills, data, hooks, tools, and external APIs.
- Managed-agent sandboxes have unrestricted outbound network access by default.
  Google provides allowlists and a credential-injecting egress proxy; both need
  deliberate configuration.
- Google says one managed-agent interaction can consume roughly 100,000 to three
  million tokens. Environment compute is free during preview, but model and tool
  usage are not.
- The public preview allows up to 1,000 agents, and inactive environments are
  deleted after seven days.
- Google Agent Development Kit and the Antigravity SDK provide code-first local
  orchestration. AI Studio provides visual prototyping.

### Live API

The preview Live API uses a stateful WebSocket. It accepts continuous audio,
images at up to one frame per second, and text, and returns audio. It supports
barge-in, tool use, input and output transcripts, proactive audio, affective
style, live transcription, and voice-to-voice translation across more than 70
languages.

Browsers can connect directly with ephemeral tokens. Google documents partner
WebRTC integrations through LiveKit, Pipecat, Fishjam, Stream, Voximplant,
Agora, and Firebase, but its native protocol is WebSocket rather than OpenAI's
direct WebRTC interface.

## What is worth learning now

### 1. Managed agent APIs have become hosted harnesses

The new OpenAI Agents API and Google Managed Agents are not wrappers around one
model call. They package a coding-style harness, sandbox, files, tools, retained
state, compaction or recovery, and observability behind an API. Anthropic now
offers the same category through Managed Agents.

The adoption question is therefore not “which agent framework has more nodes?”
It is “which runtime may hold the files, credentials, network authority, event
history, and retry budget for this workload?” Local execution and ordinary job
runners remain preferable until hosted continuity or isolation is a real need.

### 2. Multi-agent is becoming one model capability, not always an application architecture

OpenAI can now let the root model create and coordinate subagents without the
application implementing an orchestration graph. Anthropic exposes the same
basic pattern through Agent SDK subagents, while Google's current managed
surface emphasizes one capable sandboxed agent plus external frameworks.

Use this for independent searches or reviews with bounded outputs. Do not use it
for dependent reasoning, shared-file mutation, or tasks where token cost matters
more than wall-clock latency. The durable pattern remains a parent that owns
scope, reconciliation, and verification.

### 3. Voice agents are splitting conversation from work

OpenAI's GPT-Live architecture makes the useful pattern explicit: a low-latency
voice model owns turn taking, interruption, and conversational tone while a
backend Responses agent performs slower retrieval or tool work. Google Live
offers a broader live audio-and-vision stream but leaves WebRTC to partners.
Anthropic currently requires an external speech stack around Claude.

For a browser voice product, OpenAI currently offers the most direct path. For
live camera understanding, translation, robotics, or broad multimodal streams,
Google is more differentiated.

### 4. Context efficiency is moving into the platform

All three providers now offer combinations of prompt caching, server-side state,
compaction, dynamic tool search, and programmatic tool execution. These can
remove repeated tokens and intermediate tool chatter, but they also move
conversation history and execution into provider-owned state.

Treat context efficiency and retention as one decision. The cheapest-looking
stateful option may be unacceptable for sensitive data, and a stateless option
may disable background or continuation features.

### 5. Tool count is no longer a reason to dump every schema into context

OpenAI and Anthropic both expose tool search and programmatic tool calling. The
model can discover a narrow subset, then execute deterministic multi-tool code
without narrating every intermediate result. This validates the existing design
preference for small outcome-oriented tools, search, pagination, and
application-owned composition over giant always-on schemas.

### 6. Default network and permission settings need active review

Google Managed Agents start with unrestricted outbound network access. Anthropic
Managed Agents default their prebuilt agent tools to automatic execution.
OpenAI states plainly that generated code can reach everything exposed to its
environment. None of these products makes authority safe merely by calling the
runtime a sandbox.

Before any trial, set an outbound allowlist, remove ambient credentials, use a
broker or short-lived scoped token, require approval for consequential tools,
and cap total task spend.

## Operating posture

1. Keep direct, provider-neutral model calls as the default for ordinary product
   features.
2. Prefer application-owned tools and state until a hosted agent runtime solves
   a measured need for isolation, continuity, or long-running work.
3. Evaluate OpenAI first for browser voice or a managed Codex-style agent; use a
   single bounded task with explicit token and network limits.
4. Evaluate Anthropic first when tool-scale context efficiency, explicit
   retention eligibility, or the Claude Code harness as a library is the main
   requirement.
5. Evaluate Google first for live multimodal input, translation, generated
   media, Maps, robotics, or Deep Research. Set `store=false` when state and
   background execution are not required.
6. Keep multi-agent work bounded to independent branches and preserve one parent
   owner for synthesis and verification.
7. Do not automate a recurring capability scrape yet. Refresh this document
   manually after a material provider release or when a concrete project reaches
   one of the evaluation triggers above.

## Refresh procedure

Read the provider-maintained indexes first, then inspect only changed or newly
relevant pages:

- OpenAI: [developer index](https://developers.openai.com/llms.txt),
  [API guide index](https://developers.openai.com/api/docs/llms.txt), and
  [API changelog](https://developers.openai.com/api/docs/changelog).
- Anthropic: [developer index](https://platform.claude.com/llms.txt),
  [feature availability matrix](https://platform.claude.com/docs/en/build-with-claude/overview),
  and [release notes](https://platform.claude.com/docs/en/release-notes/overview).
- Google: [Gemini API documentation](https://ai.google.dev/gemini-api/docs),
  [release notes](https://ai.google.dev/gemini-api/docs/changelog), and
  [deprecations](https://ai.google.dev/gemini-api/docs/deprecations).

Update the review date only after reconciling the capability map, provider
inventories, current conclusions, and sources. Do not copy model catalogues or
prices into this page.

## Primary sources

### OpenAI

- [OpenAI developer index](https://developers.openai.com/llms.txt)
- [OpenAI API guide index](https://developers.openai.com/api/docs/llms.txt)
- [Agents API](https://developers.openai.com/api/docs/guides/agents-api)
- [Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent)
- [Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)
- [Realtime API](https://developers.openai.com/api/docs/guides/realtime)
- [WebRTC](https://developers.openai.com/api/docs/guides/voice-webrtc)
- [Plugins](https://developers.openai.com/plugins/llms.txt)
- [Workspace Agents](https://developers.openai.com/workspace-agents/llms.txt)

### Anthropic

- [Claude developer documentation](https://platform.claude.com/docs/en/home)
- [Feature availability and retention matrix](https://platform.claude.com/docs/en/build-with-claude/overview)
- [Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview)
- [Managed Agents](https://platform.claude.com/docs/en/managed-agents/quickstart)
- [Managed-agent permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies)
- [API and data retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)

### Google

- [Gemini API documentation](https://ai.google.dev/gemini-api/docs)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview)
- [Managed Agents](https://ai.google.dev/gemini-api/docs/agents)
- [Live API](https://ai.google.dev/gemini-api/docs/live)
- [Model catalogue](https://ai.google.dev/gemini-api/docs/models)
