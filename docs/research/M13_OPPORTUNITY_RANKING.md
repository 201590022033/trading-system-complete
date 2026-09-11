# M13 — Opportunity Ranking

## Status

**COMPLETE — 2026-09-11**

M13 adds a canonical research layer that answers which supplied opportunities
deserve investigation now. It does not decide a trade, predict profit, size a
position, construct an order, or call a broker.

## Canonical contracts and inputs

`OpportunityCandidate` accepts only the existing typed M3
`CanonicalInstrument`, M12 `InstrumentSuitability`, M10 `DivergenceFeature`, a
tuple of M11 `FeatureEffectiveness` records, optional M9 `MarketRegime`, factual
data grade and optional M12A `IGMapping`. M12B history can contribute only its
factual availability/data-grade metadata through the already evaluated
suitability boundary. Demo history remains `RESEARCH_DATA`.

`ResearchOpportunity` retains deterministic identity, UTC evaluation time,
instrument/horizon, optional broker/EPIC mapping, research direction, evidence
summary and confidence, divergence state, regime context, suitability
dimensions, data grade, sample/effective counts, explicit uncertainty, score
components, rank, status, reasons, blockers and all input/configuration versions.
It contains no TradePolicy, entry, stop, target, quantity, position-size, margin,
gearing or order fields.

## Hard eligibility

Hard eligibility is evaluated before scoring. M12 blocks and unsupported states,
false `hard_eligible`, M3 disabled/blocked governance, future suitability and
canonical/broker identity mismatches cannot receive a score or rank. Missing
learned M11 evidence produces `INSUFFICIENT_EVIDENCE`, also unranked. These
states remain in the full result for audit and cannot be compensated for by a
soft component.

An execution mapping is not required for a research opportunity. A candidate
that is research-suitable but execution-unsuitable may be ranked and is labelled
`RESEARCH-ONLY` with mapping unavailability retained.

## Ranking components and formula

`RankingConfig` version `opportunity-ranking-v1` declares defaults; none were
optimized against P&L. Positive components are each normalized to `[0, 1]`:

- suitability: M12 soft suitability score;
- effectiveness support: share of learned M11 features with positive support,
  retaining neutral and negative support;
- evidence depth: effective samples relative to the configured evidence target;
- stability: M12 stability state;
- directional strength: M10 dominance margin;
- regime context: support from exact M11 instrument+horizon+regime evidence;
- divergence state: distinct configured values for agreement, conflict,
  dominance-with-conflict, low evidence and unavailable evidence;
- data quality: factual grade and availability only.

Default positive weights are respectively 0.25, 0.20, 0.15, 0.10, 0.10, 0.08,
0.07 and 0.05. Explicit uncertainty and known-cost penalties have default
weights 0.10 and 0.05. The bounded score is:

`100 × clamp(weighted positive components − weighted penalties, 0, 1)`

These are transparent configuration defaults, not architecture truth. No return,
Sharpe, threshold, feature subset or instrument selection optimization occurred.

## Score and direction semantics

`ranking_score` is labelled
`COMPARATIVE_RESEARCH_RANKING_SCORE_NOT_A_PROBABILITY_OR_EXPECTED_RETURN`.
It is an ordering aid only—not probability of profit, win probability, trade
confidence or expected return.

Direction comes only from causally available M10 current signal evidence.
Positive/negative dominance yields `LONG`/`SHORT`; balanced conflict yields
`WATCH`; low or unavailable directional evidence yields `UNKNOWN`. Historical
average returns never manufacture direction. Rankable candidates without a
supported trade direction remain `WATCH` rather than being forced long or short.

## Divergence, effectiveness and regime

M10 states are not flattened: `HIGH_AGREEMENT`, `HIGH_DISAGREEMENT`,
`DOMINANT_WITH_CONFLICT`, `LOW_EVIDENCE` and `UNAVAILABLE` remain visible with
dominance, disagreement, agreement and coverage metadata. Bullish dominance
with conflict therefore differs from pure bullish agreement and balanced
conflict.

M11 estimates remain contextual evidence, never production weights. Sample and
effective counts, confidence, insufficient cells, fallback levels, shrinkage
outcomes and negative feature IDs are retained. Negative learned evidence lowers
the effectiveness component and adds a deterministic reason rather than being
discarded. Broader hierarchical fallback adds explicit uncertainty.

M9 regime is descriptive. It changes only the documented regime-context
component using exact contextual M11 support; no regime label is assumed
universally bullish/bearish and no thresholds are optimized. Future-dated
effectiveness, divergence, regime or suitability input cannot enter an earlier
evaluation.

## Uncertainty and explanations

Structured uncertainty identifies limited samples, broader M11 fallback,
unknown liquidity/costs, unavailable regime, weak/conflicted direction and
non-execution-grade data independently. Unknown liquidity remains unknown rather
than becoming bad liquidity. Reasons and blockers are deterministic phrases
derived from these typed states; no LLM explanation is a source of truth.

## Determinism, top-N and persistence

`OpportunityRanker.rank(..., top_n=5)` sorts by score descending, then instrument,
horizon and deterministic opportunity ID. All rankable candidates receive a
rank; `top_opportunities` is only a view of the first N. `opportunities` retains
lower-ranked, weak, insufficient, blocked and unsupported candidates for audit.

M13 adds no persistence schema. If append-only ranking-run persistence is added
later, it must retain IDs, evaluation/configuration versions, components, ranks,
reasons, blockers and provenance without secrets or overwriting earlier runs.

## Runtime boundary and deferrals

The ranker is not connected to Flask, the legacy scorer, adaptive production
weights, portfolio logic, risk, Railway workers, broker adapters or execution.
Legacy runtime behavior is unchanged and IG execution remains disabled.

TradePolicy/entry/exit geometry belongs to M14. Position sizing, portfolio
allocation, exposure, margin and execution remain deferred to later explicitly
authorized milestones. M14 is not started.

## Validation

Twelve focused tests cover hard gates, insufficient and negative evidence,
divergence distinctions, regime isolation, fallback/unknown uncertainty,
research-versus-execution suitability, deterministic ties/top-N, provenance,
score semantics, forbidden trade fields, disabled execution, legacy scoring and
future-input invariance. The full safe suite passes 375 tests; all 39 protected
artifacts remain byte-identical.
