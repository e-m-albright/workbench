# Frontier coding model providers

Last reviewed: 2026-09-03

This document owns the current selection posture for frontier coding models used
through an independent agent harness. It compares model capability, subscription
portability, corporate jurisdiction, and treatment of sensitive prompts. General
harness ownership remains in [AI Tooling](ai-tools.md). Open-weight local
inference remains in [Open Model Inference](open-model-inference.md).

Prices, quotas, model names, and policies are volatile. Recheck primary sources
before purchasing or sending a new class of sensitive data.

## Current conclusion

OpenAI remains the primary provider. ChatGPT subscription access works directly
in Pi, and GPT-5.6 Sol has the strongest independently measured coding-agent
result among the reviewed non-Anthropic options.

A second model is still valuable for independent review, different failure modes,
and provider outages. No third provider currently clears both required bars:

1. demonstrated coding capability close enough to GPT-5.6 Sol for difficult
   implementation and review work
2. sufficiently clear data handling and corporate trust for repositories and
   prompts that may contain privileged personal or professional context

The best current options are therefore different depending on which bar matters:

- **Best subscription candidate to test:** Z.ai's $18 GLM Coding Plan. The
  anonymous Ox Alpha preview was GLM-5.3-Flash; the plan also includes the
  stronger full GLM-5.3 and officially supports Pi. Its benchmark case is still
  predominantly vendor-reported rather than independently reproduced.
- **Best other capability candidates:** Kimi K3 and Qwen3.8 Max. Both need a
  same-harness local evaluation. Direct consumer access does not yet clear the
  privacy bar.
- **Best privacy-compatible independent reviewer:** a paid Google Gemini API
  project. Paid Gemini API prompts and responses are not used to improve Google
  products. This is metered API access rather than subscription arbitrage, so it
  should be reserved for bounded reviews rather than used as an idle fallback.
- **Best US subscription alternative:** xAI is accessible in Pi, but Grok 4.6
  lacks enough independently reproduced coding-agent evidence and the consumer
  privacy policy permits broad improvement and research use of user content.

OpenCode Go is not part of the preferred path. It is primarily a reseller and
routing layer over API access to open or third-party models. The discount is real,
but it adds another party that receives prompts without improving the underlying
model. That trade is unattractive when capability and privileged-data handling,
not minimum cost, are the selection criteria.

Anthropic remains technically capable but is not part of the active selection.
Claude subscription use in Pi is billed as metered extra usage rather than drawn
from plan limits, and Anthropic is currently paused as a daily provider.

## Ranked shortlist for this workflow

This ranks practical fit for a Pi-based primary and independent reviewer. It is
not a claim that each adjacent model differs by a measurable amount.

1. **OpenAI GPT-5.6 Sol** - primary model; best combined capability, subscription
   portability, and established controls.
2. **Z.ai GLM-5.3** - best subscription-backed second-model canary; officially
   supports Pi, but independent benchmark reproduction and Coding Plan coverage
   under the API Data Processing Addendum still need confirmation.
3. **Google Gemini paid API** - best privacy-compatible independent reviewer;
   capable but not proven Sol-equivalent, and too expensive for unconstrained
   long-context loops.
4. **Kimi K3** - strongest alternative capability candidate after GLM; direct
   consumer policy permits training on prompts and files.
5. **Alibaba Qwen3.8 Max** - promising coding results, but weaker independent
   evidence and unresolved privileged-data terms.
6. **xAI Grok 4.6** - US subscription route in Pi, but incomplete coding evidence
   and broad consumer data-use terms.
7. **MiniMax M3** - capable lower-cost model, below the demonstrated frontier bar
   and still subject to direct-provider diligence.
8. **Cerebras-hosted GLM** - excellent speed, but currently sold out and serving
   an older GLM generation.
9. **Xiaomi MiMo V2.5 Pro** - exceptional economics without evidence of equivalent
   difficult-task capability.

**Excluded rather than ranked:** Anthropic is paused despite frontier capability.
Cursor Composer is not portable to Pi. OpenCode Go is a gateway rather than a
model and adds another processor without improving model capability.

## Capability evidence

Benchmarks measure a model and harness together. Scores from different harnesses,
benchmark versions, or vendor reports are not interchangeable.

| Model family | Current evidence | Confidence against GPT-5.6 Sol | Selection implication |
|---|---|---|---|
| **OpenAI GPT-5.6 Sol** | Artificial Analysis scores Sol at 80 on its Coding Agent Index and reports that it led DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA in the Codex harness at release. | Baseline | Primary model. |
| **Anthropic Claude Fable 5.1** | Artificial Analysis reports Fable 5.1 at 91.4% on Terminal-Bench v2.1. This is the strongest current evidence of a peer or superior family, but it is Anthropic. | High | Capability peer, intentionally paused. |
| **Kimi K3** | Moonshot reports 88.3 on Terminal-Bench v2.1 and 67.3 on DeepSWE. Its paper says it still trails the strongest proprietary models. Independent same-harness reproduction remains incomplete. | Medium | First non-US model to canary for review and implementation quality. |
| **Alibaba Qwen3.8 Max** | Published results place it near Sol on Terminal-Bench, but the strongest current numbers are vendor or partner reported and its results vary substantially across coding benchmarks. | Medium-low | Canary after Kimi; do not infer parity from one terminal benchmark. |
| **Google Gemini 3.8 Flash** | Artificial Analysis scores it at 59 on the general Intelligence Index, matching the earlier Sol score, but equivalent current coding-agent evidence is incomplete. | Medium-low | Strong independent-review candidate because privacy and organizational diversity compensate for uncertain coding parity. |
| **xAI Grok 4.6** | Independent general evaluations exist, but current coverage lacks a comparable Terminal-Bench or broad coding-agent result. | Low | Do not buy as the second coding model yet. |
| **Z.ai GLM-5.3** | Z.ai reports 66.9 on DeepSWE v1.1, 28.3 on Terminal-Bench 3.0, and strong long-horizon coding gains. Independent same-harness reproduction is still missing. Ox Alpha was the preview name for the smaller GLM-5.3-Flash, not a separate frontier company or model. | Medium-low | Best $18 subscription canary; promising second reviewer, not proven Sol-equivalent. |
| **MiniMax M3** | MiniMax reports 66.0 on Terminal-Bench v2.1 and 59.0 on SWE-Bench Pro. | Low | Useful lower tier, below this decision's capability bar. |
| **Xiaomi MiMo V2.5 Pro** | Subscription economics are exceptional, but evidence does not establish frontier-equivalent coding. | Low | Exclude from this decision despite price. |
| **Cerebras-hosted GLM** | Very high throughput, but the available Code plan advertises GLM 4.7 and is sold out. | Low | Speed option, not the current second frontier model. |

### What benchmark parity would not prove

A reviewer can add value without matching the primary model's aggregate score.
The useful question is whether it finds real defects the primary model misses
without flooding the review with false positives. Model-family diversity matters
more for this job than another OpenAI model with nearly identical training and
failure modes.

A second provider should therefore pass two separate canaries:

1. **Review canary:** blind review of representative diffs with known and unknown
   defects. Measure unique valid findings, false positives, and unnecessary
   rewrite pressure against GPT-5.6 Sol reviewing its own work.
2. **Implementation canary:** several bounded tasks requiring repository
   exploration, edits, and verification. Measure correctness and intervention,
   not prose quality or benchmark claims.

Do not test a provider on privileged repositories until its privacy route has
already passed review.

## Subscription portability into Pi

| Provider | Subscription economics | Pi access | Important boundary |
|---|---|---|---|
| **OpenAI Codex** | $20 Plus; $100 Pro 5x; $200 Pro 20x | Official ChatGPT OAuth through `openai-codex` | Individual Codex content may be used for training unless ChatGPT model-improvement training is disabled. OpenAI now says the ChatGPT control applies to Codex content; there is no separate Codex training page. |
| **Anthropic Claude** | Pro and Max plans | OAuth exists, but third-party use draws from paid extra usage | No subscription arbitrage in Pi. |
| **Kimi Code** | $19, $39, $99, and $199 plans | Subscription OAuth through `kimi-coding` | The consumer privacy policy permits training and optimization on user content. |
| **xAI SuperGrok** | $30 and $100 plans | Subscription OAuth through `xai` | API no-training terms do not automatically govern consumer subscription traffic. |
| **OpenCode Go** | $10 for up to $60 nominal monthly usage | API key through `opencode-go` | Coding-agent use is allowed; gateway contractual privacy remains insufficiently documented. |
| **Z.ai GLM Coding Plan** | Starts at $18 | Coding-plan key through `zai` | Strong economics; direct jurisdiction and policy risk remain. |
| **Alibaba Qwen Coding Plan** | $50 global | Plan key through `qwen-token-plan-individual` | Interactive coding only; no scripts or application backends. |
| **MiniMax Token Plan** | $22, $55, and $132 | Subscription key through `minimax` | Coding-tool support is explicit; direct policy review remains required. |
| **Xiaomi MiMo Token Plan** | $6, $16, $50, and $100 | Regional plan keys through `xiaomi-token-plan-*` | Interactive coding only; not a general API allowance. |
| **GitHub Copilot** | $10, $39, and $100 with explicit monthly credits | OAuth through `github-copilot` | Discounted credits rather than uncapped frontier inference. |
| **Cerebras Code** | $50 and $200 | API key through `cerebras` | Advertised as usable in any compatible agent; currently sold out. |
| **Google Gemini** | Consumer subscriptions exist | Subscription is not portable; paid API works through `google` | Use a billing-enabled API project for the stronger data terms. Never send sensitive data through the unpaid API tier. Cost makes it better for bounded reviews than daily overflow capacity. |
| **Cursor Composer 2.5** | Draws from Cursor plan usage or metered model rates | Cursor only; not available in Pi | Cursor describes it as its own model. No reviewed primary source says it is a Kimi copy or discloses Kimi as its base. |

## Corporate and privacy assessment

"Base" identifies the model lab or parent company, not necessarily the entity
that signs an international user's contract. A Singapore contracting entity does
not erase a China-based parent, engineering organization, or cross-border data
path.

| Provider | Company base and contracting context | Prompt treatment relevant to this use | Trust assessment for privileged context |
|---|---|---|---|
| **OpenAI** | United States; San Francisco | Individual ChatGPT and Codex content may train models unless the user opts out through ChatGPT Data Controls. OpenAI's current Codex help says that control applies to Codex, including Computer Use screenshots. API and business data are not used for training by default; ordinary API abuse logs can retain content for up to 30 days. | **Acceptable with the ChatGPT control verified.** Mature commercial controls, but consumer defaults require active configuration. |
| **Google** | United States; Mountain View | Paid Gemini API prompts and responses are not used to improve products and are covered by Google's processor terms. Limited safety logging remains. Unpaid API and AI Studio content may be human reviewed and used for training. | **Best second-provider privacy posture reviewed.** Use paid API only. |
| **Anthropic** | United States; San Francisco | Commercial API controls are mature, but plan portability is the blocking issue for Pi. | **Acceptable privacy, currently excluded for product reasons.** |
| **xAI / SpaceXAI** | United States | API requests are not trained on by default and are retained for 30 days unless zero data retention is enabled. Its consumer policy allows user content to be used to develop and improve services and train models, and explicitly asks users not to include personal information. | **Do not use subscription OAuth for privileged context without a clearer product-specific control.** Young operating history and broad consumer terms increase risk. |
| **Moonshot AI / Kimi** | Model lab based in Beijing; global service controlled by Novascent Private Limited | The August 2026 global privacy policy says prompts, files, and generated content may be used to train and optimize models. It also permits broad improvement, advertising, service-provider sharing, and international transfers. | **Fails the direct-subscription privacy bar.** A separately contracted zero-retention route may differ. |
| **Alibaba / Qwen** | Parent and model lab based in China; international cloud service uses an overseas contracting and hosting structure | The global coding plan is limited to interactive coding. The reviewed global plan page does not provide a sufficiently specific no-training commitment for sensitive source code. The China plan explicitly authorizes model-improvement use. | **High diligence requirement.** Do not send privileged context based only on a plan-specific API key. |
| **Zhipu AI / Z.ai** | Model lab based in Beijing; global service is controlled by Jingsheng Hengxing Technology Pte. Ltd. in Singapore and says API data is generally processed in Singapore | The published API Data Processing Addendum says Z.ai acts as processor, processes customer data only to provide and support the API, does not store prompt or generated content, and handles other data under deletion terms. The remaining ambiguity is whether an individual Coding Plan subscription is contractually treated as an API Service under that addendum. | **Promising with one contract check.** Use coding-only or sanitized material until Z.ai confirms the Coding Plan is covered by the API Data Processing Addendum. |
| **MiniMax** | Model lab based in Shanghai; international platform uses an overseas service entity | Token-plan documentation provides a subscription key but the reviewed product page does not establish a sufficiently strong privileged-data contract. | **High diligence requirement.** Do not infer API privacy from model availability. |
| **Xiaomi / MiMo** | Parent and model team based in Beijing | Token-plan documentation restricts use to coding tools but does not establish a sufficiently strong privileged-data commitment on the plan page. | **High diligence requirement.** Price does not offset the unresolved data boundary. |
| **Cerebras** | United States; Sunnyvale | US commercial inference provider with an API-key product intended for third-party tools. Product-specific retention and training terms still need confirmation before sensitive use. | **Promising route, unavailable and currently below the capability bar.** |
| **OpenCode Go** | Independent OpenCode service; the reviewed product documentation does not clearly establish the operating legal entity and jurisdiction | The product page claims no training and zero-day retention for Kimi, Qwen, GLM, MiniMax, and MiMo routes. It reports 30-day retention for Grok and OpenAI routes. The gateway itself still receives prompts, and no reviewed contractual privacy policy resolves that layer. | **Deprioritized.** It adds an intermediary to discounted API access without adding model capability. Avoid privileged material and Meta Contributor models. |
| **Cursor / Composer** | Cursor is a US company; Composer is served as a Cursor-provider model | Cursor calls Composer 2.5 its own agentic model and does not disclose Kimi as its base. It is optimized for Cursor's tools and is not portable to Pi. Cursor remains another processor of repository context when used. | **Not a Pi backup.** Treat claims that Composer is a Kimi copy as unsupported speculation unless Cursor discloses the provenance. |

## Gemini cost-controlled canary

Use a dedicated Google AI Studio project so the audit experiment has an isolated
cap and usage record.

1. Open [AI Studio Spend](https://aistudio.google.com/spend), select the test
   project, and set a small **Monthly spend cap**. The cap is experimental and
   enforcement can lag by about ten minutes, so a running agent can overshoot.
2. Prefer [AI Studio Prepay](https://aistudio.google.com/billing): load the $10
   minimum and leave auto-reload disabled. Requests stop when the balance reaches
   zero, subject to the same near-real-time billing lag.
3. Monitor the test in [AI Studio Usage](https://aistudio.google.com/usage).
4. Run bounded review prompts with an explicit file or diff set. Do not give
   Gemini an unconstrained repository crawl until its cost per useful finding is
   understood.

Record total cost, input and cached-input tokens, unique valid findings, false
positives, and whether Sol agrees with each finding. A useful second reviewer is
one that finds defects Sol missed, not one that produces the longest report.

## Current operating posture

1. Keep **OpenAI GPT-5.6 Sol through the ChatGPT subscription** as Pi's primary
   frontier model.
2. Disable model improvement in
   [ChatGPT Data Controls](https://chatgpt.com/#settings/DataControls) before
   privileged use. OpenAI's current Codex help states that this ChatGPT control
   applies to Codex content; the previously documented separate Codex link does
   not exist.
3. Trial the **$18/month Z.ai GLM Lite plan** as the subscription-backed second
   coding model. Use full GLM-5.3 for difficult implementation and review; use
   GLM-5.3-Flash, formerly Ox Alpha, for faster lower-stakes work. Begin with
   coding-only or sanitized repositories until Z.ai confirms that individual
   Coding Plan traffic is governed by its API Data Processing Addendum.
4. Keep personal, medical, relationship, and privileged professional context on
   the controlled OpenAI route or local oMLX. A model used for code review does
   not need access to the unrelated personal context available to the primary
   assistant.
5. Use **paid Google Gemini API** only for bounded independent reviews while its
   coding value is evaluated. Its privacy terms are stronger than the unpaid
   tier, but metered long-context agent loops can accumulate cost too quickly to
   serve as routine overflow capacity.
6. Deprioritize OpenCode Go. Its economics do not compensate for another gateway
   in the data path or for the lower confidence of most included models.
7. Run **Kimi K3 and Qwen3.8 Max** only on public, synthetic, or deliberately
   sanitized evaluation repositories. Do not use direct Kimi subscription OAuth
   with privileged context under the current policy.
8. Do not add Grok, MiniMax, MiMo, Cerebras, or Cursor Composer merely for cheaper
   capacity. None currently meets both the capability and portability bars.
9. Revisit when a non-Anthropic model has an independently reproduced
   same-harness coding result within roughly five points of Sol and a documented
   no-training, bounded-retention route usable from Pi.

## Sources

Capability:

- [Artificial Analysis: GPT-5.6 benchmarks](https://artificialanalysis.ai/articles/gpt-5-6-has-landed)
- [Artificial Analysis: Terminal-Bench v2.1](https://artificialanalysis.ai/evaluations/terminalbench-v2-1)
- [Kimi K3 technical report](https://arxiv.org/html/2607.24653v1)
- [Kimi K3 technical blog](https://www.kimi.com/blog/kimi-k3)
- [MiniMax M3 announcement and benchmark disclosure](https://www.minimax.io/blog/minimax-m3)

Access and economics:

- [Pi provider documentation](https://pi.dev/docs/latest/providers)
- [OpenAI Codex pricing and limits](https://developers.openai.com/codex/pricing/)
- [OpenCode Go](https://dev.opencode.ai/docs/go/)
- [Kimi Code pricing](https://www.kimi.com/resources/kimi-k2-7-code-pricing)
- [Z.ai GLM Coding Plan](https://docs.z.ai/devpack/overview.md)
- [Z.ai supported tools, including Pi](https://docs.z.ai/devpack/tool/others)
- [Z.ai confirmation that Ox Alpha was GLM-5.3-Flash](https://z.ai/subscribe)
- [Alibaba Cloud global Coding Plan](https://www.alibabacloud.com/help/en/model-studio/coding-plan)
- [MiniMax Token Plan](https://platform.minimax.io/docs/token-plan/intro)
- [Xiaomi MiMo Token Plan](https://mimo.mi.com/docs/en-US/price/token-plan)
- [GitHub Copilot plans](https://github.com/features/copilot/plans)
- [xAI pricing](https://x.ai/pricing)
- [Cerebras Code](https://www.cerebras.ai/code)

Privacy:

- [OpenAI: how individual ChatGPT and Codex content is used](https://help.openai.com/en/articles/5722486-how-your-data-is-used-to-improve-model-performance)
- [OpenAI: using Codex with a ChatGPT plan and current data controls](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- [OpenAI Codex authentication and applicable data controls](https://developers.openai.com/codex/auth/)
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
- [Google Gemini API terms](https://ai.google.dev/gemini-api/terms)
- [Google Gemini billing, prepay, and project spend caps](https://ai.google.dev/gemini-api/docs/billing)
- [xAI API security and retention](https://docs.x.ai/developers/faq/security)
- [SpaceXAI consumer privacy policy](https://x.ai/legal/privacy-policy)
- [Kimi global privacy policy](https://www.kimi.ai/user/agreement/userPrivacy?version=v2)
- [Z.ai privacy policy and API Data Processing Addendum](https://docs.z.ai/legal-agreement/privacy-policy.md)
- [Cursor Composer 2.5 documentation](https://cursor.com/docs/models/cursor-composer-2-5)
