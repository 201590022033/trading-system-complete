# Source Reliability and Learning Engine

## Goal
Learn **how much to trust each evidence source in context**, not whether a source is globally "good" or "bad".

## Suggested hierarchy of learned scores
`source -> source+asset -> source+sector -> source+regime -> source+horizon`, with conservative fallback to broader levels when sample counts are low.

## Minimum outcomes to record
For every directional evidence item, evaluate after configurable horizons such as intraday (when data exists), 1, 3, 5 and 20 sessions:
- signed forward return / aligned return;
- hit/miss/flat;
- maximum favorable/adverse excursion if available;
- whether the information was already reflected in an opening gap;
- sector/index-relative return.

## Score components
Start interpretable. Consider a bounded composite of:
- sample-size-adjusted directional accuracy;
- mean aligned return;
- information coefficient where suitable;
- false-positive rate;
- average lead time;
- recency weighting;
- consistency across rolling windows;
- source independence (penalize duplicated/syndicated stories counted multiple times).

Use shrinkage/Bayesian-style priors or simple minimum-sample gates before allowing extreme reliability values.

## No self-fulfilling leakage
Do not score a source using market outcomes that occurred before its actual publication/ingestion timestamp.
Deduplicate copied Reuters/SENS/headline syndication where possible.

## Output contract
Every adaptive decision should be explainable with something like:
- regime = `risk_off_high_vol` (confidence 0.77)
- sector = `gold_mining`
- technical = +0.42 (weight 0.35)
- macro/cross-asset = +0.61 (weight 0.30)
- authoritative event = +0.70 (weight 0.25)
- community sentiment = -0.10 (weight 0.10, low historical reliability)
- final adaptive score = ...
- benchmark legacy score = ...

The initial implementation should operate in shadow mode and compare against the legacy score.
