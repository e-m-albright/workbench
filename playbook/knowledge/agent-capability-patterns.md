# Agent Capability Patterns

> **Last reviewed**: 2026-07. Notes on emerging agent-harness capabilities and orchestration patterns — what each is, how it reshapes the workflow, and the tradeoffs. Timestamps like `[source 01:38]` reference the announcement videos these notes were taken from; pricing and benchmark figures date from those announcements and age quickly.

## 1. Advisor Strategy

Addresses the trade-off between intelligence and cost. Pairs a high-intelligence model (Opus) with a more cost-effective model (Sonnet or Haiku).

**How it works**: Instead of standard task decomposition, the smaller model (executor) handles the primary work and tool calls. It only calls the "Advisor" via a tool call when it gets stuck or needs feedback. [source 01:38]

**Performance**: On multilingual SWE-bench, Sonnet + Opus (as advisor) scored 2% higher than Sonnet alone while reducing costs by approximately 11%. [source 02:58]

**Benefits**: Lower costs, increased execution speed, and improved reliability for complex tasks.

## 2. Monitor Tool (Claude Code)

Eliminates the need for "polling loops," where an agent constantly checks the status of background processes.

**How it works**: Claude can create background scripts that monitor progress, errors, and results. When a process finishes, it sends an interrupt to Claude. [source 05:42]

**Impact**: Significant token savings and the ability to run more background processes simultaneously within Claude Code. [source 06:08]

**Usage**: Not active by default — must be explicitly prompted (e.g., "use the monitor tool to observe for errors"). [source 06:38]

## 3. Managed Agents (Anthropic)

Managed infrastructure service that handles the "grunt work" of deploying agents to production.

**Core capabilities**: Anthropic provides secure sandboxing, authentication, logging, and tool execution. [source 08:06]

**Persistent sessions**: Supports long-running autonomous sessions (hours) where progress persists even if you disconnect. [source 08:14]

**Pricing**: Standard token rates apply plus a runtime fee of **$0.08 per session hour** (at announcement). [source 09:18]

## 4. OpenAI Agent Builder (competitor)

Visual, low-code canvas for composing multi-step agentic workflows. [source: [OpenAI video](https://www.youtube.com/watch?v=44eFf-tRiSg)]

**Core capabilities**:
- **Visual workflow construction** — drag-and-drop nodes to define task flow, branching, and loops
- **Handoffs** — route queries between specialized agents (e.g. general assistant -> "Coder" agent for technical questions)
- **Tool integration** — File Search, Code Interpreter, MCP (Model Context Protocol) for external data/app access
- **Guardrails** — constrain outputs to stay within safety/operational parameters

**Positioning**: Competes directly with LangGraph, n8n, and (less directly) with Claude Code's more code-first approach. The move is from "chatbots" (single-turn) to "agents" (developer defines architecture, runtime manages state and tool calls).

**Tradeoffs to watch**:
- **Error surface area** — every handoff and tool call is a new failure mode. A bad handoff in step 2 derails the whole chain
- **Latency** — multi-agent chains are meaningfully slower than single model calls; better fit for async background jobs than real-time UX
- **Lock-in** — visual builders hide the actual orchestration code. Migrating to a different runtime later usually means rebuilding the graph

**Principal-eng read**: The interesting bet is whether visual composition beats code. For prototyping, yes — anyone can sketch a workflow. For production, the usual pattern holds: visual builders get you to a demo fast, then teams hit a ceiling and rewrite in code (LangGraph, custom orchestration, or Anthropic's Agent SDK) for debuggability, version control, and testing. Worth tracking to see if OpenAI closes that gap with better eval/observability in-canvas.
