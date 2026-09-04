# ADR 0013: OI2 operational orchestration and truthful degradation

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
