# ADR 0008: Additive multi-agent intelligence context

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Status
Accepted for M9 on 2026-09-03.

## Context
Adaptive explanations must reach the existing Bull/Bear/General research flow
without replacing or silently changing Trader, Risk, Manager or Executor
governance.

## Decision
Add an `intelligence_context` field to `MarketObservation` and populate it via a
separate adapter. Researchers append the profile/regime/adaptive summary to
their text but retain existing stance and confidence logic. Emit disagreement
telemetry in the step result. Label simulated execution explicitly as `paper`.

## Consequences
- Existing agent method signatures remain stable.
- Explanations are available to dashboards/logging without affecting votes.
- A context-disabled compatibility test proves proposal, risk assessments and
  manager decision remain identical.
- No broker or live-execution path is introduced.
