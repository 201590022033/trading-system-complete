# M20 Read-Only Canonical Top-5 GUI

M20 adds a dedicated **Canonical Top 5** tab to the existing dashboard without
removing or changing legacy panels. It answers which canonical research records
rank highest and why; it is not a trade ticket or execution surface.

The panel manually refreshes `GET /api/v1/opportunities?limit=5`, preserves the
backend rank order, and renders at most the available records. Cards display
rank, instrument, horizon, canonical LONG/SHORT/WATCH/UNKNOWN direction,
Opportunity Score, eligibility, regime, divergence, evidence depth, suitability,
data grade, execution suitability, reasons, uncertainty, and blockers. Missing
fields remain visibly unavailable and are never fabricated.

Every score is displayed as `Opportunity Score: value / 100` with the nearby
statement “Comparative research score — not probability of profit.” The browser
does not calculate ranking, direction, suitability, risk, or readiness.

Each card uses a keyboard-accessible native details element. On expansion it
fetches canonical policy, risk, and intent endpoints and displays authoritative
entry timing/reference, stop status/price, target status, time exit,
invalidation, risk status, approved size/loss budget, readiness, blockers, and
compact provenance. Current unresolved stops show `UNRESOLVED`; null sizes show
`Not available`. No stop, target, reward/risk, margin, or gain is inferred.

Readiness is rendered exactly from the intent API (`READY_FOR_PREVIEW`,
`NOT_READY`, `BLOCKED`, or `UNRESOLVED`) and is never called ready to trade.
Empty canonical data displays “No canonical opportunities available yet” and
explains that ranking has not been populated. API, malformed-response, 404/409,
and 503 conditions receive clear non-technical states and never fall back to a
legacy HOLD or recommendation.

The panel includes status live regions, labeled navigation, labeled refresh and
detail regions, and textual states so color is never the only signal. It adds no
BUY, SELL, take-trade, place-order, auto-trade, sizing, or broker control.
Credentials, tokens, account IDs, and raw authentication material are neither
requested nor displayed.

Legacy discovery, analysis, portfolio, system, and disabled broker-handoff UI
remain present. M20 adds no fixture to production, periodic canonical polling,
runtime decision logic, order construction, broker action, or M21 work.

## 2026-09-18 public research refresh extension

The later dashboard extension adds an explicit on-demand refresh of the curated
public cash-share universe. It computes matured, cost-labelled research evidence
through M11/M12/M10 and orders qualifying results with the existing M13 ranker.
The default screen may start this bounded refresh once; a five-minute cooldown
prevents repeated scans. The selector includes all curated shares, but the
operational technical analyser remains limited to its supported benchmark
subset. The read-only chart works for the wider catalog. The ranking is held in
web-process memory and must refresh after restart. No LLM text can canonize an
unverified ticker. See ADR 0022.
