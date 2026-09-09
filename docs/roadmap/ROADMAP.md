# Linear Fusion Roadmap

Only one milestone is ACTIVE. Advancement requires tests, docs and a commit.

## M0 — Baseline Freeze & Verification [COMPLETE 2026-09-09]

Preparation commit `374fbae8d177b5e6da33382bcd72b2cd0a30cfed` recorded the
approved architecture and roadmap on `master`. The safe suite passed 234 tests
with Python 3.12.2 in `.venv-m0`; all 39 protected HR11 artifacts matched their
recorded SHA-256 hashes. No trading or research computation changed.
Next authorized milestone: M1 — Canonical Domain Contracts [NOT STARTED].

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
