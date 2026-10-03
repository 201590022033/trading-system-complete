# ADR 0037 — Causal Swing technical and multi-horizon shadow path

Accepted 2026-10-03, following attribution acceptance commit 781c0ab.

Owner explicitly authorizes correcting the two-indicator / one-horizon gap.
Evolve the worker and Yahoo adapter; preserve the legacy ranker and simulator.
Add a separate exact-version Swing 1.1.0 shadow definition, not a promotion.
Use real daily OHLCV, EMA20/50, Wilder RSI14/ATR14, prior-session structure,
relative volume and date-aligned broad benchmark strength. Compute from causal
full acquisition history before retaining only 60 bars. Missing inputs stay
unavailable; never synthesize OHLC from closes. Store one frozen feature decision
per instrument/session/version and independent 3/4/5-session close-return labels.
Labels enter at the next observable session after the actual decision; do not
backdate entry to the signal close. Research labels are not stop/target execution
or actual OST net profitability. Finite-history initialization is explicit.

No new provider, tick stream, account configuration change, live order, scoring
promotion or Railway deployment. The benchmark remains visible. ATR geometry,
intraday stop ordering, trailing, catalysts/calendar, sector mappings, actual OST
costs and walk-forward/ablation validation remain separate gates.

Candidate core setup is declared before outcomes: close > EMA20 > EMA50;
close above prior-20 OHLC high OR prior close at/below its then-current EMA20
and current close above EMA20; Wilder RSI in [50,70]; volume above the prior-20
average; positive matched-date 20-session broad benchmark excess; and valid
structural/ATR geometry. Reference stop is the lower of prior-10 low and close
minus one ATR, reference target two times the resulting risk above the close.
These are unoptimized hypotheses, not claims of optimal settings or an executed
policy. Missing inputs make the setup unavailable, not a negative signal.
M11 present/absent cohorts expose sample size, shrinkage, negatives and uncertainty.
Overlapping sessions and instruments are not independent validation samples.

Storage: decisions deduplicate by account/instrument/session/version; all screened
instruments, not only winners, get three small labels. No extra provider calls
or full-year bar persistence. Read/label windows are bounded at 5,000 records
and disclosed; this is not a hard storage/cost cap or unlimited historical memory.
Actual Railway $5 acceptance and hot/archive retention remain existing gates.
