# Market Regime Engine

## Current context — 5 October 2026

The original feature/profile contract below is retained as its delivery checkpoint. Existing regime and feature registries are reused. Separate Swing 1.1.0 now adds EMA20/50, Wilder RSI/ATR14, relative volume and independent 3/4/5-session labels; 1.2.0 adds cash-only daily policy replay and 1.3.0 adds bounded AI hypothesis comparisons. These are research lanes and do not change default ranking weights. Invalid OHLC, verified sector/FX/commodity context, actual event availability and prospective evaluation remain admission gates. The complete local six-family engine and 30-minute radar are proposed. See [current state](../CURRENT_STATE.md), [Swing readiness](../research/SWING_NARRATIVE_READINESS.md) and [document index](../DOCUMENTATION_INDEX.md).


---

## Objective
Classify context before selecting/weighting indicators.

## Initial interpretable regimes
Keep the first version deterministic and testable:
- trend: bull / bear / range;
- volatility: low / normal / high;
- risk: risk-on / neutral / risk-off;
- rand: strengthening / neutral / weakening;
- commodity sub-regimes: gold strength, oil inflation/energy shock, PGM/resources strength.

Do not force one mutually exclusive mega-label; a feature vector or multiple labels is preferable.

## Candidate features
- J200 trend slope/returns;
- ADX or trend-strength proxy;
- realized volatility / ATR percentile;
- USD/ZAR trend/volatility;
- gold, Brent and PGM trends;
- VIX/risk proxy;
- global equity trend;
- SA/US yield proxies where available.

## Development rule
Version 1 is transparent thresholds calibrated from historical distributions. Later versions may learn boundaries if walk-forward evidence justifies it.

## Output
A `MarketRegime` object should include labels, feature snapshot, confidence and version. Signal fusion must log the regime used.
