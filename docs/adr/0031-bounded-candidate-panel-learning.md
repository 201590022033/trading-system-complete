# ADR 0031 — Bounded daily candidate-panel evidence

Accepted as an operational repair within the sole active demo workspace. This
supersedes the selected-only learning feedback in ADR 0029, without changing the
legacy benchmark, paper execution, or the separate shadow-runtime job model.

## Context

The v3 Railway worker schedules the daily paper cycle, not the historical
observation/decision/outcome jobs. Its v1 learning ledger recorded only Top-5
eligible LONG ideas. That cannot reveal whether selection was better than the
other screened shares, and its signal-close entry assumption was not executable
after the signal was known. Small storage was intentional after the IG tick and
full-chart incident, but the chosen sample omitted a comparison group.

## Decision

For each newly evaluated completed session, store one compact, immutable
candidate decision per screened cash share, including rank, direction,
eligibility, selected flag and a few already-computed technical, regime and
news summaries. No full bars, article text, ticks or model weights are stored.
Four subsequent completed bars are needed to label it: first later close is a
hypothetical entry, fourth later close is exit after three sessions. Deduct
declared 10 bps round-trip cost. Unselected candidates receive the same label.

Compare selected and other cash-share returns only within matched signal,
entry and exit sessions. Report an additional nonoverlapping-session count to
avoid treating overlapping holds as independent evidence. The bounded 5,000-row
query supports roughly 90+ three-session comparisons for the current small
universe; `READY_FOR_REVIEW` requires 30 nonoverlapping comparisons. This is
descriptive shadow research, not a trained return model or an accuracy claim.
The selected-only v1 outcomes remain historical but no longer affect ranking.
Actual closed paper-trade outcomes retain their existing governed learner path.

## Limits and next gate

Yahoo completed-close data provides a retrospective proxy, not an executable
quote; 10 bps may understate actual spread and slippage. Selection may be absent
on some sessions, resulting in no matched comparison. The 5,000-row cap is a
query bound, not data retention; database size must be monitored and older
evidence archived before space pressure. Do not promote a model or claim Sharpe
until there is a defined nonoverlapping cash-return series, sample counts,
uncertainty, realistic costs and walk-forward testing. ETFs and SSFs remain out
of this pipeline pending verified instrument and cost contracts.
