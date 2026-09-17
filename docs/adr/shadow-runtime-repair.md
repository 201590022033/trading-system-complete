# ADR: reuse MI serialization and repository-owned transactions

Status: accepted for local repair; native PostgreSQL deployment validation pending.

The audit found split runtime SQLite/PG state and independently committed writes
inside nominal transactions. Extend the existing repository/store rather than
introduce a queue, service, ORM or alternative scoring path.

Both adapters use repository-owned nested savepoints. PostgreSQL retains bound
parameters and native migration SQL. Its MI view adapts only existing internal
store statements/rows (placeholders, upserts, boolean/JSON/time serialization),
reusing domain serialization instead of duplicating it. Schema changes remain
explicit, additive and version/checksum tracked. No automatic Railway migration.

One bounded worker claims due rows by compare-and-swap and persists heartbeat.
There is no distributed queue or extra worker service. Historical research is
local/on-demand. Native PostgreSQL validation is still required because the
local fixture intentionally emulates types, row locking and FK DDL.
