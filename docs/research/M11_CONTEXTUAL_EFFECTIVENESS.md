# M11 — Contextual Feature Effectiveness Learning

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

Canonical Swing remains pinned to 1.0.1 with exact new-record attribution. Separate 1.1.0 technical, 1.2.0 policy and 1.3.0 AI research do not replace M13 ranking/M14 policy/M15 veto. M16 targets are evaluation requirements, not execution approval; Live remains disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

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
