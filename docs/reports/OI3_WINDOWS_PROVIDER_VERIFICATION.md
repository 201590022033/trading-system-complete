# OI3 Windows provider verification - 2026-09-06

OI3 remains **DEFERRED/BLOCKED**, not complete. The owner resumed only its
outstanding provider/source/discovery verification from `1fc8994`. This pass
does not activate HR12 or change HR11 results. Prior browser acceptance remains
historical evidence; no new browser acceptance is claimed.

## Second verification pass — 2026-09-08

The local development environment was bootstrapped on the owner's Windows laptop
(Project Python 3.12.2, fresh `.venv`). Ollama 0.33.2 is installed; the default
`llama3.2:3b` model is **not** present, but `llama3:latest` is. GPU inference
crashes with a CUDA/toolchain error on this machine, so CPU-only execution was
enabled via the new `OLLAMA_LOCAL_OPTIONS={"num_gpu":0}` `.env` setting.

| Component | Actual result | Remaining limitation |
| --- | --- | --- |
| Local Ollama | AVAILABLE via `SentimentProviders` with `llama3` on CPU | GPU path fails; default `llama3.2:3b` not installed |
| Ollama `/api/generate` | Valid structured JSON for permitted Sasol headline; assets include `OIL` (+1) and `ZAR` (-1) | One sample headline, not a production accuracy claim |
| Dashboard `/api/feed/news` | Items returned with `llm_used: true`, `analysis_provider: ollama_local`, `analysis_model: llama3` | Subsequent requests may time out on CPU and fall back to keywords |
| Keyword fallback | Confirmed when Ollama is unreachable or budget exhausted | — |
| Ollama Cloud | NOT_CONFIGURED; OLLAMA_API_KEY MISSING | No authenticated generation or account/model entitlement verified |
| Moonshot/Kimi | NOT_CONFIGURED; MOONSHOT_API_KEY and KIMI_API_KEY MISSING | No authenticated generation or account/model entitlement verified |
| Moneyweb RSS | AVAILABLE in dashboard feed | Dated public observations only |
| Moneyweb SENS | HTTP 403 challenge page remains visible | No challenge bypass attempted |
| NewsAPI | NOT_CONFIGURED; NEWSAPI_KEY MISSING | Optional source; no requests sent |
| Safe suite | Focused provider tests 12/12 pass; full suite pending below | — |

The verification script `scripts/verify_ollama_ai.py` now exercises the local
Ollama path directly without leaking credentials. Four new focused tests cover
`OLLAMA_LOCAL_OPTIONS` parsing/merging, generation timeout, and scanner keyword
fallback after a successful-then-failing provider.

## Scope established from repository state

Read README, the governing architecture/roadmap documents, laptop/environment
handoffs, OI3 architecture/report/checklists and source policy documentation.
Inspected `sentiment_providers.py`, `sentiment_analyzer.py`, `source_catalog.py`,
`jse_adapter.py`, `dashboard_feeds.py`, `opportunity_scanner.py` and recent history.
Routing/discovery already existed in `3762f9b` and `43a0248`; rebuilding them was
unnecessary. The two remaining checklist items were real AI comprehension and
failure handling, and additional permitted sources with AI-backed discovery.
The referenced MASTER_VSCODE_AGENT_PROMPT.md is absent, as already documented.

## Actual Windows checks

Python 3.12.10. Bounded checks ran at approximately 14:49 UTC on 2026-09-06,
outside the network sandbox after initial sandbox calls failed. Those initial
connection failures are not evidence that the external providers were down.
No credential values, response headers, cookies or full provider bodies were
printed or saved. No model installation, cloud generation or login was attempted.

| Component | Actual result | Remaining limitation |
| --- | --- | --- |
| Local Ollama | UNREACHABLE at default loopback endpoint; CLI absent from PATH | Model presence/inference unverified; need running service with configured model |
| Ollama Cloud | NOT_CONFIGURED; OLLAMA_API_KEY MISSING | No authenticated generation or account/model entitlement verified |
| Moonshot/Kimi | NOT_CONFIGURED; MOONSHOT_API_KEY and KIMI_API_KEY MISSING | No authenticated generation or account/model entitlement verified |
| Moneyweb RSS | AVAILABLE; three parsed items requested/returned | One bounded observation, not an uptime claim |
| Moneyweb SENS | AVAILABLE; two parsed items requested/returned | Prior Codespaces HTTP_403 is historical; no challenge bypass used |
| NewsAPI | NOT_CONFIGURED; NEWSAPI_KEY MISSING | Optional source; no requests sent |
| Scanner | Five retained real items, zero AI items, keyword provenance; no ticker impacts in this sample | Does not establish AI comprehension |
| Yahoo/discovery | SASOL, NPN and BTI all TECHNICAL_ONLY; zero unavailable in this three-symbol smoke | Sample only, not validation of the entire universe |

Yahoo result source timestamps were `2026-09-04T00:00:00+02:00`. Discovery kept
`execution_enabled=false`. These are dated public daily observations, not fresh
real-time quotes, trading recommendations or evidence of predictive accuracy.
The existing discovery universe is fixed by adapter metadata; AI adds mapped
news impacts to it, not newly validated tradable listings. Live Ollama-backed
ticker impacts could not be verified without Ollama.

Credential/configuration presence checks found `.env` ABSENT. OLLAMA_HOST,
OLLAMA_LOCAL_MODEL, OLLAMA_CLOUD_MODEL, MOONSHOT_MODEL and KIMI_MODEL were MISSING,
so existing code defaults applied. REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
were also MISSING. Offline development requires none of these credentials.

## Provider contracts and public source review

The existing Ollama cloud route uses the documented direct API with bearer
authentication. See [Ollama authentication](https://docs.ollama.com/api/authentication)
and [generation API](https://docs.ollama.com/api/generate). These documents support
the transport contract, not this account's successful access.

The existing Kimi route, `https://api.moonshot.ai/v1/chat/completions`, and default
`kimi-k3` appear in the [official Kimi API reference](https://platform.kimi.ai/docs/api/chat).
No default model was changed speculatively. Authentication, supported options and
structured response success still require an actual configured account check.

Efficient Group's [economic updates](https://www.efgroup.co.za/news-and-media/economic-updates/)
page exposes dated public commentary links, including August 2026 entries.
The [disclaimer](https://www.efgroup.co.za/about-us/disclaimer/) was reviewed;
it does not establish an automated ingestion licence or stable supported feed.
Added an independently disabled `public_manual` catalogue entry. No scraper or
content import was added. Public-link availability is not automation permission.

Existing policy remains authoritative for all other sources: BusinessLIVE,
Reuters, IG, Standard Bank, MyBroadband and BlackStone commentary remain
manual/licensed/permission-gated as recorded; Reddit/X/Telegram/Discord need their
approved API/access prerequisites. TradingView algorithmic use remains excluded.
Private Facebook and broker account access were not attempted. This pass did not
revalidate every disabled site's availability or change its permission status.

## Offline verification deliverables

Eight new provider tests exercise local/cloud/Kimi requests, model/key aliases,
provenance, credential isolation, missing configuration, HTTP auth failure,
fallback/backoff, invalid/truncated Ollama output, validation, scan budgets and
local probe throttling. Three discovery tests exercise the actual router-to-
scanner-to-discovery path with explicitly synthetic responses, SOL-to-SASOL
mapping, technical-only output, unknown ticker isolation and unavailable data.
One catalogue test preserves Efficient Group's disabled automation state.
No production routing or research algorithm was changed.

Focused deliverables: provider/feed suite **18 passed**; combined provider,
discovery, source-policy and feed suite **27 passed**. Full safe suite:
**196 passed, zero failures**. Environment diagnostic PASS. All 45 protected
analysis/baseline paths retain their committed bytes, including all 39 recorded
immutable hashes. Historical research reports were not edited or regenerated.

## Exact unresolved items / next OI3 action

1. ✅ Local Ollama AI comprehension is verified. Cloud/Kimi verification remains
   blocked on missing keys; configure an authorized Ollama Cloud/Moonshot key and
   supported model, then repeat the bounded headline/dashboard check.
2. Verify AI-backed ticker impacts on real permitted news and broader discovery
   coverage. The discovery scanner already mixes news scores with Yahoo technicals;
   live Ollama-backed impacts are now possible locally but not yet validated across
   the full universe.
3. Establish a supported feed/permission for additional commentary ingestion,
   including Efficient Group if desired, before enabling a connector. Existing
   public Moneyweb/SENS paths worked in this Windows check. NewsAPI is optional.

No successor milestone is activated. Stop here; HR12 remains NOT STARTED.
