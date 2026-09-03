# ADR 0008: Additive multi-agent intelligence context

## Status
Accepted for M9 on 2026-09-03.

## Context
Adaptive explanations must reach the existing Bull/Bear/General research flow
without replacing or silently changing Trader, Risk, Manager or Executor
governance.

## Decision
Add an `intelligence_context` field to `MarketObservation` and populate it via a
separate adapter. Researchers append the profile/regime/adaptive summary to
their text but retain existing stance and confidence logic. Emit disagreement
telemetry in the step result. Label simulated execution explicitly as `paper`.

## Consequences
- Existing agent method signatures remain stable.
- Explanations are available to dashboards/logging without affecting votes.
- A context-disabled compatibility test proves proposal, risk assessments and
  manager decision remain identical.
- No broker or live-execution path is introduced.
