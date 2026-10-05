# ADR 0021 — Preserve Deferred OI3 While Activating HR11

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Intraday CFD remains DEVELOPMENT/DATA_VALIDATION_REQUIRED. HR11/streaming engineering is reusable infrastructure, not an admitted strategy or verified cash-share volume feed. The current Swing deployment uses daily local uploads with streaming disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06 (HR11).

## Decision

The owner explicitly requested implementing HR11 while OI3 external AI/source prerequisites remain incomplete. Record OI3 as DEFERRED, preserving its code, commits and outstanding checklist; HR11 is the sole ACTIVE milestone. This documented transition implements the newer mandate and does not claim OI3 completion.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
