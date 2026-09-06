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
