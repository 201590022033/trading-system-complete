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
