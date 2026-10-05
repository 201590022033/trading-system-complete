# Local Swing backtest engine — proposed acceptance contract

Design version 0.1, 5 October 2026. Proposal only. No new engine, strategy adoption, provider connection or infrastructure change is delivered by this document. Starting implementation: `master@8a0e7c11a1b2714cd7ffcdd5cbfe0e013e74b148`.

The owner wants the engine specified and proven before implementing the adaptive loop and dashboard changes. “Bulletproof” means explicit assumptions, causal calculations, reproducible accounting and adversarial verification. It cannot mean guaranteed returns, perfect source data or knowledge of an unobserved intraday path.

## 1. Decision: extend a small deterministic local replay core

Use the existing Python environment and domain contracts. Build a deterministic event-driven daily core with optional real intraday refinement, instrument/execution adapters, and a separate experiment runner. Avoid introducing a large external backtest framework before the required semantics are established. External libraries may later supply verified calculations or independent comparisons; they must not silently determine fill timing, calendars or costs.

Preserve the existing daily LONG replay as a frozen benchmark. Do not broaden its installed version in place, run legacy multi-agent/60–30–10 paths as the new engine, or route research orders to a broker. Engine changes need their own version; changing an indicator is an experiment, not a change to the accounting simulator.

## 2. Existing foundations and limitations verified in code

| Component | Reuse | Limitation for this project |
|---|---|---|
| `application/opportunities/swing_technical.py` | Observable-bar technical snapshot and attributed outcomes | Existing specific equity features; not six independent indicator-selection programs |
| `domain/policy/swing_shadow.py` | Frozen LONG geometry; later observable-close entry, stop-first ambiguous bars, adverse gaps, 3/4/5-session outcomes | No trailing; hypothetical 10/25/50 bps costs; observed provider sessions rather than verified calendars; not a portfolio or FX/product model |
| `application/opportunities/swing_policy.py` | Frozen decisions and observations | Existing policy/version-specific lane; keep historical records intact |
| `application/opportunities/swing_research.py` | Dataset ingestion, bounded proposals and baseline comparisons | Current-share catalog, fixed ETF benchmark, restricted grid, reused retrospective holdout, no portfolio drawdown; unsuitable as six-family validation proof |
| `domain/evaluation/experiment.py` | Immutable experiment IDs, boundaries, baseline and stage/decision vocabulary | Runner must additionally enforce all chronological boundaries and contamination controls |
| `domain/evaluation/metrics.py` | Explicit return/cost/calendar contexts and unavailable/insufficient states | Supply verified portfolio series and effective sample evidence; do not invent these inputs |
| `backtest.py` | Preserve historical close-based indicator benchmark | Aligned future-close returns do not establish executable entry/stop/trailing performance |

Read the corresponding tests before extending these components. Reuse `test_swing_policy.py`, `test_swing_technical.py`, `test_swing_research.py` and `test_experiment_registry.py` as characterization coverage, not proof that the proposed engine already exists.

## 3. Two outputs: setup research and executable simulation

**Diagnostic event study:** evaluate all dated eligible signals and matched controls over 3/4/5 sessions. Outcomes can overlap; explicitly report that these are event observations, not cash-funded independent trades. Useful for indicator comparisons and stock personalities.

**Portfolio replay:** chronological simulated decisions, risk limits, order fills, capital allocation, positions, fees, cash, financing, mark-to-market equity and exits. Correlated events compete for the same capital. This alone supplies portfolio drawdown and periodic portfolio returns.

Never combine their sample counts, annualize overlapping event returns as portfolio returns, or describe a hypothetical executed trade as actual broker evidence.

## 4. Data and time contracts

Each immutable dataset manifest records content hashes, provider/retrieval time, instrument identity, listing/currency, price basis, activity semantics, timezone/session calendar, date coverage, quality/revision flags and corporate-action treatment. Each bar has a session/bar end and an availability time. Dataset download today does not prove historical point-in-time availability; label reconstructed historical research distinctly from contemporaneous shadow observations.

Admission is per relevant instrument/window/required feature. Preserve valid unaffected windows, but reject a required window containing invalid OHLC, unverified sessions, estimated inputs or unexplained gaps. Distinguish closed-market dates, missing expected sessions, genuine zero volume and absent volume. Display averages cannot enter any feature, fill or validation calculation. Never manufacture 30-minute bars from daily OHLC.

Corporate actions need consistent OHLC and volume adjustments, position/share changes and cash distributions without double-counting. Validate identifiers through ticker changes and delistings. Unverified history is exploratory only. Dated universes and membership prevent selecting stocks or benchmarks by later success. Keep an explicit current-universe survivorship warning until a historical universe is verified.

Features, normalizers, benchmarks, learned thresholds and selected indicators may use only inputs available by the decision timestamp. The entry is the next eligible executable observation, never an earlier price from the signal bar. Preserve existing later-close benchmark semantics; a next-open model is a separate specification requiring a before-open decision and validated calendar/price timing.

For sessions held, declare whether the entry session counts. Preserve the legacy rule of 3/4/5 observed sessions after entry in benchmark replay; the new model counts verified eligible market sessions and flags any difference. FX day boundaries and weekend conventions are explicit. All horizon labels follow the selected product calendar.

## 5. Deterministic execution and accounting

Chronological sequence: apply eligible corporate actions and carried-order gap rules; process the eligible observation and previously effective orders; mark portfolio value and costs; expose newly available data; compute decisions; reserve risk/capital and schedule new orders. Define a total order for equal timestamps and do not spend unavailable sale proceeds or unrealized gains. Every state transition has a reason and input references.

Orders have explicit signal/submission/eligibility times, side, type, expiry, quantity, trigger and fill assumptions. A touched limit is not automatically guaranteed liquidity. Baseline research fills may assume full fills only with a disclosed liquidity envelope; unavailable bid/ask, capacity or fill evidence blocks an execution-ready claim. Intraday fills require their own spread/participation assumptions.

An initial stop and entry-based R are frozen. A trail only tightens, uses completed observable data and becomes effective on the next eligible observation. A price already beyond a newly calculated invalidation level requires an executable exit rule, not a fictitious fill at that level. Daily stop/target ambiguity uses conservative ordering and records the ambiguity. Known opening gaps precede the later range; adverse stop gaps fill at the available worse price. No favourable gap improvement without a justified order model. Mirror these rules for SHORT experiments without weakening the current cash-LONG boundary.

Maintain cash, reserved cash/margin, quantities, realised/unrealised P&L, account-currency conversion, fees, spread, slippage, financing and equity. No double-counted costs. Fee minimums, rounding, lot/contract multipliers and currency precision are product-specific. Missing required conversion or costs produces unavailable/assumption-limited output, not zero. Size smaller when a wider valid stop increases per-unit risk. Margin replay is an explicit adapter, never inferred from equity sizing.

## 6. Independent hypothesis adapters

Four equity families have separately versioned entry/trailing/exit indicators, benchmarks, parameters and tests, with pooled-to-sector-to-stock adaptation when evidence permits.

USD/ZAR and gold have their own specifications and fixture suites. They do not inherit a traded-share volume requirement or a fixed equity benchmark. FX provider activity is separately named and verified; missing activity supports a registered price-only comparison, not invented volume. Currency quote direction, bid/ask inversion, financing and session boundaries are explicit.

Gold distinguishes XAU/USD, theoretical timestamp-aligned XAU/ZAR, ETFs, CFDs, futures and miners. Theoretical rand gold is not an executable product price. Futures activity is a proxy if applied to spot; contract rolls and publication delays are controlled. A rolled continuous price series cannot itself supply contract P&L. ETF trading sessions and spreads differ from underlying gold. Miners stay equity hypotheses.

## 7. Indicator selection and validation runner

An indicator plugin declares version, role, formula/seed, lookback, warm-up, required inputs, timestamp availability and valid market types. Freeze a small initial candidate catalogue; new indicators or removal/replacement of indicators are registered experiments. Test incremental value against a no-indicator/simple-price baseline. Correlated EMA/MACD/ROC measures are competing specifications unless an interaction experiment is declared.

For each family: chronological outer evaluation folds, inner training/selection only, training-fitted scaling, and purge/embargo based on full event label intervals and feature dependencies. Validate across all instruments sharing folds, not just one ticker at a time. The reserved final period is locked until the candidate is frozen. Once viewed, it cannot be called untouched again. Log every tried/rejected configuration and allocate a bounded trial budget; repeated testing requires multiplicity controls and a fresh evaluation design.

Reports include gross/net expectancy, costs sensitivity, hit rate, payoff, turnover/exposure, conservative MFE/MAE, portfolio drawdown/returns where valid, independent episode counts, uncertainty and stability across folds/regimes. Bootstrap or other uncertainty calculations must respect temporal and cross-asset/event dependence. Any provisional episode minimum is eligibility, not confidence proof. Zero samples and unresolved/censored outcomes are explicit, not 0% success or silent losses. A high win rate alone never selects a winner.

Historical news/economic data is an optional later adapter. Its safety contract is tested now: publication, receipt and usable availability are distinct; later explanations and revised releases cannot become earlier features. Ollama classifies cited evidence and proposes bounded experiments; it does not decide that a strategy passed statistical validation.

## 8. Mandatory verification matrix

Expected outcomes must be independently hand-calculated or derived from a simple separately written reference. Do not use the implementation under test to generate its own expected answers.

| Test group | Required fixtures / invariants |
|---|---|
| Causality | Appending/changing future bars changes no earlier features, orders or fills; delayed publication delays eligibility; same-close signal cannot enter earlier that day |
| Indicators | Constant/rising/falling series, warm-up, zero denominators, RSI/ATR seeds, gaps, benchmark alignment, NaN/infinity; independent fixed numeric answers |
| Data admission | Duplicates, out-of-order bars, estimated bars, absent versus zero activity, missing expected sessions versus holidays, action adjustments, revisions and ticker identity |
| Execution | LONG and SHORT stop/target, opening gaps, both touched, order expiry, invalid geometry, no pre-entry exits, trail activation and next-bar effect; unresolved intrabar paths flagged |
| Horizons | Exactly 3/4/5 declared sessions, holiday/weekend cases, missing-session refusal, end-of-data pending positions, no substituted entry after truncation |
| Accounting | Two competing signals, capital reservation, no double spending, partial/fill-assumption handling, lot rounding, costs, dividends/splits, FX conversion, margin/financing and equity reconciliation |
| Market identity | USD/ZAR versus reciprocal quotes, gold USD/ZAR combination, product multiplier, futures roll, ETF/underlying calendar mismatch and volume-proxy provenance |
| Selection | Feature/normalizer fit only on training, overlapping labels purged across instruments, locked final evaluation, all trials retained, matched no-volume and non-radar controls |
| Recovery | Interrupt/resume produces identical semantic artifacts; retries produce no duplicate trades; data revisions create a new version rather than rewriting frozen outcomes |
| Safety | Test/run mode cannot create broker orders, mutate canonical ranking, call external models/providers or require production credentials |

Use exhaustive bounded toy paths and deterministic seeded generative tests for accounting/causal invariants. Verify hand-built daily versus 30-minute path aggregation: only claimed intraday ordering may change, not previously observable signals. Kill selected deliberate defects in a disposable test copy (future access, stop ordering, duplicate fills, removed fees); acceptance tests must catch them. Keep protected artifacts byte-identical.

## 9. Sequential implementation gates

| Gate | Deliverable and acceptance | Work intentionally deferred |
|---|---|---|
| B0: specification | This contract, existing-component inventory, feedback design and dependency plan; reviewed by owner | Engine implementation |
| B1: data/time and oracle harness | Offline fixtures, manifests, availability/calendar admission and independently computed LONG daily paths; causality tests pass | Strategy optimisation and cloud changes |
| B2: deterministic replay/accounting | Daily order/stop/trailing/horizon state machine, cash ledger, costs and competing positions; accounting and adversarial tests pass; frozen legacy benchmark reconciled with explained differences | Claims of an edge |
| B3: market adapters | Own FX and gold LONG/SHORT synthetic fixtures, quotes, product fees/financing/conversion/roll semantics; no share-volume gate inherited | Broker connections or live trading |
| B4: experiment runner | Bounded indicator selection, inner/outer chronological folds, contamination ledger, control cohorts and reproducible evidence reports; planted-leak tests fail as expected | Automatic adoption |
| B5: engine acceptance | Verified real-data slice, independent trade audit, cost/liquidity stress and daily/intraday comparison where real data exists; full safe suite and protected checks pass | Six-family adaptive loop / new dashboard until accepted |
| F1 onward | Freeze hypothesis catalogue; run local candidates; prospective shadow; then add event categorisation, selective upload and feedback dashboard in separate milestones | Live execution remains outside scope |

B1 starts with one simple equity fixture, not six simultaneously tuned strategies; all adapters must pass B3 before using the engine to select FX/gold rules. Exactly one milestone ACTIVE. Current authorization is B0 documentation/planning; these gates do not automatically start implementation.

## 10. Definition of accepted engine

Release an engine version, immutable fixtures, dataset/config/code hashes, documented arithmetic tolerances, independently reconciled trade/cash reports, test/mutation results, limitations and cost/data assumptions. Identical frozen inputs produce identical semantic results irrespective of machine or restart; wall-clock/log fields are excluded from reproducibility comparisons. No unexplained discrepancy is accepted.

Acceptance can be scoped to verified markets/data; unsupported adapters or unavailable real history remain BLOCKED. Synthetic correctness is not real-world fill validation. No honest test suite can prove profitability. Strategy adoption additionally needs sufficient independent prospective evidence and existing M15/safety boundaries.
