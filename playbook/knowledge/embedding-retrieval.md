# Embedding retrieval

Decision guide for adding semantic retrieval to a private text corpus. This page
owns the embedding-model, provider, privacy, and local-runtime choices. Storage
choices remain in [data-stores.md](../stacks/data-stores.md), and general local
model serving remains in
[open-model-inference.md](open-model-inference.md).

**Snapshot:** 2026-08-31. Models, runtime support, prices, and data terms change
quickly. Re-check the linked primary source before uploading a corpus or choosing
a durable vector format.

## Current decision

Do not add semantic retrieval until a labeled evaluation set shows recurring
misses that lexical search cannot fix cleanly. A private corpus with a strong
full-text baseline does not benefit from a vector index merely because embeddings
are available.

When the trigger is met:

1. Keep lexical retrieval as the exact-match and offline path.
2. Add dense retrieval as a second candidate generator, then fuse ranks.
3. Benchmark on real questions before indexing the complete corpus.
4. Prefer a supported local model when privacy is the controlling requirement.
5. Use a hosted model only after its training, retention, deletion, and processing
   terms have been accepted explicitly.

At small-corpus scale, provider price and vector-database performance are rarely
the constraints. Good chunk boundaries, retrieval evaluation, and the decision to
send private text to another company matter more.

## Voyage 4 Nano on Apple Silicon

The answer depends on what “works with MLX” means.

| Path | Status | Practical consequence |
|---|---|---|
| Voyage's official checkpoint through Transformers or Sentence Transformers | Works locally, but uses PyTorch rather than MLX | Keeps text local, but adds a parallel runtime and does not use an existing MLX server. |
| The official checkpoint loaded directly by oMLX | **Not supported as of this snapshot** | Voyage uses custom bidirectional Qwen3 code. Current oMLX documentation lists BERT, BGE-M3, and ModernBERT embedding support, and its installed model adapters do not make ordinary Qwen3 support equivalent to Voyage support. |
| `sanjay920/voyage-4-nano-mlx` | Experimental MLX path | An unofficial package implements the bidirectional architecture, prompt prefixes, projection, mean pooling, and normalization. It runs directly through Python, not through oMLX's OpenAI-compatible embeddings endpoint. |
| Future `mlx-embeddings` support | Plausible, not shipped | A pull request exists for a Qwen3 bidirectional encoder, but an open pull request is not a supported runtime. |

Voyage 4 Nano is small enough for modern Apple Silicon: about 346 million
parameters and 672 MB in bfloat16 in the community port. Hardware is not the
blocker. The blocker is faithful implementation of its custom model behavior:

- bidirectional rather than causal attention;
- different trained prefixes for queries and documents;
- a per-token projection from 1,024 to 2,048 dimensions before pooling;
- mean pooling over non-padding tokens; and
- L2 normalization plus supported dimension truncation.

Relabeling the checkpoint as a standard Qwen3 embedding model could return vectors
with the expected shape while silently damaging retrieval quality.

The community port reports near-reference numerical parity and matching results on
two retrieval benchmarks. Those are encouraging maintainer-reported checks, not
independent adoption evidence. The repository had three commits, no releases, and
almost no public adoption at this snapshot. If evaluated, pin a commit, review the
small implementation, reproduce its parity tests, and keep it isolated from the
primary inference runtime.

### Cleaner local choices

- **BGE-M3 or ModernBERT:** the conservative route because oMLX documents these
  embedding families directly.
- **Standard Qwen3 Embedding:** supported by Apple's MLX Embedders library and by
  current `mlx-embeddings`, but validate it against the exact oMLX release before
  making it an operational dependency.
- **Voyage 4 Nano community port:** use only when its shared space with hosted
  Voyage 4 models or its measured retrieval quality beats the supported choices
  by enough to justify a separate package.

## Hosted providers

| Provider | Best reason to evaluate | Data boundary to verify |
|---|---|---|
| [Voyage AI](https://docs.voyageai.com/docs/embeddings) | Retrieval specialist, paired rerankers, and a shared vector space across the Voyage 4 family | Standard terms permit model-improvement use unless the account opts out. Voyage says the opt-out requires a payment method, applies only to future requests, and provides zero-day retention. Confirm the toggle before the first private request. Voyage is owned by MongoDB. |
| [OpenAI](https://developers.openai.com/api/docs/models/text-embedding-3-small) | Simple, mature embeddings endpoint when an OpenAI API project already exists | API inputs are not used for training by default. Embeddings may appear in abuse-monitoring logs for up to 30 days; the endpoint is eligible for approved Zero Data Retention. |
| [Google Gemini](https://ai.google.dev/gemini-api/docs/embeddings) | Multimodal retrieval across text, images, audio, video, and documents | Paid services do not use prompts or responses to improve products. Limited abuse-monitoring retention still applies unless the documented Zero Data Retention conditions are satisfied. Free and paid terms differ. |
| [Jina AI](https://jina.ai/embeddings/) | Search-specialist models, multilingual and multimodal options, and a paired reranker | Jina says API inputs and outputs are not used for training. Its public product page does not establish a complete sensitive-corpus retention contract, so verify retention and deletion terms before bulk upload. Jina now operates as an Elastic model brand. |
| [Cohere](https://docs.cohere.com/docs/cohere-embed) | Enterprise retrieval, multimodal embeddings, and paired reranking | Evaluate when its deployment or commercial controls solve a concrete requirement. Do not infer retention guarantees from enterprise positioning; verify the applicable agreement. |

No hosted provider is a default for a complete private corpus. The first 1-2
million tokens are inexpensive at all serious providers, so a low price does not
compensate for weaker data terms.

## Approval gate for a private corpus

Before the first complete indexing run, record:

- whether inputs or outputs may be used for training or product improvement;
- default retention and the exact control that changes it;
- whether the control applies retroactively or only to future requests;
- subprocessors, processing region, and any data-residency requirement;
- deletion behavior for request logs and stored vectors;
- whether account administrators can verify the setting independently;
- which paths or data classes must never leave the machine; and
- the model, dimensions, prompts, and normalization required to reproduce the
  index.

Treat embeddings and the derived index as sensitive data. They are regenerable,
but they are not public merely because they are numeric.

## Evaluation protocol

1. Preserve a labeled set of real questions and expected pages or sections.
2. Measure lexical top-five recall and mean reciprocal rank.
3. Compare one supported local model with no more than two hosted candidates on a
   sanitized sample.
4. Test lexical, dense, and fused retrieval separately.
5. Include exact names, identifiers, dates, paraphrases, and cross-domain
   questions.
6. Choose only if hybrid retrieval fixes observed misses without burying exact
   evidence or creating an unacceptable data boundary.
7. Store provider, model revision, dimensions, prompt mode, content hash, and
   chunk identity with every derived vector so a model change forces a clean
   rebuild.

## Sources

- [Voyage 4 Nano official model card](https://huggingface.co/voyageai/voyage-4-nano)
- [Unofficial Voyage 4 Nano MLX port](https://github.com/sanjay920/voyage-4-nano-mlx)
- [Open Voyage support pull request for `mlx-embeddings`](https://github.com/Blaizzy/mlx-embeddings/pull/67)
- [oMLX models and embeddings endpoint](https://github.com/jundot/omlx#models)
- [Apple MLX Embedders model reference](https://github.com/ml-explore/mlx-swift-lm/blob/main/skills/mlx-swift-lm/references/embeddings.md)
- [Voyage customer-data FAQ](https://docs.voyageai.com/docs/faq)
- [Voyage terms of service](https://www.voyageai.com/tos)
- [MongoDB acquisition of Voyage AI](https://www.mongodb.com/company/newsroom/press-releases/mongodb-announces-acquisition-of-voyage-ai)
- [OpenAI API data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
- [Google Gemini API Zero Data Retention](https://ai.google.dev/gemini-api/docs/zdr)
- [Jina embeddings API](https://jina.ai/embeddings/)
