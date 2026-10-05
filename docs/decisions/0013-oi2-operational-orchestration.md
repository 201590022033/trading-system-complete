# ADR 0013: OI2 operational orchestration and truthful degradation

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

The current dashboard has six sections including backend-populated Trading Strategies and the canonical Top-5. Older multi-agent/mock/merge designs remain historical context; they do not describe the default ranking path. Paper/connected cash and self-reported trades stay separate. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

- Status: Accepted
- Date: 2026-09-04

## Decision

Use a canonical run/component contract with per-component provenance and data
state. Use frozen HR7 point-in-time data as the reliable offline default. Permit
network providers only on explicit requests. Preserve the legacy signal as the
benchmark and keep it research-only. Return partial results when optional sources
fail. Centralize instrument aliases and expose exactly 30 evidence gates.

No broker submit/cancel capability is implemented; manual handoff remains locked
while no strategy is admitted.
