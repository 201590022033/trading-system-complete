# M11 — Contextual Feature Effectiveness Learning

## Status

**COMPLETE — 2026-09-09**

M11 adds a canonical research learner for attributable feature effectiveness.
It estimates supplied feature outcomes by context; it does not search strategy
combinations, optimize thresholds or produce production decisions.

## Contract and supported evidence

`FeatureOutcome` records feature ID/version/family, instrument, explicit horizon,
regime context, signal state, feature availability, evaluation time, outcome
maturity, gross return and net return. `FeatureEffectiveness` reports counts,
gross/net estimates, hit rate, dispersion/uncertainty, confidence, evidence
grade, status and lineage.

The contract supports legacy and candidate technical features, `divergence-v1`
states and causally available cross-asset features when supplied by an upstream
producer. Fabricated news, unavailable macro history and unsupported real
intraday data are not accepted implicitly.

## Causal learning and partitioning

Only outcomes satisfying `feature.available_time <= evaluated_at < maturity` and
`outcome_maturity <= learner evaluated_at` are eligible. Daily session and
intraday duration horizons remain distinct identities. Context fallback is:

`instrument + horizon + regime` → `instrument + horizon` → `instrument` → `global`.

The first level meeting the configured minimum is used; the global level is the
final fallback. Raw sample count and effective recency-weighted sample count are
reported. The default minimum and prior are versioned configuration values, not
architecture truth.

## Shrinkage, recency and costs

Net estimates shrink toward a configured prior using explicit prior strength;
sparse cells remain `INSUFFICIENT_EVIDENCE` even though the adjusted estimate is
reported. Optional recency weighting is parameterized and causal. Outcomes may
report both gross and net returns; trade-like net outcomes must be produced with
the canonical originating-position turnover semantics. No flat per-observation
cost is introduced.

Negative, unstable and insufficient evidence is retained rather than filtered.
Divergence states remain evaluable as states/features without assuming that high
agreement, conflict or low evidence is profitable.

## Runtime boundary and limitations

The learner is research-only. It is not connected to legacy scoring, opportunity
ranking, TradePolicy, risk, GUI, Railway, broker execution or live weights. No
historical artifacts were regenerated and no profitability, threshold, decay or
feature-subset optimization was performed. The local suite passes 301 tests and
all 39 immutable research artifacts remain unchanged. Predictive usefulness and
production suitability remain unknown and require later controlled evaluation.
