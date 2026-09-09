# TASKS.md
## Master Implementation Roadmap & Milestone Work Breakdown
**Standard:** Strict Linear Execution — One Milestone Active at a Time  
**Precondition for Advancement:** Code Implemented, Tests Passing, ADR Written, Git Clean  

---

### Phase 1: Baseline Lock, Canonical Contracts & Early Cloud Foundation

#### Milestone M0: Baseline Freeze & Verification
* **Objective:** Freeze current verified repository baseline, lock environment invariants, and protect all historical research artifacts.
* **Prerequisites:** Clean Git working tree on `master`.
* **Modules Reused:** `scripts/check_dev_environment.py`, `scripts/run_tests.py`, `analysis/results/hr11/baseline.json`.
* **Files Changed:** `docs/roadmap/CURRENT_MILESTONE.md`, `docs/roadmap/ROADMAP.md`.
* **New Contracts:** None.
* **Migration Strategy:** Read-only audit verification.
* **Tests Required:** Run `scripts/run_tests.py` (208 tests pass). Confirm all 39 hashes in `baseline.json` match committed bytes.
* **Risks:** Unintentional mutation of tracked CSV/JSON artifacts.
* **Rollback Point:** `git checkout master`.
* **Definition of Done:** M0 signed off; baseline commit hash recorded in `CURRENT_MILESTONE.md`.
* **Stop Conditions:** Any failing test or mismatched artifact hash.

#### Milestone M1: Canonical Domain Contracts
* **Objective:** Create the universal domain dataclasses in `domain/contracts/` (`CanonicalBar`, `TradeIntent`, `OrderIntent`, `CandidateTradePolicy`, `TradeGeometry`, `RiskDecision`, `MetricContext`).
* **Prerequisites:** M0 complete.
* **Modules Reused:** `intraday_data.py`, `provider_interfaces.py`.
* **Files Changed:** `domain/contracts/__init__.py`, `domain/contracts/market.py`, `domain/contracts/trade.py`, `domain/contracts/policy.py`.
* **New Contracts:** Universal contracts specified in Section 11 of `ARCHITECTURE.md`.
* **Migration Strategy:** Additive domain package; legacy files untouched.
* **Tests Required:** Dataclass immutability tests, serialization roundtrip tests, and UTC timezone validation tests.
* **Risks:** Typing circularities.
* **Rollback Point:** Delete `domain/contracts/`.
* **Definition of Done:** 100% test coverage on all domain contract definitions.
* **Stop Conditions:** Serialization failure or non-UTC timestamp acceptance.

#### Milestone M2: Versioned Feature Registry & Semantic Parity Testing
* **Objective:** Establish the versioned Indicator Registry, register legacy formulas as explicit `_legacy_v1` features, and implement reference tests before adding any new indicator definitions.
* **Prerequisites:** M1 complete.
* **Modules Reused:** `technical_signals.py`, `research_indicators.py`, `data_pipeline.py:SignalGenerator`.
* **Files Changed:** `domain/features/technical.py`, `domain/registry/feature.py`, `test_feature_parity.py`.
* **New Contracts:** `TechnicalFeatureDefinition` supporting explicit formula versioning.
* **Migration Strategy:** Lock legacy calculations behind `feat_*_legacy_v1` tags. Implement candidate standard formulas under `feat_*_v2` tags. Do not overwrite legacy code.
* **Tests Required:** Parity tests verifying legacy behavior matches byte-for-byte; isolation tests verifying candidate formulas execute independently.
* **Risks:** Silently modifying legacy indicator outputs.
* **Rollback Point:** Revert to `data_pipeline.SignalGenerator`.
* **Definition of Done:** Both legacy v1 and candidate v2 indicators coexisting cleanly in the registry with passing parity tests.
* **Stop Conditions:** Any change in numerical output for legacy v1 feature tests.

#### Milestone M3: Instrument Registry Reconciliation
* **Objective:** Merge `instrument_registry.py` and `intraday_instruments.py` into a unified `domain/registry/instrument.py`.
* **Prerequisites:** M2 complete.
* **Modules Reused:** `intraday_instruments.py:InstrumentDefinition`.
* **Files Changed:** `domain/registry/instrument.py`, `instrument_registry.py` (becomes compatibility wrapper).
* **New Contracts:** Canonical `InstrumentDefinition` separating underlying, signal target, data symbol, and execution symbol.
* **Migration Strategy:** Re-export legacy 6 equities from new registry; maintain all legacy aliases.
* **Tests Required:** Alias resolution tests, contract multiplier validation, and broker symbol mapping tests.
* **Risks:** Breaking legacy dashboard symbol lookups.
* **Rollback Point:** Revert `instrument_registry.py`.
* **Definition of Done:** Unified instrument registry resolving all 6 legacy equities and 9 HR11 targets without breaking existing tests.
* **Stop Conditions:** Alias resolution failure in `test_oi2_operational.py`.

#### Milestone M4: Canonical Source Registry Promotion
* **Objective:** Promote OI4's SQLite-backed `SourceRegistry` to the canonical domain registry.
* **Prerequisites:** M3 complete.
* **Modules Reused:** `market_intelligence/source_registry.py`, `market_intelligence/store.py`, `source_catalog.py`.
* **Files Changed:** `domain/registry/source.py`.
* **New Contracts:** Canonical `SourcePolicy` contract with rate limiting, latency tracking, and health status.
* **Migration Strategy:** Wrap `market_intelligence/store.py` under the domain interface.
* **Tests Required:** Source CRUD tests, toggle tests, and SQLite concurrency lock tests.
* **Risks:** Concurrency lockups.
* **Rollback Point:** Revert to `market_intelligence.source_registry`.
* **Definition of Done:** Source policies persisted, auditable, and accessible via canonical domain interface.
* **Stop Conditions:** Failure in atomic source enable/disable updates.

#### Milestone M5: Event Provenance & Configurable Clustering Engine
* **Objective:** Implement Tier-2 semantic event clustering with configurable parameters ($\Delta_{\text{cluster}}$, $\theta_{\text{sim}}$).
* **Prerequisites:** M4 complete.
* **Modules Reused:** `evidence.py:evidence_id`.
* **Files Changed:** `domain/intelligence/clustering.py`, `test_event_clustering.py`.
* **New Contracts:** `ClusteredEvent` dataclass.
* **Migration Strategy:** Pass `EvidenceRecord` outputs through `EventClusterer` before sentiment calculation.
* **Tests Required:** Syndication tests verifying that identical news stories across multiple feeds collapse into 1 cluster vote.
* **Risks:** Over-clustering independent corporate announcements.
* **Rollback Point:** Fall back to exact-match `evidence.deduplicate_evidence()`.
* **Definition of Done:** Event clustering operational with configurable window and similarity thresholds.
* **Stop Conditions:** Clustering distinct SENS announcements into a single event.

#### Milestone M6: Persistence Abstraction Layer
* **Objective:** Implement the repository persistence layer abstracting SQLite and PostgreSQL.
* **Prerequisites:** M5 complete.
* **Modules Reused:** `market_intelligence/store.py`.
* **Files Changed:** `persistence/repository.py`, `persistence/sql_models.py`.
* **New Contracts:** `StorageRepository` protocol for bars, events, decisions, and policies.
* **Migration Strategy:** SQLite remains local default; PostgreSQL connection string enabled via `DATABASE_URL`.
* **Tests Required:** Persistence tests running identically on both SQLite and PostgreSQL.
* **Risks:** Incompatible SQL dialect queries.
* **Rollback Point:** Revert to direct SQLite queries in `market_intelligence/store.py`.
* **Definition of Done:** Storage layer passing all persistence tests across both database engines.
* **Stop Conditions:** Inability to maintain transaction atomicity across repository calls.

#### Milestone M7: Early Railway Foundation Validation
* **Objective:** Deploy a minimal, read-only version of the application to Railway to validate cloud container readiness, database connectivity, and environment handling early.
* **Prerequisites:** M6 complete, Railway project provisioned.
* **Modules Reused:** `app.py`, `scripts/start_dashboard.sh`.
* **Files Changed:** `Dockerfile`, `railway.toml`, `scripts/start_railway.sh`.
* **New Contracts:** Container health check endpoint (`GET /health`).
* **Migration Strategy:** Deploy Web Service + PostgreSQL add-on. Zero broker execution, zero automated trading.
* **Tests Required:** Cloud deployment smoke tests, database migration tests, and container reboot persistence tests.
* **Risks:** Missing cloud environment variables or port binding errors.
* **Rollback Point:** Teardown Railway deployment.
* **Definition of Done:** App running green on Railway, connecting to managed PostgreSQL, surviving redeployments with persisted state.
* **Stop Conditions:** Any container boot failure or inability to connect to PostgreSQL.

---

### Phase 2: Causal Core, Regime Modeling & Disagreement Features

#### Milestone M8: Preserve & Migrate HR11 Causal Core
* **Objective:** Integrate HR11 session calendars, bar aggregation, and horizon contracts into `domain/market_data/`.
* **Prerequisites:** M7 complete.
* **Modules Reused:** `intraday_sessions.py`, `intraday_horizons.py`, `intraday_cross_asset.py`.
* **Files Changed:** `domain/market_data/sessions.py`, `domain/market_data/aggregation.py`, `domain/market_data/horizons.py`.
* **New Contracts:** Canonical session windows and timeframe aggregators.
* **Migration Strategy:** Migrate modules into domain package while maintaining full backwards compatibility with HR11 scripts.
* **Tests Required:** Re-run `test_hr11_sessions.py`, `test_hr11_horizons.py`, `test_hr11_cross_asset.py`.
* **Risks:** Unintentional alteration of bar boundary mathematics.
* **Rollback Point:** Revert to `intraday_*` modules.
* **Definition of Done:** All HR11 session and bar tests passing under new domain directory structure.
* **Stop Conditions:** Bar aggregation crossing a session boundary or misidentifying a break.

#### Milestone M9: Canonical Regime Engine & Versioning
* **Objective:** Unify `regime_engine.py` and `intraday_signals.py:regimes` into a versioned, multi-label `MarketRegime` engine.
* **Prerequisites:** M8 complete.
* **Modules Reused:** `regime_engine.py:classify_regime`.
* **Files Changed:** `domain/features/regime.py`, `test_regime_engine_v2.py`.
* **New Contracts:** `MarketRegime` vector dataclass with configurable thresholds.
* **Migration Strategy:** Preserve legacy regime formula as `regime_v1`; introduce parameterized `regime_v2` supporting ADX and realized volatility percentiles.
* **Tests Required:** Deterministic classification tests and look-ahead invariance tests.
* **Risks:** Regime flip-flopping under market chop.
* **Rollback Point:** Revert to `regime_v1`.
* **Definition of Done:** Single regime engine supplying typed `MarketRegime` vectors to daily and intraday pipelines.
* **Stop Conditions:** Any future bar data influencing current bar regime classification.

#### Milestone M10: Divergence & Disagreement Feature Implementation
* **Objective:** Implement `domain/features/divergence.py` providing price/RSI, price/MACD, and tech/news divergence as candidate features.
* **Prerequisites:** M9 complete.
* **Modules Reused:** `domain/features/technical.py`.
* **Files Changed:** `domain/features/divergence.py`, `test_divergence_features.py`.
* **New Contracts:** `DivergenceSnapshot` dataclass.
* **Migration Strategy:** Additive feature family; does not alter existing legacy score calculation.
* **Tests Required:** Peak/trough identification tests and causal as-of mutation invariance tests.
* **Risks:** Peak detection algorithms peering into future bars.
* **Rollback Point:** Delete `domain/features/divergence.py`.
* **Definition of Done:** Divergence features proven causal with zero look-ahead in test suite.
* **Stop Conditions:** Divergence feature output changing when future bars are modified.

#### Milestone M11: Contextual Effectiveness Matrix Store
* **Objective:** Implement the persistent $(I \times R \times F \times H)$ effectiveness matrix in PostgreSQL/SQLite.
* **Prerequisites:** M10 complete.
* **Modules Reused:** `indicator_effectiveness.py:ReliabilityAccumulator`.
* **Files Changed:** `domain/strategy/effectiveness.py`, `persistence/effectiveness_repo.py`.
* **New Contracts:** `EffectivenessMatrix` and `ReliabilityRecord`.
* **Migration Strategy:** Rebuild accumulator to load and update historical cell weights in database.
* **Tests Required:** Shrinkage tests, 30-observation gate tests, and weight persistence across restart tests.
* **Risks:** Contention on high-frequency weight updates.
* **Rollback Point:** Fall back to neutral 1.0 weights.
* **Definition of Done:** Reliable weight updates persisted across application restarts.
* **Stop Conditions:** Weights escaping the $[0.5, 1.5]$ boundary.

#### Milestone M12: Instrument Selection Engine
* **Objective:** Implement strategy-level candidate ranking across the permitted universe in `domain/strategy/selection.py`.
* **Prerequisites:** M11 complete.
* **Modules Reused:** `opportunity_scanner.py` (mathematical concepts).
* **Files Changed:** `domain/strategy/selection.py`, `test_instrument_selection.py`.
* **New Contracts:** `CandidateFilter` and `RankedUniverse`.
* **Migration Strategy:** Replace ad-hoc scanner with formal multi-factor filter (spread, liquidity, regime).
* **Tests Required:** Liquidity gate tests, spread filter tests, and candidate ranking reproducibility tests.
* **Risks:** Empty candidate list on market holidays.
* **Rollback Point:** Fall back to static 6-instrument list.
* **Definition of Done:** Engine deterministically selecting qualified candidate instruments from broad universe.
* **Stop Conditions:** Candidate selected with spread exceeding maximum allowance.

#### Milestone M13: Opportunity Ranking Engine
* **Objective:** Combine selection and relevance to rank candidates and emit the Top 5 opportunities.
* **Prerequisites:** M12 complete.
* **Modules Reused:** `operational_intelligence.py:scan`.
* **Files Changed:** `domain/strategy/ranking.py`, `test_opportunity_ranking.py`.
* **New Contracts:** `RankedOpportunity` and `TopOpportunitiesReport`.
* **Migration Strategy:** Replace legacy `scan_market()` with deterministic sorting on net conviction.
* **Tests Required:** Ranking invariance tests, tie-breaking tests, and empty universe graceful handling.
* **Risks:** Excessive sector concentration among Top 5.
* **Rollback Point:** Revert to scanning fixed list.
* **Definition of Done:** Exactly 5 (or fewer if disqualified) ranked opportunities emitted with full metrics.
* **Stop Conditions:** Disqualified instrument (stale data or wide spread) appearing in Top 5.

---

### Phase 3: Trade Policy, Risk Engine & Strategy Lifecycle

#### Milestone M14: Trade Policy Engine (Policy Families)
* **Objective:** Implement `domain/policy/engine.py` translating opportunities into complete `TradeIntent` records using explicit candidate policy families.
* **Prerequisites:** M13 complete.
* **Modules Reused:** `intraday_costs.py:transition_cost`.
* **Files Changed:** `domain/policy/engine.py`, `domain/policy/families.py`, `test_trade_policy.py`.
* **New Contracts:** `CandidateTradePolicy`, `EntryPolicyType`, `StopPolicyType`, `ExitPolicyType`, and `TradeGeometry`.
* **Migration Strategy:** Replace fixed thresholds with policy families (`MARKET`, `PULLBACK_LIMIT`, `STRUCTURAL_INVALIDATION`, etc.).
* **Tests Required:** Geometry calculation tests, structural invalidation tests, and risk-reward ratio validation.
* **Risks:** Stop placed on wrong side of entry price due to sign bug.
* **Rollback Point:** Revert to static horizon exits.
* **Definition of Done:** Candidate policy generating explicit `TradeIntent` records with complete geometry.
* **Stop Conditions:** Stop price placed on wrong side of entry or invalidation price undefined.

#### Milestone M15: Portfolio Risk & Exposure Engine (Unset Limits)
* **Objective:** Implement `domain/risk/engine.py` enforcing the Hard Risk Constitution and aggression slider without hardcoded numerical limits.
* **Prerequisites:** M14 complete.
* **Modules Reused:** `intraday_costs.py:transition_cost`, `merged_simulation.py:RiskAgent` (math concepts).
* **Files Changed:** `domain/risk/engine.py`, `domain/risk/constitution.py`, `test_risk_engine.py`.
* **New Contracts:** `RiskEngine` evaluating `TradeIntent` $\to$ `RiskDecision`.
* **Migration Strategy:** Limits remain unset until configured by operator. Aggression slider maps into configured envelope.
* **Tests Required:** Daily drawdown tripwire tests, max portfolio risk cap tests, and unconfigured limit refusal tests.
* **Risks:** Unconfigured risk limits allowing unconstrained sizing.
* **Rollback Point:** Revert to fixed 1-unit paper sizing.
* **Definition of Done:** Risk engine refusing execution when limits are unset and sizing within bounds when configured.
* **Stop Conditions:** Trade approved with unconfigured risk limits or exceeding account equity.

#### Milestone M16: StrategyTarget Contract & Validation
* **Objective:** Implement `domain/evaluation/target.py` enforcing formal `StrategyTarget` contracts.
* **Prerequisites:** M15 complete.
* **Modules Reused:** `hr10_robustness.py:AdmissionRules`.
* **Files Changed:** `domain/evaluation/target.py`, `test_strategy_target.py`.
* **New Contracts:** `StrategyTarget` dataclass with configurable threshold fields.
* **Migration Strategy:** Convert hardcoded admission rules into configurable policy records.
* **Tests Required:** Target satisfaction verification and constraint enforcement tests.
* **Risks:** Target criteria so stringent no strategy can pass.
* **Rollback Point:** Revert to HR10 admission rules.
* **Definition of Done:** Formal `StrategyTarget` contract evaluating candidate strategy runs.
* **Stop Conditions:** Strategy promoted to production without passing target constraints.

#### Milestone M17: Hypothesis & Experiment Registry
* **Objective:** Implement `domain/evaluation/experiment.py` enforcing single-attributable-hypothesis testing.
* **Prerequisites:** M16 complete.
* **Modules Reused:** `analysis/results/hr11/` schema concepts.
* **Files Changed:** `domain/evaluation/experiment.py`, `persistence/experiment_repo.py`.
* **New Contracts:** `Experiment` record schema.
* **Migration Strategy:** Database tables tracking baseline version, candidate version, changed variable, and attribution.
* **Tests Required:** Single-hypothesis change enforcement tests and experiment reproducibility tests.
* **Risks:** Recording uncontrolled multi-variable mutations.
* **Rollback Point:** Revert to file-based JSON report logging.
* **Definition of Done:** Fully traceable experiment database recording hypothesis $\to$ outcome.
* **Stop Conditions:** Attempt to record an experiment modifying multiple unlinked variables without factorial declaration.

#### Milestone M18: Canonical Performance Metrics & Contextual Sharpe
* **Objective:** Implement `domain/evaluation/metrics.py` with `MetricContext`-aware Sharpe, Sortino, and drawdown.
* **Prerequisites:** M17 complete.
* **Modules Reused:** `hr10_robustness.py:_metrics`, `evaluation.py:_metric_row`.
* **Files Changed:** `domain/evaluation/metrics.py`, `test_metrics_accuracy.py`.
* **New Contracts:** `MetricContext` and `PerformanceMetrics`.
* **Migration Strategy:** Correct Sharpe annualization based on sampling interval; isolate legacy formula under `legacy_sample_scaled_t_stat`.
* **Tests Required:** Parity tests against analytical return series and legacy metric preservation tests.
* **Risks:** Historical reports misinterpreting new Sharpe values.
* **Rollback Point:** Retain legacy calculation under separate name.
* **Definition of Done:** Canonical metrics reporting validated, context-aware Sharpe and Sortino ratios.
* **Stop Conditions:** Sharpe calculated on overlapping returns without explicit duration scaling.

---

### Phase 4: API, Early GUI & Broker Integration

#### Milestone M19: Canonical Opportunity & TradeIntent API
* **Objective:** Expose `/api/v2/` endpoints serving canonical Top-5 opportunities, trade intents, and risk previews.
* **Prerequisites:** M18 complete.
* **Modules Reused:** `app.py` (Flask application container).
* **Files Changed:** `api/v2_routes.py`, `app.py` (registers blueprint).
* **New Contracts:** REST API contracts for Top-5 opportunities and risk simulation.
* **Migration Strategy:** Mount `/api/v2/` blueprint beside legacy `/api/` routes in Flask.
* **Tests Required:** API parity tests, payload validation tests, and error handling tests.
* **Risks:** Route collision with legacy endpoints.
* **Rollback Point:** Unregister v2 blueprint.
* **Definition of Done:** `/api/v2/opportunities` returning canonical Top-5 payloads alongside functioning legacy routes.
* **Stop Conditions:** Any regression in legacy `/api/analysis/<instrument>` endpoint.

#### Milestone M20: Early Read-Only Top-5 Cockpit GUI
* **Objective:** Build a read-only Top-5 Opportunity Cockpit in the browser using paper/research data.
* **Prerequisites:** M19 complete.
* **Modules Reused:** `templates/dashboard.html`, `static/css/dashboard.css`.
* **Files Changed:** `templates/dashboard.html` (adds Cockpit tab), `static/js/cockpit.js`.
* **New Contracts:** UI rendering contracts for `TopOpportunitiesReport`.
* **Migration Strategy:** Add new Cockpit tab as default landing view; move legacy 30-gate panel to "Legacy Diagnostics" tab.
* **Tests Required:** Browser rendering tests, mobile viewport responsiveness, and trade card data verification.
* **Risks:** Premature removal of legacy diagnostics.
* **Rollback Point:** Revert default tab to legacy view.
* **Definition of Done:** Responsive Top-5 Cockpit rendering real backend trade intents with full geometry.
* **Stop Conditions:** UI performing client-side signal recalculations.

#### Milestone M21: BrokerAdapter Protocol & Paper Broker
* **Objective:** Implement `domain/broker/adapter.py` and `domain/broker/paper.py` for simulated order execution.
* **Prerequisites:** M20 complete.
* **Modules Reused:** `provider_interfaces.py:PaperExecutionProvider`, `intraday_router.py`.
* **Files Changed:** `domain/broker/adapter.py`, `domain/broker/paper.py`, `test_paper_broker.py`.
* **New Contracts:** `BrokerAdapter` protocol and `PaperBroker` implementation.
* **Migration Strategy:** Replace hard-failing stubs with fully simulated paper order book and cash accounting.
* **Tests Required:** Paper fill tests, partial fill simulation, slippage application, and cash balance tracking.
* **Risks:** Inaccurate fee deduction in paper accounting.
* **Rollback Point:** Revert to `PaperExecutionProvider`.
* **Definition of Done:** Paper broker accurately simulating fills, balances, and P&L.
* **Stop Conditions:** Paper adapter attempting network connection.

#### Milestone M22: IG Instrument Discovery & Contract Mapping
* **Objective:** Implement IG REST API authentication and instrument specification discovery in `domain/broker/ig_discovery.py`.
* **Prerequisites:** M21 complete, IG API credentials in `.env`.
* **Modules Reused:** `jse_adapter.py`.
* **Files Changed:** `domain/broker/ig_discovery.py`, `test_ig_discovery.py`.
* **New Contracts:** `IGContractSpec` mapping broker epic to canonical instrument ID.
* **Migration Strategy:** Query IG REST `/markets` endpoint; map contract sizes, tick values, and trading hours into Instrument Registry.
* **Tests Required:** Mock HTTP tests verifying correct contract size and margin rate parsing.
* **Risks:** Unmapped broker instruments causing discovery failures.
* **Rollback Point:** Revert to manual contract specifications.
* **Definition of Done:** Canonical instruments accurately mapped to verified IG market epics.
* **Stop Conditions:** Credentials leaked in exception strings or log files.

#### Milestone M23: IG Historical Data Gateway (Execution Grade)
* **Objective:** Implement execution-grade 5-minute historical bar retrieval via IG REST API.
* **Prerequisites:** M22 complete.
* **Modules Reused:** `domain/market_data/`.
* **Files Changed:** `domain/broker/ig_data.py`, `test_ig_data_gateway.py`.
* **New Contracts:** `IGHistoricalGateway` producing `CanonicalBar` marked `DataGrade.EXECUTION_GRADE`.
* **Migration Strategy:** Connect to IG `/prices` endpoint; transform responses into `CanonicalBar` with verified spread.
* **Tests Required:** Mock HTTP tests asserting tick size normalization and UTC timestamp correctness.
* **Risks:** IG API rate-limit exhaustion.
* **Rollback Point:** Fall back to local research CSV files.
* **Definition of Done:** Verified 5-minute bars retrieved from IG and ingested into database.
* **Stop Conditions:** Silent fallback to Yahoo Finance data when IG data is unavailable.

#### Milestone M24: Exercise HR11 on Real 5m Data (Targeted Evaluation)
* **Objective:** Run `hr11_research.py` against real 5-minute bars for supported instruments; evaluate qualified cells and leave unsupported cells as explicit `INSUFFICIENT_EVIDENCE`.
* **Prerequisites:** M23 complete.
* **Modules Reused:** `hr11_research.py`, `intraday_evaluation.py`.
* **Files Changed:** Reports in `analysis/results/hr11_real/`.
* **New Contracts:** None.
* **Migration Strategy:** Run causal evaluator against genuine historical dataset.
* **Tests Required:** Verify supported cells produce evaluated trades; verify unsupported cells remain explicitly `INSUFFICIENT_EVIDENCE` with documented reasons.
* **Risks:** Strategy showing negative net expectancy on real data.
* **Rollback Point:** Revert to baseline empty report.
* **Definition of Done:** Every supported cell evaluated causally; unsupported cells explicitly documented.
* **Stop Conditions:** Attempting to force an unsupported cell into an evaluated state without data.

#### Milestone M25: IG Streaming Market Data Gateway
* **Objective:** Implement real-time streaming market data via IG Lightstreamer in `domain/broker/ig_stream.py`.
* **Prerequisites:** M24 complete.
* **Modules Reused:** `dashboard_feeds.py`.
* **Files Changed:** `domain/broker/ig_stream.py`, `test_ig_streaming.py`.
* **New Contracts:** `MarketDataStream` protocol emitting push ticks.
* **Migration Strategy:** Connect Lightstreamer client in Worker service; stream quotes into feature cache.
* **Tests Required:** Disconnect/reconnect handling tests and price parsing tests.
* **Risks:** Memory leak in persistent streaming connection.
* **Rollback Point:** Fall back to background REST polling.
* **Definition of Done:** Live bid/ask and tick prices streaming continuously into feature engine.
* **Stop Conditions:** Streaming process blocking web request threads.

#### Milestone M26: IG Demo Account & Position Synchronization
* **Objective:** Synchronize account balances, free cash, margin, and open positions from IG Demo account.
* **Prerequisites:** M25 complete.
* **Modules Reused:** `domain/risk/engine.py`.
* **Files Changed:** `domain/broker/ig_account.py`, `test_ig_account_sync.py`.
* **New Contracts:** `AccountState` and `PositionState` dataclasses.
* **Migration Strategy:** Query IG REST `/accounts` and `/positions`; update local portfolio cache.
* **Tests Required:** Balance reconciliation tests and position parsing tests.
* **Risks:** Currency mismatch between account balance and instrument quote currency.
* **Rollback Point:** Fall back to simulated balance.
* **Definition of Done:** Real-time IG Demo balances and positions accurately reflected in portfolio engine.
* **Stop Conditions:** Desynchronization between broker position count and local database.

#### Milestone M27: IG Demo Execution & Reconciliation
* **Objective:** Implement order dispatch, amendment, cancellation, and fill reconciliation on IG Demo account.
* **Prerequisites:** M26 complete.
* **Modules Reused:** `domain/broker/adapter.py`.
* **Files Changed:** `domain/broker/ig_execution.py`, `test_ig_demo_execution.py`.
* **New Contracts:** `ExecutionResult` and `ReconciliationReport`.
* **Migration Strategy:** Dispatch `OrderIntent` to IG REST `/positions/otc` in Demo environment.
* **Tests Required:** Order placement tests, stop-loss attachment tests, and fill reconciliation tests.
* **Risks:** Stray orders in Demo account.
* **Rollback Point:** Switch execution mode to `PAPER`.
* **Definition of Done:** End-to-end execution on IG Demo with verified broker-side bracket stops.
* **Stop Conditions:** Any attempt to connect to IG Live production endpoints.

---

### Phase 5: GUI Completion, Production Hardening & Validation

#### Milestone M28: Source & Indicator Governance GUI
* **Objective:** Build dedicated UI tabs for source management (tick boxes, Add Source, weight) and indicator governance.
* **Prerequisites:** M27 complete.
* **Modules Reused:** `market_intelligence/source_registry.py`, `domain/registry/feature.py`.
* **Files Changed:** `templates/governance.html`, `static/js/governance.js`.
* **New Contracts:** Governance REST API endpoints.
* **Migration Strategy:** Integrate source and feature registry controls into the web interface.
* **Tests Required:** Checkbox toggle API tests, parameter update tests, and custom RSS feed addition tests.
* **Risks:** Malformed URL injection.
* **Rollback Point:** Reset to default source policies.
* **Definition of Done:** Operator can enable, disable, and weight sources and indicators via browser.
* **Stop Conditions:** Server accepting unverified source URL without validation.

#### Milestone M29: Portfolio & Risk Cockpit GUI
* **Objective:** Build the Portfolio and Risk tab showing live equity, margin, exposure, and the interactive aggression slider.
* **Prerequisites:** M28 complete.
* **Modules Reused:** `domain/risk/engine.py`.
* **Files Changed:** `templates/portfolio.html`, `static/js/portfolio.js`.
* **New Contracts:** Risk simulation preview endpoint (`POST /api/v2/risk/preview`).
* **Migration Strategy:** Connect live broker account stream to UI; bind slider to dynamic risk preview.
* **Tests Required:** Slider calculation tests (asserting margin and monetary risk scale dynamically without page reload).
* **Risks:** Sizing slider flooding API with calculation requests.
* **Rollback Point:** Revert to read-only balance table.
* **Definition of Done:** Operator can adjust aggression slider and view instant preview of notional exposure and maximum loss.
* **Stop Conditions:** Slider permitting user to exceed configured risk limits.

#### Milestone M30: Research & Experiment Explorer GUI
* **Objective:** Build the Research tab displaying the Contextual Effectiveness Matrix and historical experiment logs.
* **Prerequisites:** M29 complete.
* **Modules Reused:** `domain/evaluation/experiment.py`.
* **Files Changed:** `templates/research.html`, `static/js/research.js`.
* **New Contracts:** Experiment query API endpoints.
* **Migration Strategy:** Render matrix heatmap and experiment diff viewer from database.
* **Tests Required:** Heatmap rendering tests and experiment query latency tests.
* **Risks:** Heavy queries slowing down UI.
* **Rollback Point:** Paginate and cache matrix responses.
* **Definition of Done:** Searchable, auditable research explorer accessible in browser.
* **Stop Conditions:** Query latency exceeding 500ms under load.

#### Milestone M31: Railway Production Hardening
* **Objective:** Harden multi-process deployment on Railway (Web Service + Worker Service + PostgreSQL) with production monitoring and error boundaries.
* **Prerequisites:** M30 complete.
* **Modules Reused:** Entire consolidated codebase.
* **Files Changed:** `Procfile`, `railway.toml`, `scripts/start_worker.sh`.
* **New Contracts:** Worker heartbeat and health monitoring contracts.
* **Migration Strategy:** Split background tasks into Worker dyno; run Web dyno with Gunicorn/Uvicorn.
* **Tests Required:** Health check smoke tests, simulated network outage recovery tests, and memory leak soak tests.
* **Risks:** Process desynchronization between web and worker dynos.
* **Rollback Point:** Roll back to single-service container.
* **Definition of Done:** Web and Worker dynos operating cleanly on Railway; automatic recovery from simulated network drops.
* **Stop Conditions:** Any unhandled worker crash or database connection exhaustion.

#### Milestone M32: Extended Evidence-Based Demo Validation
* **Objective:** Execute an extended, evidence-based validation run in IG Demo mode evaluated against a formal `StrategyTarget`.
* **Prerequisites:** M31 complete.
* **Modules Reused:** `domain/evaluation/target.py`.
* **Files Changed:** Validation report in `analysis/results/demo_validation/`.
* **New Contracts:** None.
* **Migration Strategy:** Run system in `ASSISTED` mode on IG Demo; log every decision, execution, and reconciliation.
* **Tests Required:** Validate that target trade count, session count, regime coverage, and zero risk violations are achieved.
* **Risks:** Experiencing market regime not covered in backtests.
* **Rollback Point:** Pause execution and review attribution.
* **Definition of Done:** StrategyTarget criteria fully satisfied based on empirical Demo trading evidence.
* **Stop Conditions:** Strategy violating drawdown or risk limits during Demo execution.

---

### Phase 6: Automation Modes, Autonomous Research & Live Authorization

#### Milestone M33: Ruled Auto Mode (Demo Environment)
* **Objective:** Implement `RULED_AUTO` mode on IG Demo, executing autonomously only when strict rule criteria are met.
* **Prerequisites:** M32 target criteria satisfied.
* **Modules Reused:** `domain/policy/engine.py`, `domain/risk/engine.py`.
* **Files Changed:** `domain/strategy/automation.py`, `templates/settings.html`.
* **New Contracts:** `AutomationRuleSet` dataclass.
* **Migration Strategy:** Enable autonomous order dispatch for candidates satisfying:
  $$\text{Opportunity Score} \ge \theta_{\text{auto}} \quad \text{and} \quad \text{FDR} \le 0.05 \quad \text{and} \quad \text{Regime} \in \{\text{Approved}\}$$
* **Tests Required:** Rule veto tests (asserting rule failures require manual operator confirmation).
* **Risks:** Runaway order loop during market anomaly.
* **Rollback Point:** Emergency switch to `ADVISORY` mode.
* **Definition of Done:** Safe automated order dispatch on IG Demo strictly bounded by explicit rules.
* **Stop Conditions:** Autonomous order dispatched when any rule is unsatisfied.

#### Milestone M34: Capped Auto Mode (Demo Environment)
* **Objective:** Implement `CAPPED_AUTO` mode on IG Demo, allowing autonomous trade management within a strict daily risk budget.
* **Prerequisites:** M33 complete with zero rule violations.
* **Modules Reused:** `domain/risk/engine.py`.
* **Files Changed:** `domain/strategy/automation.py`.
* **New Contracts:** `CappedAutoBudget` contract.
* **Migration Strategy:** System autonomous up to daily allocated risk budget; halts automatically if budget is reached.
* **Tests Required:** Budget depletion tripwire tests (asserting all trading halts when budget is exhausted).
* **Risks:** Intraday drawdown compounding.
* **Rollback Point:** Downgrade to `RULED_AUTO`.
* **Definition of Done:** Autonomous demo trading strictly constrained within the daily capital cap.
* **Stop Conditions:** Any order dispatched after daily risk cap is reached.

#### Milestone M35: Autonomous Research Agent Layer (Hermes)
* **Objective:** Deploy the background autonomous research agent to monitor performance, identify factor decay, and generate single-hypothesis experiment proposals.
* **Prerequisites:** M34 complete.
* **Modules Reused:** `domain/evaluation/`, `market_intelligence/`.
* **Files Changed:** `agents/hermes.py`, `workers/research_agent.py`, `test_hermes_agent.py`.
* **New Contracts:** `AgentProposal` schema.
* **Migration Strategy:** Hermes queries Timescale/PostgreSQL analytics and posts formal `Experiment` proposals to the registry.
* **Tests Required:** Sandbox security tests (proving Hermes cannot modify risk limits or dispatch orders).
* **Risks:** Agent generating ungrounded experiment spam.
* **Rollback Point:** Disable Hermes worker task.
* **Definition of Done:** Hermes autonomously identifying decaying indicators and submitting valid experiment proposals.
* **Stop Conditions:** Hermes attempting to access broker order methods or modify risk parameters.

#### Milestone M36: Separately Authorized Live Pilot
* **Objective:** Execute a tiny live pilot on an instrument selected at authorization time using strict liquidity, spread, and risk criteria.
* **Prerequisites:** All prior milestones complete, formal StrategyTarget satisfied, written operator authorization, live IG account funded with minimal risk capital.
* **Modules Reused:** `domain/broker/ig_execution.py`.
* **Files Changed:** `domain/broker/ig_execution.py` (live flag enabled), `docs/security/LIVE_AUTHORIZATION.md`.
* **New Contracts:** `LiveTradingAuthorization` record signed with cryptographic confirmation.
* **Migration Strategy:** Pilot instrument selected dynamically based on tightest spread and lowest monetary risk. Micro-lot execution only ($R_{\text{risk}} \le \text{Configured Minimum}$).
* **Tests Required:** Live micro-order placement, fill verification, and immediate broker-side stop-loss confirmation.
* **Risks:** Financial loss of live capital.
* **Rollback Point:** Trigger emergency kill-switch (`EMERGENCY_HALT = True`), immediately closing open live positions.
* **Definition of Done:** Single live micro-order executed, verified protected by broker-side stop, and reconciled.
* **Stop Conditions:** Any discrepancy between local order intent and broker live fill.

---

### Implementation Guardrail Sign-Off
* **Status:** Specifications Corrected & Approved.
* **Execution Block:** No code will be written or executed until Milestone M0 is authorized.
* **Next Action:** Await user review and authorization to begin Milestone M0.
