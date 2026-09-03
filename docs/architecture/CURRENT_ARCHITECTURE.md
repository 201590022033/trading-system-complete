# Current Architecture — Observed Repository Baseline

This document describes the uploaded repository, not an aspirational redesign.

## Existing core modules

### `jse_adapter.py`
Current integration boundary for:
- Yahoo Finance price/history data;
- Finnhub price support;
- NewsAPI news;
- Moneyweb SENS republication parsing;
- Moneyweb RSS;
- Reddit public/API collection;
- Standard Bank OST adapter/browser integration;
- JSE ticker mappings.

### `data_pipeline.py`
Current unified observation layer:
- sliding price/VWAP buffers;
- SMA trend signal;
- RSI;
- breakout detection;
- simplified stochastic oscillator;
- news aggregation;
- `MarketObservation` and portfolio data structures.

### `sentiment_analyzer.py`
Current macro/news analysis:
- deterministic mention detection;
- keyword sentiment fallback;
- optional local/cloud Ollama-compatible LLM analysis;
- macro concepts including ZAR, GOLD, OIL and other asset/ticker mappings;
- `MacroSentimentScanner`.

### `signal_pipeline.py`
Current direct signal fusion:
- technical score weights: RSI 0.35, SMA 0.30, breakout 0.20, stochastic 0.15;
- combined score: 0.60 technical + 0.30 sentiment + bounded macro adjustment;
- hard-coded ticker macro overlays for weaker/stronger rand, gold and oil exposure;
- buy/sell thresholds around +/-0.35.

This fixed weighting is the primary target for **evolution**, not deletion.

### `merged_simulation.py`
Existing multi-agent governance:
- BullishResearcher;
- BearishResearcher;
- GeneralResearchAgent;
- LLMTraderAgent;
- aggressive/neutral/conservative RiskAgents;
- ManagerAgent;
- ExecutionAgent;
- portfolio/decision logging and labels.

### `backtest.py`
Existing walk-forward technical indicator research:
- close-only historical sequence;
- signal at t evaluated at t+horizon;
- RSI/SMA/breakout/stochastic observations;
- win rate and average aligned/forward returns;
- explicit rule that research does not automatically alter production weights.

### `evidence.py`
Additive provenance boundary introduced in M1:
- `EvidenceRecord` wraps existing `NewsItem` values;
- stable evidence IDs support deduplication;
- source identity/class/tier, timestamps, mappings, sentiment, confidence and parser version are preserved for future reliability learning.

### `regime_engine.py`
Research-only regime-v1 classifies trailing close history into independent labels:
- trend: bull, bear or range;
- volatility: low, normal or high;
- risk: risk_on, neutral or risk_off;
- version, confidence and feature snapshot are included in `MarketRegime`.
`regime_backtest.py` measures rolling-label stability without changing production weights.

### `market_profiles.py`
Research/shadow sector and instrument context introduced in M4:
- immutable, versioned profiles for required instrument and sector groups;
- configurable, case-insensitive ticker-to-profile selection;
- neutral single-stock fallback for unknown tickers;
- legacy macro coefficients centralized without changing signal defaults;
- selected profile identity included in signal decision metadata.

### `research_indicators.py`
Research-only expanded feature layer introduced in M5:
- close-based MACD and Bollinger/z-score;
- OHLC-gated ATR and ADX/DMI;
- benchmark-gated relative strength and volume-gated liquidity features;
- intraday OHLCV-gated session VWAP and opening range;
- explicit unavailable reasons and an `as_of_index` no-lookahead boundary.

### `adaptive_fusion.py`
Explainable `adaptive-fusion-v1` introduced in M6:
- normalized factor contributions with regime/profile multipliers;
- minimum-sample-gated, bounded reliability multipliers;
- full legacy/adaptive comparison in signal metadata;
- shadow-only output; public signal score and action remain legacy-controlled.

### `evaluation.py`
M7 walk-forward evaluation layer:
- 1/3/5/20-session legacy, component and adaptive ablations;
- configurable spread, fee and slippage costs;
- win-rate intervals, aligned/net returns, turnover, drawdown and close-path MFE/MAE;
- trend, volatility and profile segmentation with minimum-sample flags;
- explicit unavailable contextual series and prefix-only decision state.

### `source_catalog.py`
M8 policy boundary for specialist/community sources:
- independent enable/status/access metadata and polling intervals;
- authority-tier provenance normalization into `EvidenceRecord`;
- conversion into the existing reliability `SourceRegistry`;
- only existing permitted Moneyweb/SENS routes enabled by default;
- licensed, permission-dependent and prohibited automation disabled explicitly.

## Existing strengths
- Good separation between ingestion, observations, signal fusion and governance.
- Real SA/JSE adaptation already underway.
- Existing backtest philosophy supports evidence-gated development.
- Existing broker work can remain isolated/read-only.

## Existing gaps
- Adaptive contextual weights exist only in shadow mode and require evaluation.
- Regime classifier informs shadow fusion but does not affect production output.
- Profiles exist, but sector/regime-specific expanded indicator weighting is not yet implemented.
- No normalized source-provenance/evidence store.
- No source reliability history by sector/ticker/regime/time horizon.
- Transaction costs are configurable in research evaluation; derivative spread/liquidity data remains unavailable.
- Expanded features exist in research mode but are not yet fused or historically evaluated.
- Legacy macro coefficients are explicit profile configuration; richer conditional macro features remain unimplemented.
