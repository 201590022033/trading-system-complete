# Technical Indicator Audit

Phase: **HR0 complete**

Code baseline: `56135d6`
Scope: executable repository code, not package or documentation wish lists.

## Classification rule

- **IMPLEMENTED AND USED** means executable output contributes to the current
  legacy/adaptive score, historical signal evaluation, or current regime label.
- **IMPLEMENTED BUT UNUSED** means deterministic executable research code and
  tests exist, but the output does not contribute to current scoring.
- **AVAILABLE FROM LIBRARY** requires a declared indicator implementation from a
  dependency. The repository declares NumPy/Pandas but no TA-Lib, pandas-ta,
  `ta`, or equivalent indicator package; therefore no requested indicator is
  classified this way.
- **NOT IMPLEMENTED** means no executable calculation exists. A documentation
  mention, generic rolling primitive, or internal helper is not implementation.

All “used” scoring remains legacy/default or shadow as already documented; this
audit changes no strategy behavior.

## Existing and basic families

| Feature | Status | Exact implementation and use |
| --- | --- | --- |
| RSI | IMPLEMENTED AND USED | `SignalGenerator.calculate_rsi_signal`, 14 periods, thresholds 30/70; legacy technical weight 0.35 and backtest/evaluation use. |
| SMA | IMPLEMENTED AND USED | 5/20 SMA state with 0.1% deadband; legacy technical weight 0.30 and backtest/evaluation use. It is a state comparison, not exact-cross-only logic. |
| EMA | NOT IMPLEMENTED as a feature | Private `_ema` exists only as an internal MACD primitive; no exposed EMA value/slope/cross signal. |
| MACD | IMPLEMENTED BUT UNUSED | Research snapshot exposes EMA(12)-EMA(26), requiring 26 closes. No signal line/histogram and no score contribution. |
| Stochastic | IMPLEMENTED AND USED | Simplified 14-close range oscillator, thresholds 20/80; legacy weight 0.15 and backtest/evaluation use. It does not use high/low bars. |
| Breakout | IMPLEMENTED AND USED | Current close versus prior high/low of a 20-close window; legacy weight 0.20 and backtest/evaluation use. |
| Momentum / ROC | IMPLEMENTED AND USED only as regime context | `trend_return` is trailing 20-session price return in `regime-v1`; no standalone momentum/ROC indicator or score contribution. |
| ADX / DMI | IMPLEMENTED BUT UNUSED | Research-only ADX, +DI and -DI require 29 OHLC bars at default period 14; capability gated and not fused. |
| ATR | IMPLEMENTED BUT UNUSED | Research-only mean true range over 14 periods, requiring 15 OHLC bars; capability gated and not fused. |
| Bollinger Bands | IMPLEMENTED BUT UNUSED | 20-close mean ±2 population standard deviations plus close z-score; research-only. |
| Volume indicators | IMPLEMENTED BUT UNUSED, limited | Relative volume and median dollar volume exist behind volume capability. OBV/MFI/CMF/A-D do not. |
| Relative strength | IMPLEMENTED BUT UNUSED | Difference between aligned asset and benchmark returns over the configured period; benchmark capability required. |
| Realized volatility | IMPLEMENTED AND USED as regime context | Population standard deviation of trailing close returns drives `regime-v1`; not a direct trading-score factor. |
| Session VWAP / opening range | IMPLEMENTED BUT UNUSED | Research-only and explicitly gated on intraday OHLCV. Daily Yahoo history cannot activate these features. |

## Trend and structure families

| Feature | Status | Audit note |
| --- | --- | --- |
| Ichimoku Cloud | NOT IMPLEMENTED | No deterministic model or feature output. |
| Tenkan-sen | NOT IMPLEMENTED | — |
| Kijun-sen | NOT IMPLEMENTED | — |
| Senkou Span A/B | NOT IMPLEMENTED | — |
| Chikou Span | NOT IMPLEMENTED | — |
| Donchian Channels | NOT IMPLEMENTED | The existing close breakout resembles a channel event but does not expose Donchian bounds or registry semantics. |
| Keltner Channels | NOT IMPLEMENTED | — |
| Supertrend | NOT IMPLEMENTED | — |
| Parabolic SAR | NOT IMPLEMENTED | — |
| Aroon | NOT IMPLEMENTED | — |
| Williams %R | NOT IMPLEMENTED | — |
| CCI | NOT IMPLEMENTED | — |

## Price levels and market structure

| Feature | Status | Audit note |
| --- | --- | --- |
| Fibonacci retracements | NOT IMPLEMENTED | — |
| Fibonacci extensions | NOT IMPLEMENTED | — |
| Pivot points | NOT IMPLEMENTED | — |
| Previous high/low structures | IMPLEMENTED AND USED only inside breakout | Prior 19 close extrema are compared with the current close; values are not separately exposed. |
| Rolling support/resistance | NOT IMPLEMENTED | — |
| Swing-high/swing-low detection | NOT IMPLEMENTED | — |
| Higher-high/lower-low structure | NOT IMPLEMENTED | — |
| Breakout/retest structure | NOT IMPLEMENTED | A breakout event exists; retest state and confirmation do not. |
| Price-gap features | NOT IMPLEMENTED | — |

## Volume and flow detail

| Feature | Status |
| --- | --- |
| Relative volume | IMPLEMENTED BUT UNUSED |
| Median dollar volume | IMPLEMENTED BUT UNUSED |
| On-balance volume (OBV) | NOT IMPLEMENTED |
| Money Flow Index (MFI) | NOT IMPLEMENTED |
| Chaikin Money Flow | NOT IMPLEMENTED |
| Accumulation/distribution | NOT IMPLEMENTED |
| Volume-price confirmation | NOT IMPLEMENTED |

## Candlestick patterns

The repository has no deterministic candlestick-pattern engine. Every requested
pattern is **NOT IMPLEMENTED**:

| Pattern | Status | Pattern | Status |
| --- | --- | --- | --- |
| Hanging Man | NOT IMPLEMENTED | Hammer | NOT IMPLEMENTED |
| Inverted Hammer | NOT IMPLEMENTED | Shooting Star | NOT IMPLEMENTED |
| Doji | NOT IMPLEMENTED | Dragonfly Doji | NOT IMPLEMENTED |
| Gravestone Doji | NOT IMPLEMENTED | Bullish Engulfing | NOT IMPLEMENTED |
| Bearish Engulfing | NOT IMPLEMENTED | Morning Star | NOT IMPLEMENTED |
| Evening Star | NOT IMPLEMENTED | Harami | NOT IMPLEMENTED |
| Piercing Line | NOT IMPLEMENTED | Dark Cloud Cover | NOT IMPLEMENTED |
| Three White Soldiers | NOT IMPLEMENTED | Three Black Crows | NOT IMPLEMENTED |

## Usage boundary and implications for HR1+

`research_indicators.py` is the existing additive extension point and already
provides capability flags plus an `as_of_index` no-future boundary. HR4 should
evolve that boundary into a registry rather than duplicate it. Current Yahoo
forensic inputs contain undated close-like values only, so they cannot activate
OHLC, volume, intraday, point-in-time macro, or event features.

Ichimoku, Fibonacci context, and candlestick families were previously missing.
Their absence is established here; it is not evidence that they are valuable.
No new indicator was implemented and no production/default or shadow weight,
threshold, action, or execution path changed during HR0.

## Audit method

The audit searched all Python implementation files and inspected
`data_pipeline.py`, `signal_pipeline.py`, `research_indicators.py`,
`regime_engine.py`, `backtest.py`, `evaluation.py`, their focused tests, declared
dependencies, and maintained market-intelligence documentation. Library
availability was not substituted for repository implementation.
