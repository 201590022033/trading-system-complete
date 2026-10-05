# Ollama roles, models and learning boundaries

Reviewed 5 October 2026. Earlier machine/model checks remain in [the previous model guide](history/OLLAMA_MODELS_PRE_2026-10-05.md). They must not be treated as the installed state of the current home PC.

| Lane | Where | Current role |
| --- | --- | --- |
| News sentiment | Existing application provider configuration | Opinion/context from retrieved source content; not market data or causal proof |
| Weekly news research | Local Ollama; observed installed `llama3:latest` | Referenced case categorization and short descriptions; no cloud fallback |
| Swing 1.3.0 hypothesis research | Ollama Cloud; observed `gpt-oss:20b` proposal | Bounded volume/RSI/holding-period proposals, then frozen historical comparisons |

The weekly lane optionally selects `WEEKLY_NEWS_OLLAMA_MODEL`; configuring a name does not install it. Do not claim `llama3.2:3b` is installed because it appears in an older guide or default config. Local Ollama was reachable at port 11434. The observed GPU load failed with unsupported CUDA/PTX; the weekly scanner now defaults to CPU, 8192 context, 1536 predicted tokens and temperature 0, with a bounded 480-second request. The successful scan took about 6m38s. Ordinary sentiment keeps its existing 45-second default.

Schema-constrained responses must reference the actual supplied article/instrument/category IDs. Independently validated output rejects invented references, unsupported categories and missing required fields. An earlier unconstrained response was rejected; it was not silently repaired into evidence. Failed attempts have receipts. One automatic weekly attempt per UTC day is allowed, with at most four explicit repair retries; saved outbox delivery does not call the model again.

An LLM has no implicit browser or reliable historical news memory. Retrieval supplies dated source documents first; the model interprets those documents. It must not generate missing OHLCV, invent traded volume or retrospectively date an event.

The system stores proposals, comparisons, categorized events and outcome evidence. It does not fine-tune Ollama's model weights. The existing M11 outcome learner is separate from both local interpretation and cloud hypothesis generation. Parameter candidates are research-only, and repeated holdout results cannot automatically alter the canonical strategy.
