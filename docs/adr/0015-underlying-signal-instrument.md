# ADR 0015 — Separate Underlying, Signal Target and Tradable Instrument

Status: accepted, 2026-09-06 (HR11).

## Decision

Add immutable intraday InstrumentDefinition records around the existing UI registry. Cash/proxy/derivative identities are distinct. Unverified contract metadata stays null; execution symbols never enable live trading.

## Consequences

Existing daily research and dashboard interfaces remain unchanged. New behavior
is versioned, research/shadow-only and tested before stage advancement.
