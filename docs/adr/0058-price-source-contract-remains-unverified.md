# ADR 0058 — Source contract is required before historical admission

Accepted, 6 October 2026. R8 sought a provider-level contract for historical JSE prices, volume and point-in-time availability. The signed-in OST price-history view and its ViewPoint charting guide do not define those semantics. A dated Sasol dividend is independently established, but it falls outside the captured IRESS year. Exact close agreement on 1,250 sessions does not prove adjustment, volume eligibility or absence of revisions.

Keep OST as the primary HLCV research feed and the five IRESS OHLCV histories as separate local candidates. No alternative-source promotion, field blending, historical AI evaluation or B5 real-trade admission follows from this audit. Request a dated provider specification and an older IRESS SOL series around 13 March 2024; evaluate complete-source histories and historical as-of availability before changing the gate. See [R8 evidence](../research/PRICE_SOURCE_SEMANTICS_R8.md).
