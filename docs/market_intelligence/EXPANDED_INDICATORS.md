# Expanded Indicator Research Layer

## Current context — 5 October 2026

The original feature/profile contract below is retained as its delivery checkpoint. Existing regime and feature registries are reused. Separate Swing 1.1.0 now adds EMA20/50, Wilder RSI/ATR14, relative volume and independent 3/4/5-session labels; 1.2.0 adds cash-only daily policy replay and 1.3.0 adds bounded AI hypothesis comparisons. These are research lanes and do not change default ranking weights. Invalid OHLC, verified sector/FX/commodity context, actual event availability and prospective evaluation remain admission gates. The complete local six-family engine and 30-minute radar are proposed. See [current state](../CURRENT_STATE.md), [Swing readiness](../research/SWING_NARRATIVE_READINESS.md) and [document index](../DOCUMENTATION_INDEX.md).


---

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
