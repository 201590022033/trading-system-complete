# ADR 0034 — Reconnect Yahoo history as compact swing setup evidence

Accepted 2026-10-02 within the sole ACTIVE operational demo workspace.
No research milestone is activated and no production promotion is authorized.

## Existing pieces and broken connection

`jse_adapter.YahooFinanceFetcher` supplies public prices; HR2's
`historical_reconstruction.normalize_history` freezes normalized OHLCV with
conservative availability clocks. HR7–HR10 retain broader offline research,
including rejected strategies. M11 supplies the causal contextual learner.
`sentiment_providers` supplies Ollama news opinions, not numeric model training.
The daily operational shortlist used 60 retained closes and one-day indicator
estimates. It had no accessible longer-history three-/four-session setup context.
Old rejected research must not be repackaged as proven swing skill.

## Decision

Reuse the existing Yahoo dependency and HR2 normalizer in an explicit LOCAL
research builder, `python -m scripts.build_swing_history`. Keep source snapshots
with SHA-256 identities in ignored `analysis/cache/swing_history_v1`; do not
regenerate protected HR2/HR9/HR10 artifacts. Ship one compact versioned summary
with code to Railway. No additional historical downloads or LLM calls occur
in Railway's scheduled loop. All four ETFs and all active catalog shares are
included; failed data remains unavailable rather than zero/neutral.

Predeclared close-only states: positive 20-session trend plus a new 20-session
closing high = BREAKOUT; otherwise negative five-session return = TREND_PULLBACK;
otherwise TREND. Nonpositive 20-session trend = NO_LONG_SETUP. Each state is
separated into Satrix 40 positive/negative 20-session market context and an
explicit pooled-market fallback. Horizons of THREE and FOUR completed sessions
have independent cells. Missing/mismatched current benchmark means UNKNOWN,
never implied support. An exact session match is required for market context.

Signal cutoff is after the daily bar is conservatively available (next UTC
midnight). Entry proxy is the NEXT session CLOSE; exit is H subsequent session
closes after that entry. No trade overlaps another within a setup/context/horizon
cell, including reuse of an exit close as a new entry. Report mean gross/net,
hit rate, close-only adverse/favourable excursions, matched-date excess over
Satrix 40, and a final-third temporal holdout. Use 20 bps assumed ROUND-TRIP cost
(10 bps per leg) and 50 bps round-trip stress. These differ from the existing
10 bps total online candidate-panel assumption and are labelled, not silently
made comparable. Prices are scale-invariant for returns; this is not a sizing
or currency conversion feed. Dividends/total return and intrabar stop execution
are not modelled; unadjusted historical prices may include corporate actions.
Yahoo's Satrix 40 series contained approximately 100x down/up unit discontinuities
on April 25/29, 2025. Daily ratios outside 0.5–2 quarantine affected setup,
market-context and forward-comparison windows. Prices are not guessed/repaired;
flagged dates and excluded forward-window counts are exposed. This quality
exclusion can remove genuine large moves too and can bias results; provider
verification/total-return reconstruction remains a gate. `--cached` replays
hashed local snapshots without new downloads.

M11 estimates each isolated feature/horizon cell with its existing minimum 30
and neutral-prior shrinkage. Its LEARNED status means sample eligibility, not
profitable or validated. There is no threshold fitting, feature search, causal
macro-history invention or model training on current Ollama news. Mean intervals
are descriptive normal intervals, not HR10 bootstrap/FDR admission or promotion.
All negative and sparse outcomes remain visible. The final-third holdout is
unseen by rule fitting because the rules are fixed, but no historical revision
vintages or prospective validation are claimed.

Freeze ONLY the matching compact evidence in each daily retry input before
ranking. Retries do not reload a different report. Legacy inputs without this
snapshot remain explicitly unavailable. The candidate API and Top 5 card expose
this context separately; it does not alter effectiveness/ranking, risk, orders
or legacy signals. Compact online candidate decisions/outcomes additionally
retain setup/market/version/source hash for later comparison, without duplicating
the history. Existing online candidate outcomes remain THREE-session only;
four-session online labels and setup-conditioned online learning are not yet
implemented. Historic rows are not backfilled with hindsight classifications.

Report generation must precede the decision; future, missing, mismatched or
older-than-90-day summaries are unavailable. Regenerate locally and deploy a
reviewed refresh before expiry. Five-plus years of raw history stays off Railway;
only compact report and matching per-day evidence are deployed. Storage lifetime
and $5 cost remain measured gates, not promises. This is one useful evidence
connection, not a complete trade recommendation engine.
