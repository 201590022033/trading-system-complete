# ADR 0038 — Daily Swing shadow policy, separate from execution

Accepted 2026-10-04 under the owner's explicit request to implement the next
daily Swing shadow policy/entry-exit simulation milestone. This is one bounded
stage within the sole active workspace, not promotion or broker authorization.

## Decision

Add cash-only Swing `1.2.0` as a separately pinned RESEARCH/SHADOW definition.
The current registry pin remains `1.0.1`; technical `1.1.0`, its ETF context,
old profile snapshots, ranking, account configuration, paper fills and M15
remain unchanged. Reuse the frozen `1.1.0` EMA/Wilder/structure/volume/benchmark
snapshot and its preregistered core-setup conditions rather than duplicate
calculators or fit thresholds. Missing conditions/geometry block a policy;
false conditions record NO_SETUP. Keep these observations rather than selecting
only Top-5 or profitable outcomes. Sector/catalyst/calendar models are deferred
explicitly, not silently asserted as setup inputs.

`domain/policy/swing_shadow.py` owns versioned rules and deterministic replay.
`application/opportunities/swing_policy.py` owns persistence/orchestration.
The simulator lazily reuses existing canonical public daily availability and
completed-chart validation helpers; it cannot import/call a broker or size
orders. Existing M14 paper geometry and PaperBroker are close-observation
execution contracts. They cannot represent daily high/low ordering or alternate
holding horizons without changing benchmark behavior, so a separate research
replay is appropriate. It does not duplicate a second executable policy engine.

## Exact timing and exit hypotheses

- LONG entry proxy is the first completed close with canonical availability
  strictly after the actual policy decision clock, within seven calendar days.
  Canonical public daily availability is next UTC midnight. This is a delayed
  research proxy, not an actionable next-open or broker fill claim.
- Freeze stop at min(prior ten-session low, signal close minus Wilder ATR14).
  Nonpositive geometry is blocked. If the entry candle already touched the
  stop, invalidate rather than simulate an entry. Entry-bar highs cannot create
  pre-entry target profits. Target is entry plus twice entry-minus-stop.
- From the following observed bar, a gap below stop fills at its open; a gap
  above target fills at the target limit without price improvement. The opening
  quote establishes ordering in these cases. Otherwise stop precedes target
  when the day's range touches both, marked ambiguous; stops/targets precede
  horizon exit. No trailing rule. Independent variants exit at the 3rd/4th/5th
  observed provider session after entry, at that session's close.
- Malformed/nonfinite OHLC, stale/wrong-source/reordered charts, revised signal
  close, or missing retained signal history yield DATA_UNAVAILABLE. Pending
  entries/open simulations are distinct from expired/invalidated/closed rows.
  Verified exchange-calendar continuity and corporate-action quality remain
  required before admission. No holidays or missing sessions are invented.
- Gross payoff and R multiple accompany all-in hypothetical round-trip
  10/25/50 bps fee/spread/slippage scenarios. None is a verified OST quote.

## Persistence and compatibility

Freeze the exact profile snapshot/hash and complete policy rules/hash before
new acquisition. Existing account transactions store append-only JSON kinds
`swing-policy-decision`, `swing-policy-observation`, `swing-policy-entry` and
`swing-policy-outcome` in the existing ledger. Separate paired strategy refs,
policy/source/path hashes and idempotent decision/session/horizon IDs preserve
lineage. The source feature snapshot remains explicitly `1.1.0`, not relabelled
as policy `1.2.0`. Entry and observed path bars are frozen as they become
observable; later provider revisions cannot rewrite them. Closed/expired/
invalidated outcomes remain immutable. Missing/truncated inputs remain
unavailable instead of substituting a later entry. Reads are bounded (5,000
decisions/outcomes, at most six observation ID lookups per unfinished decision); summaries disclose
their read window. No broad migration or backfill.

Old frozen jobs lack the policy definition and opt out; no implicit current
version lookup attributes old decisions. Job retry uses existing frozen input
and committed result, never reacquisition. Both-backend ledger fixtures test
rollback and reopen behavior. Old forward-return cohorts and new policy payoffs
remain separate; no new policy outcome enters M11/ranking learning.

## Presentation and safety

Paper status exposes a separate `swing_policy_shadow` summary rendered in the
Portfolio learning area. Version, setup counts, closed variants, negative and
ambiguous counts, assumed cost stress and limitations are visible. No execution
button or account cash contribution. Exact profile detail API discovers 1.2.0;
three current cards remain unchanged. Existing configured/unconfigured canonical
API, risk veto, paper/demo gates and legacy benchmarks are preserved.

Feasibility stays UNRESOLVED: factual liquidity, exchange calendar, actual fees/
spread/slippage, account/minimum-size constraints and M15 approval have not been
established. This simulator computes unit-price research payoffs with no risk
approval, quantities, orders, account allocations or broker mutation.
Overlapping signals/horizons are not independent samples or a tradable portfolio.
Next stage must evaluate causal walk-forward/cost-stress evidence against the
unchanged benchmark and define non-overlapping portfolio allocation before any
promotion. Nothing here claims validated profitability.
