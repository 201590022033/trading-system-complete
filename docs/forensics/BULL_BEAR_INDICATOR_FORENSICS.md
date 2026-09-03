# Bull/Bear Indicator Forensics

This analysis evaluates only the four indicators that actually generated legacy
technical signals. Figures are pooled across six tickers, use overlapping
close-to-close outcomes, and are gross of costs; they are diagnostic, not
standalone strategies.

## Findings

- RSI mean-reversion was strongest in bear-labelled observations: mean aligned
  returns were 1.70% at 5 sessions and 3.03% at 20 sessions (413/409 signals).
  This contradicts a blanket rule that counter-trend RSI is always harmful, but
  pooling and overlap make it a WATCH finding.
- Stochastic in bear regimes was also positive at 3/5/20 sessions (0.69%, 1.06%,
  2.06%) but negative at one session (-0.033%). Its useful horizon appears
  multi-day rather than next-session.
- SMA in bull regimes was weak at short horizons and positive at 20 sessions
  (0.69%); SMA in bear regimes was negative at 1/3/5/20 and worst at 20
  (-1.71%). This is consistent with lag and failed-rally exposure.
- Breakout was constructive in ranges at 3/5 sessions (0.65%/1.17%, 97 signals)
  and destructive in bears at 3/5/20 (-1.21%/-1.68%/-3.62%, about 440 signals).
  The “range breakout” result may identify transitions, but regime-transition
  timing must be tested before interpreting it causally.
- RSI in ranges had only 58 signals and was negative at 3/5/20. Textbook
  range-mean-reversion was not supported in this sample.

## Unavailable or unevaluated

MACD and Bollinger/z-score values can be calculated from closes but were never
converted into signals or fused in M10; inventing thresholds here would tune the
subject. ATR/ADX require OHLC, and volume/relative strength require data absent
from the frozen experiment. Momentum beyond the existing SMA/breakout encoding
is likewise not a defined M10 signal. These are `INSUFFICIENT DATA`.

No multiple-testing correction was used. The indicator table in
`forensic_summary.json` is descriptive and should be validated with non-
overlapping outcomes, per-ticker splits and a preregistered follow-up.
