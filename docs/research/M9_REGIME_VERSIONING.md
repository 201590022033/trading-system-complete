# M9 — Canonical Regime Engine & Versioning

## Status

**COMPLETE — 2026-09-09**

M9 adds a typed, versioned regime contract without replacing historical regime
semantics or connecting candidate output to production scoring.

## Preserved reference regimes

- `regime_legacy_daily / regime-v1` delegates exactly to
  `regime_engine.classify_regime`: trailing close return supplies `bull`,
  `bear` or `range`; population standard deviation of trailing returns supplies
  `high`, `normal` or `low`; the existing composite supplies risk state.
  Defaults remain trend/volatility windows of 20 and thresholds `.02`, `.025`
  and `.008`.
- `regime_intraday_hr11 / intraday-signals-v1` remains the HR11 adapter using
  `ema_spread`, `volatility_change` and `relative_volume` to emit its existing
  `up/down/range`, `expanding/contracting/stable` and `thin/normal` labels.

Both are registered as `REFERENCE / LEGACY`; their source modules were not
rewritten.

## Canonical contract and candidate

`domain.features.regime.MarketRegime` carries evaluated time, versioned labels,
metrics, feature IDs, confidence, availability and provenance. Missing or
unsupported dimensions remain `UNKNOWN` or `UNAVAILABLE`; they are never
coerced to neutral values.

`regime_candidate_multidimensional / regime-candidate-v2` is registered as
`RESEARCH / CANDIDATE`. It uses the preserved close-series mathematics, but all
trend/volatility windows and thresholds are supplied by `RegimeParameters` at
evaluation time. Optional spread/volume inputs provide a research liquidity
state; absent inputs remain `UNKNOWN`. Macro risk is `UNKNOWN` unless an
explicit supported state is supplied. No candidate threshold is claimed to be
empirically superior.

## Causal guarantees

Availability timestamps are checked against `evaluated_at`; future observations
are excluded from the input prefix. Regression tests prove future-bar mutation
does not change an earlier classification, legacy parity remains exact, and
candidate/legacy definitions remain isolated.

## Runtime boundary

The contract is callable and testable only. No legacy scoring, opportunity
ranking, risk engine, HR8–HR11 result, GUI, Railway worker or broker behavior
consumes candidate regime output. The known HR11 insufficient-evidence result
remains unchanged.
