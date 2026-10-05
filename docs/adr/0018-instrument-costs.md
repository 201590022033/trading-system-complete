# ADR 0018 — Instrument-Specific Cost Modelling

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06 (HR11).

## Decision

Require versioned externally supplied or explicitly assumed fee schedules per instrument/timeframe/liquidity regime. Charge absolute originating state turnover with separate spread, fees, slippage and elapsed-time financing. Unknown costs prevent admission.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
