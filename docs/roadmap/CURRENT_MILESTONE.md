# Current Milestone

## M19 — Canonical Opportunity / TradeIntent API [COMPLETE 2026-09-11]

Added a storage-neutral canonical opportunity application service, explicit
serializers, non-executable `trade-intent-preview-v1`, and read-only versioned
Flask routes for opportunity list/detail, policy, risk and intent state. Top-N
retains M13 rank and evidence. Ranking score is labelled comparative research,
never probability. Unresolved M14 stops and null M15 sizes remain visible and
produce an unresolved 409 intent response.

The default canonical source is empty until supplied real upstream records.
Legacy routes remain unchanged. No broker-native order fields, PaperBroker/IG
submission, position mutation, runtime switch, GUI work, or M20 implementation
was added. See `docs/api/M19_CANONICAL_OPPORTUNITY_API.md`.

The full safe suite passes 450 tests and all 39 protected research artifacts
remain byte-identical.

Next milestone: M20 — Early Read-Only Top-5 GUI [NOT STARTED].

## M18 — Canonical Metrics [COMPLETE 2026-09-11]

Added `canonical-metrics-v1` with expanded MetricContext, immutable MetricResult,
a definition registry, explicit gross/net expectancy, resolved-outcome hit rate,
payoff metrics, canonical Sharpe/Sortino, drawdown/duration, volatility,
position-state turnover, cost decomposition, profit factor, Calmar, exposure and
separately versioned weighted expectancy. Invalid/unavailable metrics never
become zero and sample depth remains visible.

HR10's `mean / sample_std * sqrt(n)` remains `LEGACY_TSTAT_LIKE_V1`; frozen
research was not rewritten. M16 criteria preserve metric versions and M17
results can carry canonical results append-only. No thresholds, optimization,
runtime, ranking, policy, risk, broker, execution, or M19 work was added. See
`docs/research/M18_CANONICAL_METRICS.md`.

The full safe suite passes 442 tests and all 39 protected research artifacts
remain byte-identical.

Next milestone: M19 — Canonical Opportunity / TradeIntent API [NOT STARTED].

## M17 — Experiment Registry [COMPLETE 2026-09-11]

Added immutable definition, data-boundary, factorial-design, run, result and
decision contracts plus an append-only repository protocol/reference
implementation. Single-treatment attribution is the default; factorial work
must be explicit. Confirmatory preregistration, exact M16 target versions,
MetricContext, causal OOS separation, negative evidence, deterministic safe
configuration hashes and explicit baseline succession are preserved.

HR7–HR11 remain legacy/pre-registry references and were not rewritten. Durable
SQLite/PostgreSQL adapters are deferred together pending an additive canonical
migration. No optimization, auto-promotion, baseline mutation, runtime, broker,
execution, or M18 work was added. See
`docs/research/M17_EXPERIMENT_REGISTRY.md`.

The full safe suite passes 429 tests and all 39 protected research artifacts
remain byte-identical.

Next milestone: M18 — Canonical Metrics [NOT STARTED].

## M16 — StrategyTarget [COMPLETE 2026-09-11]

Added the immutable `strategy-target-v1` declaration and contextual criterion
contracts. Hard and soft requirements remain independent, unset thresholds are
`NOT_CONFIGURED`, and exact metric context plus IS/validation/OOS/walk-forward/
forward-Demo/live stage identity is required. HR10's historical sample-scaled
mean/std statistic is preserved as `LEGACY_TSTAT_LIKE_V1`; canonical annualized
Sharpe requires explicit periodicity, annualization, overlap, return, cost and
risk-free-rate context.

Target assessment produces only research-review status and can never authorize
promotion. No thresholds, candidate pass claims, optimization, strategy,
ranking, TradePolicy, RiskEngine, runtime, broker, execution, or M17 behavior
was introduced. See `docs/research/M16_STRATEGY_TARGET.md`.

The full safe suite passes 419 tests and all 39 protected research artifacts
remain byte-identical.

Next milestone: M17 — Experiment Registry [NOT STARTED].

## M15 — Risk & Exposure Engine [COMPLETE 2026-09-11]

Added the broker-neutral `risk-exposure-v1` final-veto planning boundary over
M14 `TradePolicy`. Typed operator limits, point-in-time portfolio state,
instrument contract metadata, explicit FX conversion, immutable risk evaluation
and non-executable approved-risk records preserve monetary stopped-loss sizing,
downward-only lot rounding, margin/gearing constraints, instrument/sector/factual
correlation exposure, and daily-loss/drawdown/kill-switch controls.

No production limits were invented: every mandatory absent control is
`NOT_CONFIGURED`. Missing stop, equity, margin, contract, currency or required FX
evidence produces no size. Current M14 policies therefore remain unresolved and
cannot become execution-ready. Legacy hard-coded personality sizing was not
adopted. No runtime integration, broker request, order creation, portfolio
mutation, optimization, live trading, or M16 implementation was added. See
`docs/research/M15_RISK_EXPOSURE_ENGINE.md`.

The full safe suite passes 404 tests and all 39 protected research artifacts
remain byte-identical.

Next milestone: M16 — StrategyTarget [NOT STARTED].

## M12 — Instrument Selection & Suitability Learning [COMPLETE 2026-09-09]

Added a canonical suitability evaluator around the existing instrument registry
and M11 effectiveness records. Hard eligibility is separated from soft
suitability; manual blocks, permissions, horizon support, data requirements and
execution metadata remain decisive. Research suitability is distinct from
execution suitability. Data grade, assumed versus observed costs, unknown
liquidity, feature evidence, stability and regime coverage remain separate
states. Discovered instruments remain candidate/research only.

The safe suite passed 307 tests and all 39 immutable research artifacts remain
unchanged. No ranking, portfolio selection, strategy weighting, dashboard,
Railway or broker integration was added. See
`docs/research/M12_INSTRUMENT_SUITABILITY.md`.

## M12A — IG Discovery, Authentication & Canonical Market Mapping [COMPLETE 2026-09-10]

Read-only IG discovery infrastructure is implemented with explicit DEMO/LIVE
configuration, in-memory authentication, account discovery, market search,
market detail normalization and distinct EPIC/product mappings. Automated local
tests pass, and the operator separately verified all four read-only commands
against IG Demo. No IG dealing or runtime integration is enabled. See
`docs/integrations/IG_M12A_DISCOVERY.md`.

Authentication diagnostics now make a read-only session attempt and retain
sanitized HTTP status, IG error code, conservative error category and safe
operator message. Credential, account, token, header, cookie and request-body
values remain excluded. Two-factor requirements are reported but not automated.
The safe suite passes 332 tests and all 39 immutable research artifacts
remain unchanged.

The LIVE validation error
`validation.pattern.invalid.authenticationRequest.identifier` established that
the configured value violated the v2 `/session` identifier pattern. M12A now
uses explicit `IG_IDENTIFIER` semantics, validates IG's documented 1-30
letter/digit/hyphen/underscore contract locally, retains `IG_USERNAME` only as
an alias, and keeps `IG_ACCOUNT_ID` distinct. At M12A closure no IG execution
or M12B work was active.

The subsequent DEMO HTTP 200 exposed a response-mapping defect: `/session` v2
returns `CST` and `X-SECURITY-TOKEN` in case-insensitive HTTP response headers,
while the adapter had discarded headers and searched the JSON body. The adapter
now requires and retains both tokens only in memory and does not mix v3 OAuth
tokens into the v2 contract.

Operator-provided external evidence confirms Demo authentication, enabled
preferred CFD account discovery, distinct Brent EPIC/product-variant search and
tradeable Brent market-detail normalization. Null currency, margin factor and
trading hours remained explicit. The coding workspace did not access the
operator account, and no account ID or secret is recorded.

Next milestone: M12B — IG Historical Data Ingestion & Validation [COMPLETE].

## M12B — IG Historical Data Ingestion & Validation [COMPLETE 2026-09-10]

The local read-only candidate retrieves IG `/prices/{epic}` v3 history with an
explicit documented resolution map, bounded pagination, canonical completed-bar
normalization, preserved bid/ask/last OHLC components, versioned derived mids,
UTC timestamps, provenance, duplicate/discontinuity/truncation diagnostics,
research-only data grade and factual suitability evidence. No data is persisted,
no scoring or runtime trading changes, and no HR11 rerun occurred. See
`docs/integrations/IG_M12B_HISTORICAL_DATA.md`.

The initial external history probe exposed an incorrect `Accept-Version` header.
The URL path already retained `/gateway/deal`; the gateway defaulted the v3-only
prices route to version 1 and returned HTML 404. The shared boundary now uses
IG's documented `Version` header, safely anchors all endpoint paths beneath the
gateway, and provides query-free route diagnostics.

The operator subsequently retrieved non-truncated DAY (26 accepted/1 excluded),
HOUR (39/6) and MINUTE_5 (457/70, two pages) history. External inspection proved
the 70 sampled 5-minute exclusions were structurally complete and solely outside
the requested range. The adapter now counts valid extra response records as
`excluded_outside_range`, not malformed, while continuing to filter them.
Malformed, incomplete, range and duplicate counters remain distinct; range-only
exclusions do not make completeness `PARTIAL_MALFORMED`. Completeness is scoped
to API response processing, not market-calendar coverage, and gap semantics stay
`UNCLASSIFIED_INTERVAL_DISCONTINUITIES`.

The full safe suite passes 363 tests; all 39 immutable research artifacts remain
unchanged.

The operator's final external IG Demo validation passed DAY, HOUR and MINUTE_5
history. The 5-minute result contained 457 derived-mid research bars, zero
malformed/incomplete/duplicate rows, 70 valid out-of-range exclusions, two pages
and no truncation. It reported `COMPLETE_REQUESTED_RANGE`; 24 discontinuities
remain `UNCLASSIFIED_INTERVAL_DISCONTINUITIES` because no EPIC-specific trading
calendar exists. This proves IG Demo is a viable candidate source for later HR11
validation, not full long-horizon depth or closure of the HR11 data gap. No HR11
rerun occurred.

The M12B `ai_config.py` change only prevents `.env` loading when the explicit
safe-suite flag is set. It changes no AI decision, scoring, signal, execution or
runtime trading behavior. The coding workspace did not access the operator
account; Demo data remains `RESEARCH_DATA`, historical allowance and timezone
limitations remain, and execution stays disabled.

Next milestone: M13 — Opportunity Ranking [COMPLETE].

## M13 — Opportunity Ranking [COMPLETE 2026-09-11]

Added an additive `opportunity-ranking-v1` research boundary consuming canonical
M3 identity, M9 regime, M10 divergence, M11 effectiveness, M12 suitability and
factual M12A/M12B broker/data metadata. M12 hard eligibility is applied before
scoring; blocked, unsupported and insufficient candidates remain auditable but
unranked. Research-suitable execution-unsuitable candidates may remain labelled
research opportunities.

The transparent configurable 0–100 score combines suitability, effectiveness
support, evidence depth, stability, causal directional strength, exact contextual
regime support, unflattened divergence state and data quality, with separate
uncertainty and known-cost penalties. It is explicitly a comparative research
ranking score—not profit probability, trade confidence or expected return.
Deterministic reasons, blockers, uncertainty and provenance are retained; top-N
is a view and does not discard lower-ranked or negative evidence.

No persistence, Flask/runtime integration, strategy change, TradePolicy,
position sizing, portfolio optimization or broker execution was added. The full
safe suite passes 375 tests and all 39 protected artifacts remain unchanged. See
`docs/research/M13_OPPORTUNITY_RANKING.md`.

Next milestone: M14 — TradePolicy [COMPLETE].

## M14 — TradePolicy [COMPLETE 2026-09-11]

Added a canonical, non-executable `trade-policy-v1` planning boundary over M13
`ResearchOpportunity`. It reuses the existing versioned policy enums and
`CandidateTradePolicy` snapshot, adding explicit unresolved enum states rather
than forcing numeric geometry. The only evidence-supported directional family
preserves HR11's causal next-observed-bar-open reference and canonical
horizon-end exit; audit-only records cover blocked, insufficient and WATCH
opportunities.

No validated causal stop-distance implementation exists, so stop price/distance
remain unresolved, target is optional/none, trailing is unsupported and even a
directional plan is not ready for risk review. Invalidation remains distinct
from stop loss. Reversal requires exit and separate new-policy review; it never
auto-flips. Requested risk fraction, loss budget and gearing remain unset and
unapproved.

No TradeIntent, final sizing, margin/risk approval, portfolio calculation,
persistence, runtime integration, paper preview, broker order or optimization
was added. The full safe suite passes 387 tests and all 39 protected artifacts
remain unchanged. See `docs/research/M14_TRADE_POLICY.md`.

Next milestone: M15 — Risk & Exposure Engine [NOT STARTED].

## M11 — Contextual Feature Effectiveness Learning [COMPLETE 2026-09-09]

Added canonical research contracts for matured feature outcomes and contextual
effectiveness estimates. The learner preserves causal availability/maturity
boundaries, explicit gross/net outcomes, configurable minimum evidence,
hierarchical fallback, prior shrinkage, optional recency weighting and negative
evidence. It supports technical, divergence and causally supplied cross-asset
features without fabricating unavailable inputs. Daily and intraday horizons
remain distinct.

No learned output is connected to scoring, ranking, risk, GUI, Railway or broker
runtime. The safe suite passed 301 tests and all 39 immutable research artifacts
remain unchanged. See `docs/research/M11_CONTEXTUAL_EFFECTIVENESS.md`.

Next milestone: M12 — Instrument Selection & Suitability Learning [NOT STARTED].

## M10 — Divergence & Disagreement Feature Implementation [COMPLETE 2026-09-09]

Added the research-only `divergence-v1` feature family. It measures positive,
negative, neutral and unavailable evidence separately, distinguishing low
evidence, high agreement, high disagreement and directional dominance with
residual conflict. Pair/group summaries retain instrument, horizon, availability,
feature-version and optional regime context.

Future inputs are excluded from earlier summaries; no learned weights, hindsight
pivots or synthetic macro/news history are used. The feature family is not
connected to scoring, ranking, risk, GUI, Railway or broker paths. The safe suite
passed 296 tests and all 39 immutable research artifacts remain unchanged. See
`docs/research/M10_DIVERGENCE_FEATURES.md`.

Next milestone: M11 — Contextual Feature Effectiveness Learning [NOT STARTED].

## M9 — Canonical Regime Engine & Versioning [COMPLETE 2026-09-09]

Added `domain.features.regime` with a typed `MarketRegime` contract, explicit
availability states, versioned regime definitions and a registry. Existing
daily `regime-v1` and HR11 intraday regime semantics remain reference/legacy
implementations with parity coverage. A parameterized candidate regime remains
research-only; thresholds are supplied as configuration and missing macro or
liquidity inputs remain explicit unknown/unavailable states.

The full safe suite passed 291 tests and all 39 immutable research artifacts
remain unchanged. Causal tests prove future observations cannot alter an earlier
classification. No production runtime, scoring, ranking, GUI, Railway, broker
or historical research behavior changed. See
`docs/research/M9_REGIME_VERSIONING.md`.

Next milestone: M10 — Divergence & Disagreement Feature Implementation [NOT STARTED].

## M8 — Preserve & Migrate HR11 Causal Core [COMPLETE 2026-09-09]

Added canonical `domain.market_data` facades for the preserved HR11 session,
completed-bar aggregation, horizon, cross-asset and turnover-cost contracts.
Intraday duration and daily session horizons have distinct identities.
Availability-time joins, missing-data states, session boundaries, break rules,
future-mutation invariance and position-transition costs remain unchanged.

HR11 scripts and legacy tests remain compatible. Experimental signals, profiles
and paper router were left unchanged and disconnected from production paths.
The safe suite passed 286 tests; all 39 immutable research artifacts remain
unchanged. No HR11 real-data rerun occurred and the known 180 insufficient-
evidence cells were not reinterpreted. See
`docs/research/M8_HR11_CAUSAL_CORE.md`.

Next milestone: M9 — Canonical Regime Engine & Versioning [NOT STARTED].

## M7 — Early Railway Foundation Validation [COMPLETE 2026-09-09]

Railway Web and Worker services were externally validated by the operator.
The Web service returned HTTP 200 from `/health` with `mode=RESEARCH`,
`live_execution=false` and `database=CONFIGURED_POSTGRES`; Gunicorn bound the
Railway port successfully. The Worker emitted heartbeats and recovered after
redeployment. Real Railway PostgreSQL write/verify validation passed for source
policy, evidence, clustered event and audit records, including UTC round-trip,
transaction rollback and persistence across a fresh Web container.

The local safe suite passed 281 tests and all 39 immutable research artifacts
remained unchanged. Local tests cover fail-closed PostgreSQL configuration; no
deliberate production outage test was performed. Supplied Railway logs exposed
no secrets, and no trading behavior was activated. The distinction between
local automated checks and operator-observed external evidence is recorded in
`docs/research/M7_RAILWAY_FOUNDATION.md`.

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
stable event IDs and causal `as_of` snapshots. Original EvidenceRecords and
Tier-1 exact deduplication remain unchanged. No persistence schema or runtime
scoring path changed. The safe suite passes 268 tests and all 39 protected
artifacts remain unchanged.

Next milestone: M6 — Persistence Abstraction Layer [NOT STARTED].

## M4 — Canonical Source Registry Promotion [COMPLETE 2026-09-09]

Promoted the existing OI4 source registry through an additive canonical facade.
The 16 built-in policies, custom registration, enable/disable state, manual
weights, audit behavior and SQLite restart persistence are preserved. Learned
reliability remains a placeholder; collectors and evidence deduplication are
unchanged. The safe suite passes 259 tests and all 39 protected artifacts match.

Next milestone: M5 — Event Provenance & Configurable Clustering Engine [NOT STARTED].

## M3 — Instrument Registry Reconciliation [COMPLETE 2026-09-09]

Added the broker-neutral canonical instrument registry and mapping document.
Legacy aliases, six operational equities and all nine enabled HR11 identities
remain compatible. Discovery and execution mappings remain explicit and
unresolved where unverified. The safe suite passes 254 tests; all 39 protected
artifacts remain unchanged.

Next milestone: M4 — Canonical Source Registry Promotion [NOT STARTED].

## M0 — Baseline Freeze & Verification [COMPLETE 2026-09-09]

- Preparation commit: `374fbae8d177b5e6da33382bcd72b2cd0a30cfed` on `master`.
- Safe suite: 234 passed, 0 failed, 0 skipped, 30.202 seconds, Python 3.12.2
  in `.venv-m0`, dependencies from `requirements.txt`.
- Immutable HR11 baseline: 39 expected, 39 verified, 0 mismatched, 0 missing.
- No trading/research computation, data migration, GUI or Railway behavior changed.
- Completed 2026-09-09 (Africa/Johannesburg).
- M1 completed 2026-09-09 as an additive contracts-only milestone.
- M2 completed 2026-09-09 as a versioned registry and parity-only milestone.
- Next milestone: M3 — Instrument Registry Reconciliation [NOT STARTED].

## M1 — Canonical Domain Contracts [COMPLETE 2026-09-09]

Added immutable, timezone-aware, serializable domain contracts under
`domain/contracts/`. Focused tests cover contract invariants and failure modes;
the complete safe suite passes 241 tests. Legacy behavior and historical
artifacts remain unchanged.

## M2 — Versioned Feature Registry & Semantic Parity Testing [COMPLETE 2026-09-09]

Added isolated versioned feature definitions, legacy reference wrappers,
candidate v2 calculators, registry lookup, parity tests and the semantic drift
register. Legacy runtime paths remain unchanged; all 39 protected artifacts
remain byte-for-byte verified. The safe suite passes 247 tests.

**OI4 — Market-intelligence UI redesign [PAUSED 2026-09-09; not active]**

Build a configurable market-intelligence layer and redesigned UI around three
main views: Market AI/News, Technical Intelligence, and Portfolio/Trade Summary.
Preserve the existing research, signal, ensemble and risk boundaries. No LLM or
news item may directly generate an executable trade. Broker/execution integration
remains prepare-only.

Phase A delivers the foundational `market_intelligence` package: schemas,
SQLite store with migrations, persisted source registry and additive tests.
Later phases will add Efficient Group/Dawie Roodt ingestion, PDF analysis,
Market AI structured narrative, dynamic ticker, technical explainability graph,
portfolio summary UI and ViewPoint preparation.

See [ADR 0024](../adr/0024-market-intelligence-pipeline.md).

## Dashboard recovery check - 2026-09-08

The dashboard was not listening on port 5000 at inspection; no evidence establishes
that the quote ticker terminated the previous process. Reproduced an HTTP 500
from the new sources endpoint: its module-level SQLite connection crossed request
threads. Source routes now use request-scoped connections closed at teardown.
Removed duplicate news/opportunity DOM containers and assigned the technical tab
a unique ID in the template. Existing user edits were preserved.

Validation: 29 focused feed, operational, UI, provider and legacy tests pass,
including concurrent source requests and unique DOM/navigation IDs. Browser
interaction remains unverified (Playwright is unavailable in this environment).
The first recovery process inherited sandbox network restrictions (WinError 10013);
Yahoo and Moneyweb both returned HTTP 200 outside the sandbox. Restarted the local
dashboard with network access for public-provider verification. At 16:36 SAST,
SOL intraday returned AVAILABLE (R210.62, provider bar 16:20 SAST), the JSE proxy
chart returned AVAILABLE, and news exposed 25 headlines with Moneyweb/SENS
AVAILABLE. News AI processing was still in progress; the preview was explicitly
keyword-labelled, so completed AI inference is not claimed. OI4 remains ACTIVE.

## SENS intake/cache hardening - 2026-09-08

Follow-up to the reported overload: confirmed dashboard news has one shared
in-flight refresh, a 300-second post-completion refresh interval, 100 retained
headlines and at most eight AI requests per scan. Found no proof of the original
crash. Closed two unbounded paths: SENS now streams at most 2 MiB of decompressed
response bytes, closes oversized responses and reports RESPONSE_TOO_LARGE;
non-retaining scanners keep at most 1,000 seen headlines (oldest evicted).
The SENS parser uses lazy matches and caps output at 100 items. Scanner source
intake enforces requested limits even if an adapter over-returns. Dashboard
requests remain 20 Moneyweb / 15 SENS / 8 NewsAPI items per scan.

Validation: 46 focused tests pass, including 1,000 pending polls producing one
job, repeated 1,000-item source bursts retaining at most 100, outage retention,
non-retaining dedup bounds and streamed-response early closure. Real bounded
SENS fetch returned AVAILABLE with 15 items. Restarted the dashboard to load the
fix. These checks establish bounded item counts/response size, not a long-duration
memory soak or proof of the prior crash cause. OI4 remains ACTIVE.

## Resume checkpoint - 2026-09-08 evening

OI4 remains ACTIVE and incomplete. This checkpoint saves the in-progress source
configuration/portfolio CSV UI plus dashboard recovery and SENS cache bounds.
Local SQLite runtime data is ignored and is recreated/seeded at startup. Restored
UTF-8 punctuation in dashboard assets during pre-commit review.
Tomorrow: verify browser interactions and sustained memory use under news refresh;
recheck local Ollama inference (latest running feed reported UNREACHABLE and used
keyword fallback). Source configuration is persisted but is not yet connected to
the existing dashboard collectors. The portfolio opportunities panel remains
unpopulated. Do not infer full OI4 completion or successful AI from available news.

## Previous milestone closure

**ViewPoint broker integration + bounded Ollama recovery — COMPLETE 2026-09-08**

Closed to enforce the Constitution rule of exactly one ACTIVE milestone. The
ViewPoint adapter scaffold and safety tests are in place, but no authenticated
ViewPoint payload, endpoint, selector, account, cash, position or order behavior
has been verified. Legacy OST browser code remains unchanged. Local Ollama
(0.33.2, `llama3`) is installed and verified on this laptop through the existing
`SentimentProviders` boundary; the default `llama3.2:3b` is not present. The
`OLLAMA_LOCAL_MODEL` and `OLLAMA_LOCAL_OPTIONS` settings are read from `.env`.
Cloud/Kimi keys remain MISSING and OI3 remains deferred pending those provider
verifications. HR12 is not started.

See [ADR 0022](../adr/0022-viewpoint-broker-boundary.md).

**OI3 DEFERRED/BLOCKED - Windows provider verification (2026-09-08)**

Owner-authorized OI3 verification resumed from `1fc8994`; this pass completed
available public-source checks and offline routing/discovery verification.
Moneyweb RSS and SENS succeeded here; three Yahoo discovery symbols succeeded.
Local Ollama (`llama3`) is installed, reachable and produces valid structured
output through `SentimentProviders` and the dashboard `/api/feed/news` endpoint
when CPU-only execution is enabled via `OLLAMA_LOCAL_OPTIONS={"num_gpu":0}`;
cloud/Kimi keys are MISSING. Real AI summaries for retained headlines are now
verified locally; provider failure/fallback coverage is expanded in
`test_sentiment_providers.py`. AI-backed discovery and additional permitted
commentary ingestion remain blocked until a verified feed/permission is available;
Efficient Group remains manual-only and disabled.
See [current evidence and exact blockers](../reports/OI3_WINDOWS_PROVIDER_VERIFICATION.md).
No milestone is ACTIVE; HR12 is NOT STARTED. Historical checkpoints below remain
as records of their dates and are superseded by this status where they differ.

## HR11 completion checkpoint

Completed all 15 implementation stages under the owner’s 2026-09-06 mandate.
175 safe tests pass; 39 protected hashes match. The default research report has
180 insufficient-evidence cells and no real intraday records or trades. See
`HR11.md`, `HR11_REQUEST.md` and `docs/reports/HR11_REPORT.md`.
No successor milestone has been activated.
OI3 is DEFERRED, not complete; its outstanding work below is preserved.
See ADR 0021 for the explicit milestone transition.

## Deferred OI3 context

OI2's offline acceptance did not establish a functioning current-data dashboard.
OI3 restores automatically refreshed public market data, daily/intraday charts,
and the existing macro sentiment scanner with retained headlines and explicit
AI/fallback provenance. Preserve legacy research and execution boundaries.
Acceptance requires provider-failure tests, browser interaction checks, and a
documented real-provider smoke check; unavailable providers must remain visible.

The referenced root `MASTER_VSCODE_AGENT_PROMPT.md` is absent. Follow AGENTS,
the Constitution and the owner's explicit restoration request.

## OI3 progress — 2026-09-05

- [x] Restore cached public quotes and timestamped stock/index charts.
- [x] Connect MacroSentimentScanner; retain and render headlines, macro impacts,
  source links and per-item AI/keyword provenance.
- [x] Keep pending loads responsive and preserve data on source failure.
- [x] Validate 114 safe offline tests, real-provider browser flow, mobile layout,
  and browser-only failure/retention fixtures.
- [x] Confirm real Yahoo data and ten Moneyweb headlines in the running app.
- [x] Add a separate broad-universe opportunity scan using current Yahoo
  momentum/RSI plus matched public-news impacts; baseline quote cards are not
  presented as the opportunity selection.
- [x] Verify successful real AI comprehension and provider failure handling.
  Local Ollama (`llama3`) now produces valid structured output for permitted
  headlines through `SentimentProviders` and the dashboard. CPU-only execution is
  configurable via `OLLAMA_LOCAL_OPTIONS`; fallback to keyword analysis is tested.
  Cloud/Kimi routes remain unverified because keys are missing.
- [ ] Connect additional permitted public sources and verify Ollama-backed
  ticker discovery, including Efficient Group/public commentary where legally
  accessible. Private Facebook access and SENS challenge bypass remain out of
  scope.

SENS returns HTTP 403; NewsAPI is unconfigured. These source states remain
visible. OI3 remains DEFERRED; do not infer AI-feed completion from offline tests.
See `docs/reports/OI3_RESTORATION_REPORT.md` for evidence and remaining work.

## OI2 scope — activated 2026-09-04

- [x] Inventory every substantive backend capability and its UI disposition.
- [x] Add canonical instruments, data states, analysis runs and orchestration.
- [x] Implement exactly 30 auditable evidence gates over real/available inputs.
- [x] Wire separate market, news, technical, combined-analysis and scanner APIs.
- [x] Build maintainable Flask templates/static dashboard navigation.
- [x] Expose legacy BUY/SELL/HOLD while isolating rejected HR9/HR10 research.
- [x] Keep broker handoff visibly locked; omit journaling while no suggestion is actionable.
- [x] Validate offline, partial-failure and execution-safety behavior.

OI2 must not tune HR9, alter HR10, read `.env`, automate broker login or expose
any live-order endpoint.

## OI2 acceptance record — 2026-09-04

- [x] Six canonical JSE instruments map UI, research, Yahoo and Finnhub aliases.
- [x] HR7 historical evidence drives the unchanged fixed-weight legacy scorer.
- [x] All component responses disclose source, source time, retrieval time and state.
- [x] Exactly 30 gates return, including explicit unavailable evidence.
- [x] Current-public providers are opt-in and failures preserve partial output.
- [x] No admitted strategy, executable suggestion or live-order endpoint exists.
- [x] 104 safe offline tests pass; two environment tests remain excluded.
- [x] Live local HTTP health and SOL analysis smoke requests returned 200.

## UIR1 scope — activated 2026-09-04

- [x] Search reachable/unreachable Git history, deleted paths, archives and the
  protected `generate_app.py` worktree for the reported complete dashboard.
- [x] Identify the actual origin and data state of every historical Flask UI.
- [x] Map each reported feature to historical UI evidence and surviving backend.
- [x] Stop before reconstruction because no recoverable implementation exists.
- [x] Record security/provenance concerns without exposing credentials.

UIR1 is an audit/recovery milestone. HR7–HR10 artifacts and OI1 safety
boundaries remain immutable.

## UIR1 acceptance record — 2026-09-04

- [x] Confirmed `app.py` first appears at `332666a` as a simulated ticker.
- [x] Found no templates/static dashboard in reachable, deleted or unreachable history.
- [x] Confirmed `generate_app.py` audits HTML; it does not generate the application.
- [x] Mapped all seven reported UI groups to surviving/missing backend capabilities.
- [x] Determined that “30 steps” documents simulation iterations, not a 30-check confidence model.
- [x] Identified no live data in the current UI and made no provider/network calls.
- [x] Stopped without reconstructing or changing `app.py`.
- [x] Preserved HR7–HR10, OI1, `.env` and unrelated worktree changes.

## OI1 scope — activated 2026-09-04

- [x] Build a responsive, unmistakably simulated decision-support card.
- [x] Add a canonical provenance-rich `TradeSuggestion` safety contract.
- [x] Keep all execution actions mock/manual and all provider writes disabled.
- [x] Deepen ViewPoint/Shyft and alternative-provider research using official sources.
- [x] Produce a concise Standard Bank API enquiry and execution-path comparison.
- [x] Rank genuinely new predictive data families without tuning HR9.
- [x] Run focused UI/safety tests and the full safe offline suite.

OI1 cannot change the HR10 outcome, promote HR9, authenticate to a broker, or
submit an order.

## OI1 acceptance record — 2026-09-04

- [x] Existing `/` route retained with desktop/tablet/phone decision hierarchy.
- [x] Demo is fabricated, rejected and unmistakably simulated/not live.
- [x] Stale, rejected, shadow, research and no-trade suggestions are non-actionable.
- [x] Paper provider is the only implementation; live account modes and writes fail.
- [x] Shyft's Saxo technology relationship confirmed; retail OpenAPI remains unknown.
- [x] IG, Saxo and IBKR APIs documented without claiming unverified JSE coverage.
- [x] JSE SENS/event data ranked first for the next predictive dataset milestone.
- [x] 16 focused OI1/HR10 tests and 98 safe offline regression tests pass.
- [x] Credential/network/browser probes and environment-dependent LLM script excluded.

## HR10 scope — activated 2026-09-04

- [x] Add horizon-aware purged and embargoed temporal folds.
- [x] Evaluate realizable non-overlapping trades separately from overlapping
  research observations.
- [x] Stress costs and a predeclared, modest parameter grid.
- [x] Apply transparent multiple-testing control and time-aware uncertainty.
- [x] Assign every instrument × horizon cell exactly one deterministic admission
  state without promoting any production signal.
- [x] Preserve the four HR9 baselines and all immutable HR7–HR9 artifacts.
- [x] Add a safe local UI review mode with unmistakable simulated-data labels.
- [x] Document ViewPoint/Shyft capabilities, unknowns and vendor-neutral
  read-only/paper integration boundaries.

HR10 may complete with zero admitted cells. Live execution, authenticated
scraping and production promotion remain outside this milestone.

## HR10 acceptance record — 2026-09-04

- [x] Evaluated 40 instrument × horizon cells; 0 admitted, 40 rejected, 0 insufficient.
- [x] All cells fail uncertainty and BH-FDR gates; results do not justify promotion.
- [x] Added predeclared 0/10/25-bps and 0.30/0.35/0.40 threshold grids.
- [x] Added block-bootstrap confidence intervals and exact gate diagnostics.
- [x] Focused HR7–HR10 suite passes 34 tests; safe offline suite passes 91 tests.
- [x] Excluded credential/network/browser probes and the environment-dependent
  LLM availability script from the safe suite.
- [x] Confirmed simulated UI health/snapshot labels and no provider live writes.

## HR9 acceptance record — 2026-09-04

- [x] Preserved and hash-identified the 101,536-row pre-HR9 baseline.
- [x] Extracted one authoritative versioned technical-signal definition.
- [x] Unified HR8/HR9 on signal-state turnover cost semantics.
- [x] Defined independent 1/3/5/20-session research targets.
- [x] Logged evidence counts, versions, hashes, contributions and shadow status.
- [x] Verified zero causal clock, duplicate-key, sample-gate and shadow violations.
- [x] Compared legacy, static expanded, pre-HR9 and HR9 across three cost scenarios.
- [x] Kept Flask, production signals, governance and brokers unchanged.
- [x] Rejected adaptive promotion because net performance is not consistently
  superior to the legacy benchmark.
- [x] Focused HR8/HR9 suite passes 14 tests.

## HR8 acceptance record — 2026-09-03

- [x] Estimated effectiveness by indicator/instrument/profile/regime/volatility/horizon.
- [x] Added costs, Wilson uncertainty, temporal stability and recency diagnostics.
- [x] Added a 30-observation gate and 20-observation neutral-prior shrinkage.
- [x] Bounded mature research reliability weights between 0.5 and 1.5.
- [x] Ensured walk-forward weights see outcomes only after their horizon elapses.
- [x] Persisted weak/harmful cells and kept all learned weights research-only.

## HR7 acceptance record — 2026-09-03

- [x] Built common point-in-time technical contexts for six JSE equities.
- [x] Added separate USD/ZAR, gold, Brent and JSE-index research contexts.
- [x] Joined Rand, commodity, global-risk and nominal-yield context by exact date.
- [x] Preserved distinct instrument/profile/regime/horizon evaluation dimensions.
- [x] Marked intraday and futures basis/OI/term-structure capabilities unavailable.
- [x] Added future-mutation and missing-benchmark tests; changed no strategy weights.

## HR6 acceptance record — 2026-09-03

- [x] Implemented preceding-swing Fibonacci levels and contextual confluence fields.
- [x] Ensured Fibonacci emits no automatic BUY/SELL action.
- [x] Implemented all sixteen requested deterministic candlestick patterns.
- [x] Added trend, support/resistance, volatility and optional volume context.
- [x] Made next-bar confirmation unavailable until the next bar exists.
- [x] Registered both families as deterministic shadow-only research features.

## HR5 acceptance record — 2026-09-03

- [x] Implemented full Tenkan, Kijun, current/projected cloud and Chikou context.
- [x] Used the displaced source window for the cloud visible at decision time.
- [x] Exposed cloud thickness/direction, Kijun distance, breakouts and TK cross strength.
- [x] Added 78-bar OHLC capability gate and future-mutation tests.
- [x] Registered Ichimoku as executable, deterministic and shadow-only.
- [x] Deferred all asset/regime/horizon value claims to historical evaluation.

## HR4 acceptance record — 2026-09-03

- [x] Added modular versioned technical-feature definitions and computation results.
- [x] Wrapped existing research calculators without duplicating production logic.
- [x] Preserved capability and as-of-index gates, including aligned benchmarks.
- [x] Registered all required families with honest implemented/planned status.
- [x] Prevented planned Ichimoku/Fibonacci/candlestick entries from masquerading as code.
- [x] Kept every registry computation research/shadow-only.

## HR3 acceptance record — 2026-09-03

- [x] Added point-in-time Rand trend, return, volatility and regime features.
- [x] Separated USD gold from ZAR gold and DXY/yield/risk context.
- [x] Separated Brent direction, momentum, volatility and Rand-denominated cost.
- [x] Added platinum/palladium and Rand-translation features where exact dates align.
- [x] Used prefix-only calculations, exact-date joins and no forward filling.
- [x] Kept missing official macro vintages explicit and all features research-only.

## HR2 acceptance record — 2026-09-03

- [x] Froze dated daily OHLCV for six JSE equities and a JSE All Share proxy.
- [x] Froze USD/ZAR, VIX, S&P 500, DXY, US10Y, Brent, gold, platinum and palladium proxies.
- [x] Recorded per-file dates, row counts, provider symbols and SHA-256 hashes.
- [x] Applied conservative next-day bar availability and no forward filling.
- [x] Marked release-vintage SA macro, real yields and licensed derivatives unavailable.
- [x] Documented proxy, adjustment, licensing and timestamp limitations.

## HR1 acceptance record — 2026-09-03

- [x] Added normalized raw/derived point-in-time feature and provenance contracts.
- [x] Enforced timezone-aware event, availability and decision clocks.
- [x] Added append-only persistence, stable identity and revision-aware as-of queries.
- [x] Added explicit capability/missing-data and derived-lineage validation.
- [x] Documented schema, storage, revisions, versioning and no-lookahead policy.
- [x] Kept the store research/shadow-only and production behavior unchanged.

## HR0 acceptance record — 2026-09-03

- [x] Audited executable technical features rather than documentation/library availability.
- [x] Classified implemented-and-used, implemented-but-unused and missing families.
- [x] Confirmed Ichimoku, Fibonacci and deterministic candlestick families are absent.
- [x] Identified `research_indicators.py` as the additive capability-gated extension point.
- [x] Changed no strategy, score, threshold, weight or execution behavior.

## M10 acceptance record — 2026-09-03

- [x] Audited roadmap, tests, reports, source status and security boundaries.
- [x] Produced `FUSION_COMPLETION_REPORT.md`.
- [x] Selected **continue shadow collection**; production defaults remain legacy.
- [x] Confirmed no live trading capability was added or enabled.
- [x] Final focused suite passes: 41 tests.

## M9 acceptance record — 2026-09-03

- [x] Added profile/regime/adaptive explanations to researcher output through an adapter.
- [x] Preserved researcher, Trader, Risk, Manager and Executor method interfaces.
- [x] Added legacy/adaptive/bull/bear disagreement telemetry.
- [x] Verified context-on/context-off proposal, risk and manager equivalence.
- [x] Explicitly labelled simulated execution as paper-only.
- [x] Focused suite passes: 41 tests.

## M8 acceptance record — 2026-09-03

- [x] Verified and documented access status for every named source category.
- [x] Added independently configurable source policy, authority and poll intervals.
- [x] Normalized source policy into evidence provenance and the reliability registry.
- [x] Retained enabled Moneyweb/SENS collectors and disabled restricted/unverified automation.
- [x] Disabled unauthenticated Reddit JSON fallback under current API terms.
- [x] Focused suite passes: 38 tests.

## M7 acceptance record — 2026-09-03

- [x] Added prefix-only multi-horizon walk-forward evaluation.
- [x] Added configurable costs, turnover, drawdown and close-path MFE/MAE.
- [x] Added trend/volatility/profile segments, Wilson intervals and minimum-sample flags.
- [x] Added legacy, technical-only, macro-only, source-only and adaptive ablations.
- [x] Generated a six-ticker report with 760 daily observations per ticker.
- [x] Recorded that missing contextual history and mixed results do not support promotion.
- [x] Focused suite passes: 33 tests.

## M6 acceptance record — 2026-09-03

- [x] Added explainable adaptive fusion beside the unchanged legacy output.
- [x] Added explicit regime/profile multipliers and minimum-sample-gated reliability.
- [x] Logged factor contributions and legacy-vs-adaptive comparison in decision metadata.
- [x] Kept public/default score, action, confidence and thresholds on the legacy path.
- [x] Focused suite passes: 28 tests, including unavailable-regime safety coverage.

## M5 acceptance record — 2026-09-03

- [x] Added versioned ADX/DMI, ATR, MACD, Bollinger/z-score and relative-strength research features.
- [x] Added relative-volume and median-dollar-volume features behind volume capability.
- [x] Gated session VWAP/opening range behind explicit intraday OHLCV capability.
- [x] Added per-feature availability/reason metadata and an explicit as-of boundary.
- [x] Focused suite passes: 23 tests, including future-mutation no-lookahead coverage.

## M4 acceptance record — 2026-09-03

- [x] Added immutable, versioned sector/instrument profiles covering every required group.
- [x] Moved ticker-specific legacy macro coefficients behind configurable profile selection.
- [x] Preserved legacy scoring coefficients, thresholds and clamp with characterization tests.
- [x] Added selected profile context to decision metadata as shadow-only output.
- [x] Focused suite passes: 18 tests (the previous 14 plus 4 profile tests).

## M3 acceptance record — 2026-09-03

- [x] Added transparent `regime_engine.py` with versioned `MarketRegime` output.
- [x] Added deterministic bull, bear, range, low/normal/high-volatility and risk-label tests.
- [x] Added rolling stability report with 700 observations each for NPN, SASOL and BHP.
- [x] Kept regime output research/shadow-only; production weights unchanged.

## M2 acceptance record — 2026-09-03

- [x] Added configurable in-memory `SourceRegistry` with source class and authority tier.
- [x] Added SQLite `ReliabilityStore` for source outcomes by scope and horizon.
- [x] Added conservative sample-size shrinkage toward a 50% prior.
- [x] Added duplicate outcome protection and no-lookahead timestamp validation.
- [x] Added ADR 0002 documenting the research-only boundary.
- [x] Focused suite passes: 10 tests (`test_evidence.py`, `test_legacy_scoring.py`, `test_reliability_store.py`).

## M1 acceptance record — 2026-09-03

- [x] Added additive `evidence.py` without replacing `NewsItem`.
- [x] Added stable evidence IDs from source/headline/publication time/URL.
- [x] Added provenance fields for source class/tier, timestamps, mappings, sentiment, confidence, horizon and parser version.
- [x] Added deduplication preserving first-seen order.
- [x] Added ADR 0001 documenting the compatibility decision.
- [x] Focused suite passes: 6 tests (`test_evidence.py`, `test_legacy_scoring.py`).
- [x] Network/credential-bearing scripts were not run by discovery; they remain manual-only (`test_cloud.py`, `test_ost_login.py`, browser probes).

## M0 acceptance record — 2026-09-03

- [x] Read mandatory project docs; copied the bootstrap docs into this repository.
- [x] Inspected Git state: engine and dashboard repositories were clean before M0 work.
- [x] Confirmed `.env` and browser state are ignored and `.env` is not tracked; `.env.example` contains no secret values.
- [x] Preserved existing user work; no destructive Git operations used.
- [x] Core modules compile under Python 3.12.
- [x] Added `test_legacy_scoring.py` with three characterization tests; all pass.
- [x] Restored canonical six-ticker two-year backtest; 24 report rows and finite metrics.
- [x] Recorded baseline findings in `backtest_report.md` and the indicator bible.
- [x] Committed M0 baseline artifacts.

## Laptop checkpoint — 2026-09-06

HR11 is complete and pushed at `8b7c591`; HR12 has no tracked files or commits
and is NOT STARTED. “O13” refers to OI3 (letter I), still DEFERRED/incomplete.
No research milestone is active. The current non-research deliverable is the
portable development environment and laptop handoff in `docs/LAPTOP_HANDOFF.md`.
After setup, resume the OI3 provider verification/public-source checklist through
an explicit roadmap activation; do not invent HR12 or promote HR11 signals.
The Windows MCP cleanup remains blocked by absent Windows filesystem access.

## Windows portability maintenance - 2026-09-06

No research milestone activated; OI3 remains deferred and HR12 not started.
Protected checkout bytes and UTF-8 diagnostics fixed; 184 safe tests pass on
Windows Python 3.12.10. All 45 audited protected paths match committed bytes.
See [validation](../handoffs/2026-09-06-WINDOWS-PORTABILITY.md).
