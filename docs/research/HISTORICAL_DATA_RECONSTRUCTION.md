# HR2 Historical Data Reconstruction

## Frozen retrieval

`historical_reconstruction.py` froze permitted public daily history on
2026-09-03 through the repository's existing `yfinance` dependency. Six JSE
equities and ten cross-asset proxies are stored as normalized CSV under
`analysis/data/hr2/`; exact row counts, date bounds, SHA-256 hashes, symbols and
roles are in `analysis/results/historical_feature_availability.json`.

The six JSE equities, All Share proxy, USD/ZAR, VIX, S&P 500, DXY, US 10-year
nominal-yield proxy, Brent, gold, platinum and palladium are available. Most
begin in January 2016. BHP's current `BHG.JO` symbol begins on 2022-01-31, so no
pre-listing continuity is invented.

## Timestamp treatment

Yahoo supplies daily labelled dates, not an auditable original dissemination
timestamp. HR2 conservatively marks a labelled daily bar available at 00:00 UTC
on the next calendar day. This prevents same-labelled-day close leakage but is
still an approximation; strategies needing exchange-close precision must use a
source with timestamp guarantees. Missing sessions are not forward-filled.

Each row retains raw open, high, low, close, adjusted close and volume plus
event, availability and retrieval times. Raw files are immutable research
snapshots identified by manifest hashes. Yahoo adjustments and history can be
revised, so a later retrieval is a new dataset version rather than a replacement.

## Source and capability boundary

Yahoo is an existing Tier-2 research source in `DATA_SOURCES.md`; these files are
research inputs, not licensed exchange-grade or redistribution-grade market
data. The JSE index and futures symbols are proxies, and commodity futures are
continuous vendor series with roll/adjustment limitations. They do not supply
term structure, basis, open interest quality, or executable prices.

The following remain `CAPABILITY_UNAVAILABLE`:

- SARB policy-rate release vintages;
- South African government curve/yield vintages;
- Stats SA CPI release-vintage values;
- licensed economic-surprise history;
- a separately verified US real-yield series;
- JSE futures/SSF/CFD basis, open interest, term structure and intraday data.

No current revised macro observation is treated as historically known. HR3 may
derive only point-in-time features from the frozen available market series.
