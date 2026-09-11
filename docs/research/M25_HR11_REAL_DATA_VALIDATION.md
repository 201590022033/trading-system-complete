# M25 — HR11 Real-data Validation

## Experiment

`M25-HR11-IG-DATA-SOURCE-ONLY / m25-hr11-real-data-v1` is a retrospective M17
single-treatment experiment. Its baseline is the frozen `hr11-research-v1` at
commit `b080f2f0f8f7077f6861426eb4582d4c3033a149`. The deficiency is HR11's lack
of validated real intraday input; its earlier zero-input, 180-cell
`INSUFFICIENT_EVIDENCE` report remains missing-data evidence, not demonstrated
strategy failure.

The hypothesis is that frozen HR11 produces attributable, interpretable evidence
when supplied broker-backed real data. The sole treatment is replacing absent
input with IG REST `/prices/{epic}` v3 data. Features, formulas, thresholds,
gates, profiles, regimes, sessions, horizons, costs, evaluation and robustness
remain controls. No parameter search, filter, optimization or promotion occurs.

## Boundary and classification

Preserved modules are `intraday_data`, sessions, horizons, cross-asset, costs,
features, gates, signals, profiles, evaluation, robustness, router and
`hr11_research`. Only the additive M25 bridge/artifacts are refactorable or
experimental. The bridge accepts only an `IGHistoricalSeries` from DEMO at 5m,
retains M12B accepted bars and lineage, maps `CC.D.LCO.BMU.IP` to the explicit
research contract `BRENT_IG_CFD_USD1`, and emits completed HR11 bars whose
decision clock cannot precede availability. It has no Yahoo fallback.

A factual session resolver is mandatory. Gaps remain
`UNCLASSIFIED_INTERVAL_DISCONTINUITIES`; they are never filled or interpreted as
closures. Range, incomplete, malformed, duplicate and truncation facts pass
through from M12B. Missing cross-assets remain unavailable and can only produce
insufficient evidence. Existing HR11 costs and horizons remain unchanged.

Evidence states are `SUPPORTED_EVIDENCE`, `NEGATIVE_EVIDENCE`,
`INSUFFICIENT_EVIDENCE`, `INVALID_DATA`, or `INVALID_CONTEXT`. Non-positive
results are retained as negative evidence. No M16 profitability threshold is
configured. Legacy HR11/HR10 statistics retain legacy identity; canonical M18
metrics require valid context and are never forced.

## Result

External validation was **NOT RUN — CREDENTIALS UNAVAILABLE**. The safe status
probe failed locally before network access because IG credentials were absent.
Accordingly the bounded window, requested/received/accepted bars, outcome-ready
samples and empirical metrics are unavailable. The M25 artifact records zero
received/accepted bars only as run availability, not as a strategy result.
Classification is `INSUFFICIENT_EVIDENCE`; experiment decision is `INCONCLUSIVE`.

No negative performance evidence exists because no outcome sample was observed.
The important negative operational evidence is that a factual EPIC-specific
session calendar is still unavailable; the bridge refuses to infer one. A future
authorized external run must predeclare a bounded allowance-safe window, retain
all M12B quality counters, supply the factual calendar/cost context, and report
every instrument/horizon cell without tuning.

Artifact: `artifacts/research/m25_hr11_real_data/run_manifest.json`.

## Safety and recommendation

No runtime, stream, opportunity, policy, risk, PaperBroker or IG order path is
connected. HR11 remains research-only. Recommendation: no promotion; obtain the
missing factual session/calendar context and perform the registered bounded run
before any next-stage research decision.
