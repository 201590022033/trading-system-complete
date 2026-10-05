# Roadmap — reconciled 5 October 2026

This is the current dependency sequence. [Current state](../CURRENT_STATE.md) is the capability inventory; [recent changes](../changes/2026-09-21-to-2026-10-05.md) is the dated implementation history. Earlier accumulated roadmap entries remain in [the checkpoint archive](../history/ROADMAP_PRE_2026-10-05.md). Old ACTIVE labels there are historical, not concurrent work.

| Slice | Current status | Evidence limit |
| --- | --- | --- |
| Canonical M13–M16 and durable paper workflow | Implemented | Real costs, liquidity and prospective edge unproven |
| Printable worksheet / manual Demo journal | Implemented | Self-reported fills, no broker order mutation |
| Session-aware daily v3 worker and cash/ETF research separation | Implemented | Exchange calendar and ETF execution not admitted |
| Strategy Profiles and exact version lineage | Implemented | Cards are descriptive, two strategies are placeholders |
| Swing 1.1.0 technical / 1.2.0 policy replay | Implemented research-only | Real OHLC quality still blocks admission |
| IG/Alpha provider investigation and display estimates | Implemented probes/diagnostics | JSE entitlement/coverage unresolved; estimates excluded |
| Local daily archive and cloud 1.3.0 comparison | Implemented bounded research | Zero closed first holdout samples; no automatic promotion |
| Monday brief and local Ollama research flags | Implemented bounded research | Single-publisher first cases, zero flags/boosts/samples |
| Project-wide documentation reconciliation | Completed; acceptance in CURRENT_MILESTONE | No trading behavior/configuration changes |

## Recommended next milestone

**B1: local backtest data/time contracts and independent oracle harness** — proposed, not ACTIVE. The owner has prioritised proving the engine before the wider loop. The [engine specification](../research/LOCAL_BACKTEST_ENGINE_SPEC.md) inventories reusable code and defines B1–B5 acceptance. First freeze offline fixtures, session/availability manifests, admission rules and independently hand-calculated daily replay expectations. Six-family input requirements inform these contracts; strategy optimisation and new cloud behaviour wait.

[Refinement 0.2](../research/SWING_RULE_REFINEMENT.md) now specifies the candidate entry/trailing/exit matrix, volume contribution controls and pooled momentum-personality tests. These proposed parameters still require data admission and implementation; none is an installed or validated rule.

Then, in order (each gate is a separate milestone):

1. B2: deterministic daily replay, trailing and portfolio accounting; conservative fills, costs and causal invariants; preserve legacy replay benchmark.
2. B3: independent FX/gold adapters and synthetic market-specific tests, without broker mutations.
3. B4: bounded indicator selection, nested chronological evaluation, contamination/trial register and eligible/control cohorts.
4. B5: independently audit a verified real-data slice, stress costs/liquidity, compare genuine intraday evidence where available and record engine acceptance/limitations.
5. Freeze six hypothesis catalogues and run local historical candidates plus prospective shadow comparisons. [Feedback design](../research/ADAPTIVE_SWING_FEEDBACK_LOOP.md) keeps indicator reviews independent per hypothesis.
6. Add optional real 30-minute radar/refinement, dated event retrieval and local Ollama categorisation, then selective evidence/control uploads and the feedback dashboard in dependency order.
7. Require sufficient independent prospective evidence and existing risk gates before adopting any research version. No automatic production promotion.

Do not collapse semantic news matching into measured price correlation, FX tick volume into traded-share volume, or historical holdout comparisons into prospective proof. Intraday CFD and long-term investment remain separate later programs. Live execution is outside this roadmap. Exactly one milestone may be ACTIVE; completed historical documents do not start another.
