# OI2 Confidence Gates

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

The current dashboard has six sections including backend-populated Trading Strategies and the canonical Top-5. Older multi-agent/mock/merge designs remain historical context; they do not describe the default ranking path. Paper/connected cash and self-reported trades stay separate. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

The gate engine always returns exactly 30 gates: five each for Data, Trend,
Momentum & volatility, Volume & liquidity, News & macro, and Decision.

Outcomes are `SUPPORTS_BUY`, `SUPPORTS_SELL`, `NEUTRAL`, or `UNAVAILABLE`.
Unavailable evidence is counted separately and is never treated as neutral or
supporting. The summary is evidence support—not win probability, calibrated
confidence, or expected return. Order-book, volume, researcher-quorum, and trade
risk/reward gates remain unavailable until genuine components supply them.
