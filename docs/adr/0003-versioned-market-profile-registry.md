# ADR 0003: Versioned market profile registry

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

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
