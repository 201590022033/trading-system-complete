# Fibonacci and Candlestick Context

HR6 adds deterministic structure features in `structure_pattern_features.py`.
They are research observations, never direct orders.

## Fibonacci

A preceding swing is defined from the highest high and lowest low in the prior
window, explicitly excluding the decision bar. Their temporal order determines
upswing/down-swing orientation. Retracement levels 23.6%, 38.2%, 50%, 61.8% and
78.6% are exposed with nearest-level distance, trend, volatility,
support/resistance and optional volume confluence. `automatic_action` is always
null. This permits later tests of levels alone versus contextual combinations.

## Candlesticks

The engine exposes Hanging Man, Hammer, Inverted Hammer, Shooting Star, Doji,
Dragonfly/Gravestone Doji, bullish/bearish Engulfing, Morning/Evening Star,
Harami, Piercing Line, Dark Cloud Cover, Three White Soldiers and Three Black
Crows. Mathematical body/wick/range rules are accompanied by preceding trend,
distance to rolling support/resistance, realized volatility and optional volume
confirmation.

Patterns at `t` have no next-bar confirmation. A caller may later evaluate the
same pattern with `pattern_index=t` and `as_of_index>=t+1`; only then is
confirmation available. Tests verify this boundary and future mutation
invariance. Pattern definitions are explicit v1 hypotheses whose parameter
sensitivity and economic value must be assessed out of sample; visual LLM
judgment is not used.
