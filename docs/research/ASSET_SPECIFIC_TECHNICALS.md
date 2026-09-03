# Asset-Specific Technical Research

HR7 creates a common point-in-time feature dataset with 25,384 rows across NPN,
SASOL, BHP, IMPJ, SHPJ, ABSPJ, USD/ZAR, gold, Brent and the JSE All Share proxy.
It is stored at `analysis/data/hr7/asset_technical_features.csv`; coverage and
capability flags are in `analysis/results/asset_technical_availability.json`.

## Comparable technical families

Rows contain the unchanged raw technical score components, continuous RSI/SMA/
stochastic context, MACD, Bollinger z-score, ATR, ADX/DMI direction, full
displaced Ichimoku state, gap, volume, 20-session trend/volatility regimes and
equity-relative strength versus the exact-date All Share proxy. Cross-asset
Rand, VIX, DXY, nominal yield, ZAR gold/oil and PGM context is joined by exact
date without filling missing sessions.

The same field name does not imply the same learned weight. HR8 must estimate
effectiveness separately by instrument, asset class, profile, regime and
horizon. In particular:

- banks retain rate/Rand/global-risk context but no rate-vintage claims;
- Sasol retains separate Brent, Rand, volatility and technical structure;
- IMPJ retains platinum/palladium, Rand and global-risk context;
- diversified mining uses broad market, Rand and available commodity context;
- retail/offshore earners remain separate profiles;
- USD/ZAR, gold and Brent are independent assets, not equity-profile aliases.

## Capability boundaries

Gold and Brent files are continuous public futures proxies, not complete futures
datasets. Basis, open interest, term structure, calendar spreads and roll yield
are `CAPABILITY_UNAVAILABLE`. Intraday VWAP, anchored VWAP, opening range,
session momentum/volatility, genuine SSF/CFD basis and JSE breadth are also
unavailable. Daily volume is retained where the provider supplies it but is not
treated as exchange-grade derivatives flow.

All features are prefix-derived and shadow-only. The dataset contains no learned
weights, production actions or performance claims.
