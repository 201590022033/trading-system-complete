# ADR 0027 — Isolate the streaming PostgreSQL writer

Date: 2026-09-22. Status: accepted within the active Operational demo workspace.

## Context

The Railway worker crashed after normal operation when an IG Lightstreamer
callback saved an observation while the main worker finalized the durable job.
Both threads shared one `PostgresRepository` connection. Their transaction
scopes interleaved, so releasing the outer PostgreSQL savepoint removed the
other thread's nested savepoint. Job finalization then raised
`InvalidSavepointSpecification` and terminated the process.

Serializing callbacks against other callbacks was insufficient because it did
not serialize a callback against the scheduler, job finalization or heartbeat
paths on the main worker thread.

## Decision

Each bounded PostgreSQL streaming run owns a dedicated observation repository
and connection. Lightstreamer callbacks use only that repository; the main
worker repository remains exclusive to scheduling, job state and heartbeat
work. Callback writes remain serialized with a lock.

Shutdown disconnects the stream, takes the callback lock to drain an active
write, marks the run closed to further observations, records the final accepted
count and closes the dedicated repository. A callback delivered after that
boundary is ignored. SQLite tests retain the existing injected repository and
do not create an unnecessary second connection.

## Consequences

- PostgreSQL savepoints cannot interleave across the stream and job threads.
- One additional bounded database connection exists only during an enabled
  streaming job and is closed deterministically.
- Late SDK callbacks cannot write through a closed connection.
- Observation identity and immutable deduplication remain unchanged.
- This changes no ranking, risk, broker execution or live-trading boundary.

Regression coverage injects a PostgreSQL-shaped main repository that fails if a
callback touches it, a separate writer, and an intentionally late callback after
disconnect. The test verifies one accepted observation, deterministic writer
closure, no late exception and no second write.
