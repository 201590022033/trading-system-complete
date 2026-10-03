# Swing narrative implementation check — 2026-10-03

The imported R200/3–5-session narrative is a research design, not evidence of
profitability or factual Standard Bank fees/fractional access. Its two proposed
weight sets are untested hypotheses, not implemented optimized configurations.
This check distinguishes reusable code from active workflow behavior.

## Attribution acceptance (ADR 0036)

New exact Swing `1.0.1` runs carry paired profile identity/version through M11
estimates, M12 suitability, M13 opportunities, M14 policy, M15 approval, intent,
paper orders/fills/positions/book, closed outcomes, candidate decisions and
comparisons. API/UI expose that identity; old records expose LEGACY_UNATTRIBUTED.
M16 target/metric and M17 reference experiment chains can carry and validate
the same identity. The optional target binding creates no target thresholds.
Jobs freeze identity/hash before acquisition and retry from immutable stored
definitions. Additive SQLite/PostgreSQL migrations preserve existing accounts
and archives; legacy positions close under their original lineage. M11 cannot
borrow another profile/version/horizon through global fallback.

## Requirement-by-requirement state before the next Swing feature stage

| Narrative requirement | Verified implementation / current limitation |
|---|---|
| Three real versioned strategy profiles | Implemented; Intraday/Investment remain development-only |
| Daily decision, 3–5-session hold | Ranking evidence is `1d`; paper holds 3 sessions. Historical context covers 3/4 only. No full 3/4/5 Swing loop yet |
| Liquid JSE universe; spread/gap rejection | Curated cash registry and observed volume cap exist; no certified Top40/midcap liquidity/spread admission |
| EMA20 / EMA50 | EMA primitives exist in `research_indicators.py` and `domain/features/technical.py`; registry `ema_structure` is PLANNED. No active EMA20/50 Swing model |
| RSI14 | Runtime momentum/RSI screen exists; canonical Wilder candidate also exists but is not the active screen |
| ATR14 | OHLC-gated true-range calculator exists; worker retry inputs currently retain only close/volume. ATR is not active Swing stop validation |
| Average/relative volume | Research calculator exists; paper uses volume participation, not a separate volume-confirmed Swing ranking |
| 10/20-session structure | Legacy close breakout and 20-close paper stop exist; no validated narrative breakout/pullback policy |
| JSE/sector relative strength | Benchmark-gated calculator and exact-session STX40 historical context exist; sector-relative Swing model is not wired |
| 30-minute entry timing | Chart display/HR11 infrastructure only; session, bid/ask and cost validation missing |
| Structured SENS catalysts | Current causal news/opinion/provenance exists; typed catalyst/materiality/event-horizon model is not implemented |
| Results/ex-date/macro event blackout | No authoritative causal event calendar or deterministic blackout gate yet |
| Entry, structure + ATR stop, ≥2R target | Close-only simulator has preceding-20-close stop and configured 2R; not ATR-sanity-tested or a live order guarantee |
| Trail after +1R; day-3 review / day-5 exit | Not implemented. Simulator has 3-session/time-expiry and observed-close exits; no trailing rule |
| R200 risk budget; whole/fractional models | M15 monetary risk and whole-share simulator exist. Real OST cash/fees/fractional availability are not configured |
| Account feasibility separate from rank | Boundaries retained; existing instrument-cost rank penalty unchanged. Actual OST net reward/risk gate remains missing |
| Record predictions and alternatives before outcome | Immutable frozen ranking and screened-candidate panel exist; exact-version lineage added now |
| Learn more than BUY/not BUY | M11 estimates attributable feature/strategy outcomes; panel compares selected/other shares by market state. No proof of predictive edge or AI retraining |
| Technical-only/news/regime ablations; walk-forward edge | Evaluation/experiment/metric infrastructure exists, but this new Swing strategy has no completed preregistered cost-aware comparison |
| Sharpe | Canonical context-explicit calculator exists; not a current Swing decision input or validated online Sharpe result |
| Automated live broker execution | Prohibited/disabled. Manual OST handoff only; attribution does not enable orders |

## Ordered continuation

1. Complete/test/document/commit attribution (this slice).
2. Owner's follow-up authorizes the core Swing feature and horizon shadow slice:
   causal completed OHLCV; EMA20/50, RSI14, ATR14, volume and 10/20-session
   structure; exact benchmark alignment; separate 3/4/5-session labels and
   exact-version learning with compact snapshots. Missing inputs must block
   dependent features, never be fabricated. Preserve current rank/paper baseline.
3. Only afterwards define/test catalyst and event-risk rules, breakout/pullback
   geometry, trailing/time rules, account-specific costs and comparative
   walk-forward validation. No blanket "all in place" or profitability claim.

The intended end-to-end decision model is not complete at attribution acceptance.
Live behavior, actual OST economics and online Railway collection require
separate factual acceptance; local tests cannot establish deployment state.
