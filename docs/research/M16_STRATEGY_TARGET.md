# M16 StrategyTarget

## Purpose

`strategy-target-v1` declares multidimensional research and risk requirements
before candidate evaluation where possible. It is not an objective function,
parameter search, strategy optimizer, promotion engine, deployment gate, or
runtime trading component.

`StrategyTarget` records identity, version, creation time, strategy family,
instrument and horizon scopes, lifecycle status (`DRAFT`, `ACTIVE`, or
`DEPRECATED`), governance author, rationale, version history, experiment family,
and immutable `TargetCriterion` records. No repository-wide default target is
created and no current strategy is declared passing.

## Metric context

Every criterion carries an explicit `MetricContext`: sampling basis, period,
calendar, annualization factor, return unit, net/gross basis, cost basis,
horizon, per-trade/strategy/portfolio scope, overlap state, and risk-free rate
where applicable. Evidence must match the criterion's exact metric identity,
stage, and context. A numerically attractive value with mismatched context is
`INVALID_CONTEXT`, not comparable evidence.

## Legacy and canonical risk-adjusted metrics

HR10's historical field named `sharpe` is preserved without altering frozen
reports. Its exact `mean(trade return) / sample standard deviation * sqrt(n)`
formula has the explicit identity `LEGACY_TSTAT_LIKE_V1`. It is a t-stat-like
sample-scaled statistic, not canonical annualized Sharpe.

`CANONICAL_ANNUALIZED_SHARPE` requires non-overlapping periodic decimal returns,
an explicit annualization factor, net/gross basis, and explicit annual risk-free
rate. The implementation subtracts risk-free rate per period and annualizes by
the square root of the declared periods per year. Missing context returns
`INVALID_CONTEXT`; insufficient or constant observations return `UNAVAILABLE`.
No periodicity is inferred from a label.

## Hard, soft, and unset requirements

Criteria are independently `HARD` or `SOFT` and use minimum, maximum, or
required-true comparisons. Hard failure determines
`HARD_REQUIREMENTS_FAILED`; soft success cannot average it away. Missing hard
evidence remains `EVIDENCE_INCOMPLETE`, and mismatched evidence remains
`INVALID_EVIDENCE_CONTEXT`.

A `None` threshold is explicitly `NOT_CONFIGURED`. M16 invents no Sharpe,
expectancy, sample, drawdown, risk, gearing, duration, or exposure threshold.
Even when all configured hard criteria are satisfied, the result is only
`REQUIREMENTS_SATISFIED_FOR_REVIEW`; `promotion_authorized` is permanently
false in M16.

## Multidimensional evidence

Metric identities support net and gross expectancy, total/effective/OOS/forward
sample depth, canonical Sharpe, legacy HR10 statistic, Sortino, drawdown and loss
limits, walk-forward stability, regime robustness or declared specialization,
base/stressed costs and slippage sensitivity, parameter stability, stress
survival, forward duration/expectancy/drawdown, operational stability,
historical-forward divergence, gearing, margin feasibility, liquidity, and data
grade.

Separate target instances retain incompatible family and horizon identities,
such as intraday scalping, short-term swing, daily directional, and long-term
investment. Universal performance across regimes is not presumed: a criterion
may declare required regimes and allowed specialization explicitly.

## Evidence-stage separation

`IN_SAMPLE`, `VALIDATION`, `OUT_OF_SAMPLE`, `WALK_FORWARD`, `FORWARD_DEMO`, and
`LIVE` are distinct enum states. They cannot be merged by supplying an
observation from another stage. Forward/Demo targets may independently require
duration, sample count, net expectancy, drawdown, operational stability, and
bounded divergence from historical evidence. No such evidence is fabricated or
claimed for current strategies.

## Risk interaction

Promotion research may declare maximum intended loss, daily strategy loss,
portfolio open risk, drawdown, gearing, and margin feasibility criteria. These
cannot change or bypass M15. `RiskEngine` remains the final runtime veto and its
operator hard controls remain authoritative.

## Deferred to M17 and later milestones

- M17 may register experiments and associate them with predeclared targets; it
  is not implemented here.
- Automatic promotion/deployment remains absent.
- Canonical portfolio performance aggregation and the broader M18 metric engine
  remain separate future work.
- No parameter search, threshold tuning, ranking, policy, risk-engine, runtime,
  broker, or execution behavior changes are included.
