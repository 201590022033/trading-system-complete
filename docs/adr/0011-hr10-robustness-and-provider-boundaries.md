# ADR 0011: HR10 robustness and provider boundaries

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: Accepted, 2026-09-04

## Decision

Evaluate HR9 with horizon-aware purge/embargo folds and non-overlapping trades,
then apply deterministic cell-level admission gates. Keep overlapping HR9
diagnostics for comparison but never interpret them as independent trades.

Define vendor-neutral `MarketDataProvider` and `ExecutionProvider` contracts.
HR10 supplies only a paper preview implementation; submit and cancel hard-fail.
No ViewPoint or Shyft authenticated adapter is authorized.

## Consequences

Results are more conservative and may reject every candidate. Provider research
can continue without coupling analysis code to a changing broker platform, and
live execution requires a later explicit ADR and user authorization.
