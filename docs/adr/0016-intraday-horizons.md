# ADR 0016 — Separate Intraday and Session Horizon Families

Status: accepted, 2026-09-06 (HR11).

## Decision

Keep daily 1/3/5/20 contracts immutable. New minute:5/15/30/60 and session_close:EOD IDs carry explicit units, roles and versions. EOD uses supplied session close, not calendar midnight.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
