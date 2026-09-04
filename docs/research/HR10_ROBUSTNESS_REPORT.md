# HR10 Robustness and Admission Report

## Decision

HR10 admits **0 of 40** instrument × horizon cells for continued shadow
evaluation. All 40 are `REJECT`; none lack the 30 completed-trade minimum.
This is an unfavorable but valid result. HR9 remains shadow-only and no global
or production promotion is authorized.

## Predeclared design

- Targets remain independent at 1, 3, 5 and 20 sessions.
- Three expanding temporal folds use a purge of H sessions and an embargo of H
  sessions for target horizon H. Training labels therefore finish before the
  protected test boundary.
- Overlapping forward-return rows remain available in the immutable HR9 report,
  but HR10 admission uses non-overlapping completed trades: information cutoff
  and entry at close[t], exit at close[t+H], signals inside the holding interval
  ignored, long/short supported, flat skipped, and two turnover units charged
  per completed round trip.
- Costs: 0, 10 and 25 bps per turnover unit. Primary admission cost: 10 bps.
- Replayable sensitivity grid declared before final evaluation: HR9 action
  thresholds 0.30, 0.35 and 0.40. Other learner parameters cannot honestly be
  varied from a frozen decision artifact without retraining and are deferred.
- Uncertainty: deterministic moving-block bootstrap with block length
  `round(sqrt(trades))`, 1,000 resamples, seed 20260904.
- Multiple testing: Benjamini–Hochberg FDR at 5% over the 40 primary HR9
  instrument × horizon hypotheses. This controls expected false discoveries
  while retaining more power than family-wise Holm control.

## Admission gates

The exact machine-readable rules are in `hr10_robustness.py` and the result
artifact. Admission requires at least 30 completed trades, positive mean net
return at 10 bps, positive 95% block-bootstrap lower bound, positive results in
at least two of three folds, drawdown no worse than 25%, positive 25-bps stress,
positive results for at least two of three thresholds, adjusted p ≤ 0.05, and
outperformance of legacy under identical execution semantics.

Across the 40 rejected cells: all fail the positive uncertainty bound,
drawdown, and multiple-testing gates; 38 fail 25-bps cost stress; 35 have
non-positive primary net performance; 34 fail threshold stability; 33 fail fold
stability; and 25 fail legacy comparison. These are overlapping failure counts.

## Reproducibility

Run offline with `.venv/bin/python hr10_robustness.py`. The result records input
hashes, code commit, configuration, seed, timestamp, counts, raw/adjusted
p-values and every grid result in `analysis/results/hr10_robustness.json`.
The source HR9 artifacts are read-only and unchanged.
