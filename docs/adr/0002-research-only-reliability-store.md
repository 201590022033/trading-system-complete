# ADR 0002: Research-Only Source Reliability Store

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

- **Status:** Accepted
- **Date:** 2026-09-03

## Context

Adaptive fusion eventually needs source reliability by scope and horizon, but using early or sparse results to change live recommendations would be unsafe. Existing production scoring must remain unchanged while the learning data accumulates.

## Decision

Add `reliability_store.py` with:

- an in-memory `SourceRegistry` for configurable source definitions and authority tiers;
- a SQLite-backed `ReliabilityStore` for evidence outcomes;
- configurable scope keys and horizons;
- duplicate outcome protection using `(evidence_id, scope_key, horizon)`;
- rejection of `evaluated_at` timestamps before `observed_at`;
- conservative shrinkage toward a 50% prior using 20 prior samples.

The store is not connected to production signal weights. Promotion remains a later shadow-mode decision requiring evidence.

## Consequences

- Reliability can be learned by source, sector/ticker scope and horizon without rewriting collectors.
- Small samples cannot produce extreme reliability values.
- The current store is intentionally local and minimal; persistence lifecycle, outcome ingestion and rolling/recency weighting belong to later milestones.
- No broker writes or capital allocation are introduced.
