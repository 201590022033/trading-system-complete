# OI2 — COMPLETE OPERATIONAL INTELLIGENCE DASHBOARD, BACKEND RE-WIRING & END-TO-END INTEGRATION

You are working autonomously overnight in the existing:

`trading-system-complete`

repository.

This is a major integration milestone.

Do **not** treat this as a cosmetic UI task.

Do **not** create another demonstration screen populated with fabricated values.

Do **not** stop after making Flask render attractive HTML.

Your task is to create the missing operational application layer that connects the surviving backend systems to a newly designed production-quality research dashboard.

The repository archaeology has already established that the remembered historical dashboard cannot be recovered from Git. Therefore you are explicitly authorized to design a new frontend and orchestration layer.

The goal of this milestone is:

> **Bring every usable backend capability identified during the audits into one coherent frontend, with working controls, accurate data provenance, clear unavailable/error states, and strict research/execution safety boundaries.**

By the end of this run the owner should be able to launch the application, select an instrument or scan the market, retrieve current market information where available, scan news, run technical analysis, inspect a 30-gate evidence/confidence assessment, see a BUY/SELL/HOLD analysis, inspect detailed reasoning and provenance, and use the Standard Bank/Shyft section for the safest currently supported manual execution handoff.

The application must be useful even when some external APIs are unavailable.

Do not wait for user feedback during this run unless a genuine safety/credential/repository-corruption stop condition occurs.

---

# 0. GOVERNING PRINCIPLES

Before touching code, read in this order:

1. `AGENTS.md`
2. `docs/agent/CONSTITUTION.md`
3. `docs/architecture/CURRENT_ARCHITECTURE.md`
4. `docs/architecture/TARGET_ARCHITECTURE.md`
5. `docs/roadmap/ROADMAP.md`
6. `docs/roadmap/CURRENT_MILESTONE.md`
7. `docs/ui/UI_RECOVERY_REPORT.md`
8. `docs/ui/DECISION_UI.md`
9. `docs/integrations/MARKET_DATA_EXECUTION_MATRIX.md`
10. `docs/integrations/VIEWPOINT_RESEARCH.md`
11. `docs/integrations/SHYFT_RESEARCH.md`
12. `docs/integrations/STANDARD_BANK_API_ENQUIRY.md`
13. `docs/research/HR9_ADAPTIVE_ENSEMBLE_REPORT.md`
14. `docs/research/HR10_ROBUSTNESS_REPORT.md`
15. `docs/research/NEXT_SIGNAL_RESEARCH.md`
16. relevant ADRs including the canonical `TradeSuggestion` safety ADR.

Then inspect the actual code.

The constitution remains authoritative.

Core rules:

- EVOLVE; DO NOT DESTROY.
- Reuse existing working backend modules.
- Do not duplicate a subsystem merely because connecting it is inconvenient.
- Search for existing functionality before implementing new functionality.
- Keep HR7–HR10 evidence immutable unless a narrowly necessary adapter/test/doc change is required.
- HR9/HR10 rejected research must remain research/shadow information only.
- Do not make rejected research an operational trade recommendation.
- Do not place live orders.
- Do not automate broker login.
- Do not bypass MFA/CAPTCHA.
- Do not expose credentials.
- Do not read or print `.env`.
- Never invent API availability.
- Never invent live prices.
- Never convert simulated data into a “live” label.
- Never invent confidence values merely to populate the interface.

---

# 1. STARTING REPOSITORY / GIT SAFETY

First:

```bash
git status --short
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
git log -10 --oneline
```

Expected recent history includes the UIR1 archaeology work, with `bc008a2` expected to be the latest recovery/audit commit unless the repository has legitimately advanced since then.

Do not blindly reset to that commit if HEAD has moved.

Document actual HEAD.

Known unrelated working-tree changes have historically included:

- `generate_app.py`
- `requirements.txt`
- `.vscode/settings.json`

Inspect status and preserve unrelated user changes.

Do not discard, reset, overwrite or commit unrelated modifications.

Do not inspect `.env` contents.

Confirm only that it is ignored/untracked as appropriate without displaying it.

Before broad modifications, create an internal safety record of:

- HEAD
- branch
- working-tree status
- files this milestone expects to modify.

---

# 2. DEFINE ONE ACTIVE MILESTONE

Create/activate:

## OI2 — Operational Intelligence Dashboard & End-to-End Orchestration

This remains **one milestone** even though it has internal phases.

Do not start HR11 or another predictive-research milestone during this run.

Do not tune HR9.

Do not modify HR10 admission gates merely to obtain passing signals.

The purpose of OI2 is operational integration of existing capabilities and creation of the missing user-facing application.

---

# 3. FIRST PHASE: COMPLETE BACKEND CAPABILITY INVENTORY

Before designing the orchestration code, audit all surviving backend functionality.

Search the complete repository for:

- market-data providers;
- Yahoo integrations;
- Finnhub integrations;
- quote retrieval;
- historical bars;
- NewsAPI;
- Moneyweb;
- SENS;
- sentiment analysis;
- LLM sentiment;
- technical indicators;
- legacy signal engines;
- bull/bear/general researchers;
- trader;
- risk agents;
- manager/governance;
- executor;
- portfolio;
- paper trading;
- Standard Bank OST;
- browser/manual-login components;
- Shyft support/linking;
- instrument profile mappings;
- regimes;
- macro/cross-market relationships;
- HR7 features;
- HR8 evidence;
- HR9 outputs;
- HR10 admission results;
- provider interfaces;
- `TradeSuggestion`;
- data timestamps/provenance;
- stale-data handling;
- cached evidence;
- current Flask routes/API routes;
- Socket.IO behavior;
- scheduled/async/background workers if any.

Use code search, tests, docs and history.

Do not rely solely on filenames.

Produce:

`docs/ui/OI2_BACKEND_INVENTORY.md`

with a machine-useful matrix:

| Capability | Existing implementation | Status | Inputs | Outputs | External dependency | Safe for UI? | UI destination | Action |
|---|---|---|---|---|---|---|---|---|

Statuses:

- `WORKING_LOCAL`
- `WORKING_NETWORK`
- `REQUIRES_CREDENTIAL`
- `PARTIAL`
- `RESEARCH_ONLY`
- `MOCK_ONLY`
- `BROKEN`
- `UNUSED`
- `UNKNOWN`

The inventory must cover **all substantive backend audit findings**, not only the systems mentioned in this prompt.

Any existing backend capability omitted from the UI must have a documented reason.

---

# 4. CORE ARCHITECTURE — CREATE THE MISSING ORCHESTRATION LAYER

The dashboard must not directly call arbitrary research modules from route handlers.

Create a clear application/orchestration layer.

Target conceptual flow:

```text
                       ┌──────────────────────┐
                       │ MarketDataProvider   │
                       └──────────┬───────────┘
                                  │
                                  ▼
┌──────────────────┐     ┌──────────────────────┐
│ News/SENS/Macro  │────▶│ Intelligence Context │
└──────────────────┘     └──────────┬───────────┘
                                    │
┌──────────────────┐                │
│ Technical Engine │────────────────┤
└──────────────────┘                │
                                    ▼
                          ┌────────────────────┐
                          │ Evidence/Gate      │
                          │ Evaluation         │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │ Legacy Decision    │
                          │ BUY/SELL/HOLD      │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │ TradeSuggestion    │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │ Human Review       │
                          └─────────┬──────────┘
                                    │
                                    ▼
                          ┌────────────────────┐
                          │ Manual/Paper       │
                          │ Broker Handoff     │
                          └────────────────────┘
```

Suggested concepts/classes, adapting names to existing architecture:

```python
OperationalIntelligenceService
InstrumentAnalysisService
MarketScannerService
NewsAnalysisService
TechnicalAnalysisService
ConfidenceGateService
TradeDecisionService
BrokerHandoffService
DashboardSnapshot
AnalysisRun
AnalysisComponentResult
```

Do not create wrappers merely for ceremony.

Prefer composition around existing engines.

---

# 5. CANONICAL ANALYSIS RUN

Create a versioned, serializable canonical object representing one user-requested analysis.

Conceptually:

```python
AnalysisRun:
    run_id
    instrument
    requested_at
    completed_at

    market_data
    news_analysis
    technical_analysis
    macro_analysis
    regime_analysis

    confidence_gates
    aggregate_evidence

    legacy_decision
    research_comparison

    trade_suggestion

    data_sources
    warnings
    unavailable_components
    errors

    status
```

Possible statuses:

- `PENDING`
- `RUNNING`
- `PARTIAL`
- `COMPLETE`
- `FAILED`
- `STALE`

Every component must expose:

- source;
- source timestamp;
- retrieval timestamp;
- live/delayed/historical/simulated state;
- success/failure;
- reason if unavailable;
- provenance/version where applicable.

---

# 6. DATA STATE MUST BE FIRST-CLASS

Define data-state semantics centrally:

```text
LIVE
DELAYED
CURRENT_PUBLIC
HISTORICAL
CACHED
SIMULATED
UNAVAILABLE
UNKNOWN
```

Never infer `LIVE` merely because retrieval occurred recently.

A Yahoo quote must be labeled according to what the provider actually guarantees.

A Finnhub quote must be labeled according to actual capability/entitlement.

A cached value must show age.

A historical bar must never appear visually identical to a current quote.

A simulated ticker may remain available as a fallback/demo mode, but must never silently replace failed real-data retrieval.

Every price card should include:

- provider;
- market timestamp if known;
- retrieval timestamp;
- age;
- state label;
- freshness/staleness indicator.

---

# 7. INSTRUMENT UNIVERSE AND CANONICAL SYMBOL MAPPING

Create/reuse a canonical instrument registry.

It must distinguish:

- user/display symbol;
- Yahoo/provider symbol;
- Finnhub/provider symbol;
- research identifier;
- Standard Bank/Shyft symbol if known;
- asset class;
- exchange;
- currency;
- sector/profile;
- supported capabilities.

Do not equate related instruments merely because they share a sector.

Explicit aliases may be supported where defensible, e.g. mappings such as:

```text
SOL ↔ SASOL
SHP ↔ SHPJ
```

only if code/data confirm the intended identity.

Do not present `GOLD` commodity research as instrument-specific evidence for an arbitrary gold miner.

Do not present sector evidence as exact single-stock evidence.

The UI should clearly distinguish:

- instrument-specific evidence;
- sector evidence;
- cross-market evidence;
- proxy evidence.

---

# 8. NEW FRONTEND — GENERAL DESIGN

Build the frontend from scratch around actual operational workflow.

Use the existing Flask stack unless a compelling technical reason requires a narrow change.

Do **not** introduce React/Vue/Node build complexity simply to build the dashboard.

Prefer:

- Flask templates;
- clean CSS;
- lightweight JavaScript;
- Fetch/JSON;
- Socket.IO only where continuous updates provide real value.

Create maintainable separation, e.g.:

```text
templates/
    dashboard.html
    partials/...

static/
    css/dashboard.css
    js/dashboard.js
```

rather than another enormous inline HTML string inside `app.py`.

Refactor `app.py` toward application routing/bootstrap.

Maintain reasonable compatibility with existing health/snapshot tests/routes where possible.

---

# 9. PRIMARY NAVIGATION

Create an application with these primary views/tabs:

1. **Dashboard**
2. **Market Scanner**
3. **News & SENS**
4. **Technical Analysis**
5. **30-Gate Confidence**
6. **Broker / Execution**
7. **Research / Diagnostics**
8. **System Status**

These may be one responsive page with sectional navigation or actual routes.

The user should never have to inspect JSON manually to understand what the system found.

---

# 10. DASHBOARD / LANDING PAGE

This is the main screen.

Top header:

```text
TRADING INTELLIGENCE DASHBOARD
```

Display:

- application mode;
- market/data status;
- current selected provider;
- most recent successful update;
- system health;
- network/external-service availability if known.

Prominent instrument selector:

```text
[ Instrument ▼ ]
[ Horizon ▼ ]
[ ANALYZE INSTRUMENT ]
[ FULL MARKET SCAN ]
```

Support practical horizon choices.

Do not pretend HR10's 1/3/5/20-session targets are equivalent to intraday horizons.

Where the backend supports only daily/session analysis, say so.

If there is an existing current-data technical path, expose its real cadence.

---

# 11. ANALYZE INSTRUMENT — ONE-CLICK END-TO-END WORKFLOW

The `ANALYZE INSTRUMENT` button must orchestrate all available analyses for the selected instrument.

It must not merely call one endpoint.

Workflow:

```text
1. Validate instrument.
2. Retrieve latest permissible market data.
3. Retrieve/prepare historical data needed for technicals.
4. Determine data freshness.
5. Run technical analysis.
6. Run news/SENS analysis.
7. Run available sentiment analysis.
8. Run available macro/cross-market context.
9. Determine regime/profile.
10. Evaluate the 30 evidence gates.
11. Run legacy decision engine.
12. Build BUY/SELL/HOLD result.
13. Construct TradeSuggestion only if safety rules permit.
14. Build broker/manual handoff information.
15. Return complete AnalysisRun.
```

If a component fails, do not abort every other component unless it is fundamentally required.

Result can be:

`PARTIAL`

with unavailable components clearly listed.

---

# 12. ASYNCHRONOUS/PROGRESS EXPERIENCE

Some scans may take seconds.

Do not freeze the browser with no feedback.

Display progress such as:

```text
Market data .............. COMPLETE
Technical indicators ..... COMPLETE
News sources ............. RUNNING
SENS ..................... COMPLETE
Sentiment ................. UNAVAILABLE
Macro context ............ COMPLETE
Confidence gates .......... WAITING
Decision engine ........... WAITING
```

Use sensible background/thread/task mechanisms already compatible with Flask.

Do not introduce an entire queue infrastructure unless actually necessary.

Prevent duplicate identical scans from hammering APIs.

---

# 13. MARKET DATA PANEL

Create a proper current-market panel.

Show where available:

- instrument;
- current/last price;
- bid;
- ask;
- spread;
- open;
- high;
- low;
- previous close;
- volume;
- percentage move;
- timestamp;
- source;
- data state;
- age.

Only display fields actually available.

Unavailable values:

`—`

with tooltip/explanation.

No fabricated bid/ask, volume or intraday range.

Display a small price/history chart from actual available bars.

Do not fabricate intraday candles from daily closes.

---

# 14. FULL MARKET SCANNER

Restore the conceptual functionality the owner expects by implementing a real market-scanning workflow.

Button:

## `FULL MARKET SCAN`

The scanner should run the lightweight/safe subset of analysis across the configured supported universe.

Results table:

| Rank | Instrument | Price | Direction | Evidence | News | Technical | Risk | Freshness | Action |
|---|---:|---:|---|---:|---:|---:|---|---|---|

Possible direction:

- BUY
- SELL
- HOLD
- NO TRADE
- INSUFFICIENT DATA

Do not rank insufficient-data instruments above usable candidates.

Ranking must be deterministic and documented.

Do not call something “81% probability of profit” unless it is genuinely calibrated as such.

A candidate score may instead be called:

- Evidence score;
- Gate support score;
- Directional conviction;
- Opportunity rank.

Clicking a result must load the full instrument analysis.

Cache scan results with source timestamps.

Allow user refresh.

Avoid excessive API use.

---

# 15. SEPARATE MARKET NEWS SCAN BUTTON

Create a prominent:

## `SCAN MARKET NEWS`

This must be distinct from technical analysis.

Connect all surviving safe/permissible news systems discovered in the inventory.

Expected discovered families may include:

- NewsAPI;
- Moneyweb;
- JSE/SENS;
- other existing repo collectors;
- existing sentiment components;
- authoritative event sources.

Do not invent connectivity.

When network/API credentials are absent:

- show source as unavailable;
- explain why;
- continue other sources.

Results should show:

- headline;
- source;
- publication timestamp;
- retrieval timestamp;
- instrument relevance;
- category;
- sentiment if genuinely calculated;
- confidence/evidence;
- link where permissible;
- authoritative vs media vs community classification.

Group important SENS/company announcements separately.

---

# 16. NEWS SUMMARY / DIRECTIONAL VIEW

After a news scan, show a concise panel:

```text
NEWS / EVENT VIEW

Directional implication: BULLISH / BEARISH / MIXED / NEUTRAL / INSUFFICIENT

Supporting:
• ...
• ...

Contradicting:
• ...
• ...

Authoritative events:
• ...

Source coverage:
5/7 available
```

Do not collapse all headlines into a sentiment number without provenance.

If an LLM is unavailable, use existing deterministic/fallback methods and label limitations.

---

# 17. SEPARATE TECHNICAL ANALYSIS BUTTON

Create:

## `RUN TECHNICAL ANALYSIS`

This must function independently of news.

Use existing technical engines rather than rebuilding arbitrary calculations.

Inventory and expose all useful available outputs.

Likely categories:

- trend;
- momentum;
- mean reversion;
- volatility;
- breakout;
- stochastic;
- RSI;
- moving averages;
- MACD if implemented;
- Bollinger if implemented;
- ATR if implemented;
- support/resistance where existing;
- volume where actual volume data exists.

Do not add an indicator simply because the UI mock lists it.

Only add new calculations if needed for the 30-gate engine and justified/tested.

Show:

```text
TECHNICAL VIEW: BUY / SELL / NEUTRAL / MIXED

Trend
Momentum
Volatility
Range/breakout
Volume/liquidity
Regime
```

Each technical result needs:

- value;
- interpretation;
- direction contribution;
- timeframe/data window;
- data timestamp;
- source/version.

---

# 18. REGIME AND PROFILE MUST BE VISIBLE

Where available show:

```text
Market regime:
TRENDING BULL
TRENDING BEAR
RANGE
HIGH VOLATILITY
UNKNOWN
```

and instrument/profile, e.g.:

```text
Energy / Sasol
Gold miner
PGM/diversified miner
Financial
Retail/consumer
Index
FX
Commodity
```

Do not use simplistic universal interpretation such as:

`RSI high = SELL`

without considering regime where existing architecture already conditions interpretation.

---

# 19. DESIGN AND IMPLEMENT THE 30-GATE CONFIDENCE SYSTEM

The historical 30-step confidence checker cannot be recovered.

Therefore implement a new explicit, auditable:

# 30-GATE TRADE EVIDENCE CHECK

It must not masquerade as a trained statistical probability model.

The dashboard must distinguish:

### A. Gate support score

from:

### B. Statistical/model confidence

if statistical confidence actually exists.

Never call `27/30` a 90% probability of profit.

---

# 20. EXACT 30-GATE STRUCTURE

Implement exactly 30 versioned gates grouped into 6 categories of 5.

Prefer existing backend evidence.

A gate can return:

```text
SUPPORTS_BUY
SUPPORTS_SELL
NEUTRAL
CONTRADICTS_BUY
CONTRADICTS_SELL
UNAVAILABLE
INSUFFICIENT_DATA
STALE
```

Each gate must include:

- gate ID;
- category;
- name;
- input evidence;
- evaluation timestamp;
- result;
- direction contribution;
- weight;
- explanation;
- source/provenance;
- availability reason.

### GROUP A — DATA QUALITY & MARKET STATE

1. Current-data availability
2. Data freshness
3. Historical-data sufficiency
4. Spread/liquidity quality where available
5. Abnormal/stale/data-anomaly check

### GROUP B — TREND & STRUCTURE

6. Short-term trend
7. Medium trend
8. Price vs key moving-average structure
9. Trend consistency / slope
10. Breakout / structural direction

### GROUP C — MOMENTUM & VOLATILITY

11. RSI/regime-aware momentum
12. MACD or authoritative equivalent if available
13. Stochastic/secondary momentum
14. ATR/volatility suitability
15. Momentum/price agreement or divergence evidence

### GROUP D — VOLUME / LIQUIDITY / MARKET CONFIRMATION

16. Volume confirmation
17. Relative-volume context
18. Liquidity suitability
19. Price/volume agreement
20. Volatility/liquidity risk compatibility

Where unavailable due data capability, return `UNAVAILABLE`.

Do not fabricate volume/order-book data.

### GROUP E — NEWS / EVENTS / MACRO / CROSS-MARKET

21. Recent company-news direction
22. SENS/authoritative-event check
23. News-source agreement
24. Macro/sector/cross-market context
25. Event-risk/conflicting-news check

### GROUP F — DECISION QUALITY / RISK / AGREEMENT

26. Legacy signal direction
27. Bull/Bear/General researcher agreement where available
28. Technical vs news agreement
29. Risk/reward feasibility
30. Contradiction / no-trade override check

If an existing backend supports a more appropriate gate than one of these, adaptation is allowed, but:

- keep exactly 30;
- document the substitution;
- preserve the six-category concept;
- ensure every gate is meaningful and nonduplicative.

Create a version identifier:

`confidence_gate_set_version`

---

# 21. AGGREGATE GATE SCORING

Create transparent scoring.

Do not hide unavailable gates.

Show separately:

```text
Available gates:       24 / 30
Supports BUY:          16
Supports SELL:          3
Neutral:                5
Unavailable:            6
Contradictions:         3
```

Then calculate a documented **Evidence Support Score**, not a fake probability.

Example conceptual range:

```text
Strong BUY evidence
Moderate BUY evidence
Weak / mixed
Moderate SELL evidence
Strong SELL evidence
```

Implement conservative coverage gates.

Example:

- insufficient available evidence → `INSUFFICIENT EVIDENCE`;
- major risk override → `NO TRADE`;
- serious stale data → `STALE / DO NOT ACT`.

Do not force BUY or SELL.

---

# 22. 30-GATE UI

Make this one of the signature elements of the application.

Visualize all 30 gates as compact status blocks:

```text
01 ✓ Data available
02 ✓ Fresh
03 ✓ History adequate
04 ? Spread unavailable
...
30 ✗ Contradiction detected
```

Allow expansion to show explanation.

Summary:

```text
30-GATE EVIDENCE CHECK

Available: 26/30
Supports trade: 19
Neutral: 4
Opposes: 3
Unavailable: 4

Evidence support: STRONG BUY
Coverage quality: GOOD
```

The user must be able to understand exactly why the score exists.

---

# 23. LEGACY BUY / SELL / HOLD ENGINE

Recover and wire the surviving legacy decision path.

This is critical.

Locate the actual implementation and characterize it with tests before changing behavior.

Show prominently:

```text
LEGACY ANALYSIS

BUY
SELL
HOLD
NO TRADE
INSUFFICIENT DATA
```

Never replace its result with HR9.

The result card must show contributing components where available.

For example:

```text
Technical       +0.41
News            +0.18
Macro           -0.05
Legacy score     0.54
Decision         BUY
```

Use actual existing logic and actual values.

Do not invent this exact weighting if existing code differs.

---

# 24. COMBINED OPERATIONAL DECISION

Create a careful orchestration policy around existing components.

The dashboard needs a useful final analysis, but do not claim predictive certainty the backend has not demonstrated.

Show:

```text
OVERALL VIEW

BUY
SELL
HOLD
NO TRADE
INSUFFICIENT DATA
```

Under it, display:

- legacy decision;
- technical view;
- news view;
- gate evidence;
- regime;
- major contradictions;
- data quality.

The operational decision policy must be deterministic, documented and tested.

A severe data-quality or risk gate can force `NO TRADE`.

Insufficient evidence can force `INSUFFICIENT DATA`.

Do not force a trade simply because technical and news scores exist.

---

# 25. TRADE ANALYSIS CARD

For actionable non-rejected operational analysis, show:

```text
TRADE ANALYSIS

Instrument
Direction
Last/current price
Price source
Data timestamp
Horizon

Suggested entry
Suggested stop
Suggested target
Risk/reward
Risk amount / maximum risk
Position-size suggestion

Evidence support
Key reasons
Contradictions
Expiry/stale-after
```

Reuse/extend canonical `TradeSuggestion`.

Do not calculate position size without a defined account/risk input.

If account capital is unknown, show:

```text
Position size: requires account/risk setting
```

or calculate illustrative size only when explicitly labeled.

---

# 26. DO NOT CONFUSE RESEARCH CONFIDENCE WITH OPERATIONAL ANALYSIS

HR9 and HR10 belong in a separate research diagnostics area.

Display clearly:

```text
ADAPTIVE HR9 RESEARCH
STATUS: REJECTED / SHADOW ONLY

HR10 robust admission:
0 admitted
```

where relevant.

Do not allow HR9 output to alter operational BUY/SELL/HOLD unless a future formally approved milestone promotes it.

Research results may be useful as comparison/diagnostics only.

---

# 27. RESEARCH / DIAGNOSTICS PANEL

Create a collapsible/secondary research view.

Include where useful:

- legacy result;
- HR7 features;
- HR8 indicator evidence;
- HR9 shadow result;
- HR10 admission status;
- evidence sample counts;
- research horizon;
- regime;
- profile;
- contribution detail;
- timestamps;
- unavailable reason.

Do not overwhelm the main trade screen with this.

The main screen is for fast human interpretation.

The research screen is for inspection.

---

# 28. STANDARD BANK / SHYFT SECTION

Create a central, useful broker/execution area.

It must reflect what is actually known.

Header:

```text
STANDARD BANK / SHYFT
```

Show:

- configured broker path;
- connectivity status;
- account connectivity status;
- quote capability if any;
- position capability if any;
- execution capability;
- whether official API access has been confirmed.

Current safest supported workflow is expected to remain manual unless actual official entitlement exists.

Support safe actions such as:

### `COPY TRADE DETAILS`

Copies a clean ticket:

```text
Instrument:
Direction:
Entry:
Stop:
Target:
Quantity:
Risk:
Time/Horizon:
Generated:
Expiry:
```

### `OPEN SHYFT`

Only open an official/public Shyft destination or configured safe external URL.

Do not include credentials.

### `MARK AS ENTERED MANUALLY`

This records local/manual state only.

It must **not** claim the broker accepted the trade.

### `MARK AS DISMISSED`

Records user decision.

If existing read-only Standard Bank browser components are usable safely, expose their status/read-only capabilities in this section.

Do not automate login or order submission.

---

# 29. OST / EXISTING STANDARD BANK BACKEND

Audit surviving Standard Bank/OST modules.

For every surviving capability determine:

- safe;
- obsolete;
- login-required;
- network-required;
- browser-required;
- read-only;
- unsupported.

Wire safe read-only status/functions to the frontend where practical.

For unavailable capabilities, show:

```text
STANDARD BANK OST
Status: LOGIN REQUIRED / NOT CONNECTED / RETIRED / UNKNOWN
```

Do not simply remove the section.

---

# 30. NEWS / TECHNICAL / FULL ANALYSIS MUST REMAIN SEPARATE

The UI needs these separate controls:

- `SCAN MARKET NEWS`
- `RUN TECHNICAL ANALYSIS`
- `ANALYZE INSTRUMENT`
- `FULL MARKET SCAN`

Each does exactly what its name says.

`ANALYZE INSTRUMENT` combines the others.

The separate buttons remain important for troubleshooting and human inspection.

---

# 31. SOURCE RELIABILITY

Where the repository already models source reliability, expose it.

A news/source result may show:

```text
Source reliability: HIGH / MEDIUM / LOW / UNKNOWN
```

or existing quantitative evidence.

Do not equate authority/popularity with learned predictive reliability.

Where there is no evidence, label `UNKNOWN`.

---

# 32. SENS

Use the surviving SENS functionality if operational.

SENS is an important authoritative event source.

The UI should distinguish:

```text
SENS / AUTHORITATIVE COMPANY ANNOUNCEMENTS
```

from general news.

Do not claim that the future licensed point-in-time SENS research dataset already exists if it does not.

Operational retrieval and historical predictive research are separate concepts.

---

# 33. MACRO / CROSS-MARKET PANEL

Where existing backend relationships exist, expose them without oversimplification.

Relevant examples may include:

- USD/ZAR;
- Brent;
- gold;
- global risk;
- sector relationships;
- index conditions.

Do not hard-code simplistic statements such as:

```text
Brent up = JSE down
Gold up = risk off
Weak rand = banks down
```

Use existing contextual model/profiles.

Show:

```text
Cross-market context:
SUPPORTIVE / NEGATIVE / MIXED / UNAVAILABLE
```

with explanation.

---

# 34. ERROR HANDLING MUST BE USER-FACING

Do not dump stack traces into the browser.

For each service:

```text
NewsAPI: API key not configured
Finnhub: unavailable
Yahoo: returned delayed/current-public quote
SENS: network timeout
Technical analysis: complete
```

The application must continue operating when optional services fail.

Log detailed exceptions server-side.

Expose concise diagnostics.

---

# 35. SYSTEM STATUS PAGE

Create a status screen showing every major subsystem:

| Subsystem | Status | Last success | Data mode | Notes |
|---|---|---|---|---|

Include:

- Flask;
- market-data providers;
- Yahoo;
- Finnhub;
- historical data;
- news;
- Moneyweb;
- SENS;
- sentiment;
- technical engine;
- legacy decision;
- confidence engine;
- broker provider;
- Standard Bank/OST;
- HR7;
- HR8;
- HR9;
- HR10.

This provides a simple answer to:

> “What is actually working right now?”

---

# 36. API DESIGN

Create clean JSON endpoints.

Exact paths can adapt to architecture, but likely:

```text
GET  /api/system/status
GET  /api/instruments
GET  /api/market/<instrument>
POST /api/analysis/<instrument>
POST /api/analysis/<instrument>/news
POST /api/analysis/<instrument>/technical
POST /api/scan/market
GET  /api/analysis/<run_id>
GET  /api/research/<instrument>
POST /api/trade/<suggestion_id>/manual
```

Maintain `/health`.

Do not create a live-order endpoint.

No endpoint should submit an actual broker order.

---

# 37. CACHING / RATE CONTROL

Implement sane caching.

Examples:

- current quote: short TTL based on provider;
- news: several minutes;
- SENS: sensible interval;
- technicals: tied to bar freshness;
- macro context: provider-appropriate;
- market scan: cache constituent results.

Do not repeatedly call external APIs each second.

A Socket.IO display update must not imply recalculation of expensive analysis every second.

Separate:

```text
PRICE UPDATE CADENCE
```

from:

```text
INTELLIGENCE RECALCULATION CADENCE
```

---

# 38. STALE DATA

Centralize stale rules.

TradeSuggestion already has expiry/stale semantics; use them.

If analysis becomes stale:

```text
STALE — REFRESH BEFORE ACTING
```

Disable broker-copy/manual-action workflow where appropriate.

Stale/rejected research must never masquerade as executable.

---

# 39. FRONTEND VISUAL HIERARCHY

Main dashboard should prioritize:

### LEVEL 1 — immediate decision

- instrument;
- price;
- data state;
- BUY / SELL / HOLD / NO TRADE;
- evidence quality;
- horizon;
- refresh time.

### LEVEL 2 — action/risk

- entry;
- stop;
- target;
- risk;
- trade ticket.

### LEVEL 3 — evidence

- 30 gates;
- technical;
- news;
- SENS;
- macro.

### LEVEL 4 — research diagnostics

- HR7–HR10;
- raw contributions;
- versions;
- sample counts.

Do not put research jargon ahead of the trade decision.

---

# 40. RESPONSIVE DESIGN

It must work on:

- desktop;
- laptop;
- tablet;
- phone.

On smaller screens:

- cards stack;
- decision remains at top;
- tables become scrollable/cards;
- 30 gates remain legible;
- buttons remain large enough;
- no horizontal page breakage.

---

# 41. NO FAKE CONTENT

This requirement is absolute.

Do not populate the operational UI with:

- fake BUY;
- fake 76% confidence;
- fake price;
- fake stop;
- fake target;
- fake news;
- fake Standard Bank connectivity.

Demo/simulated values may exist only in an explicit:

`DEMO / SIMULATION MODE`

which the user deliberately selects or which is clearly identified as fallback.

Real mode should show unavailable fields rather than fabricated ones.

---

# 42. EXECUTION SAFETY

Existing safety remains mandatory.

These must remain impossible:

- research → live execution;
- rejected → execution;
- stale → execution;
- `NO TRADE` → execution;
- missing data → execution;
- live broker write through provider interface.

Add explicit tests.

---

# 43. USER SETTINGS / RISK SETTINGS

Add simple persistent local settings if appropriate:

- preferred instrument universe;
- default horizon;
- account currency;
- optional account size;
- risk-per-trade percentage;
- max risk;
- data provider preference.

Never store passwords/API secrets in browser local storage.

Credentials continue through existing secure/environment mechanisms.

Do not read `.env` to display them.

---

# 44. MANUAL TRADE JOURNAL STATE

If useful and safe, support local state:

```text
IDEA
REVIEWED
ENTERED_MANUALLY
DISMISSED
EXPIRED
```

This is application metadata.

It is not broker confirmation.

Store only if repository already has a suitable persistence mechanism or implement a minimal local non-secret store with tests.

Do not create a large database migration unless necessary.

---

# 45. PERFORMANCE

The dashboard must remain responsive.

Avoid:

- running whole historical research on every page refresh;
- reading 100k-row artifacts unnecessarily;
- re-running HR10;
- calling every network service every second;
- blocking Flask request threads for long periods when avoidable.

Use precomputed research artifacts where appropriate.

---

# 46. TESTING — BUILD CHARACTERIZATION FIRST

Before rewiring an existing engine, create characterization tests for its current behavior.

Then add OI2 tests.

Required categories:

## UI rendering

- dashboard route loads;
- instrument selector exists;
- analyze button exists;
- full market scan exists;
- news scan exists;
- technical scan exists;
- 30-gate panel exists;
- BUY/SELL/HOLD panel exists;
- Standard Bank/Shyft panel exists;
- system status exists.

## API

- instruments;
- market snapshot;
- news scan;
- technical analysis;
- full analysis;
- market scan;
- system status.

## Data provenance

- simulated cannot say live;
- historical cannot say live;
- cached exposes age/state;
- stale status works;
- missing provider fields remain unavailable.

## 30-gate system

- exactly 30 gate definitions;
- stable IDs;
- all serialize;
- unavailable gates remain visible;
- coverage calculation correct;
- contradiction override works;
- no fake probability claim.

## Decision

- legacy engine is actually used;
- insufficient evidence can result in HOLD/NO TRADE/INSUFFICIENT;
- contradictory evidence is visible;
- HR9 rejected output does not become operational decision.

## TradeSuggestion safety

- rejected cannot preview;
- shadow cannot preview;
- stale cannot preview;
- no-trade cannot preview;
- live account modes rejected;
- no live submission path.

## Broker handoff

- copy-ticket contains expected fields;
- manual mark does not place order;
- external Shyft action is link/handoff only.

## Failure handling

Simulate:

- Yahoo failure;
- Finnhub failure;
- NewsAPI unavailable;
- SENS unavailable;
- partial analysis;
- timeout;
- stale data.

The UI/API must degrade gracefully.

---

# 47. REGRESSION SUITES

Run all safe focused tests including:

- HR7;
- HR8;
- HR9;
- HR10;
- provider interfaces;
- OI1;
- UIR1;
- OI2.

Then run full safe/offline suite.

External tests requiring:

- network;
- credentials;
- browser login;
- cloud access;
- Reddit;
- LLM provider;

must be clearly reported as:

`EXCLUDED / NOT EXECUTED`

rather than silently ignored.

Do not fake passes.

---

# 48. LIVE/NETWORK SMOKE TEST

Where internet is available and the provider requires no secret, perform a minimal safe smoke test.

Do not perform bulk scraping.

Do not trigger paid operations.

Verify at least one real instrument path if legitimately accessible.

Record:

- provider;
- instrument;
- retrieval;
- timestamp;
- state label;
- whether current/delayed/historical.

If no safe live/public provider works during this run, the application must still be complete and show accurate unavailable states.

---

# 49. SECURITY REVIEW

The previous archaeology reportedly encountered a credential-like historical value.

Do not reproduce it.

Do not print it.

Do not migrate it into new code.

Do not add it to documentation.

If possible, identify only the affected service/file/history location in a security note without exposing the secret.

Create/update:

`docs/security/CREDENTIAL_ROTATION_REQUIRED.md`

stating:

- a historical credential-like value was detected;
- it should be rotated if still valid;
- it was not copied;
- no secret value is included.

Do not rewrite public Git history during this milestone.

---

# 50. DOCUMENTATION

Create/update at minimum:

```text
docs/ui/OI2_BACKEND_INVENTORY.md
docs/ui/OPERATIONAL_DASHBOARD.md
docs/ui/THIRTY_GATE_CONFIDENCE.md
docs/ui/OI2_INTEGRATION_REPORT.md

docs/architecture/CURRENT_ARCHITECTURE.md
docs/architecture/TARGET_ARCHITECTURE.md

docs/roadmap/CURRENT_MILESTONE.md
docs/roadmap/ROADMAP.md

docs/integrations/MARKET_DATA_EXECUTION_MATRIX.md
```

Create an ADR for the orchestration/dashboard architecture if constitutionally appropriate.

Document:

```text
DATA
  ↓
INTELLIGENCE COMPONENTS
  ↓
30-GATE EVIDENCE
  ↓
LEGACY DECISION
  ↓
TRADE SUGGESTION
  ↓
HUMAN REVIEW
  ↓
MANUAL/PAPER BROKER HANDOFF
```

---

# 51. BACKEND-TO-FRONTEND TRACEABILITY MATRIX

Before declaring OI2 complete, produce:

`docs/ui/OI2_TRACEABILITY_MATRIX.md`

Every surviving/backend audited capability must appear.

Example:

| Backend capability | Module | API | UI component | Tested | Operational status |
|---|---|---|---|---|---|
| Yahoo quote | ... | ... | Market card | yes | working |
| Finnhub | ... | ... | Market card/status | yes | credential required |
| Moneyweb | ... | ... | News panel | yes | ... |
| SENS | ... | ... | SENS panel | yes | ... |
| Legacy signal | ... | ... | BUY/SELL/HOLD | yes | working |
| HR9 | ... | ... | Research diagnostics only | yes | rejected/shadow |
| Standard Bank OST | ... | ... | Broker panel | yes | read-only/manual |

**No audited capability may silently fall through the cracks.**

This traceability matrix is one of the milestone acceptance gates.

---

# 52. COMPLETION CHECKLIST

Do not declare milestone complete until all are true or explicitly documented as externally blocked:

```text
[ ] New landing/dashboard exists
[ ] Actual backend data feeds are wired where usable
[ ] Real/simulated/delayed/historical state is truthful
[ ] Instrument analysis works end to end
[ ] Full Market Scan exists
[ ] Scan Market News works
[ ] Technical Analysis works
[ ] SENS component appears
[ ] Macro/cross-market context appears where available
[ ] Exactly 30 confidence/evidence gates exist
[ ] 30 gates use real backend evidence
[ ] Gate explanations are visible
[ ] BUY/SELL/HOLD legacy analysis is visible
[ ] Trade analysis card exists
[ ] TradeSuggestion safety remains enforced
[ ] Standard Bank/OST section exists
[ ] Shyft manual handoff exists
[ ] Research diagnostics exposes HR7-HR10 safely
[ ] System Status page exists
[ ] Missing services report unavailable rather than vanish
[ ] All relevant backend inventory items are mapped to UI
[ ] Responsive desktop/mobile layout works
[ ] Safe test suite passes
[ ] External exclusions documented
[ ] No secret committed
[ ] No live order route exists
```

---

# 53. DO NOT STOP AT A PRETTY SCREEN

This is especially important.

The milestone is **NOT COMPLETE** because:

- Flask renders;
- CSS looks nice;
- buttons appear;
- mock JSON is returned;
- simulated ticker works;
- a fake BUY card is displayed.

Every primary action must hit a real orchestration/service path.

Every panel must consume real backend results or expose an explicit unavailable state.

---

# 54. IF BACKEND COMPONENTS ARE BROKEN

If a surviving backend component is obviously broken:

1. write a characterization/reproduction test;
2. determine whether the fix is narrowly scoped and safe;
3. repair it if practical;
4. document the repair;
5. wire it to the UI;
6. run regression tests.

Do not abandon the whole milestone because one optional data source is broken.

If repair requires credentials/licensing unavailable tonight:

- implement the provider/UI boundary;
- expose configuration requirement;
- test with mock fixtures;
- continue.

---

# 55. AUTONOMOUS OVERNIGHT EXECUTION

Proceed autonomously through OI2.

Do not ask the user to approve:

- filenames;
- CSS choices;
- ordinary architecture;
- route naming;
- minor refactors;
- test fixtures;
- documentation layout.

Make reasonable engineering decisions consistent with repository constitution.

If you encounter a nonessential uncertainty, document it and continue.

Only stop early for:

- risk of destroying user work;
- inability to determine repository state safely;
- credentials/secrets requiring exposure;
- destructive operation;
- live-trading action;
- architecture decision that would irreversibly replace core functioning code without evidence.

---

# 56. VALIDATION USING THE RUNNING APPLICATION

Before finishing, actually launch the app.

Resolve port conflict safely if another stale process is using the port.

Do not kill unrelated processes blindly.

Verify main views manually or via browser-capable tooling where available.

At minimum inspect:

- dashboard;
- one instrument analysis;
- news button;
- technical button;
- 30 gates;
- market scan;
- BUY/SELL/HOLD display;
- Standard Bank/Shyft section;
- research diagnostics;
- status page.

Check browser console/server logs for errors.

Verify mobile/responsive layout using available tooling or viewport tests.

---

# 57. SCREENSHOTS / UI REVIEW ARTIFACTS

If browser/screenshot tooling is available, capture representative screenshots or otherwise document the rendered states:

1. dashboard idle;
2. analysis completed;
3. partial/unavailable external-source state;
4. 30-gate expanded view;
5. market scanner;
6. broker handoff;
7. research diagnostics.

Store only if normal repository practice supports it.

Do not add huge unnecessary binary artifacts.

---

# 58. FINAL GIT REQUIREMENTS

Review:

```bash
git status
git diff --stat
git diff
```

Verify:

- no `.env`;
- no credentials;
- no browser cookies;
- no tokens;
- unrelated user changes remain untouched;
- HR9/HR10 immutable artifacts remain unchanged unless explicitly expected;
- no generated junk.

Commit OI2 milestone work.

A sensible message:

```text
feat OI2: wire operational intelligence dashboard
```

If multiple checkpoint commits are necessary during the overnight run, they must all belong clearly to OI2.

Do not include unrelated files.

---

# 59. REQUIRED FINAL REPORT

Your final response must be detailed enough for the owner to assess the overnight work without immediately rerunning archaeology.

Use these headings:

## 1. Repository state

- starting HEAD
- ending HEAD
- branch
- commit(s)
- preserved unrelated changes

## 2. What was built

Summarize the complete operational architecture.

## 3. UI

List every page/tab/panel and action.

## 4. Backend integration matrix

Summarize every major backend subsystem and whether it is:

- wired and working;
- wired but credential-required;
- wired but network unavailable;
- research only;
- unsupported.

## 5. Market data

Explain exact live/delayed/current-public/historical/simulated behavior.

Do not say “live” loosely.

## 6. Market scanner

Explain universe, ranking and operation.

## 7. Market-news scanner

List connected sources and unavailable sources.

## 8. Technical analysis

List actual engines/indicators wired.

## 9. 30-gate confidence/evidence checker

List all 30 gates, scoring semantics, coverage handling and overrides.

## 10. BUY/SELL/HOLD

Identify exact legacy backend path used and how the operational decision is constructed.

## 11. Standard Bank / OST / Shyft

Explain exactly what is working, read-only, manual, unknown or blocked.

## 12. HR7–HR10

Confirm their frontend visibility and strict research/safety boundaries.

## 13. Tests

Give:

- focused test counts;
- full safe/offline counts;
- failures;
- exclusions;
- network smoke-test results.

## 14. UI launch

Exact command, for example:

```bash
.venv/bin/python app.py
```

and exact URL.

## 15. Remaining blockers

Only genuine external/data/licensing/credential blockers.

## 16. Acceptance checklist

Repeat the OI2 checklist with PASS / PARTIAL / BLOCKED.

## 17. Recommended next milestone

Recommend **one** next milestone only.

Do not start that next milestone.

---

# 60. DEFINITION OF SUCCESS

OI2 succeeds when the application has changed from:

> “a simulated research ticker/demo card”

into:

> **a real operational research dashboard that orchestrates the surviving trading-system backend, exposes what is actually working, provides separate news and technical scanning, performs transparent 30-gate evidence assessment, restores a useful BUY/SELL/HOLD analysis workflow, performs full-universe scanning, and creates a safe human-reviewed Standard Bank/Shyft trade handoff without live-order automation.**

The owner should be able to open the application tomorrow and meaningfully explore the system without needing to read source code to determine what works.

Do not wait for further instructions.

Begin OI2 now.