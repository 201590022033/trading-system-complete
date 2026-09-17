# M7 — Early Railway Foundation Validation

## Current shadow release — 2026-09-17

The operator evidence below applies only to the historical M7 release, not the
new shadow-learning migrations or runtime. This repair program has not accessed
or deployed Railway. New deployment remains blocked pending native disposable
PostgreSQL validation. Architecture stays one web + one bounded worker + one
PostgreSQL database. `/health` now tests schema reachability, and the worker
entrypoint executes bounded due jobs rather than merely printing a heartbeat.
Follow [the current runbook](../operations/SHADOW_MIGRATION_RUNBOOK.md).

## Status

**COMPLETE — 2026-09-09**

M7 was closed from operator-observed Railway evidence. The coding workspace did
not access Railway directly; the external results below were supplied by the
operator and recorded without extending them beyond what was observed.

## External validation

- Web service deployed and publicly reachable.
- Gunicorn listened on `0.0.0.0:8080`; `/health` returned HTTP 200.
- Health reported `mode=RESEARCH`, `live_execution=false`, and
  `database=CONFIGURED_POSTGRES`.
- The separate `trading-worker` service deployed with
  `python -m workers.heartbeat`, emitted recurring structured heartbeats, and
  resumed after redeployment.
- Railway PostgreSQL write validation passed for source policy, evidence,
  clustered event and audit records using IDs prefixed `M7_VALIDATION_`.
- After a fresh Web container redeployment, verify mode found the same records.
  Persistence across redeployment therefore passed.
- The validation utility includes a transaction rollback probe in `write`; the
  rollback check passed as part of the reported `PASS WRITE` run.
- UTC timestamp round-trip passed.

## Local and safety validation

The local safe suite passed 281 tests with zero failures. The immutable research
baseline remained 39/39 verified and unchanged. Local regression coverage
requires `DATABASE_URL` and prevents silent SQLite substitution in the
PostgreSQL path. No deliberate production database outage test was performed.

Operator review of supplied Web, Worker and PostgreSQL logs found no
credentials, passwords, tokens, broker keys or `DATABASE_URL` contents. No
headed browser dependency is part of the Railway startup path. No trading
behavior was activated.

## Evidence boundary

Local automated tests establish code behavior and fail-closed configuration.
Railway deployment, health, Worker, PostgreSQL round-trip and restart results
are manually observed external evidence supplied by the operator. The project
does not claim that the coding workspace itself connected to Railway.

Next milestone: **M8 — Preserve & Migrate HR11 Causal Core [NOT STARTED]**.
