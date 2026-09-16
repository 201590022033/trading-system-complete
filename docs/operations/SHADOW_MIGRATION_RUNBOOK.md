# Shadow runtime migration and operator validation

Status: local repair validation only. Railway has **not** been accessed or
deployed. Do not deploy until native PostgreSQL upgrade/concurrency tests pass
on a disposable local database and the remaining forensic gates are closed.

Architecture: one web service, one bounded worker, one PostgreSQL database.
No Redis, Celery, continuous research runs, extra services or live brokerage.

## Explicit migration

1. Operator takes and verifies a database backup through the normal authorized
   process. Never paste connection URLs or backup contents into diagnostics.
2. On an approved database only, set `DATABASE_URL` through secret management.
   Do not run the command against Railway as part of this local repair.
3. Run `.venv\Scripts\python.exe -m scripts.migrate_postgres` (Linux uses the
   environment's `python`). This command does not load `.env` or print the URL.
4. Check `postgres_schema_migrations`: versions 1 and 2 and their checksums must
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

## Validation still required before deployment

Run native PostgreSQL (not the SQLite DB-API emulator) tests for populated
migration repeatability/rollback, JSONB and UTC timestamp adaptation, locks,
simultaneous duplicate contributions, claims, stale owners and status windows.
Then check safe health/status output and process restart using that disposable
database. No external deployment is authorized by this repair program.
