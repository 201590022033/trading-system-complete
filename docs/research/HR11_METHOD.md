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
