# Shadow runtime migration and operator validation

Status: local repair validation complete. Native PostgreSQL 18 validation passed
on the disposable local database at `127.0.0.1:5433`. Railway deployment is
operator-authorized without a paid-plan backup; this is an explicit accepted
loss-of-rollback risk. Secret configuration and migration remain guarded.

Architecture: one web service, one bounded worker, one PostgreSQL database.
No Redis, Celery, continuous research runs, extra services or live brokerage.

## Explicit migration

Before any external deployment, run the local guarded preflight with Railway
variables supplied by the deployment environment (never commit them):

`.venv\\Scripts\\python.exe -m scripts.deployment_preflight --check-database`

The preflight requires `DATABASE_URL`, `APP_MODE`, `PORT`, `COMMIT_SHA` and
`WORKER_ID`, refuses `APP_MODE=LIVE`, requires PostgreSQL, requires a clean Git
tree, and performs only `SELECT 1` against the configured database. It does
not invoke Railway or apply migrations. It never prints values of any required
variable.

1. On the explicitly approved database, set `DATABASE_URL` through secret management.
   Do not run the command against Railway as part of this local repair.
2. Run `.venv\Scripts\python.exe -m scripts.migrate_postgres` (Linux uses the
   environment's `python`). This command does not load `.env` or print the URL.
3. Check `postgres_schema_migrations`: every version in `persistence/migrations/postgres`
   and its checksum must
   exist. Statements and version rows share one transaction and an advisory
   migration lock. On failure the full migration transaction is rolled back;
   fix the cause privately and rerun. Do not edit an applied migration.
5. Inspect old invalid/orphan records privately. NOT VALID foreign keys enforce
   new relationships without deleting preexisting records; canonical validation
   excludes invalid legacy outcomes from new contributions. Never fabricate
   prices, sessions, or labels to pass validation.

Migrations preserve old tables/rows and add MI tables, missing columns, indexes,
tracking and relationship guards. No DROP/RESET or automatic data repair runs.
The web and worker **do not migrate PostgreSQL automatically**. Schema readiness
must be established before starting either process.

## Runtime and bounded jobs

Web MI source/document/analysis/provenance state uses the same configured
repository as shadow learning and status. The PostgreSQL MI view reuses existing
store serialization with a narrow bound-parameter SQL adapter; it never opens
SQLite. The local fallback is SQLite only when no PostgreSQL URL is configured.

`python -m workers.heartbeat` runs one job per cycle, then sleeps (30s default).
It reads bounded due work, claims via compare-and-swap, persists completion and
heartbeat, and recovers only retryable RUNNING jobs older than 300 seconds.
Handlers must finish within that lease. Attempts are capped at five. Missing
handlers fail non-retryably with `MISSING_HANDLER`; they are not successful no-ops.
Completed persisted jobs are authoritative regardless of stale caller objects.

Initial causal handlers accept explicit observation/session/price evidence in
durable checkpoints. Nothing schedules a historical research run or downloads
market data implicitly. Approved providers must be wired explicitly; unavailable
provider handlers fail closed. No due jobs means only bounded status queries
and one heartbeat write, not market collection or LLM work.

Required process configuration: `DATABASE_URL`, `APP_MODE`, `PORT` (web),
`COMMIT_SHA`, `WORKER_ID` (worker), and approved provider settings if enabled.
No IG, Standard Bank or ViewPoint credentials are read by these paths.

Local web/worker/reliability share `SQLITE_DB_PATH` (default
`market_intelligence.db`). Runtime reliability no longer creates a separate
`reliability.db` or consults `RELIABILITY_DB_PATH`; existing standalone research
stores are not deleted or imported. `ReliabilityStore(':memory:')` remains a
test-only opt-in. `/api/learning/reliability/<source_id>` is a read-only summary.

MI host integration uses `runtime_handlers(repository, mi_provider=approved_provider,
mi_text_loader=approved_loader)` passed to the bounded runner. The CLI does not
guess a provider or load arbitrary import paths from jobs/environment. Until
those approved dependencies are supplied, MI jobs fail closed; idle cycles make
no provider calls. Each refresh consumes one document (20,000 extracted text
characters maximum), reuses durable cache, and saves snapshots/provenance. No
continuous LLM schedule is installed.

## Validation completed locally; deployment prerequisites remain

Native PostgreSQL write/read, rollback, separate-process verification, and
repeatable migrations passed against PostgreSQL 18 on port 5433. The DB-API
fixture and offline suite cover the broader shadow-learning lifecycle. Before
external deployment, run the guarded preflight, verify a backup, and perform
the approved Railway migration and health/restart checks. No external
deployment is authorized by this repair program.
