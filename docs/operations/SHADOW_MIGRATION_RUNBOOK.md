# Persistence migration and deployment validation — current boundaries

Reviewed 5 October 2026. Current operating guidance is [the v3 paper runbook](../repair/PAPER_LOOP_RUNBOOK.md) and [current state](../CURRENT_STATE.md). The earlier shadow repair's native PostgreSQL results and accepted rollback constraints remain in [the historical migration record](../history/SHADOW_MIGRATION_RUNBOOK_PRE_2026-10-05.md); do not treat its old deployment restriction as today's hosting state.

## Explicit migrations only

Web/worker startup does not migrate PostgreSQL. Before a schema change, review the actual migration files and target, arrange a backup/recovery plan, and supply secrets privately. A documentation deploy requires no migration. Existing profile attribution and newer append-only research records did not require a broad persistence rewrite.

`python -m scripts.deployment_preflight --check-database` is a read-only preflight requiring a clean checkout and private deployment settings. It rejects Live mode, requires PostgreSQL, and performs a connection check; it does not invoke Railway or migrate. Do not print DATABASE_URL or full environment listings.

For a separately authorized migration target, `python -m scripts.migrate_postgres` applies the checked-in additive migrations. Applied version/checksum records and SQL share a transaction/advisory lock. Do not edit an applied migration or drop/reset tables. Missing/invalid legacy evidence stays excluded from new contributions, not repaired with invented prices or labels. Review schema readiness before starting the services.

## Shared state and worker schedule

Web and worker use the same PostgreSQL repository. A configured PostgreSQL failure never silently falls back to SQLite. For isolated local checks, use a distinct SQLite path and disable inherited dotenv/configuration as in [Quick Start](../../QUICKSTART.md).

Current Railway deployment is one web service, one bounded daily worker and PostgreSQL. The worker cron is 06:00 UTC / 08:00 SAST and exits after work. Continuous heartbeat mode remains a CLI capability, not the current deployment schedule. Completed jobs and frozen inputs are authoritative; retries cannot recreate market observations or duplicate outcome contributions.

The current daily source is LOCAL_UPLOAD. Missing uploads, invalid OHLC, unsupported instruments and absent entitlement remain visible failures. Separate local weekly-news receipts/outboxes support delivery retry without another model call. Research and journal accounts are separate from simulator cash.

## Acceptance and recovery

Run the offline suite and protected-artifact verifier. Native database concurrency/recovery validation belongs only on the guarded disposable localhost validator. For an actual deployment, separately inspect health, committed paper cycles, data freshness and idempotent research delivery. Roll back application code when appropriate; never erase durable state to make a health check pass.

This runbook does not authorize a production migration, provider request, new model call or broker order. Research remains shadow/paper; Live execution stays disabled.
