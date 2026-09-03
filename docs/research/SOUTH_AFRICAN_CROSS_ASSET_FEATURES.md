# South African Cross-Asset Features

HR3 derives 84 research columns across 2,781 union-calendar dates in
`analysis/data/hr3/cross_asset_features.csv`. The manifest records version,
coverage and file hash.

## Feature families

Each available market series exposes raw close, 1/5/20-observation returns,
20-observation realized volatility, trend deviation and z-score. USD/ZAR also
has an explicit 20-observation Rand regime: rising USD/ZAR beyond 3% is
`rand_weakening`, falling beyond 3% is `rand_strengthening`; missing history
stays missing rather than neutral.

Exact-date interactions provide USD gold and `gold_zar = gold_usd × USDZAR`,
plus Rand-denominated Brent, platinum and palladium levels and 5/20-observation
returns. Brent direction, momentum, volatility and Rand translation remain
separate. Gold likewise remains separate from DXY, nominal yields, VIX and a
continuous global-risk composite. No single feature is assigned a universal
bullish/bearish sign.

## Point-in-time rules

All rolling calculations use only current and earlier observations. Inputs are
joined on exact labelled dates without forward filling. A feature row is
available no earlier than the next-day boundary inherited from HR2. Missing
market holidays or history produce nulls. The future-mutation test verifies that
changing later inputs cannot change an earlier feature row.

These are descriptive features, not signals or promoted weights. SARB rates, SA
yield curves, CPI vintages, surprises and real yields remain unavailable and are
not imputed. Commodity futures are continuous proxies and cannot establish
futures term structure, roll yield or executable basis.
