# M8 — Preserve & Migrate HR11 Causal Core

## Status

**COMPLETE — 2026-09-09**

The canonical `domain.market_data` package now exposes the preserved HR11 causal
infrastructure through compatibility facades. The existing `intraday_*` modules
remain available to HR11 scripts and tests; their formulas and research outputs
were not rewritten or regenerated.

## Classification

Preserved: `intraday_data`, `intraday_sessions`, `intraday_horizons`,
`intraday_cross_asset`, `intraday_costs`, `intraday_evaluation` and
`intraday_robustness`.

Refactorable but not behaviorally rewritten in M8: `intraday_instruments`,
`intraday_features`, `intraday_gates` and `hr11_research`.

Experimental and left unchanged: `intraday_signals`, `intraday_profiles` and
`intraday_router`. None is connected to the dashboard, ranking, risk, broker or
Railway worker.

## Canonical contracts

- `domain.market_data.sessions` and `aggregation` expose the existing explicit
  session windows and completed-bar aggregation.
- `domain.market_data.horizons` distinguishes intraday duration horizons from
  daily session horizons; their identities cannot collide.
- `domain.market_data.cross_asset` preserves availability-time as-of joins,
  event-age limits, lineage and explicit missing states.
- `domain.market_data.costs` preserves position-transition turnover charging:
  unchanged positions cost zero, entry/exit charge one side, and reversals
  charge both sides.

Completed bars remain unavailable until their interval is complete and all
required source bars are available. Session boundaries, breaks, timezone
normalization and daylight-saving-aware explicit intervals remain enforced.
Future observations cannot mutate an earlier completed interval. Evaluation
continues to use prefix slicing, matured outcomes, non-overlapping holding
windows and purged/embargoed evidence boundaries.

## Evidence boundary and limitations

The local suite passed 286 tests and all 39 protected research artifacts remain
unchanged. This milestone preserved causal infrastructure only. It did not
rerun HR11, alter the known 180 insufficient-evidence cells, claim strategy
success or failure, or promote any strategy to production. Real execution-grade
5-minute data and later IG historical integration remain prerequisites for any
real-data HR11 evaluation.

Next milestone: **M9 — Canonical Regime Engine & Versioning [NOT STARTED]**.
