# ADR 0004: Capability-gated expanded indicators

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
