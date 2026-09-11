# M15 Risk & Exposure Engine

## Scope and authority

`domain.risk` is the final-veto planning boundary between a canonical M14
`TradePolicy` and any future order-intent milestone. It returns immutable
`RiskEvaluation` evidence and, only after every mandatory check succeeds, an
`ApprovedRiskIntent`. Neither type is a broker request. The engine has no order,
position mutation, or execution dependency.

The governance sequence remains human permission, learned relevance, AI
recommendation, trade policy, risk-engine veto, and only then a future order
intent. Opportunity rank, learned effectiveness, regime, divergence, and AI
outputs cannot enlarge or override a human hard limit.

## Contracts

- `RiskLimits` holds operator controls. Every `None` is `NOT_CONFIGURED`, never
  unlimited.
- `PortfolioRiskState` is a timestamped snapshot of equity, cash, margin, open
  stopped risk, daily loss, drawdown, gross notional, and explicit exposure
  buckets.
- `InstrumentRiskMetadata` carries timestamped multiplier, lot/minimum size,
  margin factor, currency, sector, and factual correlation buckets. Broker
  adapters may populate it, but generic contracts contain no IG-specific logic.
- `FXConversion` is an observed, timestamped conversion from price/P&L currency
  into account currency.
- `RiskEvaluation` records status, inputs, checks, reductions, rejections,
  blockers, and provenance.
- `ApprovedRiskIntent` is a non-executable planning record containing the capped
  size and risk estimates.

The statuses are `APPROVED`, `REDUCED`, `REJECTED`, `UNRESOLVED`,
`NOT_CONFIGURED`, and `BLOCKED`.

## No stop, no size

M14 has no validated causal stop implementation. Its current policies therefore
remain `UNRESOLVED`, and M15 returns no position size. M15 never derives an ATR,
percentage, volatility, or other default stop. A later policy may enter risk
review only with a validated entry and stop already present on the correct loss
side.

## Sizing and reductions

For resolved geometry, raw units are:

`loss budget / (absolute entry-stop distance * contract multiplier * FX rate)`

Leverage is a constraint, not a sizing source. The engine caps loss budget by
per-trade and remaining portfolio stopped-risk limits, then caps units by gross
notional, instrument, sector, configured correlation buckets, gearing, available
margin, and margin-utilization limits. Every material cap is retained as a
reduction reason. It performs constraint enforcement, not covariance estimation
or portfolio optimization.

Units are rounded down to the configured lot increment. Rounding never increases
loss. If the rounded quantity is zero or below the factual minimum deal size,
the evaluation is rejected. Contract multiplier, lot size, minimum size,
currency, and margin factor are mandatory for approval; missing values remain
unavailable rather than being invented.

## Hard controls and unset limits

M15 defines no numerical production defaults. Approval requires explicit
operator configuration for per-trade risk, daily loss, portfolio open risk,
gross notional, gearing, margin utilization, instrument exposure, sector
exposure, correlated exposure, drawdown, and the emergency pause state. A
missing control returns `NOT_CONFIGURED`. Active portfolio/operator kill
switches block new risk. Configured daily loss, drawdown, open-risk, or existing
margin tripwires reject new risk before sizing.

Loss metrics are represented as nonnegative loss magnitudes. `daily total loss`
is realised plus unrealised loss. This milestone does not infer gains/losses from
signed broker P&L; a later broker-state adapter must normalize that explicitly.

## Margin, gearing, and currency

Estimated margin is notional times the supplied margin factor. Missing margin
metadata makes evaluation `UNRESOLVED`; the engine does not infer margin from
leverage. Final gearing includes existing gross notional plus the candidate.
Requested gearing, when present, may tighten the hard gearing ceiling but cannot
relax it.

Same-currency risk uses a factor of one. Different currencies require an exact,
timestamped `FXConversion` in the instrument-to-account direction. Missing or
mismatched FX evidence blocks monetary sizing; no 1:1 assumption is made.

## Causality and exposure semantics

Policies, limits, portfolio state, contract metadata, and FX observations dated
after `evaluated_at` are blocked. Frozen contracts and copied read-only mappings
make the result immutable evidence: later equity, FX, margin, or position changes
cannot rewrite an earlier decision.

Instrument and sector exposure use canonical IDs supplied by the registry and
portfolio snapshot. Correlation enforcement uses only explicit factual buckets
in metadata. Dynamic covariance, Kelly sizing, historical limit optimization,
liquidity estimation, and market-impact modeling are deferred.

## Deferred work and known limitations

- Current M14 policies cannot be approved because their stop and entry prices
  are intentionally unresolved.
- Live broker account/position synchronization is a later milestone; M15 accepts
  snapshots but does not fetch or mutate them.
- IG market detail may omit margin factor or currency; those facts block approval.
- No liquidity cap is applied without a factual, timestamped capacity contract.
- Cash is recorded for audit but no universal cash-settlement rule is assumed.
- No `OrderIntent`, broker-native request, Demo dealing, live trading, runtime
  integration, optimization, or M16 work is included.
