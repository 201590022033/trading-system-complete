# ADR 0019 — Short-Term Data Quality Grades

Status: accepted, 2026-09-06 (HR11).

## Decision

Research, delayed-public and execution-grade are explicit provenance classes. Intraday bars denote completed interval ends. Local ingestion cannot precede defensible availability. Public/proxy data cannot satisfy an execution-grade gate. No default source is execution-grade.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
