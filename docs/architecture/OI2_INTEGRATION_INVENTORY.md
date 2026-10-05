# OI2 Integration Inventory

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

The current dashboard has six sections including backend-populated Trading Strategies and the canonical Top-5. Older multi-agent/mock/merge designs remain historical context; they do not describe the default ranking path. Paper/connected cash and self-reported trades stay separate. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

| Capability | Existing asset used | OI2 status |
|---|---|---|
| Legacy signal | `signal_pipeline.legacy_technical_score` | Operational benchmark |
| Technical calculation | `UnifiedDataPipeline` | Operational on HR7 history |
| Point-in-time evidence | HR7 asset technical features | Default, historical |
| Yahoo quotes | `YahooFinanceFetcher` | On demand, graceful failure |
| SENS/Moneyweb | existing public fetchers | On demand, graceful failure |
| HR10 research | frozen reports/artifacts | Diagnostics only |
| Broker boundary | `provider_interfaces` | No live provider; handoff disabled |
| Simulation | legacy prototype/random fetchers | Not used by OI2 |

The previous inline prototype was a simulated presentation surface. Its
compatibility endpoints remain non-live but no longer generate simulated prices
or a fabricated trade idea.

## OI3 correction — 2026-09-05

OI2 did not render news items or charts and did not invoke MacroSentimentScanner.
OI3 now exposes cached Yahoo charts/quotes and retained scanner headlines with
AI/keyword labels. See `OI3_PUBLIC_FEEDS.md`; real AI provider availability still
requires resolution in the current runtime.
