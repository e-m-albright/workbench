# LLM Eval & Observability Tooling

> **Last reviewed**: 2026-03 survey (pricing/maturity snapshots date from then). The recommendation is framed for a PydanticAI + pydantic-graph stack; the landscape sections generalize to any agent system. See also [`ai-tools.md`](ai-tools.md) for the durable ownership model and [`../tools-to-evaluate.md`](../tools-to-evaluate.md) for graduated picks.

## Landscape Overview

The tooling splits into two categories that increasingly overlap:

| Category | Purpose | Examples |
|---|---|---|
| **Eval Frameworks** | Test prompts/agents before deploy, run in CI | Promptfoo, pydantic-evals, DeepEval, Inspect AI |
| **Observability Platforms** | Trace, monitor, and evaluate in production | Langfuse, Logfire, Arize Phoenix, Braintrust, W&B Weave |

The most capable production stacks combine one from each category. No single tool does everything well.

---

## 1. Promptfoo

**What it is**: Open-source CLI + library for LLM eval and red-teaming. YAML-driven configs, runs locally, stores results in your repo. Used by OpenAI and Anthropic internally.

**Maturity**: High. 15k+ GitHub stars, active development, strong community. Now maintained/backed by OpenAI (as of early 2026).

| Dimension | Details |
|---|---|
| **Core model** | Define prompts, providers, test cases in YAML. Run `promptfoo eval`. Get a comparison table. |
| **Providers** | 90+ supported: OpenAI, Anthropic, Google, Azure, Bedrock, Ollama, any OpenAI-compatible API |
| **Assertion types** | Exact match, substring, regex, JSON schema, semantic similarity, LLM-graded rubrics, cost thresholds, latency thresholds |
| **LLM-as-judge** | Built-in via `llm-rubric` assertion type. Define rubric in natural language, judge model scores output. |
| **Red teaming** | 67+ attack plugins: prompt injection, PII leak, jailbreaks, toxicity, hallucination. Standout differentiator. |
| **CI/CD** | First-class. GitHub Actions, GitLab CI, Jenkins. Quality gates with min score thresholds. |
| **Agent eval** | Dedicated agent eval support: traces multi-step agent execution, asserts on tool calls, step counts, intermediate reasoning |
| **Dataset mgmt** | YAML/JSON files in repo. No centralized platform — results stay local as JSON/HTML. |
| **Self-hosted** | Entirely local by default. No cloud dependency. |
| **Pricing** | Free, open-source (MIT) |

**Unique strengths**: Security/red-teaming is best-in-class. YAML config is version-controllable. Zero vendor lock-in. Perfect for pre-deploy testing.

**Key limitation**: No production monitoring. No centralized dashboard for experiment tracking across runs. Results are local files.

**PydanticAI integration**: No native integration. Would need custom provider wrapper or use via OpenAI-compatible API passthrough.

---

## 2. Braintrust

**What it is**: Managed eval + observability platform. Full lifecycle from dataset curation to CI enforcement to production monitoring.

**Maturity**: High. Well-funded, production-proven at scale, strong enterprise adoption.

| Dimension | Details |
|---|---|
| **Core model** | Datasets + experiments + scorers. Define scorer functions, run experiments, compare results in web UI. Production traces become test cases with one click. |
| **Tracing** | Real-time trace inspection with drill-down into tool calls. Hierarchical span view. |
| **Scoring** | LLM-based, code-based, or human scoring. "Loop" feature generates custom scorers from natural language. |
| **CI/CD** | Built-in CI integration. Evaluations run automatically on every change. Quality gates block deploys on regression. |
| **Agent support** | Detailed traces across agent steps, tool calls. Multi-step agent workflows traced end-to-end. |
| **Dataset mgmt** | Centralized dataset management. Version control. Collaborative annotation. |
| **Prompt mgmt** | Prompt versioning, A/B testing, playground for iteration |
| **Self-hosted** | Cloud-only for Starter/Pro. Hybrid deployment on Enterprise. |
| **Pricing** | **Starter**: $0/mo (10K scores, 1GB included, then $2.50/1K scores). **Pro**: $249/mo (unlimited spans/scores). **Enterprise**: Custom. |

**Unique strengths**: Best managed platform for teams treating eval as a release-level concern. Production traces become eval cases. Shared UI for PMs + engineers.

**Key limitation**: Proprietary, closed-source. Cloud-only below Enterprise tier. Per-score pricing can get expensive at scale.

**PydanticAI integration**: No native integration. Generic Python SDK would work for sending traces.

---

## 3. Langfuse

**What it is**: Open-source (MIT) LLM engineering platform. Observability + evals + prompt management. YC W23 company, Series A backed.

**Maturity**: High. 20k+ GitHub stars, multiple commits/week, broad ecosystem adoption. One of the most actively maintained tools in the space.

| Dimension | Details |
|---|---|
| **Core model** | Ingest traces via SDK/API, view in web UI. Run evals on traces. Manage prompts. Annotate datasets. |
| **Tracing** | Hierarchical traces capturing LLM calls, tool use, retrieval, agent steps. OpenTelemetry-compliant. SDKs for Python/JS. |
| **Evals** | LLM-as-judge, custom score rubrics, dataset versioning, human annotation queues. Evaluate on production traces or offline datasets. |
| **Prompt mgmt** | Version-controlled prompts, playground, A/B testing |
| **Dataset mgmt** | Full dataset management with versioning. Production traces become dataset items. |
| **Self-hosted** | Docker Compose (5 min setup), Kubernetes via Helm. Same codebase as cloud. MIT license — truly free self-hosted. |
| **Framework support** | OpenTelemetry, LangChain, LlamaIndex, OpenAI SDK, LiteLLM, and more. Framework-agnostic. |
| **Pricing** | **Hobby**: Free (50K units/mo, 2 users, 30d retention). **Core**: $29/mo (100K units). **Pro**: $199/mo (unlimited history). **Self-hosted**: Free (core features unlimited). Enterprise license for SSO/RBAC/support. |

**Unique strengths**: Truly open-source and self-hostable with no feature gating. Broadest integration ecosystem. Strong community. Good balance of observability + eval.

**Key limitation**: Self-hosted operational overhead (~$3-4K/mo infra for medium-scale). Reported 15% tracing overhead in benchmarks. Less deep agent-specific features than some alternatives.

**PydanticAI integration**: No native PydanticAI integration, but OpenTelemetry-compliant — can receive OTel traces from any source. Would work with Logfire as instrumentation layer + Langfuse as backend (documented pattern).

---

## 4. Pydantic Logfire

**What it is**: Full-stack observability platform from the Pydantic team. Built on OpenTelemetry. First-party integration with PydanticAI and pydantic-evals.

**Maturity**: Medium-High. Backed by Pydantic's Series A. Production-ready but younger than Langfuse/Datadog. Pricing restructured Jan 2026.

| Dimension | Details |
|---|---|
| **Core model** | `logfire.instrument_pydantic_ai()` — one line to trace all agents. Captures the full application stack, not just LLM calls. |
| **Tracing depth** | Agent execution flows, every tool call (args, response, latency), multi-turn conversations, streaming chunks. Also traces HTTP, DB queries, Pydantic validation — full-stack. |
| **AI-specific features** | Conversation panels, token tracking per request/model, cost monitoring with alerts, tool call inspection, streaming visibility |
| **Eval integration** | Native integration with pydantic-evals. Experiment results auto-appear in Logfire UI for visualization and comparison. |
| **OpenTelemetry** | Built on OTel natively. All data is OTel spans. Can export to any OTel-compatible backend. |
| **Self-hosted** | Cloud-only currently. Enterprise self-hosted available on request. |
| **Pricing** | **Personal**: $0/mo (10M spans, 1 seat, 3 projects). **Team**: $49/mo (5 seats, 5 projects). **Growth**: $249/mo (unlimited seats/projects). Overage: $2/M spans. |

**Unique strengths**: Only platform with first-party PydanticAI support. Traces the entire stack (not just LLM layer), so you can debug whether a problem is in the AI or the backend. Native pydantic-evals integration. Very generous free tier (10M spans).

**Key limitation**: Tightly coupled to Pydantic ecosystem. Younger platform with smaller community. Cloud-only for most users. Less mature eval features compared to dedicated eval platforms.

**PydanticAI integration**: **Best-in-class**. First-party, one-line setup. This is THE observability tool designed for PydanticAI.

---

## 5. Pydantic Evals (pydantic-evals)

**What it is**: Standalone Python library for evaluating non-deterministic functions. Code-first, Pythonic, designed for agent evaluation. Part of the pydantic-ai monorepo but independent package.

**Maturity**: Medium. In **beta** as of v1.70.0 (March 2026). API may change. Span attributes for Logfire integration still iterating.

| Dimension | Details |
|---|---|
| **Core model** | Define `Dataset` of `Case` objects. Each case has inputs, optional expected outputs, metadata, and evaluators. Run `dataset.evaluate_sync(task_fn)` to get an evaluation report. |
| **Evaluator types** | **Code-based**: regex, type validation, exact match, PII detection. **LLM-as-judge**: accuracy, hallucination, instruction-following. **Span-based**: analyze OTel traces to evaluate HOW the answer was reached (tool calls made, steps taken). |
| **Dataset mgmt** | YAML or JSON serialization. Version-control in repo. Load/save programmatically. |
| **Task definition** | Any async Python function. Not limited to LLM calls — can evaluate tools, pipelines, full agent workflows. |
| **Concurrency** | Concurrent execution with retry strategies built in |
| **Metrics** | Quality, performance, cost, reliability metrics out of the box |
| **Logfire integration** | Optional. `pip install 'pydantic-evals[logfire]'`. Results auto-appear in Logfire UI. |
| **Pricing** | Free, open-source |

**Unique strengths**: Span-based evaluation is a killer feature for agents — evaluate not just what the agent returned but HOW it got there (which tools it called, in what order, whether it retried correctly). Pure Python, Pythonic API. Works with any async function, not just PydanticAI agents.

**Key limitation**: Beta status means API instability risk. No web UI on its own (needs Logfire). Less mature than DeepEval for metric coverage. Small community so far.

**PydanticAI integration**: **Native**. Designed to work with PydanticAI agents. Span-based evaluators hook into PydanticAI's OTel instrumentation.

---

## 6. Arize Phoenix

**What it is**: Open-source AI observability and evaluation platform. Originally built for ML engineers, now focused on LLM tracing. Backed by Arize AI.

**Maturity**: High. Active development, strong community, broad framework support. 10k+ GitHub stars.

| Dimension | Details |
|---|---|
| **Core model** | Ingest traces, run experiments, evaluate with LLM-judge or code. Prompt management and playground. |
| **Tracing** | Built on OpenTelemetry. Captures model calls, retrieval, tool use, custom logic. Multi-step agent traces. |
| **Evals** | LLM-based evaluators for relevance, toxicity, hallucination, accuracy. Code-based checks. Human labels. Online evals on production traffic. |
| **Agent support** | Complete multi-step agent traces. Decision-path analysis. Behavioral drift detection. |
| **Experiments** | Track prompt/model/retrieval changes. Compare across experiments. |
| **Unique** | Bias detection, behavioral drift monitoring. Stronger on ML-ops heritage features. |
| **Self-hosted** | Fully open-source (Apache-2.0 + BSD-3). Docker/K8s deployment. Runs locally, in Jupyter, or in cloud. |
| **Pricing** | **Open-source**: Free, unlimited. **AX Free (cloud)**: 25K spans/mo, 7d retention. **AX Pro**: $50/mo (50K spans, 15d). **AX Enterprise**: Custom (SOC2, HIPAA, self-hosted support). |
| **Framework support** | OpenAI, Anthropic, Google, LangGraph, CrewAI, LlamaIndex, DSPy, Vercel AI SDK, and PydanticAI |

**Unique strengths**: Strongest open-source self-hosted option with full feature parity. ML-ops heritage brings drift detection and bias analysis. Deepest framework support list.

**Key limitation**: Higher integration overhead than lightweight alternatives. Prompt versioning less clean than dedicated tools. More ML-ops oriented, less "LLM-native" than Langfuse.

**PydanticAI integration**: **Has one.** `openinference-instrumentation-pydantic-ai` auto-instrumentation library produces OTel-compatible traces.

---

## 7. Weights & Biases Weave

**What it is**: Observability + eval toolkit for AI applications from W&B. Extends their ML experiment tracking heritage to LLM/agent workflows.

**Maturity**: Medium-High. Backed by W&B's established platform and enterprise customer base. Open-source components on GitHub.

| Dimension | Details |
|---|---|
| **Core model** | Auto-log all inputs, outputs, code, metadata. Organize as traces. Run evaluations across dimensions (accuracy, latency, cost, UX). |
| **Tracing** | Automatic granular logging. Visualize traces of LLM calls and agent workflows. Development + production monitoring. |
| **Evals** | Evaluation framework with scoring tools. Multi-dimensional scoring. Version-linked (score tied to exact prompt/model/dataset version). |
| **Agent support** | Full agent workflow tracing. Multi-step execution tracking. |
| **Self-hosted** | Yes. Self-managed deployment using Altinity ClickHouse Operator. Enterprise-grade. |
| **Pricing** | Usage-based. Enterprise typically $315-400/seat/month. Free tier exists but limited. |
| **Integration** | Broad — supports major frameworks. Strong Bedrock/AWS integration. |

**Unique strengths**: If you already use W&B for ML experiment tracking, Weave is a natural extension. Strong traceability — links eval scores to exact versions. Enterprise-grade self-hosting.

**Key limitation**: Expensive. Enterprise-oriented pricing. Overkill if you don't need the broader W&B platform. Less LLM-native than newer tools.

**PydanticAI integration**: No native integration. Generic Python tracing would work.

---

## 8. OpenTelemetry GenAI Semantic Conventions

**What it is**: Emerging standard for how LLM/agent traces should be structured. The `gen_ai.*` namespace standardizes span attributes across all tools.

**Maturity**: **Development** status (experimental). Core attributes are stable enough to build on. Agent spans spec is newest.

### Key Specifications

| Spec | Status | Covers |
|---|---|---|
| `gen_ai.` client spans | Experimental | Model calls: system, model, tokens, temperature |
| `gen_ai.` events | Experimental | Input/output messages, tool definitions |
| `gen_ai.` metrics | Experimental | Token usage, latency, cost |
| `gen_ai.` agent spans | Development | `create_agent`, `invoke_agent`, `execute_tool` operations |

### Span Naming Convention

```
{operation} {name}
```
Examples: `chat gpt-4o`, `invoke_agent research_agent`, `execute_tool web_search`

### Key Attributes

- `gen_ai.system` — provider name (openai, anthropic, etc.)
- `gen_ai.request.model` — model identifier
- `gen_ai.usage.input_tokens` / `output_tokens` — token counts
- `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.version` — agent identity
- `gen_ai.input.messages`, `gen_ai.output.messages` — opt-in, potentially sensitive

### Why It Matters

Before this, every tool used incompatible custom trace formats. Now, traces from Logfire can flow to Langfuse, Phoenix, Datadog, or Jaeger without re-instrumentation. **This is the interoperability layer.** Adopt OTel-native tools and you avoid vendor lock-in.

### Who Supports It

| Tool | OTel Support |
|---|---|
| **Logfire** | Native. Built entirely on OTel. |
| **Langfuse** | OTel-compliant. Accepts OTel traces. |
| **Arize Phoenix** | Built on OTel. |
| **Braintrust** | Custom SDK, OTel export possible |
| **W&B Weave** | Custom SDK primarily |
| **Promptfoo** | Not applicable (eval framework, not observability) |

---

## Head-to-Head Comparison

### Feature Matrix

| Feature | Promptfoo | Braintrust | Langfuse | Logfire | pydantic-evals | Phoenix | Weave |
|---|---|---|---|---|---|---|---|
| **Open Source** | MIT | No | MIT | No | MIT | Apache-2.0 | Partial |
| **Self-hosted** | Local-only | Enterprise | Docker/K8s | Enterprise | Local | Docker/K8s | Enterprise |
| **Pre-deploy eval** | Excellent | Good | Basic | Via p-evals | Excellent | Good | Good |
| **Production tracing** | No | Excellent | Excellent | Excellent | No | Excellent | Excellent |
| **LLM-as-judge** | Yes | Yes | Yes | Via p-evals | Yes | Yes | Yes |
| **CI/CD gates** | Excellent | Good | Basic | No | Scriptable | Basic | Basic |
| **Agent tracing** | Basic | Good | Good | Excellent* | Span-based | Good | Good |
| **Dataset mgmt** | YAML files | Web UI | Web UI | Via p-evals | YAML files | Web UI | Web UI |
| **Red teaming** | Best-in-class | No | No | No | No | No | No |
| **PydanticAI native** | No | No | No | **Yes** | **Yes** | Yes (OpenInf) | No |
| **OTel native** | N/A | No | Yes | **Yes** | Yes | **Yes** | No |
| **Free tier** | Unlimited | 10K scores | 50K units | **10M spans** | Unlimited | 25K spans | Limited |

*Logfire agent tracing is excellent specifically for PydanticAI agents.

### Pricing Comparison (Monthly)

| Tier | Braintrust | Langfuse | Logfire | Phoenix (Cloud) | Weave |
|---|---|---|---|---|---|
| **Free** | 1M spans, 10K scores | 50K units, 2 users | 10M spans, 1 seat | 25K spans | Limited |
| **Mid** | $249 (unlimited) | $29-199 | $49-249 | $50 | Usage-based |
| **Enterprise** | Custom | Custom + self-host | Custom + self-host | Custom + self-host | $315-400/seat |

---

## Recommendation for a PydanticAI + pydantic-graph Stack

### Recommended Stack

```
Pre-deploy eval:     pydantic-evals  (native PydanticAI, span-based agent eval)
                     + Promptfoo     (red-teaming, security testing, CI gates)

Observability:       Logfire         (first-party PydanticAI, full-stack tracing)

Production evals:    Logfire + pydantic-evals  (experiment results in Logfire UI)

Backup/complement:   Langfuse        (if you need self-hosted, or want broader
                                      ecosystem tooling alongside Logfire)
```

### Rationale

1. **Logfire is the obvious choice for PydanticAI observability.** One-line setup, traces agent loops including tool calls with args/response/latency, multi-turn conversations, and the entire backend stack. No other tool has this depth for PydanticAI specifically.

2. **pydantic-evals is the natural eval companion.** Span-based evaluation (assert on HOW the agent behaved, not just WHAT it returned) is critical for graph-based agent systems where execution path matters. Results flow into Logfire automatically.

3. **Promptfoo fills the security gap.** Neither Logfire nor pydantic-evals do red-teaming. Promptfoo's 67+ attack plugins and CI/CD quality gates complement the Pydantic stack for pre-deploy security testing.

4. **Langfuse is the hedge.** If Logfire's cloud-only limitation becomes a problem (data sovereignty, cost at scale), Langfuse is the strongest self-hosted alternative. It accepts OTel traces, so you could use Logfire as instrumentation layer and Langfuse as the observability backend.

### Architecture for pydantic-graph agents

```
pydantic-graph agent
    |
    |-- logfire.instrument_pydantic_ai()  --> Logfire (traces)
    |                                          |
    |                                          +--> OTel export to Langfuse (optional)
    |
    |-- pydantic-evals Dataset
    |       |-- Code evaluators (output format, correctness)
    |       |-- LLM-as-judge evaluators (quality, helpfulness)
    |       |-- Span-based evaluators (tool call sequence, graph path)
    |       |
    |       +--> Results --> Logfire UI
    |
    |-- promptfoo (CI/CD)
            |-- Red team scans on prompt changes
            |-- Quality gates (min score thresholds)
            |-- Regression testing on eval dataset
```

### Risks and Considerations

- **pydantic-evals is beta.** API may change. Have a migration plan. The core concepts (Dataset, Case, Evaluator) are stable, but span attribute names may shift.
- **Logfire is cloud-only for most users.** If you need air-gapped or on-prem, Langfuse or Phoenix are better choices.
- **OTel GenAI agent spans are still "Development" status.** The convention will evolve. Building on Logfire insulates you since Pydantic tracks the spec closely.
- **No single tool covers everything.** The 3-tool stack (Logfire + pydantic-evals + Promptfoo) is the minimum for comprehensive coverage of a production agent system.

---

## Resources

- [Promptfoo Docs](https://www.promptfoo.dev/docs/intro/)
- [Braintrust Platform](https://www.braintrust.dev/)
- [Langfuse Docs](https://langfuse.com/docs/observability/overview)
- [Logfire AI Observability](https://logfire.pydantic.dev/docs/ai-observability/)
- [Pydantic Evals Guide](https://ai.pydantic.dev/evals/)
- [Arize Phoenix Docs](https://arize.com/docs/phoenix)
- [W&B Weave Docs](https://docs.wandb.ai/weave)
- [OTel GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [OTel GenAI Agent Spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
