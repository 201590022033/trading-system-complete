# ADR 0033 — Lean scheduled worker, exact horizon and mandatory ETF research

Date: 2026-10-02. Accepted within the sole ACTIVE operational workspace.

Evolve the daily PAPER loop, preserving the legacy benchmark and v3 account.
Actual paper outcomes declare their planned completed-session horizon, including
early stops/targets. Learner and ranking adapter select that exact strategy
horizon. Historic DELAYED_EXIT rows are not silently relabelled. One-day
technical estimates retain their distinct methodology. Candidate and benchmark
entries must be strictly after the actual decision, not merely an old signal bar.

The four existing listed ETFs have a separate canonical research shortlist and
compact candidate decision/outcome kinds, reusing context charts with volume.
Both cash and ETF sessions participate in fingerprints. All four admission rows
remain visible on missing data/cash. OST cash, fees, spread and sizing remain
unconfigured, never substituted with simulator cash. ETFs do not enter cash
simulator pending orders. The HR11 suitability adapter uses its fully funded
cash-security contract; canonical identities retain index_etf/etf. Suggestions
are for manual OST/Shyft review and paper/demo journalling only; no orders,
broker mapping or adaptive production promotion.

Railway cron runs at 00:00 UTC (02:00 SAST), processes at most ten due jobs and
exits. SCHEDULED_IDLE is healthy until the next run plus two hours, then stale.
An explicit service-role entrypoint prevents worker/web startup confusion.
Web and PostgreSQL remain available. Old completed input/ranking snapshots
are compressed after 90 days, at most 100 per run, transactionally with gzip,
base64 and verified SHA-256. Latest ranking and uncompleted inputs are protected.
Record-ID reads and immutable conflicts read through the archive. List queries
show recent snapshots. Compact evidence, fills, policies, intents and outcomes
are never automatically deleted; no evidence is discarded.

## Cost and retention evidence

Oct 2 usage ~$2.57 for the current billing period, primarily RAM. Observed RAM:
web 256 MB, PostgreSQL 177 MB, worker 121 MB. Removing idle worker RAM suggests
~$4.0–$4.6 monthly resource usage at observed web/DB load, NOT a guarantee.
Railway identifies this workspace as trial. API refused a $5 cap (minimum $10)
and refused alerts without an active subscription. No higher cap or paid plan
was applied. Budget acceptance remains CONDITIONAL.

Volume 143 MB/500 MB; logical DB 10,041,023 bytes. Latest input 113,185 bytes
compresses to 17,574; ranking 127,416 to 6,441, before base64. Forecast reserves
100 MB free, 90 days raw, 252 sessions/year and 2x row/index overhead, with
46 KB/session compact evidence provision. Roughly six years fit at those rates;
this is a review forecast, not a proven longest lifetime from one day's data.
Compact history has no automatic expiry. Online reads remain bounded at 5,000
rows per kind (~14 months at 17 shares/day, ~5 years at four ETFs/day); retained
history is not all actively used in each estimate. Longer online use needs a
tested aggregation model, not an unbounded query on the $5 worker.

Tests cover exact horizon feedback, delayed entry exclusion, separate ETF API,
unconfigured account, both-backend archive protection and immutability, bounded
cron exit and missed-run staleness. Live acceptance is recorded in the milestone.
October 8 is a review checkpoint, not guaranteed outcome maturity or profitability.
Thirty independent comparison windows and cost-sensitive performance remain pending.
