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

Owner decision, 5 October 2026: **B5 PARTIAL_CLOSED; R1 read-only research integration ACTIVE.** ADR 0051 supersedes the historical deferral statements below. R1 exposes verified software/report evidence and provisional source comparisons; it does not certify real-data replay or activate trading. Deferred RAW/action, intraday semantics and real-trade audit gates remain visible.

Latest B5 audit preparation adds an independent 36-case observed-price cash reference with 72 matching directional fee checks; it does not admit data or run engine replay. Source research corroborates dividends and identifies OST ordinary/ADR payment-date mixing. Mandatory cash-source RAW/action and intraday semantics remain unresolved. Execution readiness and unsupported FX/gold are separate from the specification's permitted scoped cash research acceptance. See ADR 0050 and the continuation record; B5 remains incomplete.

Autonomous continuation update: official pilot daily calendar/hours are now captured; OST/IRESS daily prices and volumes match all 23 dates, and native IRESS UTC OHLC matches 177 table rows. Opt-in directional OST fees and 368 post-hoc cost/capacity cases are delivered. 921 safe tests, eight killed defects and 54 protected checks pass. Full B5 remains externally BLOCKED on action/adjustment completeness, intraday interval/volume definitions and execution/product evidence. The following integration milestone remains deferred. See [continuation evidence](../research/LOCAL_BACKTEST_B5_CONTINUATION.md).

**B5: real-data engine acceptance — BLOCKED.** B1–B4 are implemented in an isolated local lane. The resumed full B5 attempt froze 23 daily/368 actual intraday Yahoo SOL bars, verified issuer identity, investigated Alpha/IG and stressed published fees. No complete daily/intraday aggregates reconcile; calendar/action/product/fill evidence still blocks admission and independent real trades. Final software verification passes 906 safe tests, seven killed defects and 54 protected artifacts. See [dated B5 evidence and precise blockers](../research/LOCAL_BACKTEST_REAL_DATA_ACCEPTANCE.md). Complete these gates before the following integration milestone; no adaptive-loop rollout is active.

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

Implementation update: B1 completed locally; see LOCAL_BACKTEST_IMPLEMENTATION.md for evidence. B2 remains next.

B2 completed locally: deterministic replay/accounting with frozen benchmark reconciliation. B3 is next; B5 real-data acceptance remains separate.

B3 completed locally with market-specific synthetic verification. B4 chronological experiments next; real FX/gold execution evidence remains unresolved.

B4 completed locally: bounded indicator trials and chronological locked evaluation. B5 audit/acceptance next. No strategy adopted.

B5 software/audit delivery complete; external-data acceptance BLOCKED. No subsequent milestone activated. 900 safe tests and 54 protected artifacts pass; seven defects killed.
