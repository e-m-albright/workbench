# Open-model inference

Canonical comparison of open-weight model families, local runtimes, routing layers,
managed inference hosts, and serverless GPU platforms. This page owns the current
ranking and provider taxonomy. Host-specific measurements and setup details remain
in the [local Apple Silicon runbook](https://github.com/e-m-albright/dotfiles/blob/main/docs/local-llm-stack.md).

**Snapshot:** 2026-08-29. Model availability, throughput, and prices move quickly;
re-check the linked primary source before spending money or changing a default.

## Current decision

The useful architecture is a barbell:

1. Run private and ordinary work locally through **oMLX** on Apple Silicon.
2. Send coding and genuinely difficult non-sensitive work to the existing frontier
   provider.
3. Use an isolated, sanitized subtask when private work needs frontier research.
4. Add a paid open-model host only when a model is too large for the laptop or
   sustained automation makes local throughput insufficient.

The local acceptance floor is **30 generated tokens per second**. The target is
50-80; 100+ is valuable only when the model remains capable enough to complete the
work without recovery turns.

## Local model ranking: M4 Pro, 48 GB

These are candidates that fit, or plausibly fit, the machine's roughly 37-40 GB
practical Metal working-set ceiling. Throughput is not a quality score.

| Rank | Model | Base release | Tested MLX build | Local generation speed | Artificial Analysis intelligence | Current take |
|---|---|---|---|---:|---:|---|
| 1 | [Qwen3.6-35B-A3B oQ4e + MTP](https://huggingface.co/Jundot/Qwen3.6-35B-A3B-oQ4e-mtp) | 2026-04-15 | 2026-07-02 | 76.8 at 4K; 80.3 at 16K; 50.7 at 64K | 32 reasoning; 25 non-reasoning | Best demonstrated speed and agent quality. Active trial. |
| 2 | [Gemma 4 26B-A4B](https://huggingface.co/lmstudio-community/gemma-4-26B-A4B-it-QAT-MLX-4bit) | 2026-04-02 | 2026-06-04 | 57.5 at 4K; 50.5 at 16K; 33.9 at 64K | 26 reasoning; 20 non-reasoning | **Rejected as the local default.** Slower than Qwen with no observed quality advantage; weights removed after the A/B. |
| 3 | [GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) | 2026-01-19 | Current 4-bit build tested 2026-08 | 62.0 at 1K; 51.2 at 4K; 33.4 at 16K | Not on the current Artificial Analysis board | The likely model meant by “ZLM”: **GLM**, from Z.ai. It clears the speed floor but is older than the preferred five-month window. |
| 4 | [Gemma 4 E4B](https://huggingface.co/Grunzig/gemma-4-E4B-it-qat-oQ4e-fp16-mtp) | 2026-04-02 | 2026-08-20 | Up to 87 | 12 reasoning; 9 non-reasoning | Attractive quick model, but its intelligence score is far below Qwen and Gemma 26B. |
| 5 | [Gemma 4 E2B](https://huggingface.co/mlx-community/gemma-4-e2b-it-4bit) | 2026-04-02 | 2026-04-02 | Up to 107.6 | 10 reasoning; 6 non-reasoning | Clears 100 tokens per second, but is classifier/extraction grade rather than a primary agent. |
| 6 | [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | 2026-08-05 | Current 4-bit build tested 2026-08 | About 19 | 52 xhigh; 44 medium; 35 non-reasoning | Highest-intelligence small open-weight model in Artificial Analysis, but its dense architecture violates the local 30 tok/s floor. Use hosted inference if its quality is needed. |

Local figures come from the [oMLX performance explorer](https://omlx.ai/benchmarks/performance)
on an M4 Pro with 20 GPU cores and 48 GB. Artificial Analysis figures are its
current hosted-model [open-weight leaderboard](https://artificialanalysis.ai/leaderboards/models?weights=open),
not measurements of this Mac. The two sources answer different questions: local
runtime speed versus broad model intelligence and hosted economics. Reproduce the
local numbers before adopting a default.

A direct local A/B on 2026-08-29 generated 512 tokens from a short prompt at
71.4 tokens per second for Qwen and 64.8 for Gemma after warm-up. Both solved a
small coding task, dependency-scheduling problem, and tool call correctly; Qwen
followed the JSON-only instruction more precisely, while Gemma's code was more
concise. Gemma showed no compensating advantage, so Qwen remains the default and
Gemma's local weights were removed.

A supervised operational evaluation on 2026-08-29 found Qwen reliable at bounded
meeting extraction and tool-call formation. Calendar conflict detection was
accurate once event intervals were serialized unambiguously. Inbox prioritization
improved materially when given relevant personal context, but still added
speculative rationale and over-alerted on a recognized sign-in flow. The result is
**approved for supervised private assistance, not autonomous operational writes**.

### Why Qwen3.8 does not replace Qwen3.6 locally

Artificial Analysis's `xhigh` label is a reasoning-effort setting used to measure
quality. It usually increases the number of reasoning tokens and therefore total
response time, but it is not the cause of Qwen3.8-27B's low token-generation rate.
The model is dense and must stream all 27B parameters through memory for each
decode step; the M4 Pro is memory-bandwidth-bound.

Matching-hardware oMLX results show the optimization ceiling more clearly:

- A conventional 4-bit build produced 14.3 tok/s on an M4 Pro 48 GB.
- An oQ4e build with native multi-token prediction produced 25.9 tok/s. This is a
  large improvement, but still below the 30 tok/s floor and far below the 50 tok/s
  interactive target.
- An experimental oMLX 0.6.3 release-candidate recipe with Neural Engine prefill
  and native multi-token prediction reached 53 tok/s for prose and 72 tok/s for
  code on an M4 Max. That machine has roughly twice the memory bandwidth; the
  result does not transfer to an M4 Pro.

Lower-bit quantization could improve throughput further, at a quality cost, but no
current result supports a reliable 50 tok/s for general prose on this hardware.
Qwen3.7 Plus and Max are hosted products without a suitable open local checkpoint.
Qwen3.8 Flash-Next is open weight but roughly 180B total parameters, so even a
2-bit checkpoint consumes about 45 GB before runtime overhead. The generation
number is not the selection criterion: no Qwen3.7 or Qwen3.8 shape currently fits
both the memory envelope and the 50 tok/s Pi target.

Qwen3.6 itself delivers roughly 63-71 tok/s for warm short-context oMLX requests.
A real Pi session with about 25K tokens of accumulated context displayed about
38 tok/s end to end while oMLX decode remained near 60 tok/s. The gap includes
prompt processing, time to first token, the full tool schema, and Pi's accounting.
The next performance work should therefore benchmark fresh, 8K, 16K, and 25K Pi
sessions; verify prefix-cache reuse; compare a narrower private tool set; and tune
multi-token-prediction depth. Revisit the model only when a challenger clears 50
tok/s in the Pi harness, not merely in a short raw-server benchmark.

### Next local challengers

| Model | Creator | Why it matters | Gate before download |
|---|---|---|---|
| Muse Glimmer 30B | Meta | Artificial Analysis small-model leader on openness, with intelligence 35 | Matching M4 Pro MLX evidence above 30 tok/s; 30B dense models usually miss the floor. |
| G9v3-39A5B | AI9Stars | Intelligence 34 with only 5B active parameters | First-party model card, viable MLX conversion, tool support, and matching-hardware throughput. |
| Ling 3.0 Tiny | InclusionAI | Intelligence 25 with 1.3B active parameters and strong hosted speed | MLX availability and evidence that its lower capability still completes real operational work. |
| Nemotron 3.5 Lightning | NVIDIA | Intelligence 24 with 3.6B active parameters and 1M context | Downloadable weights, MLX support, and quality sufficient to displace Qwen rather than merely run faster. |

### Models that do not fit the local decision

- **Qwen3.8-Max:** the August 2026 flagship is much more capable but is a
  multi-trillion-parameter model. Open weights do not make it laptop-sized.
- **DeepSeek V4 Pro / Flash:** the official models are far too large. Small
  Qwen-based distills either fall below 30 tokens per second or no longer
  represent the full model's capability.
- **Kimi K2.6 / K3:** the official Moonshot models are far too large for 48 GB.
  Small “Kimi” models found locally are third-party distillations, not compressed
  copies of the complete model.
- **MiniMax frontier MoEs:** useful through hosted inference, not a laptop target.
- **Dense 27B-32B models:** they often fit at 4-bit but are memory-bandwidth-bound
  around 10-25 tokens per second on this hardware.

### Server-class open-model signals

GLM-5.2 and Nemotron 3 Ultra strengthen the hosted or self-managed side of the barbell without changing the laptop decision. GLM-5.2 is a 753-billion-parameter mixture-of-experts model with a one-million-token context window and MIT-licensed weights; Artificial Analysis placed it at the top of its open-weight intelligence index in June 2026, but it used substantially more output tokens than peers. Nemotron 3 Ultra is roughly 550 billion total parameters with 55 billion active per token. CodeRabbit found review quality near its baseline and competitive latency, but frequent retries for malformed or incomplete structured output. The reusable lesson is to measure time and cost to a validated completion, including retries, rather than compare one-shot intelligence or token speed alone. Neither model is a local M4 Pro candidate.

Sources: [Simon Willison on GLM-5.2](https://simonwillison.net/2026/Jun/17/glm-52/) and [CodeRabbit on Nemotron 3 Ultra](https://www.coderabbit.ai/blog/nemotron-3-ultra-release).

## Open-weight model families

“Open weight” means downloadable weights. It does not by itself mean an
Open Source Initiative-approved license, disclosed training data, reproducible
training, or unrestricted commercial use. Verify every release rather than
inheriting a lab-level label.

Artificial Analysis's [open-model catalogue](https://artificialanalysis.ai/models/open-source)
is the completeness baseline. The registry below includes every creator on that
catalogue as of 2026-08-29, plus historically important open research programs
that its current benchmark does not list. Hugging Face's
[Summer 2026 open-model census](https://huggingface.co/blog/state-of-open-models-summer-2026)
is the second omission check.

### What the Openness Index means

The [Artificial Analysis Openness Index](https://artificialanalysis.ai/methodology/openness-index)
scores six components from 0 to 3, then normalizes the 18-point total to 100:
weight access and license; pre- and post-training data access and license; and
methodology disclosure and code/license availability. A downloadable model can
therefore be “open weight” while scoring poorly because its data, training code,
or commercial rights remain closed.

On the intelligence-versus-openness chart, the “most attractive quadrant” means
high scores on both displayed axes. The Pareto line contains models for which no
other plotted model is at least as open and intelligent while being strictly
better on one dimension. Neither concept accounts for local memory, Apple Silicon
throughput, tool reliability, or task fit.

### Complete current creator registry

| Creator | Families represented | Tracking posture |
|---|---|---|
| AI21 Labs | Jamba | Hybrid architecture; hosted and research watch. |
| AI9Stars | G9 | **Local watch:** G9v3-39A5B has 5B active parameters and competitive small-model intelligence. |
| Alibaba | Qwen | **Local default and frontier watch.** |
| Allen Institute for AI | OLMo, Tulu | Openness and reproducibility reference. |
| Arcee AI | Trinity and derivatives | Specialist lab; verify each base model and license. |
| Baidu | ERNIE | Major Chinese open-weight and API program. |
| ByteDance Seed | Seed, Seed-OSS | General, coding, and multimodal watch. |
| Cohere | Command, Aya, North | Enterprise, multilingual, retrieval, and coding models. |
| Databricks | DBRX | Historical enterprise MoE reference. |
| Deep Cogito | Cogito | Reasoning derivatives; provenance matters. |
| DeepSeek | V, R, and distills | Frontier hosted family; full weights exceed the laptop. |
| Google | Gemma | Major open-weight family; Gemma 4 26B lost the local A/B. |
| IBM | Granite | Permissive enterprise and code models. |
| InclusionAI | Ling | **Local watch:** efficient MoEs including Ling 3.0 Tiny. |
| Kimi / Moonshot AI | Kimi | Frontier hosted MoEs and long context. |
| LG AI Research | EXAONE, K-EXAONE | Bilingual and reasoning models with local-size releases. |
| Liquid AI | LFM | Efficient alternative architectures and edge models. |
| LongCat | LongCat | Large MoE program; hosted/server watch. |
| MBZUAI Institute of Foundation Models | K2 Think | Open reasoning research and regional foundation models. |
| Meta | Llama, Muse | Major ecosystem; Muse Glimmer currently leads the small chart on openness. |
| Microsoft | Phi | Small and edge-oriented models. |
| MiniMax | MiniMax M | Frontier hosted MoEs. |
| Mistral | Mistral, Mixtral, Devstral, Codestral, Ministral | European general, coding, and efficient-model program. |
| Motif Technologies | Motif | Motif 3 frontier-scale open-weight model. |
| Multiverse Computing | HyperNova | Compressed and efficient model program. |
| NVIDIA | Nemotron | **Local watch** at Nano/Lightning sizes; frontier models remain server-class. |
| Nanbeige | Nanbeige | Small and general Chinese open-weight models. |
| Naver | HyperCLOVA X SEED | Korean-language and regional foundation models. |
| Nex AGI | Nex | Agent-oriented frontier models. |
| Nous Research | Hermes | Tool-use and agent fine-tunes; evaluate the upstream base separately. |
| OpenAI | gpt-oss | Open-weight releases are distinct from its proprietary frontier line. |
| OpenBMB | MiniCPM | Edge and multimodal models, including MiniCPM5-1B. |
| OpenChat | OpenChat | Historically influential conversation fine-tunes. |
| Perplexity | R1 1776 and derivatives | Search-company model derivatives; verify base provenance. |
| Prime Intellect | INTELLECT | Open and distributed training experiments. |
| Reka AI | Reka | Small multimodal and general models. |
| SK Telecom | A.X | Korean-language foundation models. |
| Sapiens AI | Agnes | Frontier-scale open-weight program. |
| Sarvam | Sarvam | Indian-language and efficient MoE models. |
| ServiceNow | Apriel | Enterprise reasoning and workflow models. |
| Snowflake | Arctic | Enterprise open models and embeddings. |
| SpaceXAI / xAI | Grok | Open releases lag the proprietary production line. |
| StepFun | Step | Large multimodal and reasoning models. |
| Swiss AI Initiative | Apertus | Public-interest multilingual open foundation models. |
| TII UAE | Falcon | Historically important permissive family. |
| Tencent | Hunyuan, Hy | Full-spectrum Chinese foundation-model portfolio. |
| Thinking Machines | Inkling | Frontier-scale open-weight research model. |
| Trillion Labs | Tri | Small reasoning models. |
| Upstage | Solar | Korean-language and enterprise models. |
| Xiaomi | MiMo | Frontier reasoning and agent models. |
| Z AI | GLM | Agentic, coding, and long-context family; Flash is locally plausible. |

### Additional open research programs

| Creator | Families | Why retained |
|---|---|---|
| 01.AI | Yi | Influential earlier Chinese open-weight family. |
| Baichuan | Baichuan | Important earlier Chinese family. |
| BigScience | BLOOM | Landmark community-trained multilingual program. |
| EleutherAI | GPT-NeoX, Pythia | Foundational open training and evaluation artifacts. |
| Hugging Face | SmolLM, SmolVLM | Small-model and edge baseline from the central model hub. |
| Shanghai AI Laboratory | InternLM | Long-running general and multimodal open-model program. |
| Stability AI | StableLM | Historically notable open family with lower current momentum. |

## The inference stack

The layers solve different problems and should not be ranked as if they were
substitutes.

```text
model weights
    ↓
local runtime or managed inference host
    ↓
optional router / API gateway
    ↓
agent harness or application
```

### Local and self-hosted runtimes

| Runtime | Role | Current take |
|---|---|---|
| [oMLX](https://github.com/jundot/omlx) | Open-source, MLX-native multi-model server for Apple Silicon | **Active local default.** Prefix caching, model swapping, OpenAI and Anthropic APIs, tool parsing, and current Mac benchmarks. |
| [LM Studio](https://lmstudio.ai/) | Polished local app and headless server using MLX or llama.cpp | **Fallback.** Easiest model browser; closed-source application and less aligned with the current multi-model routing experiment. |
| [Ollama](https://ollama.com/) | Portable model manager and local API | **Broad compatibility fallback.** Convenient, but previous Apple Silicon measurements trailed native MLX. It is a runtime, not a model router. |
| [mlx-lm](https://github.com/ml-explore/mlx-lm) | Apple's reference MLX language-model library | **Foundation and experiment layer.** Prefer oMLX when lifecycle, APIs, caching, and model management matter. |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Portable GGUF runtime and benchmark baseline | **Compatibility and measurement tool.** Useful across hardware; MLX currently wins generation throughput on this Mac. |
| [vLLM](https://github.com/vllm-project/vllm) | High-throughput CUDA production serving | **Cloud/server default.** Not the native Apple Silicon choice. |
| [SGLang](https://github.com/sgl-project/sglang) | High-performance structured generation and serving | **Production alternative to vLLM.** Relevant when deploying dedicated GPU infrastructure. |

### Routers and API gateways

Cloudflare spans two layers. **Cloudflare AI Gateway** is a gateway/router for
requests sent to model providers; **Workers AI** is Cloudflare's managed inference
product and runs supported models on Cloudflare infrastructure. Saying simply
“Cloudflare is a router” collapses two different products.

| Provider | Owns model GPUs? | Current take |
|---|---:|---|
| [OpenRouter](https://openrouter.ai/) | Mostly no | **Pragmatic hosted-model aggregator.** One API, model/provider failover, and routing controls; another party still sees the traffic. |
| [LiteLLM](https://github.com/BerriAI/litellm) | No | **Self-hosted gateway reference.** Broad provider normalization, budgets, fallback, and routing; too much infrastructure for the current personal stack. |
| [Vercel AI Gateway](https://vercel.com/ai-gateway) | No | Strong application gateway when already using Vercel; no reason to add it solely for Pi. |
| [Portkey](https://portkey.ai/) | No | Mature gateway and observability control plane; organization-oriented rather than needed locally. |
| [Cloudflare AI Gateway](https://developers.cloudflare.com/ai-gateway/) | No, for the gateway product | Observability, caching, retries, fallback, and provider routing; attractive when the application already lives on Cloudflare. |
| Workbench Pi router | No | **Active policy layer.** Explicit frontier/private/auto modes with a local classifier and sticky privacy boundary. |

Plain `pi` remains the explicit frontier path. Workbench deploys only the two
privacy shorthands:

```bash
piv  # explicit private/local
pia  # automatic, conservative routing
```

Auto classifies each user input until any input routes private. That transition is
one-way for the session: later inputs remain local unless the user explicitly
overrides the boundary. Connector data stays conservative in auto because its
sensitivity cannot be known before retrieval. Calendar, Granola, or selected Gmail
work may use plain `pi` in a fresh session when the user deliberately values
frontier intelligence over local handling.

Provider routing chooses where to run the same model. Model routing chooses which
model should answer. The first is operationally mature; the second must be judged
on completed work, recovery turns, latency, and privacy, not selected-call price.

### Managed open-model inference hosts

These vendors expose model APIs and operate the accelerated infrastructure.

| Provider | Best reason to use it | Current take |
|---|---|---|
| [Together AI](https://www.together.ai/) | Broad open-model catalogue and serious serving infrastructure | Strong direct default when catalogue breadth matters. |
| [Fireworks AI](https://fireworks.ai/) | Fast serverless paths and strong inference engineering | Strong latency-oriented direct host. |
| [DeepInfra](https://deepinfra.com/) | Low token prices | Cost-floor option for non-critical batch workloads. |
| [Baseten](https://www.baseten.co/) | Production deployment, optimization, and dedicated endpoints | Best when owning a customized deployment matters more than catalogue shopping. |
| [Groq](https://groq.com/) | Very high generation speed on supported models | Specialized silicon; availability and model coverage decide fit. |
| [Cerebras](https://www.cerebras.ai/inference) | Extremely high throughput and coding-oriented plans | Compelling for supported models when raw speed is the requirement. |
| [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/) | Edge-adjacent, OpenAI-compatible serverless inference | Good for bursty personal workloads: 10,000 neurons/day free, then model-specific token pricing at $0.011/1,000 neurons on the $5/month Workers Paid plan (as of 2026-08). Its catalogue does not currently include Qwen3.6, so it is not a drop-in hosted mirror of the local tier. |
| Model owner APIs | Lowest-friction first-party access | DeepSeek, Moonshot, Z.ai, Mistral, and others are often cheapest or earliest at the source; privacy and jurisdiction still matter. |

Use [Artificial Analysis](https://artificialanalysis.ai/) for current cross-host
latency, throughput, quality, and price comparisons instead of preserving a price
table that will rot.

### Serverless GPU and bring-your-own-model platforms

These rent execution rather than merely exposing a fixed model catalogue.

| Platform | Best fit | Current take |
|---|---|---|
| [Modal](https://modal.com/) | Python-native functions, custom inference code, scale-to-zero jobs | **Default custom serverless GPU platform.** Best developer experience for code-owned workloads. |
| [Runpod](https://www.runpod.io/) | Serverless workers plus inexpensive dedicated pods | **Cost/control alternative.** More infrastructure responsibility than Modal. |
| [Replicate](https://replicate.com/) | Packaging and publishing prebuilt model APIs | **Fastest path to a public model endpoint.** Less control and usually not the cost floor. |
| [Baseten](https://www.baseten.co/) | Production model deployments with optimization and support | Choose for a durable service, not a casual experiment. |
| [Together dedicated endpoints](https://www.together.ai/dedicated-endpoints) | Dedicated copies of supported open models | Choose when moving from shared token pricing to predictable sustained load. |
| [CoreWeave](https://www.coreweave.com/) | Large dedicated GPU infrastructure | Not truly a simple personal serverless path; relevant at sustained scale. |
| AWS, Google Cloud, Azure | Enterprise identity, compliance, and existing cloud commitments | Use only when an existing platform commitment outweighs complexity and cost. |

Billing model follows duty cycle:

- Use local inference for privacy and interactive single-user work.
- Use per-token managed inference for occasional access to large models.
- Use serverless GPU for custom code with bursty demand.
- Use dedicated endpoints or GPU instances only after sustained utilization makes
  idle capacity economical.

### Why no personal Modal or Runpod endpoint

The current decision is to defer a self-hosted cloud endpoint. Scale-to-zero keeps
occasional inference cheap, but a cold worker must start its container and load
model weights before answering; for large models, roughly 30-90 seconds is a
reasonable planning range even though caching can improve individual starts.
Keeping a worker warm removes that delay but turns a bursty personal workload into
continuous GPU rent.

At Modal's August 2026 rates, an L4 is about $0.80/hour, an A10 about $1.10/hour,
an L40S about $1.95/hour, and an A100 80 GB about $2.50/hour. Eight hours per day
therefore costs roughly $192, $264, $468, or $600 per month; continuous service is
about three times those figures. The larger GPUs needed for materially more
capable weights are the least economical. Runpod has the same duty-cycle shape:
flex workers scale to zero, while active workers trade a discount for continuous
billing.

A dedicated endpoint becomes worthwhile only when one of these changes: request
volume amortizes warm time, custom weights or inference code are unavailable from
a managed host, or a measured privacy/control requirement justifies the operating
cost. Until then, the barbell remains local oMLX plus frontier or managed
per-token APIs.

## Benchmark sources

No leaderboard answers the whole selection question. Track the benchmark, what it
actually measures, and whether the score belongs to the model, provider, runtime,
or model-plus-harness system.

| Source | Measures | Use | Main limitation |
|---|---|---|---|
| [oMLX Performance Explorer](https://omlx.ai/benchmarks/performance) | Prompt processing, generation speed, memory, context, and acceleration on specific Macs | **Primary local throughput evidence** | Community runs vary by quantization and settings; it does not establish model quality. |
| [Artificial Analysis open-weight leaderboard](https://artificialanalysis.ai/leaderboards/models?weights=open) and [size views](https://artificialanalysis.ai/models/open-source/small) ([all](https://artificialanalysis.ai/models/open-source), [tiny](https://artificialanalysis.ai/models/open-source/tiny), [medium](https://artificialanalysis.ai/models/open-source/medium), [large](https://artificialanalysis.ai/models/open-source/large)) | Composite intelligence, openness, parameters, hosted price, speed, latency, and Pareto discovery by size | **Primary cross-model, creator-discovery, and hosted-economics view** | Hosted performance is not local Mac performance; the composite index and Pareto chart omit task fit and local runtime behavior. |
| [Artificial Analysis provider leaderboard](https://artificialanalysis.ai/leaderboards/providers) | Provider latency, throughput, and price for the same models | Choose among hosts after choosing a model | Provider fleets and prices change quickly. |
| [Arena.ai](https://arena.ai/leaderboard) | Blind human preference across text, coding, vision, and other categories | Preference and interaction-quality signal | Popularity, style, and sampling mix affect Elo; weak for cost and deterministic task completion. |
| [SWE-bench Verified](https://www.swebench.com/) | Real repository issue resolution | Coding-model evidence | Scores are model-plus-harness and sensitive to scaffolding, tools, and compute budget. |
| [Terminal-Bench 2.0](https://www.tbench.ai/leaderboard/terminal-bench/2.0) | End-to-end terminal-agent tasks | Agent/harness effectiveness | Benchmark-tuned harnesses may not be good daily products. |
| [LiveCodeBench](https://livecodebench.github.io/) | Contamination-aware code generation over time | Fresh coding ability | Narrower than repository-level agent work. |
| [Aider leaderboards](https://aider.chat/docs/leaderboards/) | Code editing and edit-format performance | Editing reliability and local coder comparisons | Aider's harness and task mix do not directly reproduce Pi. |
| [Berkeley Function-Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) | Function and tool-call correctness | Tool schema and invocation quality | Does not test a complete multi-turn agent loop. |
| [Hugging Face Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard) | Standard open-model academic evaluations | Broad discovery and reproducibility | Static benchmark saturation and fine-tune overfitting reduce decision value. |
| [HELM](https://crfm.stanford.edu/helm/) | Reproducible multi-scenario evaluation | Research-grade coverage and transparency | Slower release cadence than the model market. |
| [OpenCompass](https://opencompass.org.cn/) | Broad multilingual model evaluation | Cross-check Chinese and multilingual releases | Configuration and benchmark selection still shape rankings. |

The canonical selection sequence is:

1. Use Artificial Analysis and Arena to discover credible model families.
2. Use coding, tool-calling, or domain benchmarks that match the intended work.
3. Use oMLX to reject candidates that miss the local memory or speed floor.
4. Run the final candidates through the same local Pi task suite and verifier.

## Evaluation protocol

Record these fields for every serious local candidate:

- Exact repository and weight revision
- License
- Release date and base model
- Quantization and on-disk size
- Total and active parameters
- Runtime and acceleration settings
- Prompt-processing and generation speed at 4K, 16K, and 64K
- Peak memory and time to first token
- Tool-call correctness across a multi-turn loop
- Structured-output validity
- A small coding task, a retrieval/summarization task, and a general reasoning task
- Recovery turns and verifier outcome, not just first-response preference

A/B tests should keep the harness, tools, prompt, context, and verifier constant.
The local default changes only when a challenger clears the 30-token-per-second
floor and wins enough completed tasks to justify its operational cost.

The current stack is ready for supervised daily use. Remaining acceptance work is
bounded rather than blocking: perform one physical network-disconnect run, measure
Pi throughput at representative context sizes, and continue reviewing operational
outputs before any unattended write or durable-memory path is enabled. Software-
offline inference and fail-closed provider failure have already passed.

## Sources

- [oMLX performance explorer](https://omlx.ai/benchmarks/performance)
- [Artificial Analysis open-model catalogue](https://artificialanalysis.ai/models/open-source)
- [Artificial Analysis small open-model view](https://artificialanalysis.ai/models/open-source/small)
- [Artificial Analysis Openness Index methodology](https://artificialanalysis.ai/methodology/openness-index)
- [Hugging Face Summer 2026 open-model census](https://huggingface.co/blog/state-of-open-models-summer-2026)
- [Qwen3.6 model card](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- [Qwen3.8-Max announcement](https://www.alibabacloud.com/blog/qwen3-8-max-a-new-bar-for-coding-and-cowork_603421)
- [Qwen3.8 standard M4 Pro benchmark](https://omlx.ai/benchmarks/performance/y1rd0cih)
- [Qwen3.8 MTP M4 Pro benchmark](https://omlx.ai/benchmarks/performance/g0n4lm5o)
- [Qwen3.8 experimental M4 Max optimization](https://github.com/Weschera/Qwen3.8-27B-oMLX-MTP-Mac)
- [Qwen3.8 Flash-Next model card](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)
- [Gemma 4 announcement](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/)
- [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- [DeepSeek V4 announcement](https://api-docs.deepseek.com/news/news260424)
- [Fireworks serverless pricing](https://docs.fireworks.ai/serverless/pricing)
- [OpenRouter pricing and routing](https://openrouter.ai/pricing)
- [Runpod serverless pricing](https://docs.runpod.io/serverless/pricing)
- [Modal pricing](https://modal.com/pricing)
