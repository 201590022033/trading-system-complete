# ADR 0032 — Small daily market-first decision brief

Accepted as an operational extension of the sole active demo workspace. This
evolves the existing Railway paper worker and preserves its canonical ranking,
paper broker, risk vetoes, legacy benchmark and shadow-only adaptive boundary.

## Problem

The daily worker observed only cash-share charts and returned a Top-5 list.
Selected-versus-unselected labels were useful for testing that list, but did
not capture larger market conditions or present a coherent trade/no-trade
decision. They could not establish profitability. The old persistent shadow
jobs were not connected to the daily Railway schedule.

## Decision

Once per daily paper cycle, also fetch the four already catalogued listed JSE
ETF daily charts (STX40, STXFIN, STXRES, STXIND). Freeze at most 60 timestamp/
close points for each; never admit them to ranking, sizing or execution. At the
same causal cutoff as the cash-share scan, derive 20-session ETF moves and the
fraction of observed cash shares with positive 20-session moves. Classify
SUPPORTIVE/DEFENSIVE/MIXED only when a fresh STX40 ETF series and at least six
cash shares are available. Otherwise report INSUFFICIENT_CONTEXT.

Persist one compact daily decision brief inside the existing immutable ranking
snapshot. It shows the market view, up to five legacy-ranked share ideas and
specific review/wait reasons. It may filter a review idea because of defensive
context, a currently held paper position or even one-share simulated-cash
affordability. It does not alter the canonical score, risk engine or pending
paper trade flow. It uses delayed completed closes, not executable quotes; the
cash amount is simulated, not the user's actual broker balance. The brief is
shown prominently in Portfolio and remains human-review-only.
The cycle also caches its aggregate candidate-learning summary in that snapshot
so frequent dashboard reads do not repeatedly scan thousands of outcome rows.

Candidate-panel decisions now freeze market state and sector along with the
individual candidate features. Mature matched-session outcomes report
selected-versus-other edge separately by market state, with the existing 30
nonoverlapping-session review gate. No learned adjustment is applied without
walk-forward evaluation, realistic costs, uncertainty and governance approval.

The same daily cycle also freezes at most four compact ETF benchmark decisions
and labels each only after four later completed bars: first later close is the
hypothetical entry, fourth later close the three-session exit. An independent-
session summary compares subsequent **gross** ETF moves with holding cash in
each frozen market state. This directly tests whether the broad-market view
had value, but omits actual spread/fees and cannot justify ETF trading.

## Resource and failure boundary

The additional frozen ETF payload is capped at 240 two-field bars and four
small benchmark decisions/outcomes per new completed session; duplicate-session
inputs stay compact. A missing or invalid
benchmark fails the brief closed to INSUFFICIENT_CONTEXT while cash-share paper
position management continues. ETF and SSF admission remains separate work
requiring instrument-specific spread, liquidity, fees and (for SSF) contract,
margin and expiry evidence. No live broker order path is introduced.
