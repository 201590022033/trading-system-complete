# ADR 0039 — IG Swing volume readiness, blocked equity admission

Date: 2026-10-04. Status: accepted for diagnostics; price-feed admission blocked.

Owner requested investigation of IG volume and integration where appropriate.
Reuse M12B IGReadOnlyAdapter and historical normalization. Authenticated Railway
Demo search found Sasol, Naspers and Shoprite candidate EPICs. Both market detail
and direct DAY history returned HTTP 403 `unauthorised.access.to.equity.exception`
for each. Successful search is not historical entitlement. No volume observation
or cash-share mapping is established by this test.

Extend IGHistoricalSeries summaries with explicit lastTradedVolume field counts,
missing versus zero, and numeric trailing relative-volume availability. Numeric
coverage never establishes exchange turnover semantics or cash-strategy admission.
Official IG schema says lastTradedVolume is generally null for non-exchange-traded
instruments: https://labs.ig.com/reference/prices-epic.html.

Add bounded read-only readiness diagnostics to the existing Swing worker loader,
frozen input, committed ranking, paper status and Portfolio model display. No
provider calls occur on HTTP status reads or frozen-job retry. Diagnostic calls
are opt-in via PAPER_IG_SWING_DIAGNOSTICS=1, Demo only; at most three candidates,
70 points/one page each and immediate stop on authentication or quota failure.
After a permission denial prefer a manual probe after entitlement changes to
repeated scheduled requests. The explicit CLI is `python -m scripts.ig_swing_data`;
exit 2 indicates blocked checks, 0 observed history awaiting semantic validation.
Neither result authorizes cash feed use. All other universe keys remain unmapped.

Do not bypass the denial, switch accounts/environments or activate orders. Do not
merge Yahoo traded volume with IG midpoint bars, relabel CFDs as cash equities,
replace missing volume with zero, or silently pool source-dependent outcomes.
Existing Swing 1.0.1/1.1.0/1.2.0 definitions, Yahoo cash benchmark, ranking, learning,
paper risk and replay remain unchanged. No schema migration or new series storage.

Once IG confirms equity-history access, re-probe DAY history and verify exact JSE
share/exchange identity, currency and quote units, session calendar, adjustment
basis, last-traded OHLC and volume scope against exchange data. Then implement
whole-series cash admission with frozen provenance and separated source cohorts.
If only CFD midpoint history is available, use a separate CFD research strategy;
the current cash Swing strategy cannot claim its traded-volume gate is satisfied.
