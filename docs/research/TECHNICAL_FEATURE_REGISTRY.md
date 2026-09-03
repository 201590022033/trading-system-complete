# Technical Feature Registry

`technical_feature_registry.py` is the HR4 modular catalogue for deterministic,
independently evaluable research features. It wraps the existing expanded
indicator layer instead of duplicating its calculations and reserves explicit
entries for HR5/HR6 implementations.

Every definition records name, family, required inputs, default parameters,
minimum warm-up, supported timeframes, output fields, interpretation notes,
capability requirements, feature version, implementation source and honest
implementation status. `compute()` returns a shadow-only availability result;
planned features cannot be called as if implemented.

## Current executable entries

- Trend: MACD and ADX/DMI.
- Volatility: ATR and Bollinger/z-score.
- Momentum/context: aligned relative strength.
- Volume/flow: relative volume and median dollar volume.
- Structure/intraday: session VWAP and opening range, only with declared
  intraday OHLCV.

These adapters retain `research_indicators.py` capability and `as_of_index`
guards. The registry accepts an aligned benchmark series only for the relative-
strength calculation.

## Registered planned entries

The registry explicitly marks SMA/EMA structure, Aroon,
Supertrend, Parabolic SAR, continuous RSI, OHLC stochastic, ROC, Williams %R,
CCI, Keltner, realized-volatility change, OBV, MFI, Chaikin flow,
accumulation/distribution, Donchian, support/resistance, swing structure and gaps
as planned. Full Ichimoku became executable in HR5. Fibonacci context and all
specified deterministic candlestick patterns became executable in HR6 through
`structure_pattern_features.py`; they remain non-directional research context.

Fibonacci and candlestick entries are feature contexts, never unconditional
BUY/SELL signals. No registry feature contributes to production/default weights.
The machine-readable catalogue is
`analysis/results/technical_feature_registry.json`.
