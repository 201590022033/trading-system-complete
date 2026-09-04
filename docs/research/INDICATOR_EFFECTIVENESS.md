# Indicator Effectiveness Learning

HR8 adds `indicator_effectiveness.py`, an interpretable research learner over
the frozen HR7 dataset. The machine output contains 2,471 indicator × instrument
× profile × trend regime × volatility regime × horizon rows; 1,688 meet the
30-observation gate. There are 320 instrument/indicator/horizon walk-forward
weight traces summarized in `analysis/results/indicator_effectiveness.json`.

## Estimation contract

- Horizons: 1, 3, 5 and 20 observations.
- Cost: 10 bps per unit of signal-state turnover.
- Uncertainty: 95% Wilson hit-rate interval.
- Shrinkage: 20-observation neutral 50% prior.
- Gate: fewer than 30 active observations always returns reliability weight 1.0.
- Stability: temporal-half sign agreement is required for full influence.
- Recency: 252-observation half-life diagnostic.
- Bound: mature research reliability remains between 0.5 and 1.5.

Walk-forward weights at decision index `t` include an earlier signal outcome
only when its full horizon has elapsed. Tests mutate future outcomes and verify
that earlier weights remain unchanged. These are research weights only;
production/default weights remain frozen.

HR9 recovery identified and corrected an inconsistency between HR8's batch
turnover cost and its walk-forward accumulator. Both now use 10 bps per unit of
originating signal-state turnover. HR8 and HR9 also share the authoritative
versioned definitions in `technical_signals.py`; the evidence contract version
remains `indicator-effectiveness-v1` because its documented intended semantics
did not change.

## Indicators evaluated

The first learning pass covers legacy RSI, SMA, breakout and stochastic;
continuous MACD direction; Bollinger mean reversion; ADX-filtered DMI; and full
Ichimoku cloud direction. Positive and negative cells vary materially by asset,
regime and horizon. For example, some 20-day NPN bull/high-vol trend cells are
positive while NPN RSI/stochastic cells in the same broad context are negative;
IMPJ also contains both positive trend-following and damaging mean-reversion
cells. This supports conditional evaluation but is not yet out-of-sample proof.

The table intentionally retains weak and harmful cells. Attractive extrema are
multiple-tested, overlapping and in-sample; HR11 must raise the admission bar.
Fibonacci and candlestick conditional performance is evaluated in later matched
research rather than assigned a weight from pattern definitions alone.
