# Data readiness check — 6 October 2026

The collection/upload/worker path is operating, but the saved prices are incomplete. This check recovered Sasol prices separately and kept data acceptance gates intact.

- Windows collector last ran 6 October 07:30:30 SAST, result 0; next run 7 October 07:30:30 SAST.
- Railway upload observed at 05:30:15 UTC; worker heartbeat 06:01:10 UTC and next scheduled 7 October 06:00 UTC.
- All 21 saved charts end on 2 October. Across 5,229 daily rows, 876 have invalid OHLC. Sasol has 19; Satrix40 has one (21 April).
- Fresh direct Yahoo checks for SOL.JO and STX40.JO still omit 5 October and expose the unfinished 6 October session. The collector correctly excludes it. Refreshing today would not resolve the missing completed day.
- The previously captured IRESS SOL.JSE daily table contains 250 valid completed OHLCV bars through 5 October. All 249 overlapping closes match Yahoo. All overlapping volumes differ, so the recovery retains the complete IRESS feed separately rather than mixing Yahoo volume with IRESS prices.
- All 19 invalid Sasol dates have valid observed alternatives. The separate recovery yields EMA20/50, Wilder RSI/ATR and prior 10/20-session structure. Its snapshot remains PARTIAL with ALIGNED_BENCHMARK_UNAVAILABLE because STX40 lacks 5 October. Satrix40's one old OHLC defect is distinct from this latest-session alignment gap; benchmark relative return uses closes.
- IRESS browser showed a blank page after reload; the OST browser check timed out. No current authenticated download was acquired. Moneyweb/SENS and issuer announcements are useful corporate-action evidence, but do not replace missing price bars. Previous Alpha search did not establish a verified JSE mapping. No additional paid/LLM probes were made.
- Live evidence remains 25 pending and zero matured at each 3/4/5-session horizon, with zero independent selected/control outcomes and zero valid AI holdout samples. A 5 October close can be the first post-decision entry reference, not a completed 3-session return. No inferred session or unfinished bar is used to mature outcomes.

## Repeating the offline check

From the main repository:

```powershell
.\.venv\Scripts\python.exe scripts/check_swing_data_readiness.py --iress-sasol <captured-SOL-daily-table.csv> --output <report-directory>
```

The command reads the existing dataset and optional Sasol export, writes Coverage-audit.json and Sasol-source-recovery.json, and does not contact providers, upload data, run workers or call a model. The source file hash identifies the captured artifact; check time is expressly not its historical capture/publication time. Raw source evidence is retained outside Git.

## Next dependency

Acquire a completed 5 October STX40 benchmark row and dated provider definitions for adjustment/actions and volume, then introduce any alternative feed through a separately versioned provenance-preserving dataset contract. Until then, the recovered file remains offline research evidence, the cloud worker continues its existing schedule and B5 remains PARTIAL_CLOSED. Continue accumulating actual later sessions; only evaluate baseline/AI performance after valid mature samples exist.

## Verification

Five new parser/coverage tests plus 44 existing technical/research/policy tests pass. Tests reject wrong product identity, closing-price disagreements, invalid source OHLC and duplicate sessions, preserve original inputs and exclude unfinished sessions. Existing SQLite/PostgreSQL causal tests confirm exact 3/4/5-session maturity, negative costs-adjusted outcomes, control cohorts and retry deduplication. Full safe suite: 937 tests passed in 89.156 seconds. All 54 protected checks passed. No live or model calls occurred during tests.
