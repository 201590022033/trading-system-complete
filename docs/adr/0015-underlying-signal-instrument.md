# ADR 0015 — Separate Underlying, Signal Target and Tradable Instrument

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06 (HR11).

## Decision

Add immutable intraday InstrumentDefinition records around the existing UI registry. Cash/proxy/derivative identities are distinct. Unverified contract metadata stays null; execution symbols never enable live trading.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
