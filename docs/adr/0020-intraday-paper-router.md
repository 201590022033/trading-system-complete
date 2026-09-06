# ADR 0020 — Paper-Only Short-Term Routing

Status: accepted, 2026-09-06 (HR11).

## Decision

A pure paper preview maps an admitted, fresh, costed research decision to its exact instrument. No broker implementation, account credentials or network path is introduced. Live submit and cancel hard-fail using the existing execution exception.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
