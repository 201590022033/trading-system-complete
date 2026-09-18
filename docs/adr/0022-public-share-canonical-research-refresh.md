# ADR 0022 — Public cash-share research refresh

Status: implemented locally, pending milestone review, 2026-09-18.

The six operational shares are a historical benchmark, not the definition of
the research universe. The dashboard may select any share from the existing
curated `JSE_TICKERS` public catalog. The operational analyser and its frozen
identity registry stay unchanged.

An explicit bounded refresh obtains at most 30 catalogued daily public series
with four concurrent requests. Identity, `.JO` data symbol, ZAR currency,
daily cadence, monotonic dates and seven-day freshness are checked. A daily
close is considered available only after the next UTC midnight. The last bar
never supplies a forward outcome. The existing M11 learner estimates causal
1-day momentum and RSI evidence, using the existing signal-state turnover
cost function with a disclosed 10-basis-point research assumption. M12
suitability and M10 divergence form typed inputs to the unchanged M13 ranker.
Only M13 ranked results enter the read-only Top 5 service. Provider failures
and invalid or sparse price series are reported as unavailable, never given
surrogate scores. Valid but unranked candidates are counted separately.

Market Intelligence or an LLM can propose a known catalog entry for attention,
but its text, confidence and ticker string cannot create a canonical identity
or promote a share into the ranking. Adding an entirely new share beyond the
current catalog needs a verified data-symbol mapping and provider validation.
The refresh is local/in-process and on-demand; it is not durable across a web
restart. Broker mappings, production analysis, execution and Railway worker
responsibilities remain unchanged.
