# Gap Analysis

## Preserve
- `JSEDataAdapter` abstraction and existing source collectors.
- `UnifiedDataPipeline` concept.
- current technical `SignalGenerator` as legacy feature provider.
- `JSESignalEngine` legacy score as benchmark.
- Bull/Bear/General -> Trader -> Risk -> Manager -> Executor governance.
- existing walk-forward philosophy.
- Standard Bank OST work, isolated and read-only.

## Refactor gradually
- hard-coded ticker macro rules -> sector/instrument profiles;
- fixed source/technical weights -> versioned adaptive fusion;
- aggregated sentiment without provenance -> normalized evidence records;
- one report horizon -> multi-horizon, regime-segmented evaluation.

## Add
- regime engine;
- source reliability store/scoring;
- source deduplication/provenance;
- sector and instrument context;
- wider technical feature library with data-capability checks;
- transaction-cost/liquidity awareness;
- legacy/adaptive shadow comparison and explainability.

## Explicitly avoid
- wholesale framework rewrite;
- new UI work before signal architecture is evidence-backed;
- end-to-end black-box model that directly decides trades;
- private social scraping with user passwords;
- live broker execution during this roadmap;
- adding five collectors in parallel before normalized evidence contracts exist.
