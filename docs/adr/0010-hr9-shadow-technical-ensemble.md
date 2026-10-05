# ADR 0010: HR9 shadow technical ensemble

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Railway now hosts durable shared paper/research state and a bounded 08:00 SAST scheduled worker. Local daily collection is at 07:30 SAST. Earlier non-deployment statements are checkpoint-specific; new research records reuse the append-only ledger without a broad strategy migration. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Status
Accepted for HR9 on 2026-09-04.

## Context
HR8 learned conditional technical-indicator effectiveness, but interrupted work
created 101,536 adaptive decisions before HR9 was defined. That implementation
duplicated signal definitions, used a flat per-observation cost in its online
learner, and did not define how its four horizons should be consumed.

## Decision
Preserve `adaptive_technical_decisions.csv` and its SHA-256 as the immutable
pre-HR9 baseline. Use `technical_signals.py` as the single versioned signal
definition for HR8 and HR9. Charge costs per unit of originating signal-state
turnover. Treat 1, 3, 5 and 20 sessions as independent research targets, never
as four votes on one action. Record HR8 evidence-contract identity, sample
counts, input hash, horizon role and cost assumptions on HR9 output.

HR9 remains research/shadow-only and has no Flask, governance, broker or
production-score integration. Promotion requires later robustness evidence.

## Consequences
- HR8 and HR9 cannot silently diverge on indicator signal definitions.
- The pre-HR9 artifact remains reproducible and available for causal comparison.
- HR9 v2 decisions are explainable and independently addressable by horizon.
- Corrected costs change some learned weights and 2,393 of 101,536 actions.
- Negative and unstable net results prevent adaptive promotion.
