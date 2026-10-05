# ADR 0004: Capability-gated expanded indicators

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Existing feature/regime/evaluation infrastructure remains reusable. New daily Swing technical/policy versions are isolated research; invalid OHLC and missing dated events still block admission. Six-family local backtests and 30-minute sector-relative radar are proposed, not validated or enabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Status
Accepted for M5 on 2026-09-03.

## Context
The legacy pipeline stores close-like prices in a buffer called `vwap_buffers`.
That is sufficient for its characterized behavior but cannot honestly support
OHLC, volume, derivatives, or intraday indicators.

## Decision
Add a separate research-only calculator with explicit `DataCapabilities`,
typed market bars, per-feature availability, and an `as_of_index` boundary.
Do not extend or change the legacy `TechnicalIndicators` contract in M5.

## Consequences
- Expanded features cannot silently change current signal weights.
- Backtests can distinguish unavailable data from neutral indicator values.
- Intraday VWAP/opening range cannot be fabricated from daily closes.
- Later fusion and evaluation milestones can consume a stable versioned
  snapshot without coupling collection to scoring.
