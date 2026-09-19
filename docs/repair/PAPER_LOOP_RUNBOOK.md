# Running the repaired PAPER loop

The implementation is opt-in. Railway activation was authorized on 2026-09-19:
the production database was backed up and migrated, and both services configured
with `/app/config/paper.railway.json`. Deployment acceptance must verify actual
worker cycles, not merely this configuration. This is not evidence of profitability.

## Configure and start

Run from the repository root, using its virtual environment. Review
`config/paper.example.json`: its capital, costs, participation cap and risk limits
are simulation assumptions, not facts about a real account. Use a separate account
ID for changed configuration; changing an existing account's configuration fails.
Never supply LIVE mode. No real broker credentials are needed.

Set PAPER_LOOP_CONFIG to the absolute configuration path in BOTH web and worker
environments. Both must use the same DATABASE_URL (PostgreSQL), or the same
absolute SQLITE_DB_PATH for local experiments. A configured but unavailable
PostgreSQL database never falls back to SQLite.

For an operator-approved PostgreSQL target, explicitly run additive migrations
before startup: `python -m scripts.migrate_postgres`. Web/worker startup does not
migrate PostgreSQL. The authorized Railway migration was applied explicitly after
a custom-format backup on the Postgres persistent volume.

One bounded worker tick: `python -m scripts.run_paper --config config/paper.example.json`

Continuous worker: add `--continuous`. The scheduler enqueues once per configured
interval; each heartbeat processes at most one due job. The existing deployment
heartbeat also composes paper work when PAPER_LOOP_CONFIG is set. Existing due
shadow work can precede the paper job: one tick is not a promise of a fill.
Use the existing dashboard startup in another process with the same environment.

Read `/api/paper/status` for account, positions, recent cycles and outcomes.
`/api/v1/opportunities?limit=5` and the existing Top-5 display read committed M13
rankings from that worker. Refresh in configured paper mode is read-only; it
does not schedule another pipeline. Missing evidence and stale state stay visible.

Set PAPER_PAUSED=1 in the worker environment and restart it to block new entries.
Existing positions may still close on a valid later observation. Stopping the
worker stops processing altogether; it does not liquidate anything. Restart uses
the saved account and frozen jobs, not a reset balance.

## Supported model and boundaries

- Curated ZAR public cash shares; long-only, fully funded whole shares. Other
  currencies, derivatives, short borrow and real account balances are not wired.
- Yahoo daily completed-close observations, conservatively available the next
  UTC day; no guessed holiday calendar, fabricated OHLC, intrabar execution,
  guaranteed stop price, or licensed intraday feed. Freshness defaults to one day;
  weekend/stale data blocks entries rather than being relabelled current.
- Entry requires an earlier ranked proposal and a later complete observation.
  The structural stop uses preceding 20 closes; target defaults to 2R. Positions
  exit at the next available new observed session close, or the first valid
  observation after stop/target/expiry. Missing data cannot generate a fill.
  Gaps may exceed risk budgets: configured stop loss is not a loss guarantee.
- M15 limits, observed volume participation, closing-fee reserves and explicit
  slippage/commission cap entry size. Volume is a simulation capacity constraint,
  not proven executable liquidity. Aggression never overrides a veto.
- Exits record immutable net outcomes and fill lineage. Only causally mature
  one-session outcomes reach the existing M11 learner; 30 observations are needed
  for its learned cell. Delayed exits are not mislabeled one-day samples.
- News consumes already persisted, policy-enabled evidence from existing
  collectors. PAPER_NEWS_ENABLED=1 enables bounded ingestion of the existing
  Moneyweb/SENS collector in the worker; first availability is never refreshed.
  Sentiment is labelled opinion; macro tags remain context, not invented risk.
- Legacy operational analysis, shadow learning and market-intelligence screens
  remain separate diagnostics. They cannot substitute an alternate Top-5 ranker.
  Legacy shadow aggregates lack verified strategy/horizon attribution and remain
  provenance-only; new paper strategy outcomes supply learned ranking evidence.

## Validation and remaining operational work

`python -m scripts.run_tests` blocks external socket connections and dotenv.
Manual provider/broker/LLM probes are deliberately excluded. Native PostgreSQL
acceptance is separate: `python -m scripts.validate_paper_postgres --url ...`,
restricted to an explicitly disposable localhost paper_validator database. It
tests migrations, competing account transactions, rollback and process recovery.

The Railway configuration uses R100,000 simulated capital and conservative risk.
The Portfolio & demo workspace reads the durable ledger. PAPER_CONTROL_TOKEN on
the web service unlocks authenticated aggression, pause/resume and enqueue-only
check controls. Retrieve the key privately from Railway variables; never publish
it in source, URLs or logs. These controls cannot enable real-money execution.
IG read diagnostics are enabled in DEMO mode, but require IG_API_KEY,
IG_IDENTIFIER (or IG_USERNAME), and IG_PASSWORD. No credential means no connection.
Cloud AI credentials and a concrete IG streaming transport remain prerequisites
for those separate capabilities. Long-duration soak/load testing and
profitability/walk-forward validation are not performed.
Audit records and broker checkpoint history grow with fills; archival/compaction
is not supplied. Portfolio scope is one independently funded paper account per
configuration, not consolidated cross-broker capital or automatic cash transfers.

No code connection remains missing within this bounded Gates 2–5 paper model.
Broader intraday/short/derivative geometry, real multi-account liquidity and live
execution are intentionally outside it and must not be inferred as completed.
