# ADR 0042: Local daily data, cloud Swing hypothesis research

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Accepted 2026-10-04. Owner explicitly requests local daily OHLC storage and an
online ongoing strategy research loop. Start at clean master 5bd04f1.

Reuse YahooFinanceFetcher, the canonical share/context registry, Swing technical
snapshots, conservative shadow replay, shared PAPER ledger and Ollama Cloud
transport. Add separate research profile 1.3.0; preserve all prior definitions
and canonical default 1.0.1. No legacy multi-agent strategy path is reconnected.

Local collector downloads bounded one-year completed daily ZAR histories once
per UTC collection date, stores dated files and an atomic latest snapshot under
ignored runtime/local-swing-data, and retries upload without downloading again.
Daily Windows task runs at 07:30 local time as the current interactive user,
starts missed runs when available, and ignores concurrent starts. Requires a
powered-on signed-in computer. No password is stored by the task. Raw observations
are kept; damaged OHLC is not averaged into research. Retired symbols are skipped.

Authenticated HTTPS ingress accepts at most 2MB, 34 charts and 600 bars/chart.
Identity, currency, interval, dates, observability and finite numeric fields are
validated. Real but damaged/missing fields remain visible to conservative quality
gates. Reject explicit estimates, unknown identities, future data and rollback
of source observation time. Token is generated privately, ignored locally and
sent to Railway stdin; no token is exposed by public status APIs. Snapshots and
research records reuse an isolated research-only account, without schema changes.

The full source archive stays local. Railway necessarily receives a bounded
working OHLC copy for historical evaluation: this is not an architecture with
zero price data in the cloud. LOCAL_UPLOAD makes the canonical paper worker read
that copy instead of polling Yahoo. Dashboard public quote/chart/news feeds are
separate, still on-demand cloud paths; no claim that every web price request is
moved locally. Source switch happens only after verified real upload; missing
uploads never silently switch back to Yahoo.
The paper adapter restores the existing JSE daily midnight+02 session marker so
the source-format cutover alone cannot manufacture a new completed session.
Existing conservative daily availability is next UTC midnight, so evening
collection would exclude the same day's bar. Cloud job moves to08:00 SA (06UTC),
after the07:30 local collection. SWING_WORKER_CRON_HOUR=6 makes idle status match
the actual host cron. If local startup happens after08:00, evaluation waits for
the next scheduled cloud run or explicit bounded evaluation.

Scheduled Railway worker invokes research once per run after existing jobs. One
Ollama Cloud attempt per UTC day is reserved durably before the request. Same
chart hash reuses its immutable result. No need for a continuous compute loop.
The model sees training-period indicators, five recent training OHLC observations
per instrument, baseline metrics and previous training comparisons. It cannot
see current holdout prices/statistics or run arbitrary code. Allowed hypothesis
grid: relative-volume minimum 1/1.2/1.5; RSI ceiling65/70; holding3/4/5 sessions.
Existing EMA trend, breakout/reclaim, RSI floor50, relative return, structural/
ATR stop and fixed2R conservative exit rules stay fixed. Entry filter changes
exist only in this research harness and never modify canonical policy records.
Freeze accepted or rejected proposal before testing, retaining model identity,
context hash, dataset identity, exact profile and experiment parameter version.

One chronological retrospective holdout uses the last40 observed sessions with
six purged sessions before it. Signal features use only observable histories;
entries use later closes; signals are non-overlapping per instrument. Record
sample counts, unresolved bars, gross win rate and assumed10/25/50bps costs.
Daily reuse can overlap holdouts; there is no portfolio drawdown, certified
exchange calendar, corporate-action or survivorship guarantee. ALWAYS mark
NOT_ELIGIBLE_PROSPECTIVE_WALK_FORWARD_REQUIRED; never auto-promote, resize or trade.
This is AI-assisted hypothesis refinement, not fine-tuning model weights or a
validated strategy. Empty samples remain empty, never manufactured profitability.

Next stage: real-source/calendar quality, richer exit hypotheses under separate
versioned replay contracts, prospective frozen experiment scoring, portfolio
drawdown/turnover and actual costs, followed by review before any promotion.
