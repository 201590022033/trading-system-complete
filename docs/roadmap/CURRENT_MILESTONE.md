# Current Milestone

**ACTIVE: M6 — Adaptive fusion in SHADOW mode**

## M5 acceptance record — 2026-09-03

- [x] Added versioned ADX/DMI, ATR, MACD, Bollinger/z-score and relative-strength research features.
- [x] Added relative-volume and median-dollar-volume features behind volume capability.
- [x] Gated session VWAP/opening range behind explicit intraday OHLCV capability.
- [x] Added per-feature availability/reason metadata and an explicit as-of boundary.
- [x] Focused suite passes: 23 tests, including future-mutation no-lookahead coverage.

## M6 immediate checklist

- [ ] Add adaptive fusion beside the unchanged legacy score.
- [ ] Weight explainably by regime, market profile, reliability and feature evidence.
- [ ] Log factor contributions and legacy-vs-adaptive comparison.
- [ ] Keep default/production action on the legacy score.

## M4 acceptance record — 2026-09-03

- [x] Added immutable, versioned sector/instrument profiles covering every required group.
- [x] Moved ticker-specific legacy macro coefficients behind configurable profile selection.
- [x] Preserved legacy scoring coefficients, thresholds and clamp with characterization tests.
- [x] Added selected profile context to decision metadata as shadow-only output.
- [x] Focused suite passes: 18 tests (the previous 14 plus 4 profile tests).

## M3 acceptance record — 2026-09-03

- [x] Added transparent `regime_engine.py` with versioned `MarketRegime` output.
- [x] Added deterministic bull, bear, range, low/normal/high-volatility and risk-label tests.
- [x] Added rolling stability report with 700 observations each for NPN, SASOL and BHP.
- [x] Kept regime output research/shadow-only; production weights unchanged.

## M2 acceptance record — 2026-09-03

- [x] Added configurable in-memory `SourceRegistry` with source class and authority tier.
- [x] Added SQLite `ReliabilityStore` for source outcomes by scope and horizon.
- [x] Added conservative sample-size shrinkage toward a 50% prior.
- [x] Added duplicate outcome protection and no-lookahead timestamp validation.
- [x] Added ADR 0002 documenting the research-only boundary.
- [x] Focused suite passes: 10 tests (`test_evidence.py`, `test_legacy_scoring.py`, `test_reliability_store.py`).

## M1 acceptance record — 2026-09-03

- [x] Added additive `evidence.py` without replacing `NewsItem`.
- [x] Added stable evidence IDs from source/headline/publication time/URL.
- [x] Added provenance fields for source class/tier, timestamps, mappings, sentiment, confidence, horizon and parser version.
- [x] Added deduplication preserving first-seen order.
- [x] Added ADR 0001 documenting the compatibility decision.
- [x] Focused suite passes: 6 tests (`test_evidence.py`, `test_legacy_scoring.py`).
- [x] Network/credential-bearing scripts were not run by discovery; they remain manual-only (`test_cloud.py`, `test_ost_login.py`, browser probes).

## M0 acceptance record — 2026-09-03

- [x] Read mandatory project docs; copied the bootstrap docs into this repository.
- [x] Inspected Git state: engine and dashboard repositories were clean before M0 work.
- [x] Confirmed `.env` and browser state are ignored and `.env` is not tracked; `.env.example` contains no secret values.
- [x] Preserved existing user work; no destructive Git operations used.
- [x] Core modules compile under Python 3.12.
- [x] Added `test_legacy_scoring.py` with three characterization tests; all pass.
- [x] Restored canonical six-ticker two-year backtest; 24 report rows and finite metrics.
- [x] Recorded baseline findings in `backtest_report.md` and the indicator bible.
- [x] Committed M0 baseline artifacts.
