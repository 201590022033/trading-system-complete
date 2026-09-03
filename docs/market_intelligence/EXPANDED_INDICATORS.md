# Expanded Indicator Research Layer

`research_indicators.py` adds `expanded-indicators-v1` beside the legacy
`SignalGenerator`. It does not contribute to production scores.

## Feature availability

Every feature returns an `available` flag, optional value and reason. Inputs
declare `DataCapabilities` rather than allowing the calculator to infer richer
data from close prices.

- Close history: MACD, Bollinger bands and close z-score.
- OHLC: ATR, ADX, +DI and -DI.
- Aligned benchmark: relative strength over the configured period.
- Volume: relative volume and median dollar volume.
- Explicit intraday OHLCV: session VWAP and opening-range high/low.

Daily Yahoo close-like data must not claim intraday capability. Missing inputs
produce unavailable features; inconsistent declared capabilities raise an
error rather than silently substituting closes.

## Time boundary

The calculator slices every input at `as_of_index` before calculating values.
Tests mutate all later bars and verify the earlier snapshot is unchanged. This
is the contract backtests must use when evaluating the expanded layer.
