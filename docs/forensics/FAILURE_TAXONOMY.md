# Failure Taxonomy

Fifteen of 24 adaptive rows had negative mean net return in the frozen
reconstruction. The categories below are conservative diagnostics, not proven
causes; one primary label was assigned per row.

| Failure category | Rows | Interpretation |
| --- | ---: | --- |
| Horizon mismatch/instability | 4 | Same ticker had a positive adjacent horizon, so timing is more plausible than universal uselessness. |
| Downside/volatility exposure | 4 | Negative result coincided with materially adverse excursion; close-only data cannot isolate shocks. |
| Technical signal noise or lag | 4 | Gross performance stayed negative without adjacent support; NPN/IMPJ dominate. |
| Transaction-cost burden | 3 | Gross edge was positive but the configured 10 bps turnover charge made net negative. |

Structural failure applies to the entire experiment: adaptive context did not
actually adapt. Regime/profile multipliers cancelled after single-factor
normalization, while macro/source inputs were unavailable. Other requested
categories—wrong sector sensitivity, excessive macro/sentiment weight, stale or
duplicated sources, commodity/Rand misunderstanding—cannot be assigned because
those components produced no observations.

Most important negative clusters:

- IMPJ at 1/3/5 sessions: -0.91%/-1.46%/-1.06% net, negative in both halves.
- NPN at every horizon, especially 20 sessions (-0.59%; second half -1.29%).
- BHP 20 sessions (-0.57%) despite short-horizon positives.
- Bear-regime breakout and SMA signals were materially negative at longer
  horizons in pooled indicator diagnostics.
