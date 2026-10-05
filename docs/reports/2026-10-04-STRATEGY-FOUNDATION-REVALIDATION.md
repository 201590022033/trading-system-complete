# Strategy foundation revalidation — 2026-10-04

## Current context — 5 October 2026

The original findings, test counts, deployment restrictions and planned items below belong to their recorded checkpoint. They are preserved as evidence and must not be read as today's operating instructions.

Canonical Swing remains pinned to 1.0.1 with exact new-record attribution. Separate 1.1.0 technical, 1.2.0 policy and 1.3.0 AI research do not replace M13 ranking/M14 policy/M15 veto. M16 targets are evaluation requirements, not execution approval; Live remains disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Repository and scope

Verified origin `https://github.com/201590022033/trading-system-complete.git`,
clean `master`, starting HEAD `c27488b46f79e5a29d114d0bd20e747e480da6e2`.
Remote HEAD matched before cloning into this task's isolated workspace.
The requested foundation already shipped in `27902cc`; attribution in
`781c0ab` and separate technical shadow work in `c27488b` also predate this
request. Preserve these rather than duplicate or roll them back. No new
research milestone is activated. The root MASTER_VSCODE_AGENT_PROMPT remains
absent; AGENTS, Constitution and the current owner request govern.

## Verified architecture

- `domain/strategy/profile.py` owns immutable profiles, paired semantic-version
  references and capability declarations; `registry.py` resolves exact versions
  and explicitly pins current versions. Current Swing is 1.0.1; historical
  1.0.0 and separate technical shadow 1.1.0 remain discoverable.
- Three current profiles truthfully declare Swing ACTIVE_RESEARCH_PAPER,
  Intraday DEVELOPMENT_DATA_VALIDATION_REQUIRED and Investment DEVELOPMENT.
  Placeholders allow research only and link no trading workflow. None claims
  validation or grants execution permission.
- `application/strategy_profiles.py` exposes GET list/current/exact-version
  routes without repository/provider/worker access. Dashboard template and
  `static/js/strategies.js` render backend declarations, exact detail versions,
  errors/empty states and one link to the existing canonical Top-5 workspace.
- M13 `domain/evaluation/opportunity.py` retains its research-ranking weights;
  M14 `domain/policy/engine.py` remains non-executable research planning; M15
  `domain/risk/engine.py` remains the final veto. M16 StrategyTarget is a distinct
  evaluation requirement, with explicit profile/target binding rather than
  invented default thresholds.
- MarketProfile, HR11 IntradayProfile, policy families, bar intervals and
  intended holding horizons remain different concepts. Profile navigation
  changes no runtime configuration. Current daily ranking and three-session
  paper behavior are preserved; 3/4/5-session technical shadow is separate.
- Existing attribution pins exact identity/version before acquisition and
  checks chain equality, immutable definition hashes and learner pool isolation.
  Legacy absence remains unattributed. Existing additive SQLite/PostgreSQL
  migrations predate this task; none was added or applied to an external DB.
- Canonical API uses durable worker snapshots in configured paper mode and the
  bounded research refresh otherwise. Paper loop retains PaperBroker,
  paper-policy geometry, sizing, transactions, retries and archive lineage.
  Demo submission retains explicit feature/human permission and safety checks;
  LIVE remains prohibited. Discovery cannot activate either broker path.

## Changes in this acceptance pass

Added two focused tests in `test_strategy_profiles_api.py`: every registered
exact detail version must serialize its actual declaration with disabled
execution/validation flags while DB, canonical refresh and news calls fail;
POST/PUT/PATCH/DELETE on all three discovery route shapes must return 405
without invoking the registry. Existing feature implementation was retained.
Updated current milestone memory and this report only; architecture decisions
remain ADR 0035/0036/0037. No new architectural decision or migration required.

## Verification

Baseline: 758 safe offline tests passed in 54.646 seconds using the existing
project Python 3.12 virtual environment. Default `python` was Python 3.8 and
failed at modern typing; bare Python 3.12 lacked dependencies. These were
environment failures, resolved by selecting the established project runtime.
The safe runner disables dotenv and external socket connections.

Focused profiles/attribution/M13/M14/M15/M16/Top-5/execution/Demo tests: 126
passed. JavaScript syntax and offline DOM interaction checks passed. All 54
protected artifacts match their baseline. Final full safe suite: 760 tests
passed in 53.843 seconds. `git diff --check` passed.
No browser visual QA or native PostgreSQL acceptance was performed in this
pass; no persistence implementation changed. Diff review is limited to tests
and documentation, with no ranking, risk, legacy fusion, account or broker edits.

## Remaining gates and recommended next milestone

Foundation is already implemented; attribution and core Swing technical shadow
also exist. Next recommend a bounded Swing shadow policy/evaluation milestone:
declare causal entry/stop/target/time-exit semantics, factual liquidity and
actual cost assumptions, then evaluate exact-version 3/4/5-session outcomes with
walk-forward and cost stress before any promotion. Sector/catalyst/calendar,
OST fees/spreads/cash and validated profitability remain open. Intraday real
contract/session/data/cost validation and the separate investment model remain
deferred. This recommendation is not authorization to implement those stages.

No push, deployment, LIVE enablement or external broker mutation occurred.
