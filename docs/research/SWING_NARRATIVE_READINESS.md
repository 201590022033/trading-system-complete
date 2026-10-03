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

## Requirement-by-requirement state after core technical shadow wiring (ADR 0037)

| Narrative requirement | Verified implementation / current limitation |
|---|---|
| Three real versioned strategy profiles | Implemented; Intraday/Investment remain development-only |
| Daily decision, 3–5-session hold | Separate Swing 1.1.0 shadow stores independent 3/4/5 observed-session forward returns. Benchmark ranking remains `1d`, simulator holds 3 sessions. Shadow labels are not variable-hold execution |
| Liquid JSE universe; spread/gap rejection | Curated cash registry and observed volume cap exist; no certified Top40/midcap liquidity/spread admission |
| EMA20 / EMA50 | Calculated from full causal acquisition history, frozen before 60-bar truncation and displayed. Shadow trend/reclaim rules use them; legacy rank remains unchanged |
| RSI14 | Continuous Wilder RSI14 is calculated/displayed and forms a preregistered 50–70 candidate cohort; benchmark threshold RSI remains separate |
| ATR14 | Real normalized OHLC retained. Wilder true-range smoothing calculated/displayed; structural/one-ATR stop and 2R reference geometry provided. Not execution admission/trailing |
| Average/relative volume | Prior-20-session average excludes current bar; relative-volume value and above-average cohort wired into shadow setup |
| 10/20-session structure | Prior OHLC highs/lows exclude current session. Shadow 20-high breakout, EMA reclaim and 10-low reference stop; execution validation remains open |
| JSE/sector relative strength | Exact-date broad STX40 20-session excess return and cohort wired; missing/stale/misaligned benchmark is unavailable. Sector-relative model remains a gate |
| 30-minute entry timing | Chart display/HR11 infrastructure only; session, bid/ask and cost validation missing |
| Structured SENS catalysts | Current causal news/opinion/provenance exists; typed catalyst/materiality/event-horizon model is not implemented |
| Results/ex-date/macro event blackout | No authoritative causal event calendar or deterministic blackout gate yet |
| Entry, structure + ATR stop, ≥2R target | Shadow signal-close reference stop uses lower of prior-10 low and close minus ATR, target 2R. Actual simulator retains preceding-20-close stop; new labels use next observable close, not stop/target fills |
| Trail after +1R; day-3 review / day-5 exit | Not implemented. Simulator has 3-session/time-expiry and observed-close exits; no trailing rule |
| R200 risk budget; whole/fractional models | M15 monetary risk and whole-share simulator exist. Real OST cash/fees/fractional availability are not configured |
| Account feasibility separate from rank | Boundaries retained; existing instrument-cost rank penalty unchanged. Actual OST net reward/risk gate remains missing |
| Record predictions and alternatives before outcome | Immutable frozen ranking and screened-candidate panel exist; exact-version lineage added now |
| Learn more than BUY/not BUY | Version/horizon-isolated M11 cohort estimates for trend, breakout, reclaim, RSI, volume, benchmark strength and combined setup; present/absent cohorts and negative outcomes retained. Overlapping observations are not independent, causal indicator attribution or proof of edge |
| Technical-only/news/regime ablations; walk-forward edge | Evaluation/experiment/metric infrastructure exists, but this new Swing strategy has no completed preregistered cost-aware comparison |
| Sharpe | Canonical context-explicit calculator exists; not a current Swing decision input or validated online Sharpe result |
| Automated live broker execution | Prohibited/disabled. Manual OST handoff only; attribution does not enable orders |

## Ordered continuation

1. Attribution accepted and committed as `781c0ab`.
2. Core technical/horizon shadow slice implemented; acceptance recorded in
   CURRENT_MILESTONE. Shared Yahoo acquisition only; one feature decision per
   instrument/session/version plus three compact outcome records. Retry uses
   frozen full-history values and pinned definition. Core setup is a candidate
   hypothesis, not a promoted ranking or executable strategy.
3. Only afterwards define/test catalyst and event-risk rules, breakout/pullback
   geometry, trailing/time rules, account-specific costs and comparative
   walk-forward validation. No blanket "all in place" or profitability claim.

The intended end-to-end execution model is not complete at technical-shadow acceptance.
Live behavior, actual OST economics and online Railway collection require
separate factual acceptance; local tests cannot establish deployment state.
