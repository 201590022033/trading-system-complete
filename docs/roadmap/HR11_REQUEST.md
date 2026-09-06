You are working inside an existing South African / JSE-focused algorithmic trading research repository.

Your task is to IMPLEMENT, TEST, DOCUMENT, AND INTEGRATE a new formal milestone for short-term multi-instrument trading research.

This is not an audit-only task.

You must make the required code changes, add tests, update roadmap/governance documentation, run validation after each stage, and leave the repository in a clean, reproducible state.

The existing architecture contains mature historical-research work, including HR9/HR10-style adaptive technical ensemble evaluation, point-in-time data handling, causal/no-look-ahead tests, transaction-cost modelling, robustness gates, paper-only execution boundaries, cross-asset features, source provenance, technical feature registries, and asset-specific profiles.

The new work must build on those foundations without weakening, replacing, contaminating, or invalidating them.

==================================================
0. FIRST ACTION — READ THE REPOSITORY BEFORE CODING
==================================================

Before modifying ANYTHING:

1. Inspect the repository root and current git status.
2. Identify the current branch and current HEAD commit.
3. Confirm whether there are uncommitted changes.
4. Do NOT overwrite, discard, reset, amend, squash, or otherwise destroy work from the currently completed or partially completed milestone.
5. Treat all existing historical research outputs/artifacts as immutable unless a documented bug requires a correction.
6. Read ALL relevant Markdown files before implementation.

At minimum inspect:

- README.md
- ROADMAP.md or equivalent roadmap files
- ARCHITECTURE.md or equivalent
- ADR files / architecture decision records
- governance / constitution / development rules
- milestone documentation
- research methodology documentation
- testing documentation
- historical research documentation
- HR8 / HR9 / HR10 documentation
- agent workflow instructions
- execution / paper trading documentation
- data provenance documentation
- any TODO / PLAN / STATUS / CHECKPOINT markdown files
- any Markdown describing contracts for:
  - historical reconstruction
  - point-in-time availability
  - adaptive ensemble
  - cross-asset features
  - market profiles
  - transaction costs
  - confidence gates
  - broker/execution boundaries

Search the repo for *.md and read the relevant files before implementation.

Then summarize internally:

- current architecture
- current active/completed milestone
- invariants that must not be broken
- testing conventions
- documentation conventions
- naming conventions
- ADR conventions
- artifact/report locations
- roadmap structure

Do not begin implementation until this repository reconnaissance is complete.

==================================================
1. CREATE A FORMAL NEW MILESTONE
==================================================

Add this work to the project roadmap as a formal milestone.

Use the repository's existing naming convention.

If the historical research milestones are HR-numbered and HR11 is available, use:

HR11 — Short-Term Multi-Instrument Research Layer

If HR11 is already occupied, use the next available appropriate milestone identifier while preserving the title and intent.

The milestone must be decomposed into explicit deliverables, each with:

- objective
- implementation scope
- files/modules affected
- test requirements
- acceptance criteria
- documentation requirement
- completion state

This milestone must be implemented as a PIPELINE, not as one giant code change.

Recommended deliverable stages:

HR11.0 — Repository contract + design boundary
HR11.1 — Instrument registry
HR11.2 — Intraday data contract
HR11.3 — Bar/session/timeframe layer
HR11.4 — Intraday feature layer
HR11.5 — Short-term horizon contract
HR11.6 — Asset/instrument-specific profiles
HR11.7 — Instrument-specific cost model
HR11.8 — Cross-asset point-in-time intraday joins
HR11.9 — Liquidity/freshness/admissibility gates
HR11.10 — Intraday walk-forward evaluator
HR11.11 — Paper-only instrument router
HR11.12 — Robustness/admission framework
HR11.13 — Integrated reporting + documentation
HR11.14 — Full regression validation

If the repository uses another numbering/submilestone style, follow that style instead.

==================================================
2. CRITICAL DESIGN CONSTRAINTS
==================================================

The following are NON-NEGOTIABLE.

A. PRESERVE EXISTING HR9/HR10 BEHAVIOUR

Do not silently alter existing:

- HR9 historical decisions
- HR9 output artifacts
- HR10 robustness outputs
- technical signal definitions
- existing horizon semantics
- existing adaptive ensemble semantics
- existing transaction-cost semantics
- existing no-look-ahead guarantees

If an unavoidable compatibility change is required:

- document it
- add an ADR
- add regression tests
- preserve the old behaviour/version if at all possible

Existing daily/session horizons such as:

1
3
5
20

must remain exactly what they currently mean.

Do NOT redefine them as intraday intervals.

B. SHORT-TERM RESEARCH MUST BE A SEPARATE HORIZON FAMILY

Introduce a new intraday horizon family.

Initial intended research targets:

5 minutes
15 minutes
30 minutes
60 minutes
session close / EOD

The principal short-term target should be configurable, with 30 minutes treated as the initial primary research horizon.

Example conceptual roles:

5m   = micro confirmation
15m  = fast signal
30m  = primary short-term target
60m  = persistence/trend confirmation
EOD  = session outcome

Do not hard-code assumptions unnecessarily.

C. POINT-IN-TIME / NO LOOK-AHEAD

Every feature and evaluation decision must obey:

available_time <= decision_time

Future observations must never affect earlier decisions.

Existing causal tests should remain passing.

Add new intraday equivalents.

Mutating future bars must not alter earlier:

- features
- regime classifications
- signals
- weights
- decisions
- positions
- costs
- evaluation results

D. PAPER / SHADOW ONLY

The new layer is RESEARCH ONLY.

No live broker execution.

No production order placement.

No automatic money movement.

Any instrument routing must explicitly report something equivalent to:

mode = "paper"

or

shadow_only = True

according to repository conventions.

E. EXPLICIT UNAVAILABLE DATA

Never fabricate data.

Never silently substitute:

0

for unavailable information unless zero has explicit semantic meaning.

Prefer:

None
NaN
UNAVAILABLE
STALE
INSUFFICIENT_DATA

according to existing project conventions.

F. NO SILENT FORWARD-FILLING OF CROSS-ASSET DATA

Intraday cross-asset alignment MUST NOT merely join by calendar date.

Use proper as-of timestamp logic.

A source observation may only influence a target decision if it was actually available at or before the target decision time.

Do not use information from a later timestamp.

==================================================
3. TARGET INSTRUMENT UNIVERSE
==================================================

Implement the architecture generically, but configure an initial research universe around:

TIER 1

1. JSE broad-market/index exposure
   - Top 40 / ALSI-style exposure
   - future / CFD / proxy representation as available

2. USD/ZAR
   - FX
   - CFD/future/spot-proxy research representation

3. Gold
   - USD gold
   - ZAR-adjusted gold context
   - future/CFD/proxy representation

4. Brent crude
   - energy macro input
   - future/CFD/proxy representation

TIER 2

5. Platinum

6. Highly liquid JSE equities, initially selected from existing supported names such as:
   - Naspers / Prosus exposure as appropriate
   - Sasol
   - BHP
   - major banks
   - other existing high-liquidity names already present in project profiles

TIER 3 / FUTURE EXTENSION

7. Palladium
8. S&P 500 / global index exposure
9. selected JSE single-stock futures
10. additional CFDs

Do not pretend unsupported execution instruments are live.

Use explicit capability/configuration state.

==================================================
4. IMPLEMENT AN INSTRUMENT REGISTRY
==================================================

Create a central instrument definition/registry layer.

The current architecture is largely ticker/underlying-centric.

Separate:

UNDERLYING
SIGNAL TARGET
TRADABLE INSTRUMENT
EXECUTION SPECIFICATION

Conceptually:

Underlying:
    SASOL

Signal target:
    SASOL equity exposure

Possible tradable instruments:
    SOL.JO cash equity
    SASOL CFD
    SASOL SSF

Cross-asset context:
    Brent
    USDZAR
    resources index
    ZAR regime
    global risk regime

Create an immutable/versioned InstrumentDefinition-style model using repository conventions.

Suggested fields:

instrument_id
display_name
underlying_id
signal_target_id
asset_class
instrument_type

Examples of instrument_type:

cash_equity
index
future
single_stock_future
cfd
fx
commodity
proxy

Also support:

exchange
currency
base_currency
quote_currency
timezone
session_calendar
trading_hours

contract_multiplier
tick_size
tick_value
lot_size
minimum_trade_size

margin_type
margin_requirement
leverage
financing_applicable

commission_model
spread_model
slippage_model
exchange_fee_model
financing_model

liquidity_class

data_symbol
benchmark_symbol
execution_symbol

profile_id
sector
region

supports_intraday
supports_short
supports_volume
supports_bid_ask
supports_live_data
supports_historical_data

data_grade

version
enabled
notes

Data-grade concepts should distinguish something equivalent to:

RESEARCH_DATA
DELAYED_LIVE_DATA
EXECUTION_GRADE_DATA

Use enums/constants if consistent with the codebase.

Add validation.

Examples:

- negative tick size must fail
- zero/negative multiplier where invalid must fail
- unknown currency should be explicit
- unsupported instrument should not silently become tradable
- execution symbol must not imply live execution availability

Add unit tests.

RUN TESTS AFTER THIS STEP.

Do not continue until the new tests and relevant regression suite pass.

==================================================
5. INTRADAY DATA CONTRACT
==================================================

Create a canonical versioned intraday market-data contract.

It should support, where available:

instrument_id
event_time
available_time
decision_time

open
high
low
close
volume

bid
ask
mid
spread

trade_count if available
vwap if available
source
source_timestamp
ingestion_timestamp

timeframe
session_id
session_date
market_state

currency
data_grade
delayed flag
stale flag

provenance/version metadata

Validate timestamps carefully.

Rules:

event_time <= available_time <= decision_time

must be respected according to project semantics.

If the provider's timing semantics differ, make the contract explicit and tested.

No fabricated OHLC.

No fabricated bid/ask.

No fabricated volume.

No forward-filling missing prices.

Build adapters around the canonical contract rather than coupling feature code directly to providers.

Add tests for:

- timestamp ordering
- missing data
- stale data
- delayed data
- timezone handling
- duplicated bars
- out-of-order observations
- missing sessions
- provider failures
- future-data rejection

RUN TESTS AFTER THIS STEP.

==================================================
6. BAR / SESSION / TIMEFRAME LAYER
==================================================

Implement a deterministic timeframe/session layer.

Support at least:

5m
15m
30m
60m
1d

and a session/EOD abstraction.

Prefer canonical lower-frequency aggregation from the finest reliable source available.

Example:

5m -> 15m / 30m / 60m

with correct OHLCV aggregation.

Rules:

open   = first valid open
high   = max
low    = min
close  = final valid close
volume = sum

Do not aggregate across session boundaries.

Handle:

market open
market close
half/partial sessions if relevant
overnight instruments
FX session conventions
commodity session conventions
DST/timezone issues

Session logic must not assume all markets use JSE hours.

Add tests.

Especially test that future bars cannot alter earlier aggregated bars.

RUN TESTS AFTER THIS STEP.

==================================================
7. INTRADAY TECHNICAL FEATURE LAYER
==================================================

DO NOT create a completely separate technical-analysis framework.

Extend the existing technical feature registry.

The repository already contains concepts such as:

- RSI
- SMA
- breakout
- stochastic
- MACD
- Bollinger
- ADX/DMI
- Ichimoku
- ATR
- relative strength
- relative volume
- VWAP/session context
- Fibonacci context
- candlestick context
- support/resistance
- Donchian/channel structure
- swing structure
- gap features

Preserve existing implementations and versions unless an explicit extension is required.

Add intraday-specific versions/configuration where appropriate.

Implement or complete high-value intraday families:

TREND

- EMA fast/slow structure
- MACD
- ADX/DMI
- Ichimoku where appropriate

MOMENTUM

- RSI
- stochastic
- relative strength

VOLATILITY

- ATR
- Bollinger z-score
- realized volatility
- volatility expansion/contraction

SESSION / STRUCTURE

- session VWAP
- distance from VWAP
- opening-range high
- opening-range low
- opening-range position
- opening-range breakout
- prior session high/low
- current session high/low
- support/resistance distance
- Donchian/channel position
- price gap
- swing structure

VOLUME / LIQUIDITY

- relative volume
- dollar volume where meaningful
- volume confirmation
- VWAP-related volume context

Do not turn Fibonacci or candlestick recognition into automatic standalone trade actions.

They should remain contextual evidence unless the existing research design explicitly proves otherwise.

Each feature must define:

name
family
required inputs
warmup
supported timeframes
parameters
capability requirements
version
output fields
implementation status

IMPORTANT:

Do not assume the same parameter has the same meaning across daily and intraday data.

Create timeframe-specific parameter profiles where justified.

Example:

RSI(14) on a daily timeframe is not automatically equivalent to RSI(14) on 5-minute bars.

Do not optimize parameters by looking at the complete future dataset.

Any learned/adaptive parameter selection must be walk-forward or training-window based.

Add causal mutation tests.

RUN TESTS AFTER THIS STEP.

==================================================
8. SHORT-TERM HORIZON CONTRACT
==================================================

Create a separate intraday horizon definition module.

Do not reuse daily-session horizon identity ambiguously.

Represent horizon units explicitly.

For example:

value = 30
unit = "minute"

not just:

horizon = 30

if that could be confused with 30 sessions.

Define:

horizon_id
duration
unit
role
version

Initial set:

5m
15m
30m
60m
EOD/session-close

Every research decision should record:

target_horizon
target_horizon_seconds/minutes where appropriate
horizon_role
horizon_version

No duplicate:

instrument + decision_time + horizon

rows unless explicitly allowed by another dimension.

Add tests proving that horizons remain distinct research targets.

RUN TESTS AFTER THIS STEP.

==================================================
9. ASSET- AND INSTRUMENT-SPECIFIC PROFILES
==================================================

Extend the existing market/profile framework.

Profiles should describe market behaviour and factor relevance.

Create or formalize profiles for:

usdzar
jse_index
gold
brent
platinum
jse_equity
banks_financials
resources_miners
energy_sasol
offshore_earner

Use existing profile names when they already exist.

Do not duplicate them unnecessarily.

Profiles should support factor weighting/context for:

technical
macro
cross_asset
sentiment/event
liquidity
volatility
session context

Examples:

USDZAR:

relevant context may include:
- DXY
- US yields
- ZAR regime
- JSE risk sentiment
- commodities
- local macro/news

Gold:

- DXY
- US yields
- VIX/risk-off
- USDZAR
- gold_zar

Brent:

- global risk
- energy equities
- inflation context
- USD
- geopolitical/event inputs if supported

Sasol:

- Brent
- USDZAR
- local risk
- equity technicals
- company events

Mining/PGM:

- platinum
- palladium
- gold where relevant
- USDZAR
- China/global-risk proxies if supported by current architecture

Do not invent data sources that are not actually configured.

Add profile selection tests and regression tests.

RUN TESTS AFTER THIS STEP.

==================================================
10. INSTRUMENT-SPECIFIC COST ENGINE
==================================================

The existing generic cost framework is insufficient for comparing different short-term tradable instruments.

Build a versioned instrument-specific cost engine.

Support components including:

spread
commission
slippage
exchange fees
broker fees
financing / overnight cost where applicable
contract multiplier
tick size
tick value
minimum charge where applicable

The model should calculate costs based on actual originating signal-state turnover.

Preserve the corrected semantics already established by HR9/HR10:

entry
hold
exit
reversal

must not all be charged identically.

Example signal states:

0 -> +1 = entry
+1 -> +1 = no position turnover
+1 -> 0 = exit
+1 -> -1 = reversal / two-sided turnover where applicable

Allow costs to differ by:

instrument
instrument_type
timeframe
liquidity regime

Do NOT use arbitrary false precision.

If real broker costs are not known, use clearly labelled research assumptions.

Every evaluation output must record:

cost_model_version
cost_assumptions
spread assumption
slippage assumption
commission assumption
financing assumption where relevant

Add tests.

RUN TESTS AFTER THIS STEP.

==================================================
11. CROSS-ASSET POINT-IN-TIME INTRADAY FEATURES
==================================================

Extend cross-asset research into intraday-safe form.

Existing examples include:

USDZAR
VIX
S&P 500
DXY
US10Y
Brent
gold
platinum
palladium
JSE broad-market proxy

Preserve existing daily cross-asset logic.

Build a separate intraday-safe alignment path.

VERY IMPORTANT:

Do NOT join simply by calendar date.

Use time-aware as-of joins.

For target decision time T:

only source data satisfying:

source.available_time <= T

may be included.

If no eligible observation exists within an acceptable freshness window:

mark the feature unavailable.

Do not blindly forward-fill.

Add maximum-age/freshness rules by source.

Possible features:

gold_zar
commodity_zar
rand regime
risk-on/off
Brent momentum
gold momentum
DXY momentum
US yield momentum
SP500 momentum
VIX regime
JSE broad-market relative direction

Track provenance for every derived feature.

Derived feature records should identify input record IDs where the existing provenance system supports it.

Add mutation tests ensuring later cross-asset observations do not alter earlier decisions.

RUN TESTS AFTER THIS STEP.

==================================================
12. LIQUIDITY / FRESHNESS / ADMISSIBILITY GATES
==================================================

Create explicit short-term trading research gates.

A short-term decision must not become admissible merely because a technical score exists.

Create gates for:

DATA FRESHNESS

- data available
- quote age acceptable
- not stale
- not delayed beyond allowed research mode
- correct session state

LIQUIDITY

- minimum volume or relative-volume capability
- maximum spread if bid/ask exists
- minimum dollar/notional liquidity where appropriate
- market tradability state

FEATURE SUFFICIENCY

- required warmups complete
- minimum available signal count
- critical contextual features present where profile requires them

COST VIABILITY

Expected/raw edge should not automatically pass if realistic transaction cost overwhelms it.

Do not claim predictive expected return unless the existing architecture defines it.

At minimum ensure cost information is included in admission/evaluation.

DATA GRADE

A delayed/public source may be acceptable for research but must never be misclassified as execution-grade.

Possible gate states:

PASS
FAIL
UNAVAILABLE
INSUFFICIENT_DATA

Use existing gate conventions if present.

Add tests.

RUN TESTS AFTER THIS STEP.

==================================================
13. INTRADAY SIGNAL / ENSEMBLE LAYER
==================================================

Reuse the authoritative signal-definition philosophy.

Do not bypass the signal boundary by building ad hoc indicator logic elsewhere.

For each:

instrument
decision_time
timeframe
target_horizon

record:

signal
signal availability
signal version
signal weight
signal contribution
evidence sample count

Preserve explicit missing signals.

Do not dilute an ensemble score by pretending missing evidence is neutral evidence.

Small samples should retain neutral/default learned weights according to existing adaptive rules.

Regime-aware and profile-aware adjustments must be explainable.

Every final adaptive research record should include enough information to reconstruct:

which signal fired
what its value was
what its weight was
why the weight was used
how much it contributed

Add regression and causal tests.

RUN TESTS AFTER THIS STEP.

==================================================
14. INTRADAY WALK-FORWARD EVALUATION
==================================================

Create a dedicated causal intraday evaluator.

Do not simply reuse daily evaluation code if its assumptions are session-based.

Evaluate separately by:

instrument
instrument_type
timeframe
target horizon
profile
trend regime
volatility regime
liquidity regime where available

Metrics should include, where meaningful:

sample_count
trade_count
win_rate
mean_aligned_return
median_aligned_return
mean_net_return
median_net_return
MFE
MAE
max drawdown
turnover
costs
exposure
average holding time
profit factor if appropriate
long/short counts

Avoid overlapping-trade inflation.

For each horizon, enforce appropriate non-overlap or explicitly model stateful positions.

Preserve HR10-style causal validation philosophy.

Add purge/embargo rules appropriate to the horizon.

Make the purge and embargo duration explicit.

Do not train on observations whose forward-return windows overlap the test set.

Add tests for leakage.

RUN TESTS AFTER THIS STEP.

==================================================
15. ROBUSTNESS / ADMISSION FRAMEWORK
==================================================

Extend HR10-style robustness testing to the intraday universe.

Reuse existing primitives if they are generic enough.

Do not duplicate mathematical implementations unnecessarily.

Include:

- minimum trade/sample threshold
- block/bootstrap confidence intervals
- purged / embargoed evaluation
- multiple-comparison adjustment where appropriate
- non-overlapping trade analysis
- regime stability
- instrument/horizon cell separation

Admission results should remain conservative.

Suggested states:

REJECT
INSUFFICIENT_EVIDENCE
ADMIT_FOR_CONTINUED_SHADOW

Do NOT create a state implying approval for live trading.

Do not promote an instrument merely because one metric is positive.

Require documented admission rules.

Each cell must be evaluated separately, for example:

USDZAR + 30m
USDZAR + 60m
Gold + 30m
Brent + 30m
JSE index + 30m

Do not pool unrelated instruments in a way that hides poor performance.

Add tests.

RUN TESTS AFTER THIS STEP.

==================================================
16. PAPER-ONLY INSTRUMENT ROUTER
==================================================

Create a hypothetical/paper instrument router.

Purpose:

take an admitted research signal and map it to an InstrumentDefinition.

Example conceptual output:

signal_target = "USDZAR"
instrument_id = "USDZAR_CFD_RESEARCH"
direction = LONG
requested_notional = ...
estimated_entry = ...
estimated_spread_cost = ...
estimated_slippage = ...
estimated_total_cost = ...
mode = PAPER

Do not connect to a real broker.

Do not submit live orders.

Do not require broker credentials.

The router should refuse or flag instruments when:

disabled
insufficient data
stale data
outside session
unsupported execution
no valid cost model
liquidity gate fails
research admission fails

Add tests proving execution remains paper-only.

RUN TESTS AFTER THIS STEP.

==================================================
17. DATA SOURCE / PROVENANCE POLICY
==================================================

Respect the existing source catalogue and provenance architecture.

Do not scrape or integrate sources in violation of policy.

Existing source statuses and authority tiers must remain meaningful.

For actual short-term market data, distinguish clearly between:

licensed/authoritative
delayed/public
manual/research
unavailable

Yahoo/public delayed-style data may be useful for:

historical research
dashboard context
non-execution research

but must NOT automatically satisfy execution-grade freshness requirements.

No source should silently upgrade its data quality classification.

All new source integrations must record:

source ID
authority/data tier
access mode
status
provenance
poll/freshness policy

Add documentation.

==================================================
18. REPORTING
==================================================

Create integrated HR11 reports using existing report conventions.

At minimum include:

instrument universe
instrument registry version
data contract version
signal version
technical registry version
horizon version
cost model version
evaluation version

For every instrument/horizon cell report:

sample count
trade count
net returns
costs
turnover
drawdown
MFE/MAE
confidence interval
robustness/admission state
failure reasons
data-quality warnings

Also report:

missing capabilities
stale/delayed data exposure
unsupported instruments
insufficient samples
unavailable cross-asset features

Do not hide negative results.

==================================================
19. TESTING STRATEGY — MANDATORY TEST AFTER EVERY STAGE
==================================================

This project must be implemented incrementally.

After EACH numbered implementation stage:

1. run the new focused tests
2. run directly related existing regression tests
3. fix failures before continuing
4. record what passed

Do not accumulate twelve steps of changes and test only at the end.

At milestone completion run:

A. all new HR11 tests

B. existing HR8/HR9/HR10 tests

C. adaptive ensemble tests

D. technical-signal tests

E. technical feature registry tests

F. Ichimoku / Fibonacci / candlestick tests

G. asset-specific feature tests

H. cross-asset feature tests

I. historical feature-store tests

J. historical reconstruction tests

K. evaluation tests

L. dashboard freshness tests

M. agent integration tests

N. full repository test suite if practical

O. Python compilation/import validation

Example:

python -m compileall ...

and the project's normal pytest/unittest command.

Do not claim completion while tests fail.

==================================================
20. REQUIRED CAUSAL TESTS
==================================================

Add explicit tests proving:

1. future 5m bars cannot alter earlier decisions

2. future 15m bars cannot alter earlier decisions

3. future 30m bars cannot alter earlier decisions

4. future 60m bars cannot alter earlier decisions

5. future cross-asset observations cannot alter earlier target features

6. a source observation with available_time > decision_time cannot be used

7. missing source data is not forward-filled across invalid intervals

8. daily HR9/HR10 results remain unchanged

9. intraday horizons cannot collide with session horizons

10. transaction-cost turnover semantics remain correct

11. missing signals remain unavailable rather than becoming zero

12. delayed/stale data cannot pass an execution-grade freshness gate

13. paper router cannot place a real order

14. instrument profiles cannot silently fall back to an unrelated profile unless the registry explicitly defines that behaviour

15. timeframe aggregation cannot cross market-session boundaries

16. duplicated market bars are detected/rejected or deterministically resolved

17. out-of-order ingestion cannot create look-ahead

==================================================
21. DOCUMENTATION / ADR REQUIREMENTS
==================================================

Update the roadmap as implementation progresses.

Do not mark a deliverable complete until:

code exists
tests exist
tests pass
documentation exists

Create ADRs for major architectural decisions, especially:

ADR — Separation of Underlying, Signal Target and Tradable Instrument

ADR — Separate Intraday vs Session Horizon Families

ADR — Point-in-Time As-Of Cross-Asset Alignment

ADR — Instrument-Specific Cost Modelling

ADR — Data Quality Grades for Short-Term Research

ADR — Paper-Only Short-Term Instrument Routing

Follow repository ADR style.

Update README/architecture documentation with:

data flow

source
  ->
canonical market data
  ->
timeframe/session normalization
  ->
features
  ->
signals
  ->
adaptive ensemble
  ->
gates
  ->
evaluation
  ->
robustness/admission
  ->
paper instrument router

Document limitations.

Explicitly state:

THIS DOES NOT CONSTITUTE LIVE-TRADING VALIDATION.

==================================================
22. VERSIONING
==================================================

Do not silently mutate established research contracts.

Version new artifacts.

Examples only — follow repo style:

instrument-registry-v1
intraday-market-data-v1
intraday-horizons-v1
intraday-technical-v1
instrument-costs-v1
intraday-evaluation-v1
short-term-router-v1

If an existing component is extended compatibly, preserve old output semantics.

==================================================
23. BACKWARD COMPATIBILITY
==================================================

Existing functionality must continue to work.

Specifically preserve:

current dashboard behaviour
existing JSE ticker scoring
historical reconstruction
adaptive fusion
HR9 adaptive ensemble
HR10 robustness
existing cross-asset daily calculations
existing market profiles
agent simulations
paper execution

Where compatibility adapters are needed, write them explicitly.

No hidden migration.

==================================================
24. INITIAL RESEARCH UNIVERSE CONFIG
==================================================

Create a versioned default short-term research universe.

Initial enabled targets should preferably include:

USDZAR
JSE_INDEX
GOLD
BRENT
PLATINUM

plus a deliberately small set of highly liquid supported JSE equities.

Do NOT enable dozens of new assets immediately.

The architecture should support expansion later.

Every configured instrument must report:

enabled
data capability
history capability
intraday capability
execution type
profile
cost availability

==================================================
25. PERFORMANCE / PRACTICALITY
==================================================

Avoid unnecessary recomputation.

Cache deterministic intermediate results where consistent with architecture.

Do not introduce hidden state that makes research non-reproducible.

Research outputs should be deterministic for fixed:

data
configuration
version
random seed

Bootstrap/randomized procedures must use explicit reproducible seeds.

==================================================
26. SECURITY
==================================================

Do not expose:

API keys
tokens
credentials
private broker details

Do not write secrets into:

code
tests
logs
reports
markdown
git history

Preserve .env/.gitignore protections.

Tests involving provider failures must not leak secrets through exception strings.

==================================================
27. IMPLEMENTATION QUALITY
==================================================

Prefer:

small cohesive modules
typed dataclasses / existing project models
pure deterministic calculation functions
explicit configuration
versioned contracts
clear dependency boundaries

Avoid:

large god classes
hidden global mutation
duplicate indicator implementations
silent fallback
magic ticker mappings
magic cost numbers
network calls inside mathematical unit tests

==================================================
28. GIT WORKFLOW
==================================================

First record current:

branch
HEAD
status

Do not destroy current work.

Commit in logical stages if repository policy allows.

Suggested commit boundaries:

1. HR11 roadmap/design boundary
2. instrument registry
3. intraday data/timeframe contracts
4. feature/horizon layer
5. profiles + costs
6. cross-asset/gates
7. evaluator + robustness
8. paper router
9. reporting/docs/final regression

Do not rewrite historical commits.

==================================================
29. FINAL VALIDATION
==================================================

Before calling HR11 complete:

Run the entire targeted suite.

Run full suite if feasible.

Run compile/import validation.

Inspect git diff.

Inspect git status.

Confirm:

- no accidental secret files
- no overwritten HR9 artifacts
- no overwritten HR10 artifacts
- no unexpected changes to existing historical datasets
- no test fixtures accidentally committed as production data
- no live broker integration
- no execution mode other than paper/shadow

==================================================
30. FINAL REPORT
==================================================

At completion provide a concise but complete implementation report containing:

A. BASELINE

- starting branch
- starting commit
- initial git state

B. MILESTONE

- milestone identifier
- roadmap status
- deliverables completed

C. IMPLEMENTATION

List modules/files created or materially changed.

D. INSTRUMENT UNIVERSE

List the initially configured instruments and their capabilities.

E. DATA CONTRACT

Describe timing, session and availability semantics.

F. FEATURES

List implemented intraday feature families.

G. HORIZONS

Confirm separate:

session horizons
intraday horizons

H. COST MODEL

Describe instrument-specific cost handling.

I. CAUSALITY

List no-look-ahead protections and tests.

J. EVALUATION

Describe walk-forward and robustness architecture.

K. ADMISSION

Report which instrument/horizon cells are:

REJECT
INSUFFICIENT_EVIDENCE
ADMIT_FOR_CONTINUED_SHADOW

Do not fabricate positive findings if historical intraday data is not yet available.

L. TEST RESULTS

Report exact test counts.

Example:

Focused HR11: X passed
HR9 regression: X passed
HR10 regression: X passed
Full suite: X passed

M. ARTIFACTS

List generated research/report artifacts.

N. LIMITATIONS

Explicitly list anything still missing, such as:

licensed realtime data
bid/ask history
true broker spreads
intraday historical coverage
specific contract metadata

O. RECOMMENDATION

State whether HR11 should be:

COMPLETE
PARTIAL
BLOCKED

and explain why.

==================================================
31. IMPORTANT RESEARCH PRINCIPLE
==================================================

The objective is NOT:

"make the backtest profitable."

The objective is:

"determine whether a short-term signal survives realistic, causal, instrument-specific evaluation."

Negative evidence is valid evidence.

Do not weaken costs.

Do not remove losing periods.

Do not change thresholds purely because they improve the final result.

Do not select only successful instruments.

Do not leak test-period information into training.

Do not hide insufficient sample sizes.

==================================================
32. STOP CONDITIONS
==================================================

If any of the following occurs:

- existing HR9/HR10 results change unexpectedly
- causal mutation tests fail
- timing semantics are ambiguous
- cost calculations are internally inconsistent
- current repository work appears unfinished or conflicted
- a required architectural assumption contradicts an existing ADR

STOP THAT PARTICULAR IMPLEMENTATION PATH.

Do not destroy or overwrite the current implementation.

Document the conflict and design a compatible solution.

Continue with other safe deliverables where possible.

==================================================
FINAL OBJECTIVE
==================================================

At the end of this milestone the repository should contain a reproducible, point-in-time, causally safe, multi-instrument SHORT-TERM RESEARCH PIPELINE capable of evaluating:

JSE index exposure
USD/ZAR
gold
Brent
platinum
selected liquid JSE equities

across:

5m
15m
30m
60m
session-close

with:

instrument-specific profiles
cross-asset context
intraday technical features
realistic instrument-specific transaction costs
freshness/liquidity gates
walk-forward evaluation
purged/embargoed robustness analysis
explicit admission decisions
paper-only instrument routing
complete provenance
versioned contracts
documentation
and regression tests protecting all prior research.

Do not merely produce a design document.

IMPLEMENT IT.

TEST EACH DELIVERABLE BEFORE MOVING TO THE NEXT.

UPDATE THE ROADMAP THROUGHOUT.

PRESERVE ALL PRIOR VALIDATED RESEARCH.

LEAVE THE REPOSITORY CLEAN, DOCUMENTED, TESTED, AND REPRODUCIBLE.