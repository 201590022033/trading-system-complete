# HR11 completion report — 2026-09-06

The short-term multi-instrument research layer is implemented, tested and
research/shadow-only. All stages HR11.0–HR11.14 are complete. This establishes a
working offline research pipeline, **not demonstrated trading performance or a
new live market-data service**.

## Baseline and scope

Work started on `master` at `3762f9b3966e012d6a050345634f3003094bbcaa`.
The baseline passed 114 safe offline tests. The pre-existing empty file with a
quoted Windows Downloads pathname was preserved and excluded from commits.
`.env` and credentials were not read or committed. No broker requests or live
orders were made. The referenced `MASTER_VSCODE_AGENT_PROMPT.md` remains absent;
the owner request is preserved verbatim in `docs/roadmap/HR11_REQUEST.md`.

The owner-requested milestone transition is recorded in ADR 0021. OI3 remains
**deferred, incomplete**, with its AI-provider and public-source work preserved in
`CURRENT_MILESTONE.md`. Existing dashboard charts, current public feeds and daily
research were not replaced. No successor milestone has been activated.

## Implemented stages

| Stage | Outcome | Focused/related tests at stage boundary |
|---|---|---:|
| HR11.0 | Design, seven ADRs, immutable baseline | 114 |
| HR11.1 | Underlying/target/instrument identity registry | 16 |
| HR11.2 | Canonical bars, clocks, grades and source policies | 11 |
| HR11.3 | Explicit sessions and complete timeframe aggregation | 14 |
| HR11.4 | Existing technical registry extended for intraday | 18 |
| HR11.5 | Minute and session-close horizon family | 4 |
| HR11.6 | Strict existing-profile adapters | 7 |
| HR11.7 | Instrument costs, sizing and financing | 8 |
| HR11.8 | Timestamp as-of cross-asset joins | 6 |
| HR11.9 | Explainable signals, learned weights and research gates | 10 |
| HR11.10 | Purged walk-forward, non-overlapping evaluation | 18 |
| HR11.11 | Refusing paper-only router | 9 |
| HR11.12 | Conservative robustness and admission | 12 |
| HR11.13 | CLI, reports and connected test-only fixture | 13 |
| HR11.14 | Full regression, compilation and protected hashes | 175 |

Counts overlap across stage-specific runs; the final suite contains **61 distinct
HR11 tests plus 114 existing safe tests**. Final hardening added additional
cross-stage tests after the individual stage boundaries.

## Modules and contracts

The `intraday_*` modules implement instruments, data, sessions, features,
horizons, profiles, costs, cross-asset joins, signals, gates, evaluation, router
and robustness. `hr11_research.py` composes them into the report CLI. The existing
`technical_feature_registry.py` gains an intraday factory; its default catalog
and protected historical catalog artifact retain their old semantics.

Reused components include HR7 RSI/SMA calculations, expanded research indicators,
displaced Ichimoku, Fibonacci/candlestick context, authoritative technical signals,
existing MarketProfile definitions, ReliabilityAccumulator, HR10 bootstrap/BH and
admission primitives, and the existing live-execution-disabled exception.

ADRs 0015–0020 define identity separation, horizon IDs, as-of joins, costs, grades
and the paper boundary. All component versions appear in the generated JSON.

## Universe, data and features

Nine enabled research identities cover USD/ZAR, a JSE index proxy, gold, Brent,
platinum, Naspers, Sasol, BHP and Absa. Palladium, S&P 500 and Sasol CFD/SSF
placeholders are retained disabled. Proxy data symbols are separate from execution
symbols, contract multipliers, ticks, lot sizes, currency and financing terms.
Unknown specifications remain unknown.

Aggregation supports 5m, 15m, 30m, 60m and explicit session daily bars; the integrated
research grid uses the four intraday decision timeframes. Horizons are
`intraday_5m`, `intraday_15m`, `intraday_30m`, `intraday_60m` and `intraday_eod`, with
30m primary by default. Daily 1/3/5/20-session labels are unchanged.

Features include RSI, SMA/EMA, MACD, ADX/DMI, Ichimoku, OHLC stochastic, ATR,
Bollinger bands, realized volatility/change, timestamp-aligned benchmark relative
strength, relative volume, quote-notional liquidity, session VWAP/opening ranges,
current/prior session extrema, prior-bar Donchian/support/resistance, confirmed
swings and session gaps. Fibonacci and candles remain contextual. Warmup, missing
inputs and stale bars are explicit; no absent value is substituted with neutral
signal evidence. Cross-asset observations retain source clocks and record hashes.

**No real canonical 5m history, verified exchange calendar or instrument cost
schedule was supplied.** The committed default report therefore contains:

- 0 input records and 0 trades;
- 180 `INSUFFICIENT_EVIDENCE` base cells;
- 0 `REJECT` performance judgments and 0 `ADMIT_FOR_CONTINUED_SHADOW` cells;
- null returns, confidence bounds, costs and drawdowns where unmeasured;
- explicit missing contract metadata, data, volume/quotes and cross-asset context.

The integrated connected fixture is confined to tests and temporary directories.
It proves pipeline mechanics; it is not presented as market evidence.

## Causality, costs and evaluation

Completed interval event time must precede availability and decision clocks.
Aggregation never crosses sessions or invents missing slots. Benchmark availability
is checked at each historical decision. Source age uses event time, so late
publication does not refresh stale information. Future-mutation tests cover all
four timeframes, features, cross-asset inputs, signals and evaluation.

Evaluation uses fixed UTC weekly folds, a 60-minute purge and five-minute embargo.
Weights use only matured, non-overlapping outcomes available before the fold,
separated by instrument/type/timeframe/horizon/profile/regimes. Fewer than 30
outcomes retain default weights. Each available signal reports its value, weight,
contribution, sample count and reason; missing signals do not dilute the score.

Positions do not overlap within a cell. Entry at the next interval open exactly
at decision time is a zero-latency **paper assumption**. Missing, delayed/unaligned
execution paths cannot manufacture fills. Metrics include net/gross returns,
win rate, MFE/MAE, drawdown, turnover, monetary costs, exposure, holding time,
long/short counts and profit factor where meaningful.

Costs require explicit currency and contract sizing, spread, commission/minimum,
exchange/broker fees, tick-rounded slippage and elapsed-time side-specific financing.
Hold incurs no order turnover; reversal incurs two sides of units. Research cost
viability compares costs with observed ATR without calling that a predicted return.

Admission requires minimum trades/folds/regime samples, seeded block-bootstrap
uncertainty, static comparison, sensitivity runs, doubled-cost stress, drawdown,
fold/regime stability and BH correction. P-values on block means remain approximate.
Only continued-shadow admission exists, and the router cannot dispatch orders.
See `docs/research/HR11_METHOD.md` for exact assumptions and input schemas.

## Validation and artifacts

Final validation: **175/175 safe tests pass; 103 root Python modules compile;
39/39 protected SHA256 hashes match**. Existing HR8/HR9/HR10, signals, adaptive
ensemble, technical registry and provider/dashboard suites remain included.
Five manual network/environment probes remain excluded exactly as at baseline:
`test_cloud`, `test_llm_sentiment`, `test_ost_login`, `test_reddit`, `test_sentiment`.
No fresh browser or real-provider smoke test was needed for this offline extension;
this work makes no new claim about their current availability.

Artifacts under `analysis/results/hr11/`:

- `baseline.json`: initial branch/head and protected artifact/code hashes;
- `validation.json`: final suite, compilation and hash counts;
- `report.json` and `report.md`: full universe/cell evidence and limitations;
- `decisions.jsonl` and `trades.jsonl`: empty in the honest default run.

Reproduce with `python hr11_research.py --cutoff 2026-09-06T00:00:00+00:00`.
Implementation commits before final integration are `4971ba2` (design), `51c0ae5`
(identities/data/sessions), `0fe7132` (features through costs/joins), and `7848b5a`
(signals through robustness). The final integration and handoff commit follows them
on `master`; consult Git history for its exact hash.

## Recommendation

Continue research/shadow collection. A separate follow-up should supply authorized
5m history, versioned real sessions and verified contract/cost metadata, then run
this pipeline and review actual failures and uncertainty. Do not promote adaptive
signals or call the system execution-ready. OI3's live AI/news-provider restoration
remains a distinct unfinished task.
