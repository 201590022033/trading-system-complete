# Current Milestone

**ACTIVE: M1 — Evidence/provenance contracts**

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

## M1 immediate checklist

- [ ] Inspect existing `NewsItem`, `MarketObservation`, sentiment and adapter fields.
- [ ] Define a normalized evidence record with source, URL/id, published/observed/ingested timestamps, ticker/assets and parser version.
- [ ] Add conversion adapters without replacing existing data structures.
- [ ] Add deduplication keys and tests.
- [ ] Keep current collectors and legacy signal behavior unchanged.
