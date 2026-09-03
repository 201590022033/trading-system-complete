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
