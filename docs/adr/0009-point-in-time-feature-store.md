# ADR 0009: Append-only point-in-time feature store

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
