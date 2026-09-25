# ADR 0029 — Lean daily swing learning after Railway storage incident

Accepted 2026-09-25 as an operational repair within the sole active demo
workspace.

## Context

The Railway PostgreSQL volume reached its 500 MB limit. Read-only inspection
showed that 149,303 GER40 streaming observations occupied 203 MB and that 1,295
five-minute paper inputs repeatedly embedded full chart histories, producing
438 MB of logical chart JSON and 126 MB of compressed TOAST storage. The actual
learning ledgers contained no shadow decisions, labelled outcomes, adaptive
updates or reliability outcomes. The disposable test data was explicitly reset;
the schema and source-policy configuration were retained.

The intended user workflow is no longer intraday CFD trading. It is research on
fully funded JSE cash shares, with listed ETFs remaining a future candidate and
SSFs remaining blocked until their contracts and costs are verified. The useful
decision horizon is approximately three to four completed sessions.

## Decision

`canonical-paper-loop-v2` is a daily-close, long-only PAPER model. Its Railway
schedule is one UTC-day bucket rather than one five-minute bucket. Each retry
input retains at most 60 completed daily timestamp/close/volume points per
instrument; unused OHLC fields and longer duplicated histories are discarded.

For learning, the worker records at most the ranked Top 5 LONG candidates once
per instrument and completed source bar. A compact record contains identity,
decision and bar clocks, entry close, direction, rank, regime/version lineage,
declared three-session horizon and a 10 bps research cost assumption. It never
contains a copied chart history.

After three later completed bars exist, the worker records one immutable outcome
with exit close, gross return, declared cost, net return and WIN/LOSS/FLAT label.
These outcomes adapt into the existing `ContextualEffectivenessLearner` as
`ranked_long_3_session / ranked-long-swing-v1`. Sparse evidence is retained, but
the existing 30-sample gate and neutral-prior shrinkage remain unchanged. Only
after that gate can the research effectiveness component alter comparative M13
ranking support. It cannot alter legacy signal weights, execute a broker order,
or claim profitability.

Simulated positions normally remain open for three completed sessions unless a
daily-close stop/target observation or seven-day safety expiry occurs first.
This is not an intrabar stop guarantee.

IG streaming remains a separate, default-disabled experiment and is not part of
this loop. ETFs remain chart-only and SSFs remain blocked pending instrument,
multiplier, expiry, margin, liquidity and cost evidence.

## Consequences

- A useful sample is one compact decision plus one matured outcome, not ticks.
- Global fallback can become available after 30 matured candidates; an
  instrument-specific cell still requires 30 outcomes for that instrument.
- One year is bounded to roughly 250 scheduled inputs and no more than 1,250 new
  decision/outcome pairs before deduplication, rather than continuous ticks.
- The 500 MB Railway volume is treated as a design constraint, not enlarged to
  hide unbounded collection.
- Accuracy, profitability and promotion remain unclaimed until sufficient
  walk-forward and live-shadow evidence exists.
