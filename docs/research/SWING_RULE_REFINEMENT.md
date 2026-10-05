# Swing entry, trailing and exit research — proposal 0.2

Prepared 5 October 2026. This refines the [six hypothesis families](SIX_SWING_HYPOTHESES.md), not the installed strategy. All thresholds, indicator selections and weights below are preregistered research candidates, not validated trading recommendations. Canonical profile 1.0.1 and frozen research versions 1.1.0–1.3.0 remain unchanged.

## What the South African evidence supports

The reviewed literature gives candidates and reasons to test them; it does not establish an accurate entry/trailing/exit indicator for each JSE sector over a 3–5-session holding window. Several studies use indices or month-scale formation/holding periods. Their results cannot be translated into a short Swing edge or ticker-specific hit rate. Abstracts and accessible repository/publisher text were reviewed; inaccessible full-text details were not inferred.

| Primary source | Documented finding / scope | Consequence for this proposal |
| --- | --- | --- |
| [Kilani, Wits, 2021 — mining moving averages](https://wiredspace.wits.ac.za/items/5205d43c-5544-4a2c-a9fa-589877267049) | Mining shares, 2007–2017; performance varied with moving-average settings and price resolution, without one consistent parameter trend | Test sector/share differences; do not announce a best mining EMA |
| [Ramaube, UJ, 2021 — volatile SA markets](https://ujcontent.uj.ac.za/esploro/outputs/graduate/The-profitability-of-technical-analysis-during/9914907207691) | Top-40, 2007–2019; dual moving-average/RSI rules were not profitable overall | Include rejected/no-edge outcomes; combining indicators alone is insufficient |
| [Pieterse, UP, 2021 — technical strategies versus indices](https://repository.up.ac.za/items/2202bb2f-322e-49ad-a92a-330e1082d5e7) | Includes JSE Top-40; moving-average families, ROC, RSI and Bollinger; costs eroded much of the apparent return | Net expectancy and cost sensitivity take priority over hit rate |
| [Lourens, Wits, 2011 — price momentum and volume](https://wiredspace.wits.ac.za/items/162d87a9-3f79-4a1a-84a9-22cc1b43539e) | Formation/holding periods up to a year; volume related to momentum magnitude/persistence | Test volume interactions, but independently validate the 3–5-session horizon |
| [Page, Britten and Auret, 2013 — momentum and liquidity](https://dergipark.org.tr/en/pub/ijefs/article/275537) | JSE, 1995–2010; liquidity-conditioned momentum differed, with inconsistent low-liquidity results | Keep executable liquidity separate from a predictive volume flag |
| [Metghalchi et al., 2021 — two SA indices](https://www.tandfonline.com/doi/abs/10.1080/23322039.2020.1869374) | Tests SMA, RSI, MACD, stochastic, PSAR and ROC; reports no technical-rule advantage over buy-and-hold for the All Share | Different universes can behave differently; no universal oscillator claim |
| [Kaminski and Lo — stop-loss research, MIT manuscript / 2014 journal](https://dspace.mit.edu/entities/publication/bb69ca4b-0cdc-487f-831d-63b2e84fafee) | General stop-policy analysis using futures, not JSE sector-specific Swing validation | Compare protective/trailing policies empirically rather than assume tighter is better |

Use current [JSE ICB classifications](https://www.jse.co.za/services/indices/icb-industry) and [SA sector definitions](https://www.jse.co.za/sa-sector), with dated historical memberships. SA Resources includes Basic Materials/Energy; SA Financials includes Financials/Real Estate; SA Industrials is the broad remainder, not simply the narrower ICB Industrials industry. Banks and insurers need distinct peer groups, as do gold, platinum, diversified miners and energy businesses. Global revenue exposure is an additional dated company attribute, not an official sector label.

## Roles of indicators

Use complementary evidence groups, not a majority vote between correlated price transformations. EMA, MACD and ROC can describe overlapping momentum; RSI and stochastic are alternatives to compare, not automatically three extra votes. [Fidelity's indicator guide](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide) distinguishes trend, momentum, volatility and volume tools. It documents definitions, not their JSE accuracy.

| Decision | Candidate evidence | Question answered |
| --- | --- | --- |
| Market/setup eligibility | EMA slope, ADX/DMI or a simpler trend-efficiency measure | Is this a continuation environment or a range/recovery setup? |
| Entry structure | Prior 10/20-session high breakout, support reclaim, or Bollinger position for recovery | What observable price event would justify testing an entry? |
| Momentum timing | RSI level/change or ROC; MACD as a replacement experiment | Is momentum strengthening, exhausted or recovering? |
| Relative strength | Stock return less matched sector return; training-fitted residual for beta-aware alternative | Is this more than the sector moving together? |
| Participation | Real relative volume, close-location value; CMF or OBV as replacement confirmation | Does unusual activity accompany constructive or adverse price behavior? |
| Initial protection/trailing | ATR, known structure and gaps | How much normal movement must the stop tolerate? |
| Exit/invalidation | Failed level, loss of relative strength, predeclared stop/target/time limit | Has the tested premise failed or reached its defined endpoint? |

True VWAP requires suitable trade/volume data. OHLCV-bar approximations must be explicitly labelled; do not promise precise traded VWAP from daily data. CMF/OBV are price-volume proxies, not proof of institutional buying. Missing/invalid inputs mean unavailable, not a neutral indicator vote.

## Entry setups to test separately

**E1 — continuation breakout.** For cash-share LONG research, require admitted real data and a dated universe/sector benchmark. Start from rising EMA20 with EMA20 above EMA50, then a completed close above the previous 20-session high. Compare a bounded RSI14 momentum band (50–70) and positive five-session sector-relative strength as separate additions. ADX14 >20 is one trend-filter candidate, not an accepted accuracy threshold. Test the no-ADX alternative too.

**E2 — pullback/reclaim continuation.** Start from the same uptrend, identify a completed pullback to an explicitly declared EMA20/support zone, then a later reclaim. Compare RSI turning upward against the simpler reclaim alone. At 30-minute resolution, a completed retest must hold the frozen level; no future-confirmed pivot can become known earlier.

**E3 — post-shock recovery.** For the banks/financials family initially, test a completed reclaim of a predeclared level after a shock, with improving peer-sector strength. Compare RSI recovery through 40 or lower-Bollinger-band re-entry as separate timing alternatives. Falling deeply oversold RSI alone is not an entry. Event direction/availability must be observable; rate changes are not hard-coded as bullish.

Signals are frozen at their real availability time. Enter at a subsequent observable price under a declared execution model. A verified next-session-open model can be tested only when source availability and session timing support it; otherwise keep the existing completed-close proxy distinctly labelled. A daily-close signal cannot enter earlier that day. Reject entry gaps that invalidate structure or exceed the preregistered risk/extension bound. A candidate such as more than 1 ATR beyond the trigger is a research veto to test, not an invented fill price.

Volume is recorded on every admitted base setup, including low-volume and non-triggered controls. Compare no predictive volume filter, thresholds 1.2/1.5/2.0, and continuous volume evidence without discarding the counterexamples. Market-cap/liquidity admission remains a separate hard feasibility gate even when the predictive volume weight is zero.

## Initial stop, trailing and exit contracts

For each admitted entry price E, fix the initial stop S0 from information already observable. Candidate A uses the existing structure/ATR geometry; candidate B uses a separately specified 1.5 ATR protective distance. Require S0 below E and preserve structural validity; an invalid or excessively wide stop produces NO_TRADE, never more permitted risk. Initial R is E−S0 and never redefined after the stop moves. Position size must shrink with wider risk and remains subject to the existing risk veto.

Start with the same entry cases and compare these LONG trailing policies:

| Policy | Proposed rule | Testable claim |
| --- | --- | --- |
| T0 — baseline | Initial stop unchanged; no trailing | Reference against premature tightening |
| T1 — delayed ATR trail | After a completed close reaches E+1R, trail from the highest completed close since entry, minus k×ATR14; compare k=1.5 and 2.5 | Adaptive protection retains continuation while reducing giveback |
| T2 — delayed structural trail | Same activation; previous two completed bars' lowest low minus 0.25 ATR14 | Known structure protects a shorter move without excessive whipsaw |

For a LONG, a proposed stop may only rise: `new_stop=max(old_stop, candidate_stop)`. ATR and structure use completed observable bars. An update made after a bar closes becomes effective on the next bar; it cannot stop out earlier in the bar that calculated it. A candidate above the current observable price is an invalidation/next-price exit case, not a guaranteed fill at the higher stop. Break-even at +1R is an optional later experiment, not a required improvement.

Daily-only replay tests the previously active stop first. If stop and target are both reached in one daily bar, use conservative stop-first handling unless admitted intraday evidence resolves the order. Opening gaps use the adverse observable price and costs, not an ideal stop fill. Do not arm a new trail because a daily high reached +1R when the close-based activation rule did not.

Compare fixed 2R target against trail-only protection with the same hard holding limit. A three-, four- or five-session time limit is frozen at entry; no sixth-session extension because a winner looks promising. A predeclared horizon-close execution proxy is not a guaranteed broker fill. Signal-based exits, such as a completed close back below the breakout level, act at the next observable executable price. Test a lost-relative-strength exit only after the simpler failed-level exit; do not combine every exit rule at once.

High volume alone never forces an exit. High activity with a failed breakout/weak close is a separate exhaustion hypothesis. Partial profit-taking, PSAR/Supertrend alternatives and event-conditioned exits are later trials only if simpler policies produce adequate samples. Record all rejected experiments.

## Sector and instrument research matrix

The following choices are engineering proposals motivated by economic exposure and the reviewed mixed evidence. They are not literature-validated sector winners.

| Family | First entry comparison | Trailing/exit comparison | Personality/context to measure |
| --- | --- | --- | --- |
| H1 selected JSE share | E1 vs E2; EMA/structure base, then one RSI/ROC addition | T0 vs T1; 3/4/5-session net outcomes | Breakout follow-through, reversal tendency, gaps, liquidity and sector residual |
| H2 mining/resources | E1/E2 plus matched commodity/FX alignment; ADX or volatility expansion as one addition | T0/T1; commodity invalidation tested separately | Commodity/FX sensitivity, gap tail and ordinary pullback size; separate resource subsectors |
| H3 industrial/global exposure | E1/E2 with business-specific external driver and peer strength; ROC vs RSI | T0/T2, then T1 if supported | Offshore/local sessions, currency sensitivity, trend efficiency and event gaps |
| H4 banks/financials | E3 vs E2; RSI recovery vs Bollinger re-entry, confirmed peer recovery | T0/T2; failed-reclaim/time exit | Mean reversion versus continuation, rate/shock regime, peer-relative response |
| H5 USD/ZAR | Directional range breakout/retest; ROC/DMI alternatives | Currency ATR trail vs fixed stop/time; financing-aware | Calendar/session, carry/spread, gap and macro response; separate LONG/SHORT research |
| H6 gold | Range breakout/retest, USD gold versus ZAR exposure, dollar/yield context | Gold/vehicle ATR trail vs fixed stop/time | Volatility state, FX overlay, chosen vehicle and verified futures/listed-unit volume |

Sector ETF proxies such as existing resource/industrial/financial charts must be labelled proxies and assessed for concentration. For a peer basket, exclude the tested share and retain historical constituents. For beta-adjusted residuals, fit betas only on past data. Different exchange closes, FX timestamps and holiday calendars must be aligned causally; later overseas closes cannot explain an earlier local entry as if already known.

## A volume flag and a learnable contribution

Separate three items: activity detection, predictive evidence and liquidity/risk feasibility.

Daily relative volume: `RV=real_shares_today / mean(real_shares_previous_20_completed_sessions)`. Exclude the current day from the denominator. Intraday relative volume compares a completed 30-minute bar with the same session slot across previous comparable sessions. Do not compare midday cumulative volume with a full-day average. A verified zero-trade observation is different from missing volume; zero/invalid denominators are unavailable. Handle splits, auction/half-day sessions and scheduled index rebalances explicitly.

The initial radar label can be RV≥1.5, while retaining the exact ratio and a trailing historical percentile. Test 1.2 and 2.0 as bounded alternatives. Twenty observations provide a rough same-slot baseline, not reliable extreme-tail probabilities. Use a longer admitted training history to estimate stable percentiles. A median-based denominator is an alternative version, not a silent change.

Direction/context matters: 2× volume with positive sector-relative return and a strong close is a different case from 2× volume with a failed breakout and weak close. Close location can be represented as `(close-low)/(high-low)` when the real range is nonzero; it is unavailable for a zero-range bar. Test this interaction, rather than assume more volume always means a better buy.

The proposed interpretable research score has a volume-group contribution with candidate shares **0%, 5%, 10% and 20%** of its normalized score budget. These are bounded search candidates, not recommended trading weights. Until validated, use zero as the control. Rebalance the other groups' budget consistently; avoid adding extra credit merely because multiple correlated volume indicators exist. Adverse price/volume context must be permitted to reduce a research score. The score is not a calibrated win probability.

Select the smallest useful contribution using training and inner validation only, then freeze it for outer tests. Compare removal of volume against the same price setups, and shuffled volume within training-only matched regimes as a diagnostic. Persist threshold, normalization, group weight, interactions and fold/date lineage. News attention's existing +0.05 remains a separate research-priority adjustment, not part of this proposed trade evidence weight.

A future regularized outcome model may estimate volume effects continuously rather than search these weights. Fit it locally with pooled market/sector effects and shrink stock-specific estimates toward those priors. Report magnitude, uncertainty and stability; allow zero or negative effects. Do not infer a strong positive coefficient from a small cluster of one announcement's reactions.

## Measuring a share's momentum personality

Represent personality as an evolving measured profile, not an immutable label. Calculate it from past training data only:

- ATR as a percentage of price, overnight gap distribution and extreme adverse moves.
- Three-/five-session return persistence, reversal frequency and trend efficiency.
- Breakout failure rate, typical retest depth and time to continuation.
- Maximum favorable/adverse excursion in initial-R units, with daily path uncertainty explicitly marked.
- Sector/commodity/FX beta and residual strength, fitted on past aligned observations.
- Volume-response curve by setup/direction, liquidity, spread proxy limitations and event/regime.

Use pooled cash-market → sector/subsector → share estimates. Instrument-specific overrides require enough independent episodes across several later-date folds and acceptable uncertainty. A provisional eligibility floor might be 50 independent setup episodes over at least three validation folds, but that is not a sufficiency proof; a precision/stability test can still reject it. Sparse shares retain pooled parameters. FX/gold are separate instrument classes, not pooled as equities. Correlated shares reacting to one shock count as one event cluster for uncertainty.

Update descriptive profiles monthly and after outcomes mature. Propose rule/weight revisions on a slower, versioned review schedule. An LLM can describe observed patterns and event categories; numerical estimators/backtests measure them. Neither personality changes nor a persuasive Ollama explanation automatically rewrites the deployed policy.

## Local backtest plan and acceptance

1. Admit real daily OHLCV, historical universe/sector data, adjustments and causal availability. Aim to acquire several years with multiple regimes; the current one-year public working histories are a prototype dataset, not enough evidence for rich per-share/event models. Preserve rejected dates and coverage denominators. No averaged/estimated bars enter performance validation.
2. Preregister a small trial budget. Compare E1/E2 first with fixed baseline exits; add E3 for the financials family. Then test one momentum/regime group at a time. Freeze eligible entry cases before comparing trails/exits and volume contributions, and reserve a separate final joint-policy test. Avoid a full Cartesian search over every indicator and threshold.
3. Use chronological nested walk-forward folds: fit normalizations, sector mappings/betas, personality priors and weights on older data; select on inner validation; freeze before an outer unseen period. Purge overlapping 3–5-session labels across boundaries using actual exit/availability times, plus a declared embargo. Repeatedly consulting an outer fold turns it into validation; obtain a new future test before promotion.
4. Measure the same opportunities under baseline and alternatives. Include no-trade controls, matched dates, price-only baseline, volume ablation, and sector-adjusted outcomes. Report each of 3/4/5 horizons independently, not only the best hindsight horizon. Separate daily-only from real intraday-refined cohorts and their coverage.
5. Charge real-vehicle costs/spreads/financing where known; show conservative sensitivity when not known. Report net expectancy, loss tails/drawdown, trade count, turnover, capacity, target-before-stop/time outcomes, false breakouts, time to exit and trail giveback. Aggregate drawdown requires a chronological cash/exposure-constrained portfolio simulation; overlapping per-signal returns are not a portfolio track record.
6. Use event/date-clustered block resampling for uncertainty and account for the number of configurations tried. Daily bars do not precisely resolve same-bar stop/target or excursion order; conservatively label ambiguity rather than fabricate it. A higher win rate with worse net expectancy is rejected.
7. Run a prospective shadow period with a frozen version before considering adoption. Retain champion/challenger comparisons, data/quality states, model/proposal lineage and explicit human acceptance. M15 remains the final veto; no default weight change or Live execution is authorized by this proposal.

First implementation slice should be H1 plus one liquid, data-qualified sector example, with the pooled fallback. Establish usable daily data and complete the baseline before 30-minute drilling and event-conditioned refinements. Existing technical/effectiveness/HR11 contracts and append-only research persistence are reusable; this document adds no runtime wiring.
