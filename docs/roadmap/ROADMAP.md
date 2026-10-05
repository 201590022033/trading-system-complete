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

**Six-family Swing hypothesis contracts and admissible-data plan** — proposed, not ACTIVE. Specify entry/exit/volume/benchmark/event contracts separately for selected JSE stock, mining/resources, industrial/global exposure, banks/financials, USD/ZAR and gold. Audit real-data coverage before defining automatic radar admission.

Then, in order:

1. Implement local daily causal backtests with controls, bounded indicator searches and immutable experiment lineage.
2. Admit optional real 30-minute data and same-slot volume/sector-relative radar with documented missing-data states.
3. Retrieve verified dated SENS/news/economic records before local Ollama categorization; enforce point-in-time availability.
4. Send selective derived investigations plus denominator/control summaries to Railway with durable local outboxes.
5. Run prospective walk-forward comparisons, realistic cost/liquidity sensitivity and sufficient independent samples before any promotion.

Do not collapse semantic news matching into measured price correlation, FX tick volume into traded-share volume, or historical holdout comparisons into prospective proof. Intraday CFD and long-term investment remain separate later programs. Live execution is outside this roadmap. Exactly one milestone may be ACTIVE; completed historical documents do not start another.
