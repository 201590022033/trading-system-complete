# HR11 research contract

THIS DOES NOT CONSTITUTE LIVE-TRADING VALIDATION.

HR11 is an additive offline pipeline. Raw intraday inputs must be supplied with
explicit source, session, price-unit and availability semantics. No historical
daily artifact is converted into invented intraday bars. Missing costs, contract
metadata or source coverage remain explicit and prevent admission.

Session schedules are supplied versioned dated intervals, including half-days,
overnights and breaks. The code does not invent exchange holiday calendars.
Bar event_time means completed interval end. Features only see records available
at the decision cutoff; fills use subsequent eligible bars and explicit costs.

## Stage HR11.1

Instrument definitions separate underlying/target/contract, retain unknown metadata, reject invalid numeric specifications and preserve the existing six-symbol UI registry. Nine research targets enabled; derivative placeholders disabled.

## Stage HR11.2

Canonical bars use completed interval-end event times, explicit observed/historical-publication availability, UTC normalization, immutable provenance and no invented OHLC/quotes. Duplicate/overlapping records fail; out-of-order input is sorted without forward-filling. Provider exceptions expose only their type.

## Stage HR11.3

Explicit versioned sessions govern complete-bar aggregation, including overnight UTC/DST intervals and declared breaks. Missing slots, delayed inputs and partial final intervals never become fabricated complete bars. Daily OHLCV preserves missing volume and input lineage.

## Stage HR11.4

Extended the existing TechnicalFeatureRegistry through a separate intraday factory. Reused HR7 RSI/SMA, expanded indicators, displaced Ichimoku and contextual structure calculators; added OHLC stochastic, confirmed swings, prior-bar channels and session-bound VWAP/opening ranges. Windows are bar counts, with no claim of intraday calibration. Missing/stale prices and within-session gaps block snapshots; zero or absent volume remains unavailable.

## Stage HR11.5

Added collision-free intraday_5m/15m/30m/60m/eod labels with configurable primary 30m. Targets use actual timestamp durations and explicit session closes, rejecting spillover and declared breaks. Existing daily horizon code remains unchanged.

## Stage HR11.6

Strict instrument-to-profile selection reuses existing profile IDs and MarketProfile objects. HR7 gold/energy and explicit platinum research profiles extend the catalog. Unknown profiles raise instead of falling back to single_stock; cross-asset factors and volume requirements are explicit, uncalibrated research policy.

## Stage HR11.7

Added explicit per-instrument/currency cost schedules with turnover units, half-spread per side, tick-rounded slippage, commission minima, exchange/broker fees and elapsed-time financing. Hold has no order costs; reversal charges double units with one net-order minimum. Unknown contract metadata, invalid sizing, unsupported shorts and currency mismatches block costs. No broker cost schedule is invented.

## Stage HR11.8

Cross-asset joins now select only timestamp-available observations, enforce each source maximum event age and retain source IDs plus input record hashes. Late publication cannot refresh an old event. Return factors require consecutive same-source bars; absent or stale factors remain explicitly unavailable.

## Stage HR11.9

The authoritative technical_signal_frame now receives an intraday feature adapter. Every signal retains availability, weight, contribution and evidence count. Existing shrunk ReliabilityAccumulator weights remain neutral below 30 independent matured outcomes, separated by instrument/type/timeframe/horizon/profile/regimes with explicit purge and embargo. Research gates cover source freshness/grade, session, liquidity, spread, feature/context sufficiency and explicit costs versus observed ATR (not predicted edge).

## Stage HR11.10

Added fixed UTC weekly walk-forward folds with 60-minute purge and five-minute embargo, frozen prior-fold training evidence and one open position per instrument/timeframe/horizon. Entry is the next observed interval open at the decision timestamp, an explicit zero-latency paper assumption; exact target-end bars and complete execution paths are required. Costs, financing, non-overlap, MFE/MAE, turnover, exposure and holding times are reported. Reliability training uses only independently entered trade windows, with side-specific costs; this selection limitation is explicit.

## Stage HR11.11

Added a pure hypothetical paper-preview router, separated from broker providers. It rechecks instrument identity/enabled state, clock/session freshness, research gates, admission, direction, sizing and costs. Only ADMIT_FOR_CONTINUED_SHADOW can produce a preview; submit/cancel unconditionally raise the existing LiveExecutionDisabled exception.

## Stage HR11.12

Reused HR10 block-bootstrap confidence intervals, Benjamini–Hochberg correction and admission rules. Inference uses one-sided normal approximations on non-overlapping block means and is explicitly approximate. Minimum 30 trades, three folds, regime evidence, static baseline and two sensitivity runs are required before testing positive net/CI, fold stability, doubled-cost stress, drawdown, parameter stability, FDR and baseline outperformance. Empty metrics remain null; only reject, insufficient or continued-shadow states exist.

## Stage HR11.13

Integrated an offline CLI with explicit canonical JSONL, session calendars, full instrument definitions and cost schedules. Reports include versions, provenance, missing capabilities/context, gate explanations, trades, static baseline, sensitivity runs, regime cells and FDR-adjusted admission. A connected test-only fixture produces trades through the complete pipeline. The real default report contains zero input records, zero trades and 180 INSUFFICIENT_EVIDENCE cells; no production fixtures or fabricated live feed are used.

## Running the integrated pipeline

From the repository root, the following performs the honest default audit:

```bash
python hr11_research.py --cutoff 2026-09-06T00:00:00+00:00
```

It writes `analysis/results/hr11/report.json`, `report.md`, `decisions.jsonl`
and `trades.jsonl`. No network provider is contacted and no synthetic observations
are loaded. The committed report has zero real intraday records and 180
insufficient-evidence cells: nine enabled instruments × four decision timeframes
× five horizons. Empty metrics and uncertainty bounds are null, not profitable
zeros. Disabled instrument definitions are retained in the universe manifest.

For an actual research run, supply authorized historical data explicitly:

```bash
python hr11_research.py --input /path/to/canonical-bars.jsonl \
  --sessions /path/to/sessions.json --instruments /path/to/instruments.json \
  --costs /path/to/costs.json --units 10 \
  --cutoff 2026-09-06T00:00:00+00:00 --output /path/to/research-output
```

Input contracts:

- **Bars:** one `IntradayBar.to_dict()` JSON object per line. Real completed 5m
  bars are required for the integrated evaluator. `source` contains every
  `SourcePolicy` field; timestamps are timezone-aware ISO strings. Event time is
  the interval end. Observed availability must not predate ingestion; a
  historical-publication policy must be supported by actual publication
  provenance. Source IDs cannot ambiguously name conflicting policies.
- **Sessions:** JSON object mapping instrument IDs to lists of `session_id`,
  `session_date`, `open_time`, `close_time`, `calendar_version`, and optional
  `breaks` pairs. Supply exchange-appropriate holidays, half days and overnight
  sessions from an authorized calendar. No holiday or CFD session calendar is
  guessed by this code.
- **Instruments:** JSON list of complete `InstrumentDefinition` dataclass fields,
  using the DataGrade string values. Use `dataclasses.asdict`, rather than
  `to_dict()` presentation fields, when serializing definitions for input. The
  default registry is used when omitted; its unknown tick/lot/contract metadata
  deliberately prevents admission. A Yahoo symbol does not identify a broker
  contract. Normalize JSE cents versus rand explicitly before ingesting data;
  retain that conversion in source provenance. Never label index points as money.
- **Costs:** JSON list of `CostSchedule` fields, one per instrument ID. All fees,
  financing rates, spread, commission minima, slippage ticks and assumptions
  must be explicit in the instrument's quote currency. Unverified schedules
  require a nonempty assumptions list. Defaults never supply a zero-cost model.

No licensed intraday history, exchange calendar or verified broker schedule was
available for this milestone. The loader and callback adapter make these inputs
possible; they do not certify their accuracy or claim a newly connected live feed.

## Interpretation and limitations

Features use completed-bar prefixes. Session VWAP/opening ranges require the
actual session opening prefix; confirmed swings require two completed bars to
the right of a pivot. Existing Fibonacci/candlestick outputs remain context.
Benchmark relative strength requires exact timeframe/event alignment and
availability at **each historical asset decision**, with separate benchmark record
hashes. A benchmark learned later cannot enter an earlier feature.

Raw signal thresholds follow the authoritative technical definitions. The static
intraday comparator uses equal available-signal weights, while legacy daily
outputs are separately protected unchanged. Missing signals do not enter the
ensemble denominator. EMA windows, profile liquidity cutoffs and signal thresholds
are uncalibrated research policy, not an asserted profitable intraday strategy.

The standard policy uses fixed UTC weekly folds anchored on Monday 1970-01-05,
60-minute purge and five-minute embargo. Training evidence is frozen at the fold
start, with strict label-maturity and availability cutoffs. Additional per-decision
purge checks are conservative. A position starts only at an observed next interval
open exactly at the decision clock; delayed, unaligned or incomplete paths remain
unavailable. This assumes zero latency for paper research and must be stress-tested
before more realistic simulation. Long/short costs use their own financing rates.

The evaluator permits one open position per instrument/timeframe/horizon, including
across regime changes. Different horizons and timeframes are separate experiments,
not a combined portfolio; their returns must not be added as portfolio returns.
Exposure measures holding seconds divided by supplied elapsed session seconds.
Trade equity/drawdown compounds returns at each entry notional; monetary costs are
reported per cell in quote currency. Profit factor is null when there are no losing
trades. MFE/MAE require complete high/low observations and remain null otherwise.

Admission requires 30 trades, three folds, at least five observations in each
observed trend/volatility regime, a static baseline and two threshold sensitivity
runs (0.15 and 0.25). It then applies HR10's positive mean/95% bootstrap lower bound,
fold stability, maximum 25% drawdown, doubled-cost stress, parameter stability,
5% BH-adjusted significance and strict static-baseline outperformance. Regime means
must also be positive. The bootstrap seed is 20260906, with 1,000 moving-block
resamples and square-root block length. P-values reuse the HR10 one-sided normal
approximation on non-overlapping block means; they are approximate. BH covers all
reported base cells and observed regime subcells in one family.

Insufficient data cannot imply rejection on measured performance, nor admission.
`ADMIT_FOR_CONTINUED_SHADOW` authorizes only a hypothetical paper preview. No code
in this layer connects to a broker or promotes adaptive signals into the dashboard.

## Stage HR11.14

Full safe regression passed: 61 HR11 tests plus 114 existing tests. All 103 root Python files compiled; all 39 protected daily artifact/code SHA256 hashes match the baseline. Final hardening covers benchmark availability/lineage, each timeframe prefix, declared-break daily roundtrip, source freshness finiteness, noncausal builders, overlapping evidence and invalid paper scores. Five manual network/environment probe modules remain excluded, as at baseline. Default real-data report regenerated with 180 insufficient cells and no trades.
