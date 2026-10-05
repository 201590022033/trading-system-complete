# ADR 0036 — Exact strategy attribution without rewriting account history

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Canonical Swing remains pinned to 1.0.1 with exact new-record attribution. Separate 1.1.0 technical, 1.2.0 policy and 1.3.0 AI research do not replace M13 ranking/M14 policy/M15 veto. M16 targets are evaluation requirements, not execution approval; Live remains disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Date: 2026-10-03. Status: Accepted. Scope: attribution-only vertical slice within
the sole ACTIVE operational workspace, following ADR 0035.

New canonical on-demand runs and scheduled paper jobs pin Swing `1.0.1` before
provider acquisition. Shipped `1.0.0` remains resolvable unchanged. This new
version adds lineage, not new indicators, horizons, weights or trading authority.
The paired nullable fields are keyword-only on canonical M11–M18, policy/risk,
intent and paper contracts. Partial references fail. Attributed chains require
exact equality; legacy absence is never interpreted as Swing.

M11 partitions by exact strategy ID/version and requested horizon BEFORE its
existing instrument/regime fallback. Legacy callers see only unattributed
outcomes. Candidate/ETF/benchmark comparisons are likewise version-partitioned;
negative, sparse and immature evidence remain explicit. Current historical
Yahoo reports stay shared research references, not relabelled strategy results.

SQLite migration 0011 and PostgreSQL migration 0006 add immutable-by-repository
definition snapshots/checksums and a compact exact-version record-reference
index. Definitions are insert-only through the application interface, with
conflicting same-version writes rejected. SQL administrative access is not an
immutability/security boundary. Composite foreign keys protect new references.
No columns or rows of existing paper/account/shadow tables are rewritten.
The index intentionally has no foreign key to the hot record table: lossless
archive movement preserves identity and archived read-through.

Account configuration stays unchanged. Existing balance, book and pending plans
retain originating attribution (including NULL); legacy positions may close
normally without becoming new-version evidence. One account still processes
one scheduled cycle per bucket; an existing job owns its original checkpoint.
The exact definition is stored once, not repeated in every daily/skip input;
jobs and frozen inputs retain ID/version/checksum/schema. Retries validate
against the stored definition, not the current registry pin or UI selection.

M16 targets can bind explicitly to profile family/universe-scope tags/intended
horizons. No target or passing thresholds are invented. M17 reference experiment
chains retain exact refs; durable experiment persistence remains separate.
Raw bars/news/source reliability remain shared, and manual APP_INSPIRED journal
notes are not canonical learning attribution. Intraday/Investment stay blocked.

Rollback: disable new attributed scheduling; keep additive tables and immutable
old definitions. Do not drop lineage, reset account cash or backfill history.
PostgreSQL deployment requires explicit migration before web/worker startup.
No Railway migration, push, broker order or deployment is performed here.
