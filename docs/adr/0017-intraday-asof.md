# ADR 0017 — Point-in-Time Intraday Cross-Asset Alignment

Status: accepted, 2026-09-06 (HR11).

## Decision

Select only source records available by the target cutoff, within source-specific maximum event age. Preserve input IDs and timestamps. Never join by date or fill through stale/gap intervals.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
