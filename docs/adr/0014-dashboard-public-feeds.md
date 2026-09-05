# ADR 0014 — Restore public feeds around existing adapters

Status: accepted, 2026-09-05 (OI3)

OI2 exposed historical analysis but omitted current-price refresh, charts and the
existing AI sentiment scanner. The owner authorized restoring those capabilities.

Extend `YahooFinanceFetcher` with timestamped chart bars and extend
`MacroSentimentScanner` with optional retained results and progressive publication.
Keep the existing scalar price methods and the scanner's default one-shot behavior.
`dashboard_feeds.py` is a presentation cache/orchestrator, not a replacement data
provider or signal engine. Four workers and one refresh per canonical cache key
keep slow provider/LLM requests out of Flask response handling. Cache keys are
restricted to the six existing instruments, the existing JSE index proxy, and
four permitted ranges. News is shared across instruments and browser clients.

Use native SVG for price charts, avoiding a third-party runtime/CDN dependency.
Keep production signal weights, research artifacts and execution boundaries
unchanged. Public quotes are explicitly delayed/unverified and daily bars remain
session dates. Confirmed ZAc is converted to ZAR only in this new display path.

Consequences: caches and the bounded 100-headline archive are process-local and
reset on restart. Each process has its own rate limit; this is a local dashboard,
not a multi-worker feed service. Headline analysis has an eight-item AI budget per
scan; remaining headlines use labelled keywords. Provider/model failures retain
available results and never synthesize prices, headlines or AI results.
