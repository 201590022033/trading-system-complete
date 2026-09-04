# ADR 0011: HR10 robustness and provider boundaries

Status: Accepted, 2026-09-04

## Decision

Evaluate HR9 with horizon-aware purge/embargo folds and non-overlapping trades,
then apply deterministic cell-level admission gates. Keep overlapping HR9
diagnostics for comparison but never interpret them as independent trades.

Define vendor-neutral `MarketDataProvider` and `ExecutionProvider` contracts.
HR10 supplies only a paper preview implementation; submit and cancel hard-fail.
No ViewPoint or Shyft authenticated adapter is authorized.

## Consequences

Results are more conservative and may reject every candidate. Provider research
can continue without coupling analysis code to a changing broker platform, and
live execution requires a later explicit ADR and user authorization.
