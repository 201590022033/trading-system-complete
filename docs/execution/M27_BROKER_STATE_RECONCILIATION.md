# M27 — Read-only Broker State Reconciliation

M27 compares immutable broker and explicitly adapted internal snapshots and
returns immutable discrepancies. It never repairs, synchronizes, inserts,
deletes, submits, amends or closes anything. A clean result means only “no
differences under the supplied comparison rules”; it is not authority to trade.

Each side retains source, environment, account identity, as-of time, freshness
and source version. IG, PaperBroker, legacy portfolio, cached runtime state and
M15 risk state remain distinct. Callers must explicitly adapt an internal source
to `ReconciliationSnapshot`; no existing store is overwritten.

Account fields are compared only through configured semantic mappings. Currency
is the conservative default. Broker balance is not assumed equivalent to paper
cash or equity. Available funds, balance and P&L can be compared only when a
caller declares aligned semantics and supplies explicit tolerances; missing
fields are informational, not zero.

Position matching is deterministic: exact broker deal ID, then unique exact EPIC
plus direction within the account snapshot, then unique exact canonical
instrument mapping. There is no fuzzy or closest-symbol matching. Unresolved
EPICs remain visible. Broker-only positions are CRITICAL; internal-only,
direction, quantity, entry and account differences have typed severities.
Unavailable/non-comparable fields are INFO, while stale state is WARNING.

Quantity comparison requires an explicit per-EPIC unit label matching the
internal unit. Missing conversion metadata yields
`SEMANTICALLY_NOT_COMPARABLE`; no multiplier is guessed. Unrealized P&L requires
both values, the same currency and timestamps within the configured maximum
skew. Otherwise it is non-comparable. Quantity, levels, account values, P&L and
timestamp skew tolerances are caller-supplied nonnegative values; exact zero is
allowed and no financial tolerance is embedded.

A successful zero-position snapshot compared with an available flat internal
snapshot can be CLEAN. Unavailable endpoints produce explicit critical
discrepancies and never masquerade as flat. Stale broker and internal snapshots
remain independently visible.

PaperBroker comparison is supported only through an explicit read-only adapter
snapshot and mismatch does not identify either source as wrong. Legacy portfolio
comparison is deferred until its cash/position units have a factual adapter.
M15 risk state may be adapted later for comparison only; M27 never recalculates
risk, modifies limits or grants approval. API/UI exposure and persistence are
deferred; callers may append results in an existing repository later.

External reconciliation was not run because IG credentials are unavailable in
this workspace. A future check must authenticate read-only, retrieve snapshots,
adapt a known internal snapshot, print a sanitized summary and terminate without
dealing calls.

M25 external empirical HR11 validation remains pending/inconclusive.
