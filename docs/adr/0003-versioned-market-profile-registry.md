# ADR 0003: Versioned market profile registry

## Status
Accepted for M4 on 2026-09-03.

## Context
Ticker-specific macro coefficients were embedded in `JSESignalEngine`. M4
requires explicit sector/instrument context without changing the characterized
legacy signal path or prematurely enabling adaptive behavior.

## Decision
Add immutable, versioned `MarketProfile` objects and a configurable in-memory
`ProfileRegistry`. Move the existing macro coefficients into default ticker
profiles, retain a generic single-stock fallback, and emit selected profile
identity as shadow-only decision metadata.

## Consequences
- Existing macro scores remain numerically compatible and testable.
- Profile selection is reusable by later indicator, fusion and evaluation work.
- Unknown instruments receive neutral macro sensitivities rather than guessed
  sector exposure.
- Richer macro channels remain research hypotheses for later evidence gates.
