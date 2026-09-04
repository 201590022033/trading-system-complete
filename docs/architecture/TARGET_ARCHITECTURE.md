# Target Architecture — Evolutionary Adaptive Intelligence Layer

## Design principle
Insert context and learning **around the current pipeline**. Keep the existing governance system as the decision consumer.

```text
Collectors / adapters already in repo
        |
        v
UnifiedDataPipeline
        |
        +--> Evidence / provenance normalization
        |       |
        |       +--> Source Reliability Engine
        |
        +--> Market Regime Engine
        |
        +--> Sector + Instrument Context Engine
        |
        +--> Macro / cross-asset features
        |
        v
Adaptive Signal Fusion Engine
        |
        +--> legacy fixed score in parallel (benchmark)
        +--> adaptive score in shadow mode
        |
        v
Existing Bull / Bear / General Researchers
        v
Existing Trader -> Risk Agents -> Manager -> Executor
```

## Required architectural properties
- Legacy output remains available as a benchmark and rollback path.
- Adaptive weighting must be explainable: which sources/features contributed and by how much.
- Regime and sector context are explicit objects, not scattered `if ticker == ...` rules.
- Reliability is learned by **source x sector/ticker x regime x horizon**, with shrinkage/fallback when samples are small.
- Backtests can reproduce historical decisions without future leakage.
- Live broker writes are outside this target roadmap.

## Market-data and execution boundary

Future provider adapters sit beside, not inside, research evaluation. A trade
ticket may consume a timestamped, state-labelled `MarketDataProvider` snapshot;
an `ExecutionProvider` may initially preview only. The target workflow is:

`data → analysis → suggested ticket → human review → supported broker handoff → user confirmation`

No authenticated broker adapter or automatic live order path exists in HR10.

OI1 formalizes the handoff objects:

`MarketDataProvider → ResearchDataProvider → SignalEngine → TradeSuggestion → human review → ExecutionProvider → BrokerAccount`

Market and research data retain separate provenance. The canonical suggestion
is non-actionable unless it is admitted, unexpired and directional. Provider
preview remains paper-only; a later live adapter cannot be inferred from these
interfaces and requires its own safety milestone.
