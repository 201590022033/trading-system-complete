# ADR 0006: Multi-horizon walk-forward evaluation contract

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Status
Accepted for M7 on 2026-09-03.

## Context
Adaptive fusion needs comparable, uncertainty-aware evidence without leaking
future observations or pretending close-only research is an executable strategy.

## Decision
Evaluate legacy, technical-only, macro-only, source-only and adaptive models at
1/3/5/20-session horizons. At each decision, build indicators and regime only
from the prefix ending at that observation. Report aligned/net return, Wilson
win-rate intervals, turnover, compounded decision-path drawdown, and close-path
MFE/MAE. Segment by trend, volatility and profile, and flag samples below 30.

## Consequences
- Missing contextual history produces zero-sample ablations rather than
  fabricated neutral evidence or diluted available factors.
- Cost and drawdown results are configurable research approximations; overlapping
  horizon decisions are not claimed to be a capital-constrained portfolio.
- The first report cannot justify promotion because it lacks aligned historical
  macro/source evidence and results differ materially by ticker/horizon.
