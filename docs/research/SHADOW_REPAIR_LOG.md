# Shadow-learning forensic repair log

Baseline: `ea3f3a7ef229f333832d2b68ebd7b3370d117379`. Local repairs only; no push
or deployment is authorized. One web service, one bounded worker, PostgreSQL.

## Batch 1 — causal inputs and outcomes

`OperationalIntelligence.analyze` accepts an optional as-of and observation
history context. It retains the existing scoring formula and default UI path.
Historical rows must have both event and availability timestamps at/before the
cutoff. Live/news retrieval is forbidden for as-of assessment. Missing causal
news remains unavailable. Research metadata is not a scoring input. Shadow
records retain component provenance and gates.

Shadow's default horizon is `5` (five supplied trading sessions), not the UI
label `swing`. Daily horizons use the existing 1/3/5/20 session definitions;
intraday uses the existing horizon/session resolver. Callers must supply the
complete versioned session sequence; there is no inferred holiday calendar.
Missing sessions, unsupported horizons and crossing a break fail closed.

Labels require exact entry/target price timestamps and causal availability.
Missing or stale prices produce `OUTCOME_DATA_UNAVAILABLE`, never zero prices.
Raw forward return is passed once to the existing `signal_outcome`, including
previous-position turnover. HOLD is not counted as a losing active sample.
The `existing` cost identity denotes that helper's 10bps turnover model, not a
claim of instrument-specific executable intraday spreads/slippage.

Both repositories validate persisted ancestry, canonical maturity/evaluation,
finite prices, complete returns and matching instrument/horizon before evidence
contribution. UTC offsets normalize at contract boundaries. Additive SQLite
insert guards and PostgreSQL NOT VALID foreign keys preserve old rows while
enforcing new relationships. Legacy invalid rows are rejected on contribution;
operators must review them rather than silently relabel them.

The PostgreSQL DB-API fixture emulates insert-side FK enforcement. It does not
prove native PostgreSQL migration, timestamp or concurrency behavior. Deployment
remains blocked pending real PostgreSQL validation and the remaining repair
batches. No protected research artifacts are regenerated.
