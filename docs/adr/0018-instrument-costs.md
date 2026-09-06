# ADR 0018 — Instrument-Specific Cost Modelling

Status: accepted, 2026-09-06 (HR11).

## Decision

Require versioned externally supplied or explicitly assumed fee schedules per instrument/timeframe/liquidity regime. Charge absolute originating state turnover with separate spread, fees, slippage and elapsed-time financing. Unknown costs prevent admission.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
