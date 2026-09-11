# M18 Canonical Metrics

`canonical-metrics-v1` is a research-only, context-explicit metric library. It
does not replace HR8–HR11 calculations, tune strategies, change targets, or
connect to ranking, policy, risk, runtime, dashboards, or brokers.

## Inventory and context

Historical code contains duplicated expectancy/drawdown logic, both positive
and negative drawdown signs, trade and observation sample bases, flat-versus-
position-state turnover, and HR10 fields labelled Sharpe/Sortino that scale by
`sqrt(n)` without annual periodicity. Those artifacts retain their original
meaning. Canonical metrics use expanded `MetricContext`: metric ID/version,
unit, net/gross and cost basis, sampling period/calendar, periods per year,
horizon, scope, overlap, risk-free rate, benchmark, currency, and realized/
unrealized basis. Ambiguous context is invalid.

`MetricResult` is immutable and records value, context, raw/effective/minimum
sample counts, `VALID`, `INSUFFICIENT_EVIDENCE`, `INVALID_CONTEXT`, or
`UNAVAILABLE`, warnings, and provenance. Unavailable is never numeric zero.

## Definitions

- Gross/net expectancy is arithmetic mean outcome per declared unit and sampling
  scope. Costs remain explicit in the context.
- Hit rate is wins divided by resolved outcomes. Neutral outcomes remain in the
  denominator; missing/unresolved outcomes are excluded and counted in warnings.
- Average win/loss use their respective nonzero subsets. Payoff ratio is average
  win divided by absolute average loss; absent losses produce `UNAVAILABLE`.
- Canonical Sharpe is mean periodic excess return divided by sample standard
  deviation, multiplied by `sqrt(periods_per_year)`. It requires explicit
  annualization, risk-free rate, net/gross basis, and non-overlapping periodic
  returns. Zero volatility is unavailable.
- `LEGACY_TSTAT_LIKE_V1` preserves HR10 exactly as mean divided by sample
  standard deviation times `sqrt(n)`. It is not canonical Sharpe.
- Canonical Sortino requires an explicit minimum acceptable/target return and
  annualization context. Zero downside deviation is unavailable.
- Maximum drawdown is the largest peak-to-trough fraction on a declared equity
  curve. Maximum underwater duration in observation periods is reported as a
  warning metadata item.
- Periodic volatility is sample standard deviation. Annualized volatility also
  requires declared periods per year.
- Position-state turnover sums absolute transitions: flat→long 1, long→long 0,
  long→flat 1, and long→short 2.
- Cost decomposition retains gross return, transaction costs, slippage, and net
  return separately.
- Profit factor is gross profits divided by absolute gross losses. Zero loss is
  unavailable, never infinity.
- Calmar is annualized return divided by positive maximum drawdown and requires
  annualization context. Zero drawdown is unavailable.
- Exposure reports time in market plus average gross and net position exposure
  in the explicitly declared unit; notional and fractions are not mixed.

Weighted expectancy is separately versioned `weighted-expectancy-v1` and
reports effective sample size `(sum weights)^2 / sum squared weights`; it is not
silently substituted for unweighted expectancy. Uncertainty fields are carried
as warnings/provenance where available; the library invents no confidence level.

`MetricRegistry` declares each registered metric's identity, version, required
context/inputs, output unit, valid scopes, and calculator. M16 criteria now
preserve metric version. M17 results can append canonical `MetricResult` records
without altering earlier scalar/context fields.

Instrument, strategy, and portfolio scopes remain explicit. Overlapping returns
are rejected for canonical Sharpe; a future estimator would require a distinct
version. Frozen HR artifacts and conclusions remain byte-identical and mapped
only through their explicit legacy identities.
