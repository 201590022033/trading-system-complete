# Daily Swing shadow policy delivery — 2026-10-04

## Current context — 5 October 2026

The original findings, test counts, deployment restrictions and planned items below belong to their recorded checkpoint. They are preserved as evidence and must not be read as today's operating instructions.

Railway now hosts durable shared paper/research state and a bounded 08:00 SAST scheduled worker. Local daily collection is at 07:30 SAST. Earlier non-deployment statements are checkpoint-specific; new research records reuse the append-only ledger without a broad strategy migration. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

## Scope and repository

Owner authorized the daily Swing shadow policy and deterministic entry/exit
simulation described in the preceding chat. Work began on clean local `master`
at `f0f17f075c3547585d7cba90e0a2da9ae97a0f87`, origin
`https://github.com/201590022033/trading-system-complete.git`.
Baseline: 760 safe tests passed in 54.464 seconds. Reused the established
Python 3.12 project environment; safe runner disables dotenv and external
sockets. The implementation remains local, with no push or deployment.

## Delivered

- Separate cash LONG StrategyProfile 1.2.0 (RESEARCH/SHADOW) and policy
  `swing-daily-shadow-policy-v1`. Current benchmark pin stays 1.0.1; all five
  previous profile snapshots are unchanged. Reuse 1.1.0 causal technical
  calculations/core conditions; ETFs keep their separate technical research.
- Complete/no-setup/blocked decision states; later observable close entry
  within seven calendar days; entry-bar stop invalidation; fixed preceding
  structural/ATR stop; entry-based 2R target; no trailing; conservative stop,
  target, gap and ambiguous-bar handling; independent 3/4/5 observed-session
  exits. Timing is a research proxy, not an executable quote/fill claim.
- Gross payoff/R and hypothetical all-in 10/25/50 bps cost scenarios. No actual
  OST cost claims or implicit risk approval/account sizing.
- Exact definition/rules frozen before new acquisition; append-only policy
  decisions, entries, observed bars and terminal outcomes use existing paired
  references and ledger transactions. Source features remain 1.1.0. Hashes and
  IDs preserve lineage/retry; old frozen jobs opt out. Original entry/path bars
  survive price revisions; missing or inserted historical bars cannot silently
  change the observed sequence. Existing account state/configuration is intact.
- Read-only paper status/Portfolio display separately exposes counts, negative
  outcomes, ambiguity and assumed cost stress. Existing current cards, Top-5
  ranking, paper broker, M15 and Demo/LIVE boundaries remain unchanged.

ADR 0038 records exact rules, timing, conservative assumptions, reuse boundaries
and the unresolved feasibility gates. No new persistence schema or migration,
bulk historical backfill, M11/ranking learning input or broker endpoint.

## Validation and review

13 focused new policy tests cover 3/4/5 maturity, pending/open states, no
lookahead, stop/target/time precedence, gap losses, ambiguity, entry invalidation,
expiry, malformed data, source/version/rule rejection, no-setup/blocked states,
both-backend fixture restart/idempotency/rollback, provider price revisions,
missing/inserted history, old-job/ETF exclusion and benchmark equality.
The vertical comparison proves identical ranking, account state and paper-cycle
result with/without the new shadow input. The existing worker test checks
pre-acquisition freezing, cash-only decisions and retry without reacquisition.

Final focused regression group: 97 tests passed in 3.229 seconds. Portfolio
JavaScript syntax and existing offline strategy UI harness passed. All 54
protected artifacts match baseline; git whitespace checks passed. Full final
safe suite: 773 tests passed in 54.704 seconds. An intermediate full run caught an observation scan over
the ledger's 5,000-row bound; replaced it with six deterministic observation-ID
lookups per unfinished decision. No ledger limit was relaxed.

Reviewed all changes for trading regressions, version rewrites, retrospective
selection and external mutations. No weight/threshold/default paper behavior,
legacy fusion or broker gate changed. Native PostgreSQL acceptance and browser
visual QA were not run; PostgreSQL behavior uses the repository's DBAPI fixture.
Offline synthetic tests are correctness evidence, not strategy-performance
or deployment evidence.

## Files changed

- `domain/policy/swing_shadow.py` — rules, causal policy and OHLC replay.
- `domain/strategy/registry.py` — separate version, unchanged current pin.
- `application/opportunities/swing_policy.py` — append-only shadow orchestration.
- `application/opportunities/paper_host.py` — frozen definition/status exposure.
- `application/opportunities/paper_loop.py` — separate shadow sidecar summary.
- `static/js/portfolio.js` — truthful descriptive policy results.
- `test_swing_policy.py` — adverse-path, storage and benchmark regression tests.
- `test_swing_technical.py` — worker freezing/cash-only/retry checks.
- `test_strategy_profiles_api.py` — new exact version discovery expectation.
- `docs/adr/0038-daily-swing-shadow-policy.md` — architecture/timing decision.
- `docs/architecture/CURRENT_ARCHITECTURE.md` — observed implementation.
- `docs/roadmap/ROADMAP.md` and `CURRENT_MILESTONE.md` — milestone memory.
- This report — acceptance evidence and remaining gates.

## Remaining gates and next milestone

The daily policy simulator is implemented. It has no validated trading edge,
real account feasibility, M15 approval or executable portfolio allocation.
Verified exchange-session continuity, corporate-action quality, liquidity,
sector/catalyst/event data and actual fees/spreads/slippage remain unresolved.
No missing values were invented. Independent overlapping horizon observations
cannot be counted as independent trades or portfolio returns.

Next recommend a bounded evaluation milestone: freeze a point-in-time dataset
and declared costs/universe, choose chronological walk-forward splits and
non-overlapping allocation rules before measuring performance, compare this
exact policy/version against the unchanged benchmark/cash, and report sample
counts, uncertainty, drawdown and cost/period sensitivity. Collect native
PostgreSQL and browser acceptance evidence before operational deployment.
Promotion and broker execution require separate evidence/authorization.
