# ADR 0012: Canonical trade-suggestion safety boundary

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: Accepted, 2026-09-04

## Decision

Separate `MarketDataProvider`, `ResearchDataProvider`, `SignalEngine`,
`TradeSuggestion`, `ExecutionProvider` and `BrokerAccount`. Every suggestion
must carry timezone-aware decision/data/expiry clocks, source, research version,
state, evidence and risk fields. Only a non-stale `admissible` buy/sell may pass
paper preview validation; research, shadow, rejected, stale and no-trade states
are non-actionable. Even eligible preview output has no live execution route.

The UI uses a fabricated rejected suggestion and browser-local feedback. It
does not import HR9/HR10 results into the decision path.

## Consequences

Rejected or stale research cannot masquerade as an executable suggestion at the
provider boundary. Any future live provider needs explicit authorization, a new
ADR, supported broker documentation and additional confirmation controls.
