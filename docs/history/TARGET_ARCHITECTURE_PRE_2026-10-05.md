# Historical snapshot — docs/architecture/TARGET_ARCHITECTURE.md

Archived during the 5 October 2026 reconciliation from `c2ef802`. The text below describes earlier checkpoint/design context, not current operational instructions. Original text is preserved; see [the current document](../architecture/TARGET_ARCHITECTURE.md) and [current state](../CURRENT_STATE.md). Historical ACTIVE or planned labels do not activate work.

Original relative links belong to the original source location; use the current-document link above for present guidance.

---

# Target Architecture — Evolutionary Adaptive Intelligence Layer

ADR0043 introduces weekly derived context → local semantic relationships → local
historical archive screen → research flags. Later historical retrieval, dated
SENS/economic events, sector controls and walk-forward testing must precede any
market-correlation claim or trading-weight promotion.

2026-10-04 owner-directed split: local daily OHLC archive → authenticated working
snapshot → online scheduled AI hypothesis research → frozen experiment and
chronological comparison → prospective validation → reviewed strategy version.
ADR0042 implements through retrospective comparison only; no automatic adoption.

## 2026-10-03 strategy-oriented evolution

The owner now directs future canonical development around explicit, versioned
Trading Strategy Profiles. ADR 0035 implements only the foundation and dashboard
discovery shell. Mature M3–M16, source/news, risk and paper components are reused;
the older multi-agent governance below remains a benchmark, not the new canonical
strategy orchestrator. Target Swing pipeline:

`exact StrategyProfile → universe → causal market data/features/catalysts/regime
→ suitability → M13 ranking → Top 5 → M14 policy → execution feasibility/M15 risk
→ paper execution → outcome → exact-version evaluation/learning`

StrategyTarget remains a separate versioned evaluation-requirements contract.
Future generated objects must pin profile ID/version before computation and
retain exact lineage; old decisions stay LEGACY_UNATTRIBUTED. Shared raw data may
remain strategy-neutral. Research ordering is distinct from account economics
and position sizing; M15 remains the final veto. Swing is the first strategy to
mature. Intraday CFD and long-term investing remain truthful development
placeholders until their separate data/validation gates pass. No optimized
weights, generic timeframe switch, live execution or automatic promotion.
See the implementation audit for staged scope, conflicts and migrations.

2026-09-19: the bounded canonical PAPER vertical slice is implemented (ADR 0024).
It does not promote adaptive production weights, provide live execution or solve
cross-broker capital allocation. Target capabilities below remain aspirational
unless explicitly documented in the current architecture and repair runbook.

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
