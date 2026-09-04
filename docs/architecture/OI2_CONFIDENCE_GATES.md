# OI2 Confidence Gates

The gate engine always returns exactly 30 gates: five each for Data, Trend,
Momentum & volatility, Volume & liquidity, News & macro, and Decision.

Outcomes are `SUPPORTS_BUY`, `SUPPORTS_SELL`, `NEUTRAL`, or `UNAVAILABLE`.
Unavailable evidence is counted separately and is never treated as neutral or
supporting. The summary is evidence support—not win probability, calibrated
confidence, or expected return. Order-book, volume, researcher-quorum, and trade
risk/reward gates remain unavailable until genuine components supply them.
