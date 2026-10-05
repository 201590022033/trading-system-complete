# ADR 0017 — Point-in-Time Intraday Cross-Asset Alignment

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Intraday CFD remains DEVELOPMENT/DATA_VALIDATION_REQUIRED. HR11/streaming engineering is reusable infrastructure, not an admitted strategy or verified cash-share volume feed. The current Swing deployment uses daily local uploads with streaming disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06 (HR11).

## Decision

Select only source records available by the target cutoff, within source-specific maximum event age. Preserve input IDs and timestamps. Never join by date or fill through stale/gap intervals.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
