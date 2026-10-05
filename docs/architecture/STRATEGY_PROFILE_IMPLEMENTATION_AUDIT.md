# Strategy Profile implementation audit — 2026-10-03

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

Canonical Swing remains pinned to 1.0.1 with exact new-record attribution. Separate 1.1.0 technical, 1.2.0 policy and 1.3.0 AI research do not replace M13 ranking/M14 policy/M15 veto. M16 targets are evaluation requirements, not execution approval; Live remains disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Baseline and mandate

Repository: `C:/Users/Deon/Documents/GitHub/trading-system-complete`, clean
`master`, HEAD `e98b3406a2beab18d837c2d6836484a941171803` before edits.
Safe baseline: 729 tests passed in 54.466 seconds; no provider/LLM/broker probes.
The root MASTER_VSCODE_AGENT_PROMPT is absent; AGENTS, Constitution and the
owner's attached mandate govern. Foundation is a bounded deliverable within
the sole ACTIVE operational demo workspace, not a parallel active research
milestone. Existing cost/outcome/IG validation gates remain open.

## Canonical implementation inventory

Historical completion docs sometimes say disconnected/NOT STARTED; current
runtime wiring below is established from implementation, not those headings.

| Capability | Canonical implementation / boundary | Current disposition |
|---|---|---|
| Instrument registry | `domain/registry/instrument.py`; aliases `instrument_registry.py`, `intraday_instruments.py` | Reuse identities; public catalog adds research shares, not broker contracts |
| Horizons | `domain/market_data/horizons.py`, `intraday_horizons.py`; daily ID adapter `application/opportunities/public_research.py:strategy_horizon_id` | Preserve minute/session distinctions; multi-session planning needs explicit adapter |
| Technical features | `domain/registry/feature.py`, `domain/features/technical.py`, `technical_feature_registry.py`, `research_indicators.py` | Canonical version facade plus expanded diagnostic registry; runtime screen uses momentum/RSI, not all registry indicators |
| Regime | `domain/features/regime.py`; `regime_engine.py` legacy reference | Canonical candidate used by public research; preserve legacy parity |
| Divergence | `domain/features/divergence.py` | Unweighted causal evidence; not an ensemble vote to replace |
| Feature effectiveness | `domain/evaluation/effectiveness.py`; `application/opportunities/swing_history.py`, `daily_learning.py`, `paper_loop.py:paper_feature_outcomes` | M11 causal learning; compact historical context separate from rank; outcome pools require future strategy partitioning |
| Suitability | `domain/evaluation/suitability.py` | Research vs execution dimensions; liquidity and missing contracts remain explicit |
| M13 ranking | `domain/evaluation/opportunity.py`; runtime `application/opportunities/public_research.py` | Canonical ranker with unchanged score/weights; research score is not profit probability |
| M14 policy | `domain/policy/engine.py`, `families.py`, `domain/contracts/policy.py`; daily adapter `domain/policy/paper_geometry.py` | Generic unresolved research plan vs explicit close-only simulated structural geometry; not validated intrabar stops |
| M15 risk | `domain/risk/engine.py`, `constitution.py`, `paper_sizing.py` | Final veto and separate account-aware cash/volume/fee constraints |
| M16 target | `domain/evaluation/target.py`; context/metrics `domain/contracts/trade.py`, `domain/evaluation/metrics.py` | Evaluation requirements, not trading configuration; no default passing target |
| Experiments | `domain/evaluation/experiment.py` | Exact target/metric evidence references; future strategy reference required; no optimizer |
| News/SENS / MI | `jse_adapter.py`, `sentiment_analyzer.py`, `sentiment_providers.py`, `evidence.py`, `application/opportunities/news_ingestion.py`, `application/opportunities/evidence.py`, `market_intelligence/` | Causal current attributed opinion/provenance and investigation; structured catalyst model remains future |
| Source registry | `domain/registry/source.py`, `market_intelligence/source_registry.py`, `source_catalog.py`; reliability `reliability_store.py` | Canonical policy facade over existing permitted collectors; preserve enable/access controls |
| Paper broker | `domain/broker/paper.py` | Deterministic supplied-price PAPER-only broker; no network execution |
| Durable loop | `application/opportunities/paper_config.py`, `paper_loop.py`, `paper_host.py`, `workers/paper_loop.py`, `workers/heartbeat.py` | Frozen inputs, immutable account config, transactions, scheduler/dedupe, persisted snapshots, daily bounded cron |
| Persistence | `persistence/repository.py`, `sqlite_repository.py`, `postgres_repository.py`, `jobs.py`; `runtime_persistence.py` | Both-backend parity and archive/read-through; PostgreSQL migrations explicit |
| Portfolio/journal | `connected_accounts.py`, `connected_portfolio_api.py`, `manual_demo_journal.py`, `static/js/accounts.js`, `portfolio.js` | Broker cash and self-reported journal separate from internal simulator; manual inspiration is not verified strategy attribution |
| IG boundary / Demo safety | `domain/broker/ig.py`, `ig_history.py`, `ig_state.py`, `ig_streaming.py`, `execution_safety.py`, `ig_execution.py`, `ig_demo_validation.py` | Data/read-only adapters and explicit gated Demo components; no activation in this deliverable; LIVE prohibited |
| Canonical Top 5 | `application/opportunities/service.py`, `api.py`, `app.py`, `templates/dashboard.html`, `static/js/dashboard.js` | Configured mode reads worker snapshots; unconfigured mode bounded in-process research refresh; preserve single cards/workflow |

## Ownership and conflicting concepts

`domain/strategy/profile.py` owns immutable StrategyProfile, exact
StrategyProfileRef and capability/lifecycle contracts. `domain/strategy/registry.py`
owns version definitions and explicitly pinned current versions. This belongs
neither in broker adapters, a dashboard dropdown, MarketProfile nor StrategyTarget.
`application/strategy_profiles.py` is a thin read-only discovery API.

Existing concepts retained independently:

- `market_profiles.MarketProfile/ProfileRegistry` = instrument/sector/macro
  sensitivities, not a timeframe-specific trading method.
- `intraday_profiles.IntradayProfile` = HR11 instrument/data/cost context over
  MarketProfile; its `profile_id` must NOT become `strategy_profile_id`.
- Technical/regime feature IDs and versions = formula/context identities, not
  strategy identity. `policy_family_id` = geometry family, not complete strategy.
- `PaperLoopConfig.aggression` = operator risk preference, not strategy selection.
  Its immutable account config cannot be silently extended/reinterpreted.
- Legacy `1d`, HR7–HR10 `1/3/5/20` session labels, `daily_session_eod`,
  `intraday_5m/15m/30m/60m/eod`, paper `3_sessions` and Yahoo display periods
  have different meanings. A daily bar interval is not a holding horizon.
- Generic M14 currently recognizes `daily_*`/minute horizons; the paper adapter
  explicitly requires `1d`. Intended 3/4/5-session profile declarations do not
  fix that mismatch or change execution. Long-term `weeks/months/longer` are
  declared intent only, not registered executable horizons.

The Swing card's 3–5-day intent is explicit while the reused ranking retains
one-day evidence and the configured paper model holds THREE sessions. Historical
context covers three/four sessions, not validated five-session trading. All
these limits must remain visible until an evidence-backed staged change.

## StrategyTarget relationship

StrategyProfile defines the method's scope, timeframe, supported evidence and
capabilities. StrategyTarget declares success/risk requirements for evaluating
that exact method/version; one profile can have multiple target versions/stages.
Later introduce an immutable binding containing exact profile ID/version AND
target ID/version, validating family/instrument/horizon scopes. M17 experiments
pin that binding and M18 metric context. No target thresholds, default target,
passing strategy or promotion are invented in the foundation. M15 veto remains
independent and cannot be relaxed by a target or profile.

## Attribution entry and propagation (next stage, not implemented here)

1. Resolve an exact configured profile version BEFORE universe/data acquisition
   and freeze its snapshot/hash in the research run/job input. UI selection is
   navigation only and cannot retroactively supply provenance.
2. Add optional paired strategy fields/reference to OpportunityCandidate and
   ResearchOpportunity, then M14 PolicyContext/TradePolicy, M15 evaluation and
   intent, paper order/fill/book/decision/outcome, evaluation and experiment
   records. Enforce both-or-neither and exact chain equality. Include reference
   in generated IDs, idempotency keys and snapshot lineage to avoid collisions.
3. Old records deserialize as LEGACY_UNATTRIBUTED, never default to Swing v1.
   Generic raw bars/news/source reliability need not carry a strategy label:
   shared observations are inputs; strategy-specific decisions/derived evidence
   must retain it. Prefilter M11 inputs by exact strategy version/horizon before
   hierarchical fallback, which currently can drop instrument/horizon scope.
4. New writer/readers must coexist with archived snapshots and in-flight frozen
   jobs. Do not add default config fields to the existing v3 account and trigger
   an immutable config conflict. A separately versioned model/account migration
   must retain old balances/positions rather than duplicate/reset them silently.
5. Manual journal APP_INSPIRED notes remain unverified. Any later attribution
   needs a captured immutable source opportunity reference, distinct from
   self-reported execution facts and canonical learning eligibility.

## Persistence migration assessment

Foundation requires NO migration: definitions ship with code and discovery
does not access storage. For durable attribution, plan paired additive SQLite
`0011_*` and PostgreSQL `0006_*` migrations AFTER checking existing migration
sequences. An append-only strategy-definition table should key `(id, version)`
and retain canonical snapshot/hash, no overwrite. Add nullable paired references
and indexes/constraints to strategy-produced relational ledgers where needed;
JSON `paper_records` need versioned writers/deserializers and guarded lineage,
not a bulk rewrite. Archived records stay byte-identical/read-through. Forbid
partial refs and cross-version chains; retain legacy NULL/unattributed records.
Persisted targets/experiments, currently separate reference contracts, need
their own coordinated design rather than an ad-hoc table in this foundation.
Backfill only from proven original identity; never infer Swing from ticker,
horizon, account ID or old market profile. PostgreSQL migrations remain explicit,
transactional and operator-targeted; no production migration was run here.

## Dashboard organization

Trading Strategies is a new top-level discovery tab with backend-driven cards.
Each opens exact-version detail. Swing links the ONE existing Canonical Top 5
tab, not a cloned ranker or duplicated DOM. Detail discloses current horizon and
attribution limitations. The direct Top 5 tab remains for backwards compatibility;
profile-context filtering/header comes only after authenticated provenance is
actually propagated. Intraday and Investment expose implemented infrastructure
and blockers but no trading-workflow button. Portfolio/account cash and risk
controls remain account-owned. Existing news and technical views remain shared
diagnostics; legacy HR7 remains a collapsed benchmark archive.

## Scientific and legacy boundaries

No strategy weights, rules, features, thresholds, universe, holding duration,
costs, risk controls, cash assumptions or execution flags change now. A small
account must not change scientific research ordering. M13 currently has an
instrument known-cost penalty; it is preserved, not falsely described as an
account-economics filter. A later separate feasibility result must explicitly
represent HIGH RESEARCH RANK / NOT ECONOMIC FOR CURRENT ACCOUNT with real fees,
spread/slippage/minimum lot constraints; final sizing remains M15. Preserve
legacy `signal_pipeline.py` (60/30/10-style fusion), `merged_simulation.py`
multi-agent governance, `adaptive_fusion.py`, HR9 ensemble/HR10 rejected results,
HR11 research, legacy shadow/reliability ledgers and historical artifacts as
benchmarks/research. Do not activate an old system through profile selection.

## Small reversible implementation stages and tests

1. **Foundation + shell (this deliverable)**: immutable three profiles/refs,
   exact historical version resolution, read-only list/detail API, backend
   lifecycle/capability cards, existing Swing link, truthful placeholders.
   Tests: duplicates/missing versions/current pins, immutable snapshot copies,
   no LIVE modes, placeholder workflow prohibition, discovery without DB/feed,
   unknown/old versions, 405 mutations, empty/error states, XSS escaping,
   exact version navigation, async stale-response exclusion, one canonical DOM,
   preserved ranking/legacy/paper/IG safety regression suites. Rollback removes
   the additive API/tab without touching any ledger.
2. **Attribution-only vertical slice (PLANNED)**: paired refs through M13–M15,
   paper and evaluation with both-backend migrations, immutable version
   definitions, legacy readers and isolated learner pools. Keep exact old
   ranking/risk outputs; test ID collisions, mismatch rejection, archive/retry
   compatibility, native PostgreSQL rollback/concurrency and version coexistence.
3. **Swing causal data/horizon contract (PLANNED)**: explicit liquid-cash universe,
   completed daily OHLCV availability, 3/4/5-session horizons, benchmark-relative
   evidence and structured SENS/catalysts. Reuse registry EMA/RSI/ATR/volume/
   structure capabilities, no assumed implementation from names. Test leakage,
   missing data/calendar, price discontinuities, corporate actions and costs.
4. **Swing shadow policy/evaluation loop (PLANNED)**: versioned setup/geometry,
   feasibility and risk, paper outcomes, exact-target/experiment evidence,
   cost/slippage walk-forward comparisons vs preserved benchmark. Promotion
   requires sample size, uncertainty, non-overlap, stability and negative results.
5. **Intraday or Investment investigation (DEFERRED)**: only after Swing's agreed
   acceptance gate. Intraday needs verified contract/session/depth/cost data;
   Investment needs independent fundamental/valuation/vintage datasets and
   horizons. No unvalidated reuse of Swing rules or implied live authority.

Exactly one stage is executed now. Open operational gates do not become passing
through a profile lifecycle label. Push/deployment, broker submission and any
later migration are outside this foundation's implementation acceptance.
