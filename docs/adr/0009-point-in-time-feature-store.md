# ADR 0009: Append-only point-in-time feature store

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Existing feature/regime/evaluation infrastructure remains reusable. New daily Swing technical/policy versions are isolated research; invalid OHLC and missing dated events still block admission. Six-family local backtests and 30-minute sector-relative radar are proposed, not validated or enabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: Accepted

Date: 2026-09-03

## Context

The forensic reconstruction cannot replay full legacy/adaptive decisions because
historical price values lack dates/revision identity and contextual inputs were
not persisted. HR1 requires one contract for raw and derived market, macro,
technical and source features without future leakage.

## Decision

Add a normalized `HistoricalFeature` contract and append-only JSONL store. Keep
raw and derived records distinct, require lineage for available derived values,
store event/availability/decision clocks, preserve revisions as new records and
enforce `available_time <= decision_time`. Use stable content identity and
revision-aware as-of queries. Keep the feature store research/shadow-only.

JSONL is canonical for v1 because the repository has no declared Parquet engine.
Permit a later reproducible Parquet projection without changing the normalized
record semantics.

## Consequences

Historical loaders and feature builders gain a shared no-lookahead boundary and
explicit missing-data semantics. Storage is not optimized for large analytical
scans yet; HR2 may add partitioned/columnar projection with an explicit
dependency decision. Existing production pipeline interfaces remain unchanged.
