# Persistent Shadow Learning

## Current repair and deployment status

The implementation was repaired following the independent audit of `ea3f3a7`.
See [repair details](SHADOW_REPAIR_LOG.md) and the authoritative
[migration/runbook](../operations/SHADOW_MIGRATION_RUNBOOK.md). Local DB-API
behavior tests do not establish native PostgreSQL compatibility. Deployment is
not approved; Railway has not been accessed during repairs.

An observation freezes causal history and research metadata. The canonical
OperationalIntelligence path receives explicit as-of context; research fields
never affect its formula. Default shadow horizon is five supplied sessions
(`5`), not the UI label `swing`. Missing/unsupported session calendars fail
closed. Price timestamps and availability must match entry and target. The
existing signal_outcome helper receives raw returns once and previous-position
turnover; HOLD is labelled separately from active wins/losses.

Ledger contexts are recursively immutable; immutable identity collisions fail
explicitly. Outcomes require persisted ancestry and canonical arithmetic.
Contribution markers and aggregate updates share a transaction. Completed jobs
are authoritative; only expired retryable RUNNING jobs are recovered. One job
per 30-second cycle is the CLI default, with five attempts maximum.

LearningStatus reports bounded UTC event windows (future records excluded),
separate unavailable outcomes, actual contribution events and persisted worker
heartbeat timestamps. Runtime reliability shares this repository and retains
the existing summary rounding/prior. There is no automatic production promotion.

The runtime loop is incremental and broker-independent:

`market observation → existing production-path shadow decision → pending outcome → matured label → shadow evidence`.

Observations contain only information available at their timestamp. Outcomes are separate and are labelled only after the canonical horizon. Missing causal market data is recorded as `OUTCOME_DATA_UNAVAILABLE`; it is never guessed.

## State boundaries

Historical research is frozen/backtest evidence and remains local/on-demand. Persistent shadow learning stores durable observations, decisions, labels and evidence. Production adaptive state is a separately governed state and is never changed by this loop. Shadow evidence cannot automatically promote itself into production weights.

## Minimum Railway resource principle

Railway consists of one web service, one bounded worker, and PostgreSQL. The worker checks due jobs cheaply, processes bounded work, persists a checkpoint, and sleeps when no work is due. It does not rerun historical research, continuously analyse unchanged documents with an LLM, warehouse unnecessary market data, or train models.

## Deployment runbook

1. Review the additive PostgreSQL migration SQL and take the normal database backup.
2. Apply migrations in version order, beginning with the existing schema and then the shadow-learning migration.
3. Configure `DATABASE_URL`, `APP_MODE`, `PORT`, `COMMIT_SHA`, and `WORKER_ID` without placing secrets in source.
4. Run the web service and the existing minimal worker service separately.
5. Verify `/health` and `/api/learning/status`; confirm counts and timestamps are database-backed.
6. Roll back application code first if needed. Do not drop tables or reset existing Railway data.

Railway deployment and live migration are intentionally not performed by this milestone.

Required runtime variables are `DATABASE_URL`, `APP_MODE`, `PORT`, `COMMIT_SHA`,
and `WORKER_ID`. Values are supplied by the deployment secret manager and are
never returned by status endpoints. PostgreSQL migrations are additive and must
be reviewed and applied in version order before switching the web or worker
process to the new release.
