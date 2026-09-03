| Rank | Technical opportunity | Sector | Regime | Horizon | Net vs cash | Robustness | Diamond Tier |
| ----: | ----------- | ------ | ------ | -------: | ---------: | ---------- | ------------ |
| 1 | ABSPJ raw-technical trigger | Banks | range/neutral strongest | 3 | +0.142% | both halves positive; 3/4 horizons | C |
| 2 | SASOL raw-technical trigger | Energy | strongest in range/bear; mostly risk-off | 5 | +1.105% | 3/4 horizons; one half negative | C |
| 3 | ABSPJ raw-technical trigger | Banks | normal-volatility | 5 | +0.230% | second half negative | C |
| 4 | BHP raw-technical trigger | Diversified mining | bull/risk-on strongest | 1 | +0.170% | both halves positive; 2/4 horizons | C |
| 5 | SASOL raw-technical trigger | Energy | strongest in range/high-vol/risk-off | 20 | +1.917% | both halves positive; N=43 | C |
| 6 | SASOL raw-technical trigger | Energy | mixed | 3 | +0.539% | first half negative | C |

## Methodological Audit of Zero-Trade Legacy

Zero trades are mechanically expected from the frozen price-only logic, not a
warm-up or alignment bug. After the common 20-session warm-up, observed raw
technical scores span -0.50 to +0.50. With missing sentiment and macro set to
zero, legacy's `0.60 × technical` can span only -0.30 to +0.30 and cannot cross
the unchanged strict ±0.35 action threshold.

This does **not** prove historical production legacy made no trades. Production
legacy also used contemporaneous news sentiment and macro overlays, but those
point-in-time series were not persisted. A faithful full comparison is therefore
**`INSUFFICIENT HISTORICAL INPUTS`**. The 24-row result is preserved, but its
return field is now “adaptive/raw-technical net versus cash/no-trade,” never
adaptive outperformance versus full legacy.

The constrained matched audit contains 4,326 fully warmed timestamps: 4,054
both-hold cases, 272 adaptive/raw-technical-only trades, zero both-trade cases,
zero legacy-only trades and zero directional disagreements. Every timestamp has
both scores/actions and aligned 1/3/5/20-session forward returns in
`forensic_analysis.json`. Cash has zero return, turnover and cost. The simple
non-adaptive raw-technical benchmark is exactly identical to reconstructed
adaptive, so adaptive incremental performance versus that valid benchmark is
zero.

## Strongest Diamonds

There are no Tier A or Tier B adaptive diamonds. The leading descriptive
raw-technical opportunities are Absa at 3/5 sessions, Sasol at 3/5/20 sessions
and BHP at 1 session. Sasol’s 5-session result is
concentrated in range/bear observations; its regime subsets have fewer than 30
signals. At 30 bps cost stress, Sasol 3/5/20 and Absa 5 remain positive; Absa 3
and BHP 1 do not. They remain Tier C because none has incremental value over the
identical simple technical benchmark.

## Promising but Unproven

Bear-regime RSI and stochastic mean-reversion, range breakouts at 3–5 sessions,
and bull-regime SMA at 20 sessions are the most interesting individual existing
indicator effects. They are pooled, overlapping, gross-of-cost diagnostics and
were selected after inspection; none is promotion evidence.

## Adaptive Components That Hurt Performance

The active adaptive component—threshold de-diluted legacy technical scoring—was
negative in 15/24 ticker/horizon rows. It was particularly harmful for IMPJ at
1/3/5 sessions, NPN at every horizon, BHP at 20 and SHPJ at 1/3/5. Bear-regime
breakout and SMA signals were damaging at longer horizons. Regime, profile,
macro, sentiment and reliability components neither helped nor hurt because
they did not change a score in this experiment.

## Bull vs Bear Findings

Bear regimes favored RSI/stochastic counter-move signals over multiple days,
while SMA and breakout continuation were generally harmful. Bull regimes showed
weak short-horizon SMA performance and better 20-session persistence. Range
breakouts were unexpectedly positive at 3/5 sessions, while range RSI was
negative with only 58 observations. See `BULL_BEAR_INDICATOR_FORENSICS.md`.

## Sector Findings

Energy/Sasol is the strongest ticker-profile candidate, followed by banks/Absa
and one-day diversified mining/BHP. PGM/Impala and offshore-earner/Naspers are
clear negatives. Each sector has only one ticker, so none is a replicated sector
effect. Gold, agriculture, index derivatives and FX were not evaluated.

## Commodity Findings

`INSUFFICIENT DATA`. No commodity series entered the evaluation. The BHP, IMPJ
and SASOL differences are ticker-specific technical outcomes, not evidence for
commodity conditioning.

## Brent Findings

`INSUFFICIENT DATA`. Sasol’s results cannot establish any Brent mechanism,
lead/lag, inflation/rate channel or Rand interaction because Brent was absent.

## Gold / Risk-Aversion Findings

`INSUFFICIENT DATA`. There is no gold-miner ticker, gold price, DXY, yield or VIX
series. Regime-v1 risk labels come solely from each ticker’s own closes.

## Rand Findings

`INSUFFICIENT DATA`. No USD/ZAR observations or commodity×Rand interactions were
evaluated. Profile coefficients did not participate.

## Source Findings

`INSUFFICIENT DATA`. Enabled collectors produced no persisted historical input
to M7. Source-only signals, reliability, lead/decay and duplication cannot be
measured. No positive row is attributable to source intelligence.

## Horizon Findings

Usefulness is sharply horizon-dependent: Sasol favors 3/5/20 over 1; BHP favors
1/3 over 5/20; Shoprite only shows a small 20-session positive; Naspers and
Impala have no positive horizon; Absa favors 3/5/20. This instability argues
against universal weights.

## Failure Analysis

Of 15 negative rows, the conservative primary taxonomy assigns four to horizon
instability, four to downside/volatility exposure, four to technical noise/lag,
and three to transaction-cost burden. The overarching design failure is that
the “adaptive” historical experiment contained no effective context adaptation.

## Robustness / Overfitting Assessment

The analysis attempted falsification through temporal halves, adjacent horizons,
cross-ticker comparison, 0/10/20/30-bps costs, Wilson uncertainty and provider
reproduction. Provider drift changed magnitudes but no signs. Several positives
fail temporal or cost stress; no profile has a second ticker; all outcomes
overlap. No Tier A finding survives all objections.

## Missing Data With Highest Expected Information Value

1. Immutable dated OHLCV snapshots for all evaluated tickers and sector peers.
2. Timestamp-aligned USD/ZAR, Brent, gold, PGM, J200, VIX and SA/US yield series.
3. Persisted SENS/news evidence with canonical origin, publication/ingestion time
   and later outcome.
4. Licensed spread/liquidity and, if intended, SSF/CFD basis/open-interest data.
5. Multiple tickers per profile and longer out-of-sample periods.

## Recommendations

### KEEP

- Legacy production/default scoring and all paper/shadow safety boundaries.
- Explainable factor logging, provenance, capability gates and frozen-input
  forensic infrastructure.

### WATCH

- Sasol technical triggers at 5/20 sessions, Absa at 3 sessions, BHP at 1.
- Bear-regime RSI/stochastic and range-breakout hypotheses.

### DOWN-WEIGHT

- No production down-weighting is justified. For a later research proposal,
  bear-regime SMA/breakout and long-horizon NPN/BHP technical triggers merit
  explicit challenge tests before receiving influence.

### REMOVE / DISABLE

- Remove nothing from production under this mandate.
- Do not present the current M7 adaptive result as contextual adaptation; that
  interpretation is rejected.

### DATA NEEDED

- Dated immutable prices, OHLCV, cross-assets, rates, source events and realistic
  instrument costs as listed above.

### RESEARCH NEXT

- A preregistered **Frozen Context Validation** milestone: freeze dated inputs,
  ensure at least two independently varying adaptive factors, verify that
  context multipliers actually alter decisions, and test only the documented
  hypotheses with non-overlapping temporal holdouts. Do not tune production.

## Plain Answers to the Big Questions

1. Adaptive outperformance versus full legacy is not measurable: `INSUFFICIENT HISTORICAL INPUTS`.
2. In the price-only ablation, cash avoids the 15 negative raw-technical rows.
3. Sasol/energy and Absa/banks look best, without sector replication.
4. All are proxy SSF/share-CFD profiles; actual derivatives were not tested.
5. Sasol range/bear and BHP bull/risk-on subsets look best but are small.
6. Best horizons are ticker-specific; no universal winner exists.
7. Bear RSI/stochastic and longer bull SMA are promising; bear breakout/SMA hurt.
8. No macro variable was observed.
9. Brent information is unknown.
10. Gold/risk-aversion information is unknown.
11. USD/ZAR importance is unknown.
12. No source class has outcome evidence.
13. Source duplication is unmeasurable without a corpus.
14. The de-diluted technical trigger damages 15 rows; other components were inert.
15. No adaptive Tier A/B row survives the simple-technical benchmark gate.
16. The nine positives are candidates mixed with likely noise, not proven diamonds.
17. Immutable dated contextual data would increase confidence most.
18. Do not build new models/connectors or tune weights from these results.
