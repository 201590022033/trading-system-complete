# ADR 0041: Dated Swing diagnostics and display-only averages

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Accepted 2026-10-04. Owner requests averaging missing days with appropriate flags.

Existing histories contain damaged individual OHLC observations. Preserve raw
charts and frozen Swing formulas. Add separately versioned swing-display-quality-v1
diagnostics to new snapshots when damaged observations exist. Independent prior
10/20-bar ranges show usable real windows without silently reseeding Wilder ATR
or changing immutable strategy declarations.

For an isolated damaged observed bar, offer display OHLC means from up to five
preceding valid real observations, with source dates and ESTIMATED flags. First
observations and consecutive damaged observations remain unavailable. Estimates
never feed subsequent averages. Never invent volume. Bound dated details to ten,
retaining the total count. Exclude future bars and never alter source data.

Do not infer sessions from weekdays: holidays, suspensions and absent provider
rows need a verified calendar/source. Entirely absent sessions are not filled.
Averages are display annotations, not chart repairs, quotes or feature inputs.
Frozen ATR/policy gates remain conservative; explicitly marked estimates are
rejected by ATR and stop/target replay. Outcomes stay DATA_UNAVAILABLE. No schema
migration, provider calls, ranking/sizing changes or broker mutation.

Next: verified calendar/source coverage, then a separately versioned real-window
indicator policy with walk-forward evaluation before promotion.

Validation: 815 full safe tests pass; focused Swing coverage includes causality,
source immutability, isolated gaps, missing closes, window-specific availability,
bounded reports and estimated-path rejection. JavaScript syntax/diff checks pass.
