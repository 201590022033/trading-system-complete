# ADR 0005: Shadow-only adaptive fusion

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Railway now hosts durable shared paper/research state and a bounded 08:00 SAST scheduled worker. Local daily collection is at 07:30 SAST. Earlier non-deployment statements are checkpoint-specific; new research records reuse the append-only ledger without a broad strategy migration. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Status
Accepted for M6 on 2026-09-03.

## Context
Regime, profiles, reliability summaries and expanded features now have explicit
contracts. Combining them is necessary for evaluation, but no walk-forward
evidence yet supports changing default signal weights.

## Decision
Add a separate explainable fusion engine. Normalize available contextual
weights, enforce a minimum-sample reliability gate, log all contributions, and
attach the comparison to `SignalDecision.metadata.adaptive_shadow`. Continue to
derive the public score/action/confidence from the characterized legacy path.

## Consequences
- Every standard signal decision can expose legacy/adaptive disagreement.
- Reliability and context are bounded, inspectable inputs rather than opaque
  end-to-end order prediction.
- Missing shadow context cannot prevent a legacy decision.
- Promotion remains prohibited until M7 evidence and the M10 gate.
