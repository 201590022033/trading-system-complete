# Market Regime Engine

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
