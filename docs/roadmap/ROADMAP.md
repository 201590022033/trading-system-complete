# Linear Fusion Roadmap

## Persistent Shadow-Learning Foundation — ACTIVE 2026-09-16

The current implementation milestone is a durable, incremental shadow-learning
loop with SQLite local persistence and PostgreSQL runtime parity. It does not
promote shadow evidence into production adaptive state, invoke brokers, or
rerun historical research on Railway. See [shadow-learning design](../research/SHADOW_LEARNING.md).

## M30 — Bounded IG Demo Execution Validation [COMPLETE 2026-09-11]

Added a default-non-mutating two-phase validation harness over the M26–M29
boundaries. It uses only a clearly labelled synthetic validation chain, requires
fresh factual preflight and separate explicit permission for Phase B, permits one
opening mutation, never retries unknown outcomes, separates acknowledgement from
confirmation, then performs read-only state refresh and M27 reconciliation. No
close operation, GUI control, LIVE path or autonomous orchestration exists. See
[M30 validation](../execution/M30_BOUNDED_IG_DEMO_VALIDATION.md).

Phase B was not authorized or run. M25 external empirical HR11 validation remains
pending/inconclusive.

Next unfinished roadmap milestone: UNDEFINED — no post-M30 milestone is currently authorized.

## M29 — IG Demo Order Submission [COMPLETE 2026-09-11]

Added an explicit-invocation, default-disabled IG Demo MARKET adapter requiring
an exact M28 PASS and M15 approval. It maps only explicitly supported fields,
locks stable intent identity before one mutation attempt, never retries unknown
outcomes, and separates acknowledgement from confirmation. No external order,
LIVE path, GUI control or autonomous orchestration was added. See
[M29 submission](../execution/M29_IG_DEMO_ORDER_SUBMISSION.md).

M25 external empirical HR11 validation remains pending/inconclusive.

Next unfinished roadmap milestone: M30 — Bounded IG Demo Execution Validation [NOT STARTED].

## M28 — IG Demo Execution Safety Gate [COMPLETE 2026-09-11]

Added immutable context/check/decision contracts and a deterministic IG Demo-only
prerequisite evaluator covering explicit flags/human permission, M14/M15 chain,
M26 state, M27 reconciliation, exact mapping, market freshness/state, duplicate
identity, conflicts, kill switch, FX, margin and provenance. It contains no
transport or broker payload; actual repository state remains ineligible. See
[M28 safety gate](../execution/M28_IG_DEMO_EXECUTION_SAFETY_GATE.md).

M25 external empirical HR11 validation remains pending/inconclusive.

Next unfinished roadmap milestone: M29 — IG Demo Order Submission [NOT STARTED].

## M29 — IG Demo Order Submission [NOT STARTED]

Any actual Demo submission requires separate explicit authorization and a PASS
M28 decision. Live execution remains outside scope.

## M27 — Read-only Broker State Reconciliation [COMPLETE 2026-09-11]

Added immutable internal snapshot, comparison, discrepancy and result contracts
plus a pure deterministic reconciliation service. Exact deal/EPIC/canonical
matching, explicit units/tolerances, freshness, non-comparable fields and
unavailable-vs-flat semantics are retained without mutation. See
[M27 reconciliation](../execution/M27_BROKER_STATE_RECONCILIATION.md).

M25 external empirical HR11 validation remains pending/inconclusive.

Next unfinished roadmap milestone: M28 — IG Demo Execution Safety Gate [NOT STARTED].

## M28 — IG Demo Execution Safety Gate [NOT STARTED]

Any Demo execution work requires a separate explicit mandate and must preserve
all risk, reconciliation and live-execution prohibitions until approved.

## M26 — Read-only Broker Account and Position State [COMPLETE 2026-09-11]

Added immutable broker-neutral account, position and snapshot contracts plus an
IG Demo GET-only service over `/accounts` v1 and `/positions` v2. Broker currency,
balance terms, EPIC-specific positions, supplied P&L, provenance, unresolved
mappings, empty-vs-unavailable state and configurable freshness remain explicit.
PaperBroker, legacy portfolio, risk and execution stay separate. See
[M26 broker state](../execution/M26_READONLY_BROKER_STATE.md).

M25 external empirical HR11 validation remains pending/inconclusive until real
data and factual session/calendar context are supplied.

Next unfinished roadmap milestone: M27 — Read-only Broker State Reconciliation [NOT STARTED].

## M27 — Read-only Broker State Reconciliation [NOT STARTED]

Compare canonical internal/PaperBroker and broker-observed snapshots without
mutating either side or enabling Demo execution. Requires separate authorization.

## M25 — HR11 Real-data Validation [COMPLETE 2026-09-11]

Registered a single-treatment M17 experiment and added a strict M12B-to-HR11
completed-bar bridge. All strategy logic remains frozen; only IG historical data
availability may change. Credentials and a factual EPIC session calendar were
unavailable locally, so external retrieval was not run, no metrics were invented,
and the result is `INSUFFICIENT_EVIDENCE / INCONCLUSIVE`, not strategy failure.
See [M25 validation](../research/M25_HR11_REAL_DATA_VALIDATION.md).

Next unfinished roadmap milestone: M26 — Read-only Broker Account and Position State [NOT STARTED].

## M26 — Read-only Broker Account and Position State [NOT STARTED]

Normalize broker-observed account and position state without enabling Demo or
live dealing. Requires separate authorization.

## M24 — Real-time Market Streaming [COMPLETE 2026-09-11]

Added canonical read-only subscriptions, raw IG updates and market observations
with preserved bid/ask, versioned mid/spread, UTC/receipt clocks, ordering,
staleness, health and bounded reconnect/restoration. IG Demo uses the documented
session-provided Lightstreamer endpoint and PRICE item through an injectable
transport. No persistence, bar aggregation, orchestration, PaperBroker auto-fill
or broker order capability was added. See
[M24 streaming](../market_data/M24_REALTIME_STREAMING.md).

M12A/M12B superseded old M22/M23 discovery/history placeholders. The unfinished
real-data HR11 validation is explicitly retained as the next milestone:

## M25 — HR11 Real-data Validation [NOT STARTED]

Validate HR11 against factual broker data, calendars and costs under a separate
authorization. M12B's limited Demo sample did not close this research gap.

Next unfinished roadmap milestone: M25 — HR11 Real-data Validation [NOT STARTED].

## M21 — PaperBroker [COMPLETE 2026-09-11]

Added a broker-neutral protocol and explicit PAPER-only deterministic simulator
with M15 risk gating, supplied-price market fills, configured slippage/costs,
cash/equity/P&L, netted positions, duplicate and reversal protection,
cancellation, close, reconciliation and append-only audit evidence. Current
unresolved policies remain non-executable. M12A/M12B supersede old M22/M23 IG
discovery/history placeholders; remaining IG work begins with streaming/account/
Demo execution/reconciliation. No GUI or real-broker execution was added. See
[M21 PaperBroker](../execution/M21_PAPER_BROKER.md).
The full safe suite passes 468 tests and 39/39 protected artifacts are unchanged.

Next unfinished roadmap milestone: M24 — Real-time Market Streaming [NOT STARTED].

## M20 — Early Read-Only Top-5 GUI [COMPLETE 2026-09-11]

Added an accessible, manually refreshed canonical Top-5 tab over M19. It renders
research-score semantics, direction, evidence, suitability, blockers and
backend-provided readiness, with expandable unresolved policy/risk detail.
Empty/error states do not fabricate or substitute recommendations. Legacy UI is
preserved and no frontend business logic, execution control, broker action,
runtime change, or M21 work was added. See
[M20 Top-5 GUI](../ui/M20_TOP5_GUI.md).
The full safe suite passes 459 tests and 39/39 protected artifacts are unchanged.

Next milestone: M21 — PaperBroker [NOT STARTED].

## M19 — Canonical Opportunity / TradeIntent API [COMPLETE 2026-09-11]

Added framework-neutral read-only services and `/api/v1/opportunities` routes
over injected M13–M15 records. Explicit DTOs preserve comparative-score meaning,
unresolved stops, null risk size, blockers, uncertainty, timestamps and versions.
Intent previews are non-executable and unresolved prerequisites return 409.
Legacy endpoints coexist unchanged; no fabricated feed, broker order, runtime
execution, GUI, or M20 work was added. See
[M19 Canonical Opportunity API](../api/M19_CANONICAL_OPPORTUNITY_API.md).
The full safe suite passes 450 tests and 39/39 protected artifacts are unchanged.

Next milestone: M20 — Early Read-Only Top-5 GUI [NOT STARTED].

## M18 — Canonical Metrics [COMPLETE 2026-09-11]

Added context-explicit, versioned research metrics and immutable results with
visible sample depth and unavailable/invalid states. Expectancy, hit/payoff,
annualized Sharpe/Sortino, drawdown, volatility, position turnover, costs,
profit factor, Calmar, exposure and weighted estimates retain distinct units and
semantics. HR10 sample scaling remains explicitly legacy. M16/M17 can reference
metric versions/results without rewriting prior evidence. No optimization,
runtime, broker, execution, or M19 work was added. See
[M18 Canonical Metrics](../research/M18_CANONICAL_METRICS.md).
The full safe suite passes 442 tests and 39/39 protected artifacts are unchanged.

Next milestone: M19 — Canonical Opportunity / TradeIntent API [NOT STARTED].

## M17 — Experiment Registry [COMPLETE 2026-09-11]

Added an immutable, append-only scientific registry boundary covering baseline,
deficiency, one attributable hypothesis/treatment, explicit controls, M16 target,
causal data boundaries, reproducible runs, multidimensional results, retained
negative evidence, governed decisions and explicit baseline lineage. Factorial
designs must be declared. Historical HR7–HR11 remain legacy/pre-registry and
unchanged. Persistence adapters await one coordinated SQLite/PostgreSQL additive
migration. No optimization, promotion, runtime, broker, execution, or M18 work
was added. See
[M17 Experiment Registry](../research/M17_EXPERIMENT_REGISTRY.md).
The full safe suite passes 429 tests and 39/39 protected artifacts are unchanged.

Next milestone: M18 — Canonical Metrics [NOT STARTED].

## M16 — StrategyTarget [COMPLETE 2026-09-11]

Added versioned, family/horizon-scoped strategy target declarations with exact
metric and evidence-stage context. Hard failures cannot be averaged away by
soft successes, and absent thresholds remain unconfigured. HR10's t-stat-like
sample scaling retains a distinct legacy identity; canonical Sharpe requires
explicit periodic annualization context. Assessments indicate research review
readiness only and never promotion. No thresholds, optimization, runtime or
execution behavior changed. See
[M16 StrategyTarget](../research/M16_STRATEGY_TARGET.md).
The full safe suite passes 419 tests and 39/39 protected artifacts are unchanged.

Next milestone: M17 — Experiment Registry [NOT STARTED].

## M15 — Risk & Exposure Engine [COMPLETE 2026-09-11]

Added an immutable, broker-neutral final-veto risk boundary. It sizes only from
explicit monetary loss budget and validated stop distance, then applies
operator-configured loss, portfolio, notional, gearing, margin, concentration,
correlation, drawdown and kill-switch constraints. Unset mandatory limits and
missing account, contract, margin, currency or FX evidence block approval rather
than becoming permissive defaults. Lot rounding is downward-only and all caps
remain auditable. Current M14 geometry has no validated stop, so it still yields
no size. No runtime integration, broker order, execution, optimization or M16
work was added. See
[M15 Risk & Exposure Engine](../research/M15_RISK_EXPOSURE_ENGINE.md).
The full safe suite passes 404 tests and 39/39 protected artifacts are unchanged.

Next milestone: M16 — StrategyTarget [NOT STARTED].

## M12 — Instrument Selection & Suitability Learning [COMPLETE 2026-09-09]

Added canonical instrument suitability contracts using the existing registry and
M11 evidence. Hard eligibility cannot be averaged away; research and execution
suitability remain distinct. Data grade, horizon support, execution metadata,
assumed/observed cost burden, unknown liquidity, feature evidence, stability,
regime coverage and governance blockers are reported independently. Discovered
instruments remain candidate/research and no portfolio or opportunity ranking is
performed. The suite passes 307 tests and all 39 immutable research artifacts
remain unchanged. See [M12 Instrument Suitability](../research/M12_INSTRUMENT_SUITABILITY.md).

## M12A — IG Discovery, Authentication & Canonical Market Mapping [COMPLETE 2026-09-10]

Added a read-only IG adapter for explicit DEMO/LIVE configuration, authentication
and session establishment, account discovery, market search, market detail
normalization and canonical EPIC mapping. Product variants remain distinct and
credentials/tokens remain in memory only. Automated local tests pass. The
operator separately verified Demo authentication, enabled preferred CFD account
normalization, distinct Brent product search and market-detail normalization,
including preservation of unavailable metadata. The coding workspace did not
access the operator account. No dealing, historical ingestion or runtime
integration is enabled. See [IG M12A discovery](../integrations/IG_M12A_DISCOVERY.md).

## M12B — IG Historical Data Ingestion & Validation [COMPLETE 2026-09-10]

Added a local read-only candidate for IG `/prices/{epic}` v3 history. It maps
only documented resolutions, preserves bid/ask/last OHLC, produces versioned
derived-mid M8 canonical completed bars, normalizes UTC timestamps, follows
bounded pagination, and exposes gaps, duplicates, truncation, provenance,
research data grade and factual suitability metadata. No persistence, scoring,
execution, opportunity ranking or HR11 evaluation changed. Operator validation
of daily, hourly and 5-minute Demo history is complete. See
[IG M12B historical data](../integrations/IG_M12B_HISTORICAL_DATA.md).
The first external probe found that the path correctly retained `/gateway/deal`
but the shared adapter sent `Accept-Version` instead of IG's documented
`Version` header, making the v3-only prices route fall back to version 1 and
return HTML 404. The shared header and gateway anchoring are corrected. External
retrieval then returned DAY 26/1, HOUR 39/6 and MINUTE_5 457/70
accepted/excluded bars. External diagnostics proved the 70 5-minute exclusions
were structurally valid records outside the requested range. Range exclusions
are now counted independently from malformed/incomplete rows and do not cause
`PARTIAL_MALFORMED`; the requested series remains bounded and market-calendar
gap completeness remains unclaimed. The full safe suite passes 363 tests and all
39 protected artifacts are unchanged. Operator external IG Demo validation
passed DAY, HOUR and MINUTE_5 retrieval. The final 5-minute result contained 457
derived-mid `RESEARCH_DATA` bars, zero malformed/incomplete/duplicate rows, 70
range exclusions, two pages and no truncation. Its requested-range completeness
passed while 24 gaps remain unclassified without an EPIC-specific calendar.
This makes IG Demo a viable candidate for later HR11 validation but does not
prove long-horizon depth or authorize an HR11 rerun. The safe-suite `.env`
isolation added through `ai_config.py` is configuration plumbing only; no AI,
scoring, execution or runtime trading behavior changed.

Next milestone: M13 — Opportunity Ranking [COMPLETE].

## M13 — Opportunity Ranking [COMPLETE 2026-09-11]

Added a typed, deterministic `opportunity-ranking-v1` research layer over M3,
M9–M12 and factual M12A/M12B inputs. Hard eligibility precedes a transparent,
configurable comparative score; negative/insufficient evidence, divergence
conflict, fallback, uncertainty, unknown liquidity, data grade and execution
unsuitability remain explicit. Top-N is an audit-preserving view. The score is
not probability, expected return or trade confidence. No persistence, runtime
integration, optimization, TradePolicy, sizing, portfolio allocation or broker
execution was added. The safe suite passes 375 tests and 39/39 protected
artifacts remain unchanged. See
[M13 Opportunity Ranking](../research/M13_OPPORTUNITY_RANKING.md).

Older roadmap references to future IG discovery and historical ingestion are
superseded by completed M12A and M12B. Unfinished IG streaming, account/position
state beyond read-only discovery, Demo execution and reconciliation remain
future work and are not claimed or removed.

Next milestone: M14 — TradePolicy [COMPLETE].

## M14 — TradePolicy [COMPLETE 2026-09-11]

Added a typed, deterministic `trade-policy-v1` research-planning boundary. It
reuses existing policy contracts and implements only HR11-supported causal
next-observed-bar entry plus canonical horizon time-exit semantics, alongside a
non-actionable audit family. Stops remain explicitly unresolved because no
validated causal distance exists; targets are none, trailing unsupported and
reversal is exit-first with separate review. Risk requests stay unset and
unapproved. No TradeIntent, sizing, margin/portfolio risk, persistence, runtime
connection, broker call or optimization was added. The safe suite passes 387
tests and 39/39 protected artifacts remain unchanged. See
[M14 TradePolicy](../research/M14_TRADE_POLICY.md).

Next milestone: M15 — Risk & Exposure Engine [NOT STARTED].

## M11 — Contextual Feature Effectiveness Learning [COMPLETE 2026-09-09]

Added a causal, research-only effectiveness learner with typed feature outcomes
and estimates partitioned by feature, instrument, horizon and regime. It excludes
immature outcomes, supports configured minimum evidence, hierarchical fallback,
prior shrinkage, optional recency weighting, explicit uncertainty and retained
negative evidence. Divergence states are evaluable without assuming predictive
value. Canonical turnover-cost and daily/intraday horizon semantics remain
explicit. No learned effectiveness is wired into production decisions. The suite
passes 301 tests and all 39 immutable research artifacts remain unchanged. See
[M11 Contextual Effectiveness](../research/M11_CONTEXTUAL_EFFECTIVENESS.md).

Next milestone: M12 — Instrument Selection & Suitability Learning [NOT STARTED].

## M10 — Divergence & Disagreement Feature Implementation [COMPLETE 2026-09-09]

Added versioned, unweighted `divergence-v1` summaries for causal signal
evidence. The feature family preserves active, positive, negative, neutral and
unavailable counts; directional balance; disagreement; agreement; dominance;
intensity; dispersion; coverage; pair/group identity and provenance. Explicit
states distinguish low evidence from balanced conflict and directional
dominance with residual conflict. Future inputs are excluded by availability
time, and optional regime metadata remains descriptive. No price-pivot hindsight
feature, learned weight, profitability optimization or runtime integration was
introduced. The suite passes 296 tests and all 39 immutable research artifacts
remain unchanged. See [M10 Divergence Features](../research/M10_DIVERGENCE_FEATURES.md).

Next milestone: M11 — Contextual Feature Effectiveness Learning [NOT STARTED].

## M9 — Canonical Regime Engine & Versioning [COMPLETE 2026-09-09]

Added a typed, versioned `MarketRegime` contract and registry while preserving
exact daily `regime-v1` and HR11 intraday regime semantics as reference/legacy
models. A parameterized multidimensional candidate supports explicit trend and
volatility thresholds plus optional liquidity and macro dimensions, with
`UNKNOWN`/`UNAVAILABLE` states for missing inputs. Future-observation mutation
invariance and legacy parity are tested. Candidate output remains disconnected
from scoring, ranking, risk, GUI, Railway and broker paths. The suite passes 291
tests and all 39 immutable research artifacts remain unchanged. See
[M9 Regime Versioning](../research/M9_REGIME_VERSIONING.md).

Next milestone: M10 — Divergence & Disagreement Feature Implementation [NOT STARTED].

## M8 — Preserve & Migrate HR11 Causal Core [COMPLETE 2026-09-09]

Preserved the HR11 causal infrastructure behind canonical `domain.market_data`
interfaces for sessions, completed-bar aggregation, non-colliding horizons,
availability-time cross-asset alignment and position-transition costs. Backward
compatibility with the existing `intraday_*` modules and HR11 tests remains.
Explicit regression coverage proves session boundaries, timezone handling,
future-mutation invariance, missing-data propagation, horizon identity and
turnover/reversal semantics. The suite passes 286 tests and all 39 immutable
research artifacts remain unchanged. No real-data HR11 rerun or strategy
promotion occurred. See [M8 HR11 Causal Core](../research/M8_HR11_CAUSAL_CORE.md).

Next milestone: M9 — Canonical Regime Engine & Versioning [NOT STARTED].

## M7 — Early Railway Foundation Validation [COMPLETE 2026-09-09]

Operator-observed Railway validation passed for the Web service, Worker
heartbeat/recovery and real PostgreSQL persistence. The Web health endpoint
confirmed `mode=RESEARCH`, `live_execution=false` and configured PostgreSQL;
write/verify validation covered source policy, evidence, clustered event and
audit records, UTC timestamps, rollback and persistence across redeployment.
Local automated validation passed 281 tests with 39/39 immutable research
artifacts unchanged. External deployment evidence was manually supplied by the
operator; it was not accessed directly by the coding workspace. No deliberate
production outage test was performed and M7 did not activate trading behavior.
See [M7 Railway Foundation](../research/M7_RAILWAY_FOUNDATION.md).

Next milestone: M8 — Preserve & Migrate HR11 Causal Core [NOT STARTED].

## M6 — Persistence Abstraction Layer [COMPLETE 2026-09-09]

Added the domain-oriented `StorageRepository` boundary with an SQLite adapter
delegating existing `MarketIntelligenceStore` behavior and a PostgreSQL adapter
activated only by `DATABASE_URL`. Added one additive clustered-event migration;
source policies, evidence, audits and clustered events have contract coverage.
No live PostgreSQL instance was available, so integration remains unvalidated.
The safe suite passes 274 tests and all 39 protected artifacts remain unchanged.
Next milestone: M7 — Early Railway Foundation Validation [NOT STARTED].

## M5 — Event Provenance & Configurable Clustering Engine [COMPLETE 2026-09-09]

Added an isolated deterministic Tier-2 event clusterer with versioned research
policies, token-Jaccard similarity, entity overlap, bounded time windows,
stable event IDs and causal snapshots. Original EvidenceRecords and Tier-1
exact deduplication remain unchanged. No persistence schema or runtime scoring
path changed. The safe suite passes 268 tests and all 39 protected artifacts
remain unchanged.
Next milestone: M6 — Persistence Abstraction Layer [NOT STARTED].

## M4 — Canonical Source Registry Promotion [COMPLETE 2026-09-09]

Promoted the existing OI4 source registry through an additive canonical facade.
The 16 built-in policies, custom registration, enable/disable state, manual
weights, audit behavior and SQLite restart persistence are preserved. Learned
reliability, collectors and event clustering remain disconnected. The safe suite
passes 259 tests and all 39 protected artifacts remain unchanged.
Next milestone: M5 — Event Provenance & Configurable Clustering Engine [NOT STARTED].

## M3 — Instrument Registry Reconciliation [COMPLETE 2026-09-09]

Added the broker-neutral canonical instrument registry and mapping document
while preserving legacy aliases, six operational equities and all nine enabled
HR11 identities. Unresolved discovery and execution mappings remain explicit.
The safe suite passes 254 tests and all 39 protected artifacts remain unchanged.
Next milestone: M4 — Canonical Source Registry Promotion [NOT STARTED].

Only one milestone is ACTIVE. Advancement requires tests, docs and a commit.

## M0 — Baseline Freeze & Verification [COMPLETE 2026-09-09]

Preparation commit `374fbae8d177b5e6da33382bcd72b2cd0a30cfed` recorded the
approved architecture and roadmap on `master`. The safe suite passed 234 tests
with Python 3.12.2 in `.venv-m0`; all 39 protected HR11 artifacts matched their
recorded SHA-256 hashes. No trading or research computation changed.
M1 completed 2026-09-09 as an additive contracts-only milestone. M2 completed
2026-09-09 as a versioned registry and parity-only milestone. Next milestone:
M3 — Instrument Registry Reconciliation [NOT STARTED].

## M2 — Versioned Feature Registry & Semantic Parity Testing [COMPLETE 2026-09-09]

Added isolated versioned feature definitions, legacy reference wrappers,
candidate v2 calculators, registry lookup, parity tests and a semantic drift
register. Legacy runtime paths and historical artifacts remain unchanged; the
safe suite passes 247 tests and all 39 protected hashes remain unchanged.

## M1 — Canonical Domain Contracts [COMPLETE 2026-09-09]

Added immutable, timezone-aware, serializable domain contracts under
`domain/contracts/` with focused invariant tests. The complete safe suite passes
241 tests; legacy behavior and historical artifacts remain unchanged.

## OI4 — Market-intelligence UI redesign [PAUSED 2026-09-09; not active]
- Add a configurable, auditable market-intelligence layer on top of existing evidence,
  source-catalog and research boundaries.
- Redesign the UI around three tabs: Market AI/News, Technical Intelligence and
  Portfolio/Trade Summary, with a persistent hybrid pinned + AI-dynamic ticker.
- Implement Efficient Group / Dawie Roodt ingestion and a safe PDF analysis pipeline
  with hash-based deduplication.
- Produce structured market narratives, instrument candidates and inspectable
  provenance from source → theme → candidate → watchlist.
- Build a technical explainability graph from actual system state, not LLM invention.
- Prepare a broker/account abstraction for future ViewPoint integration; keep all
  execution actions manual/paper-only.
- Preserve the existing signal contract, ensemble, risk gates and research-only
  adaptive output.

Status: Phase A complete — `market_intelligence` package with schemas, SQLite store,
migrations, persisted source registry and 15 new offline tests. See
[ADR 0024](../adr/0024-market-intelligence-pipeline.md).

## ViewPoint broker integration + bounded Ollama recovery [COMPLETE 2026-09-08]
- Diagnose the local Ollama installation without broad Windows changes or model downloads.
- Establish a vendor-neutral broker-observed state boundary and ViewPoint adapter scaffold.
- Keep account, cash, positions, orders and mappings fail-closed and prepare-only.
- Preserve OST history, HR11 artifacts, OI3 separation, paper/shadow execution and `live_execution:false`.

Status: local Ollama (`llama3`) verified producing structured, attributed sentiment
output through `SentimentProviders` and the dashboard news feed. CPU-only mode is
configurable via `OLLAMA_LOCAL_OPTIONS` for GPUs with incompatible toolchains.
ViewPoint transport and authenticated broker state remain unverified pending a
sanitized user capture; the prepare-only scaffold and safety tests pass.
Closed to activate OI4 under the single-active-milestone rule.

## HR11 — Short-Term Multi-Instrument Research Layer [COMPLETE 2026-09-06]

All stages HR11.0–HR11.14 are complete. 175 safe tests pass, including 61 new
HR11 tests; 39 protected daily hashes are unchanged. The default report contains
180 insufficient-evidence cells and no fabricated intraday observations.
See `docs/reports/HR11_REPORT.md`. No successor milestone is active.

## OI3 — Restore connected market and sentiment dashboard [DEFERRED/BLOCKED 2026-09-08]
- Reuse Yahoo and MacroSentimentScanner for auto-refreshing, cached public feeds.
- Render dated price charts, retained headlines, AI summaries and macro impacts.
- Expose source failures, last-success time, delayed data and keyword fallback.
- Validate browser behavior and provider failures; preserve research/execution safety.

Progress: charts, public quotes and retained news restored; 114 offline tests and
real/fixture browser checks pass. Local/cloud Ollama and Kimi routing is
implemented. Owner-authorized Windows verification from `1fc8994` confirmed
Moneyweb RSS/SENS and three Yahoo discovery symbols; 196 safe tests pass.
Local Ollama (`llama3`) is now verified producing structured AI summaries and
provider-model attribution through the dashboard; CPU-only execution is supported
via `OLLAMA_LOCAL_OPTIONS`. Cloud/Kimi/NewsAPI keys remain MISSING. AI-backed
discovery and additional approved source ingestion remain unresolved. See
`docs/reports/OI3_WINDOWS_PROVIDER_VERIFICATION.md` for the evidence and exact
prerequisites. No successor milestone is activated.

## HR9 — Causal adaptive technical ensemble [COMPLETE 2026-09-04]
- Preserve the 101,536-row interrupted ensemble as the pre-HR9 baseline.
- Share one authoritative technical-signal definition across HR8 and HR9.
- Reuse HR8 reliability gates and correct signal-state turnover costs.
- Keep 1/3/5/20-session targets independent and fully explainable.
- Evaluate causality, uncertainty, costs, turnover, drawdown and temporal stability.
- Keep all adaptive output shadow-only and disconnected from Flask/production.

Acceptance evidence: 14 focused tests pass; 101,536 aligned causal decisions
have zero key, clock, sample-gate or shadow-boundary violations. Performance is
not consistently superior to legacy, so completion means a sound research
artifact—not adaptive promotion. See `docs/research/HR9_ADAPTIVE_ENSEMBLE_REPORT.md`.

Recommended next milestone: HR10 robustness and admission gates; not active.

## HR10 — Robustness and admission gates [COMPLETE 2026-09-04]
- Add horizon-aware purged/embargoed validation and leakage tests.
- Separate overlapping research outcomes from non-overlapping trade simulation.
- Predeclare cost, parameter-sensitivity, uncertainty and multiple-testing rules.
- Assign deterministic per-instrument/per-horizon shadow admission states.
- Reopen the existing simulated Flask UI for clearly labelled human review.
- Research ViewPoint/Shyft integration and define mock/paper-only provider boundaries.

Acceptance: reproducible offline artifacts, focused and regression tests, no live
broker writes, no adaptive production promotion, and explicit admission outcomes.

Evidence: 0/40 cells admitted and 40 rejected; 34 focused HR7–HR10 tests and 91
safe offline regression tests pass. The UI is unmistakably simulated, provider
writes hard-fail, and ViewPoint/Shyft API and licensing unknowns are documented.

Recommended next milestone: human UI review plus vendor clarification. Do not
implement live integration until official API, sandbox and licensing answers exist.

## OI1 — Operational UI, integration discovery and research reset [COMPLETE 2026-09-04]
- Evolve the simulated Flask page into a responsive human decision prototype.
- Define a stale/rejected-safe canonical trade-suggestion boundary.
- Research official ViewPoint/Shyft and viable alternative-provider capabilities.
- Prepare a Standard Bank contact pack and rank new non-HR9 research inputs.

Acceptance: mock UI and serialization tests, no executable rejected/stale
suggestion, paper-only providers, documented official-source evidence and a
single recommended next research milestone.

Evidence: responsive rejected-demo decision card and API; canonical stale/state
safety contract; Saxo/Shyft relationship and alternative APIs researched; 16
focused OI1/HR10 tests and 98 safe offline regression tests pass.

Recommended next milestone: build a licensed, point-in-time JSE SENS event
dataset and classifier; separately procure a small intraday Level 1/2 sample.

## UIR1 — Historical UI recovery audit [COMPLETE 2026-09-04]
- Locate the reported complete dashboard before any reconstruction.
- Inspect reachable/unreachable history, deleted paths, archives and protected worktree files.
- Map missing UI features to surviving backend capabilities and exact data states.
- Stop and report if no historical implementation can be recovered.

Acceptance: evidence-backed archaeology report with no invented UI replacement,
no broker/network execution and no modification of unrelated work.

Evidence: all reachable `app.py` versions, deleted paths, unreachable blobs,
archives and protected `generate_app.py` history were inspected. No complete
historical dashboard was found; reconstruction stopped pending original source
or screenshots. Surviving backend capabilities are mapped in the recovery report.

## OI2 — Operational intelligence dashboard and orchestration [COMPLETE 2026-09-04]
- Compose existing market, news, technical, legacy decision and research boundaries.
- Add a first-class data-state/provenance contract and exact 30-gate evidence system.
- Provide separate operational controls and responsive Flask templates/static assets.
- Keep broker handoff manual/paper-only and HR9/HR10 diagnostic-only.

Acceptance: complete traceability/inventory, graceful partial results, focused
and safe regression suites, truthful data states and no live-order route.

Evidence: HR7-backed legacy analysis, explicit component provenance, six-symbol
identity registry, exact 30-gate output, responsive dashboard, 104 passing safe
offline tests and successful local HTTP smoke checks.

## M0 — Protect and characterize baseline [COMPLETE 2026-09-03]
- Inspect Git state and secrets.
- Confirm `.env` is ignored/untracked; do not print secret values.
- Preserve all current uncommitted user work.
- Run existing tests/verification scripts that are safe/offline where possible.
- Add minimal characterization tests around `JSESignalEngine` fixed scoring if missing.
- Create a clean baseline commit named approximately `baseline: preserve pre-adaptive trading system` if safe and Git identity exists.
Acceptance: baseline behaviour reproducible; no secrets committed; working tree understood.

Evidence: `test_legacy_scoring.py` passes 3 characterization tests; the canonical two-year report contains 24 finite metric rows; `.env` is ignored and untracked.

## M1 — Evidence/provenance contracts [COMPLETE 2026-09-03]
- Add normalized evidence/source models without replacing current `NewsItem` immediately.
- Add adapters/conversion from current news/macro objects.
- Add deduplication keys and timestamps.
Acceptance: existing collectors can emit/convert to evidence records; tests pass.

Evidence: `evidence.py`, ADR 0001, and six passing focused tests.

## M2 — Source registry + reliability store [COMPLETE 2026-09-03]
- Configurable registry for existing and planned sources.
- Persistent local research store (SQLite is acceptable unless repo already has a preferred DB).
- Outcome evaluation by horizon; sample-size-aware score.
- No production weight changes.
Acceptance: synthetic/historical tests demonstrate score updates without leakage.

Evidence: `reliability_store.py`, ADR 0002, and ten passing focused tests.

## M3 — Regime engine [COMPLETE 2026-09-03]
- Implement transparent regime feature calculation and labels.
- Add versioned `MarketRegime` output.
- Backtest regime classification stability.
Acceptance: no future leakage; deterministic tests; docs updated.

Evidence: `regime_engine.py`, `regime_backtest.py`, `regime_stability_report.json`, and fourteen passing focused tests.

## M4 — Sector/instrument profiles [COMPLETE 2026-09-03]
- Replace scattered ticker-specific macro logic with configurable profiles, while preserving legacy behaviour as benchmark.
- Profiles: index futures/CFDs, SSF/share CFD, banks, gold miners, PGM/diversified mining, energy/Sasol, retail/consumer, agri-linked, USD/ZAR.
Acceptance: profile selection tested; legacy mode unchanged.

Evidence: `market_profiles.py`, ADR 0003, and eighteen passing focused tests;
legacy macro coefficients and clamp are characterized for equivalence.

## M5 — Expanded indicator research layer [COMPLETE 2026-09-03]
- Add ADX/DMI, ATR, MACD, Bollinger/z-score, relative strength and volume/liquidity features where data supports them.
- Add intraday VWAP/opening range only behind an intraday-data capability flag.
- Do not pretend daily Yahoo data is intraday derivatives data.
Acceptance: unit tests + no-lookahead calculations + feature availability metadata.

Evidence: `research_indicators.py`, ADR 0004, and twenty-three passing focused
tests. Intraday and volume-dependent values are capability-gated.

## M6 — Adaptive fusion in SHADOW mode [COMPLETE 2026-09-03]
- Create adaptive fusion beside legacy fixed score.
- Weight by regime, sector/instrument profile, source reliability and feature evidence.
- Every decision logs factor contributions and legacy-vs-adaptive comparison.
Acceptance: production/default signal remains legacy unless explicit config selects shadow output for research.

Evidence: `adaptive_fusion.py`, ADR 0005, and twenty-eight passing focused tests.
Every engine decision logs a shadow comparison while returning the legacy action.

## M7 — Backtest/evaluation upgrade [COMPLETE 2026-09-03]
- Multi-horizon walk-forward.
- Costs, slippage/spread assumptions, turnover, drawdown, MFE/MAE where data allows.
- Segment results by bull/bear/range, volatility, sector and instrument profile.
- Reliability calibration/ablation tests: technical-only vs macro-only vs source-only vs fused.
Acceptance: report can justify or reject adaptive weighting.

Evidence: `evaluation.py`, ADR 0006, thirty-three passing focused tests, and
`adaptive_evaluation_report.*` with 760 daily observations per ticker. Missing
historical context and unstable cross-ticker results support continued shadow,
not adaptive promotion.

## M8 — Public specialist/community source expansion [COMPLETE 2026-09-03]
Verify before integration; do not assume availability:
- TradingView SA/JSE ideas;
- IG South Africa public analysis/client sentiment where permitted;
- Moneyweb/BusinessLIVE/Reuters local markets;
- Standard Bank public commentary;
- MyBroadband JSE/stock-watch discussions;
- Reddit local finance/JSE communities;
- public X/Twitter via approved API/provider;
- legitimate public Telegram/Discord channels;
- BlackStone Futures public resources if active and accessible.
Normalize as low/medium-authority evidence and learn reliability. No Facebook private-group credential scraping.
Acceptance: access method documented, rate-limited, provenance preserved, source can be disabled independently.

Evidence: `source_catalog.py`, ADR 0007, current access verification in
`DATA_SOURCES.md`, and thirty-eight passing focused tests. Only Moneyweb RSS and
Moneyweb-hosted SENS are enabled; restricted/unverified routes remain disabled.

## M9 — Multi-agent integration [COMPLETE 2026-09-03]
- Feed adaptive evidence/regime explanations into existing Bull/Bear/General researchers.
- Preserve Risk/Manager governance.
- Add disagreement telemetry: when legacy, adaptive, bull and bear strongly disagree.
Acceptance: existing manager/executor interfaces remain stable or have a documented adapter.

Evidence: `agent_intelligence.py`, ADR 0008, and forty-one passing focused tests,
including context-on/context-off governance equivalence and paper-mode checks.

## M10 — Promotion gate [COMPLETE 2026-09-03]
Do NOT automatically promote adaptive trading.
Produce a final evidence report recommending one of:
1. reject adaptive changes;
2. continue shadow collection;
3. enable adaptive recommendations/paper trading;
4. propose a separate live-trading safety milestone for explicit user approval.

Decision: **continue shadow collection**. See `FUSION_COMPLETION_REPORT.md`.
Historical macro/source alignment is unavailable and only 9 of 24 sufficient-
sample adaptive overall rows had positive mean net return.

## Laptop handoff checkpoint — 2026-09-06

HR11 is committed/pushed; HR12 is NOT STARTED (no files or commits found).
OI3 remains deferred with the checklist in CURRENT_MILESTONE.md. No research
work is activated by environment preparation. See `docs/LAPTOP_HANDOFF.md` for
bootstrap, diagnostics, local-data transfer and exact continuation instructions.
## Market Intelligence Foundation — ACTIVE 2026-09-16

Extends the existing OI4 foundation with Efficient Group discovery, bounded
document/PDF processing, structured fact-versus-inference analysis, explicit
provenance, provider-aware analysis caching, hybrid anti-churn investigation
watchlists and a research-priority bridge. Focused and broad protected-boundary
tests pass. External source verification and UI work remain deferred. No signal,
adaptive, risk, broker, IG, ViewPoint or production UI behaviour changed.
