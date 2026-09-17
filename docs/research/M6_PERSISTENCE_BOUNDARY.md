# M6 persistence boundary

## Current extension — 2026-09-17

The historical M6 inventory below predates persistent shadow learning. Current
web MI, worker, ledger, LearningStatus and runtime reliability share the selected
repository. SQLite remains local; PostgreSQL uses native versioned migrations
and a narrow parameterized adapter reusing MI serialization. Explicit nested
transactions own commits, and SQLite write scopes reserve the writer before
read/modify/write operations. The separate in-memory ReliabilityStore is for
isolated research/tests, not runtime composition.

See [migration/runbook](../operations/SHADOW_MIGRATION_RUNBOOK.md). Native
PostgreSQL locking/type/upgrade tests remain pending. The local SQLite-emulated
DB-API contract is not evidence of native PostgreSQL validation.

## Existing state inventory

SQLite currently stores market-intelligence source policies, evidence records,
audit rows, narratives and ticker selections through
`MarketIntelligenceStore`. Historical research CSV/JSON artifacts are tracked
files and remain immutable. Reliability state has its separate research store.
Dashboard feed caches, `OperationalIntelligence.runs`, `DataBuffer` windows,
portfolio CSV state and transient streaming/provider state remain ephemeral.

## Repository boundary

`persistence.repository.StorageRepository` defines domain-oriented operations
for source policies, evidence, clustered events and audit events. The
`SQLiteRepository` delegates existing source/evidence/audit behavior to
`MarketIntelligenceStore`; M5 clustered events use one additive, versioned
SQLite migration. No existing table is altered or deleted.

`get_storage_repository()` selects SQLite when `DATABASE_URL` is absent and a
PostgreSQL adapter when it is a PostgreSQL URL. The PostgreSQL adapter accepts
an injected DB-API connection/factory, uses parameterized-boundary design and
transaction commit/rollback semantics, but no live PostgreSQL server or driver
was available in this environment. Its integration remains unvalidated.

No business logic branches on backend type, and no application-wide runtime
cutover occurs in M6. Source weighting, clustering influence and trading
decisions remain unchanged.

## Schema and concurrency

The only migration is additive `0002_clustered_events.sql`; existing SQLite
data remains readable. SQLite reuses the current single connection and locking
behavior and is not claimed suitable for unlimited multi-process writes.
PostgreSQL concurrency and managed deployment validation are deferred to M7.
