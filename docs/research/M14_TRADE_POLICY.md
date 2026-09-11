# M14 — TradePolicy

## Status

**COMPLETE — 2026-09-11**

M14 adds a typed planning boundary that converts an M13
`ResearchOpportunity` into a structured, explicitly non-executable
`TradePolicy`. It does not produce `TradeIntent`, calculate final size, approve
risk or margin, alter a portfolio, preview an order, or call a broker.

## Existing behavior inspected

The repository already contained versioned `EntryPolicyType`, `StopPolicyType`,
`ExitPolicyType`, `CandidateTradePolicy` and strict, fully numeric
`TradeGeometry` scaffolding. It had no policy engine. The numeric
`TradeSuggestion` fields in `provider_interfaces.py` are simulated annotations;
their only paper provider can preview explicitly admissible suggestions and
hard-fails submission. They are not promoted into M14 semantics.

HR11 evaluation supplies the only validated causal entry/exit convention: the
next observed execution-bar open at the decision boundary under an explicit
zero-latency paper assumption, followed by a canonical horizon-end exit. Its
`units=1` is an evaluation assumption, not approved position size. Unchanged
positions incur no turnover, entry/exit one side and reversal two sides in cost
research; there was no validated automatic reversal executor, trailing rule,
structural stop, target or live time-stop implementation.

## TradePolicy contract

`TradePolicy` retains:

- policy/opportunity/instrument/horizon identity and all relevant versions;
- LONG/SHORT direction only when M13 supplies an eligible direction;
- entry type, causal reference/timing/window, price-source state and slippage
  metadata;
- separate thesis invalidation condition/time and stop type/reference/distance/
  price/provenance;
- optional target type/reference/distance/levels and provenance;
- trailing state/rules;
- TTL, maximum holding duration, canonical time exit and exit rules;
- explicit reversal requirement/rule;
- optional requested risk/gearing fields with `NOT_EVALUATED` approval;
- deterministic reasons, blockers and immutable provenance.

`actionability` is always `NON_EXECUTABLE_RESEARCH_PLAN`. The contract contains
no final position size, quantity, approved gearing/margin, portfolio exposure or
order object.

## Supported policy families

M14 implements only families supported by repository evidence:

1. `horizon-aligned-next-bar-time-exit`: eligible LONG/SHORT research direction,
   next observed canonical bar-open reference, canonical horizon-end time exit,
   explicit pre-entry invalidation and exit-on-reversal review. Stop remains
   unresolved, target is none and trailing is unsupported.
2. `non-actionable-audit-only`: BLOCKED, insufficient, WATCH, future-dated or
   otherwise non-actionable opportunities. It carries no direction or entry
   intent.

The existing enums gain only explicit `UNRESOLVED` members. Breakout, pullback,
mean-reversion, ATR, swing, structural, fixed-target and risk/reward families are
not selected because no current canonical M13 input supplies validated causal
geometry for them.

## Entry semantics

The horizon-aligned family uses `CONFIRMATION_ENTRY` with reference
`NEXT_OBSERVED_CANONICAL_BAR_OPEN`. Policy creation never reads or fills the
future open: `entry_price` stays `None`, and the price source states that it is
unavailable until observed. The allowed window begins at policy creation and is
bounded by one configured decision-bar duration or the horizon end, whichever
comes first. Slippage metadata is carried as supplied and is never invented.

This preserves the HR11 research convention without claiming a perfect fill,
current-market order or executable next-bar instruction.

## Invalidation and stop semantics

Strategy invalidation is an event condition: the opportunity becomes ineligible
or a valid opposing direction appears before entry. It is distinct from a stop
loss. No validated causal stop level/distance exists in the current architecture,
so stop type/reference/provenance are explicitly `UNRESOLVED` and stop price and
distance remain `None`.

Because a risk engine cannot assess stopped risk without a stop boundary, even a
directional horizon-aligned policy remains `UNRESOLVED`, never
`READY_FOR_RISK_REVIEW`. Future work must provide a separately tested causal stop
input; M14 does not manufacture one from score, volatility or future bars.

## Targets and trailing

The supported family is horizon/time-based and requires no price target. Target
type is `NONE`; distance and levels remain empty. Trailing is disabled and its
rules are `UNSUPPORTED`. Existing architecture enum names are not evidence of an
implemented rule and are not silently activated.

## Time exit and horizon identity

M14 accepts canonical `intraday_<minutes>m` or `daily_*` identities plus an
upstream, causally known horizon end. TTL and maximum holding seconds equal the
interval from creation to that end. Noncanonical `1d`, absent/expired horizon
ends and absent decision-bar duration remain explicit blockers. Session/calendar
calculation stays upstream in the M8 horizon boundary; daily and intraday
identities are not mixed.

## Reversal

An opposing current position sets `reversal_required`. The rule is exit the
existing position, then require separate review of a new policy. A policy never
silently flips or creates two-sided orders. Without an opposing position, a
later valid opposing signal is an exit-review condition only.

## Requested risk intent and M15 boundary

M14 does not require a requested loss budget, risk fraction or gearing value, so
all three remain `None`; `risk_approval_status` is `NOT_EVALUATED`. This avoids
turning the historical fixed-unit research assumption into sizing policy.

M15 may approve, reduce or reject a future sufficiently specified policy. It
must own final position size, account equity, margin, exposure, concentration,
correlation, daily-loss and gearing limits. M15 is not started.

## Causality and deterministic output

Policy creation rejects future-dated opportunities and contexts. It accepts no
future bars and leaves future price-dependent fields unresolved. Later score or
regime-map mutations do not change the earlier policy because neither defines
policy geometry. IDs derive deterministically from opportunity, creation time,
family and version.

## Runtime boundary and validation

The engine has no Flask, worker, persistence, risk, portfolio, PaperBroker or IG
execution dependency. Paper and IG submission remain disabled; legacy scoring is
unchanged. No parameter, stop, target, TTL or family selection was optimized.

Twelve focused tests cover all requested gates, direction, causal entry and
future invariance, invalidation/stop separation, unresolved stops, optional
targets, trailing, canonical horizon time exits, reversal, unapproved risk,
absence of sizing/margin/order fields, provenance, determinism, disabled
execution and legacy scoring. The full safe suite passes 387 tests; all 39
protected artifacts remain byte-identical.
