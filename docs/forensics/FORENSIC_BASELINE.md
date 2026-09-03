# Forensic Baseline

## Repository subject

- Baseline commit: `c5c6e8075ac26dc35b50cb1b42c9b694be5d3fdf`.
- Initial worktree: clean on `master`.
- Focused baseline suite: 41 tests passing.
- Production/default: legacy `JSESignalEngine`; adaptive is shadow-only.
- Execution: in-memory paper portfolio; no live broker ordering.

## Construction of the reported 24 rows

The 24 M10 headline rows are the `overall` adaptive rows from six tickers
(NPN, SASOL, BHP, IMPJ, SHPJ, ABSPJ) at 1, 3, 5 and 20 sessions. Each input had
760 Yahoo daily close-like observations. The instrument profiles are,
respectively, offshore earner, energy/Sasol, diversified mining, PGM mining,
retail/consumer and banks/financials; all are modelled as SSF/share-CFD context.

At each time `t`, `SignalGenerator` sees only closes through `t`; the outcome is
the close return at `t+horizon`. Regime-v1 uses that same prefix and emits
bull/bear/range plus low/normal/high volatility and risk-on/neutral/risk-off.
The action threshold is strictly above `+0.35` or below `-0.35`.

Costs are 5 bps spread + 2 bps fees + 3 bps slippage per unit of turnover.
The legacy evaluation score is `0.60 * technical + 0.30 * sentiment + 0.15 *
macro`. Historical sentiment, macro and source arrays are absent. The adaptive
evaluation therefore has only its technical factor available.

## Critical experimental fact

With exactly one available factor, adaptive weight normalization makes all
regime and profile multipliers cancel. Thus the M10 adaptive score equals the
raw technical score. The price-only legacy ablation equals 60% of that score and
generated no trades in the stored experiment. This is not a full legacy comparator
and measures no incremental value from regime, profile, macro, Rand, commodity,
sentiment or source reliability.

That zero is expected for this frozen **price-only reconstruction**: across the
4,326 fully warmed common timestamps, raw technical scores ranged from -0.50 to
+0.50. Legacy would need a raw magnitude strictly greater than `0.35 / 0.60 =
0.5833` when sentiment and macro are zero. Signal alignment and the 20-session
warm-up do not explain the zero; the observed score support and fixed threshold
do.

## Legacy methodological audit

The zero-trade result is not a faithful replay of everything production legacy
would actually have known. Production uses the timestamp's aggregated news
sentiment and macro overlay in addition to technical indicators. The repository
has no persisted, timestamp-aligned historical news/sentiment aggregation or
macro inputs for these 760-observation series. Treating unavailable series as
zero is a valid missing-factor ablation, but it is not evidence that production
legacy would have held at every historical timestamp. Therefore the status of a
full matched legacy comparison is **`INSUFFICIENT HISTORICAL INPUTS`**.

The constrained matched-opportunity audit uses common timestamps after all four
technical indicators have their 20-session warm-up and enough future prices
exist for every requested horizon. Of 4,326 opportunities, both reconstructions
held in 4,054, adaptive/raw-technical alone traded in 272, both traded in zero,
legacy-only traded in zero, and there were no directional disagreements. Each
machine-readable opportunity records both scores/actions and subsequent
1/3/5/20-session returns.

The appropriate comparator is consequently cash/no-position (zero gross/net
return, zero turnover) and a simple non-adaptive raw-technical benchmark. The
reconstructed adaptive score and action are exactly identical to that simple
technical benchmark. All former delta values are relabelled **adaptive net versus
cash/no-trade**, not adaptive outperformance versus full legacy. There is zero
incremental return versus the simple technical benchmark.

## Reproduction result

The unchanged generator was rerun on 2026-09-03. It again returned 760 closes
per ticker, identical 1,200 row keys, sample counts, regimes, win/loss counts,
turnover and net-return signs. It was not bit-identical:

- 20 of 24 adaptive overall rows had at least one changed return-derived field;
- no sample-count or net-return-sign changes occurred;
- maximum absolute mean-net drift was 0.00068715 (6.87 bps);
- maximum absolute mean-gross drift was 0.00109945 (10.99 bps).

Diagnosis: the repository committed aggregate output but not input dates/prices
or a provider revision ID. Yahoo adjusted history is mutable, so exact M10
return reproduction is impossible from the repository alone. Optimisation was
stopped; the committed M10 report remains authoritative. Deeper analyses use
`analysis/results/forensic_price_snapshot.json`, a newly frozen reconstruction,
and are labelled separately rather than represented as exact M10 results.

## Capability limits

- No historical macro, Rand, commodity, yield, sentiment or source observations.
- No gold-miner, agriculture, index or USD/ZAR instrument in the six tickers.
- Close-only data: no valid ATR/ADX, volume/liquidity, intraday VWAP/opening
  range, basis, open interest or real execution-spread forensics.
- Yahoo adapter exposes values without dates, preventing calendar-period/event
  attribution and precise lead/lag analysis.
