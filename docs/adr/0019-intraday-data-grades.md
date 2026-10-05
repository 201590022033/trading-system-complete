# ADR 0019 — Short-Term Data Quality Grades

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Intraday CFD remains DEVELOPMENT/DATA_VALIDATION_REQUIRED. HR11/streaming engineering is reusable infrastructure, not an admitted strategy or verified cash-share volume feed. The current Swing deployment uses daily local uploads with streaming disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06 (HR11).

## Decision

Research, delayed-public and execution-grade are explicit provenance classes. Intraday bars denote completed interval ends. Local ingestion cannot precede defensible availability. Public/proxy data cannot satisfy an execution-grade gate. No default source is execution-grade.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
