# Paper loop repair, Gates 1–5

Authorized 2026-09-19. Starting commit: 9953a93. One active repair milestone,
with sequential checkpoints. No real broker execution or production promotion.

1. Repair Gate 1's incomplete causality, identity and display integration.
   News opinions must retain their availability/provenance; undated aggregates
   cannot become factual signals. Persisted trade outcomes are strategy evidence,
   never attributed to an individual indicator. Use the existing M11 learner and
   M13 ranker, with a separately versioned paper research evidence channel.
2. Gate 2: additive SQLite/PostgreSQL storage for immutable paper cycle inputs,
   ranking snapshots and outcomes, plus a locked account checkpoint. Use the
   existing durable worker/job claims for bounded scheduling. Persist fetched
   inputs before processing; retries use the frozen input. No weekend/calendar
   guessing: daily holding counts actual new observed complete sessions.
3. Gate 3: resolve M14 entry/stop/target from an earlier ranked opportunity and
   a later observed price, using preceding completed-close structure. Explicitly
   label this a close-observation paper model; do not invent OHLC or intrabar fills.
   Include stop, target, expiry and invalidation rules; gaps fill at observed price.
4. Gate 4: adapt the paper cash ledger to M15, with explicit configuration for
   loss/exposure limits, commission, slippage, lot units and aggression. Fully
   funded ZAR cash-equity model only. Aggression scales requested risk below hard
   limits. Account cash, reserved costs, stops and observed volume cap final size.
5. Gate 5: connect canonical ranking -> M14 -> M15 -> existing PaperBroker ->
   stop/target/expiry exits -> immutable net outcomes -> causal M11 -> later M13.
   Serialize paper state, isolate accounts, make cycles/retries idempotent, and
   expose durable read-only status/rankings through the existing API.

Verification: regression tests for unavailable/future evidence, prior versus
next observation fills, gap exits, stale prices, risk caps, low cash, kill switch,
transaction rollback, duplicate/restarted/competing workers and negative learning.
Use the repository safe test runner, block external sockets and dotenv, verify
protected artifacts. Native PostgreSQL validation uses a disposable local schema
if accessible; never migrate a remote service during this repair.

Runtime: provide a bounded CLI and heartbeat composition plus a documented paper
configuration. Configuration is explicit simulation capital/assumptions, not a
claim about a real account or executable liquidity. Missing runtime dependencies
must yield a visible unavailable state. No deployment or push before verification.

Gate 2 foundation: transactional account checkpoints, immutable inputs/outcomes,
bounded indexed reads and idempotent scheduled jobs pass both SQLite and the
PostgreSQL behavioral fixture. Complete outcome processing awaits Gate 5.

Gate 3: paper-close-structure-v1 resolves entry on a later complete observation,
preceding 20-close structural stop, configured 2R target, one observed-session
exit and maximum elapsed-time expiry. This is a disclosed paper execution model,
not an optimized strategy or an intrabar stop guarantee. Focused policy/risk
regressions pass. No production/default M14 policy behavior changed.

Gate 4: explicit PAPER configuration feeds M15 from the paper ledger. The
adapter applies whole-share rounding, cash with closing-fee reserves, observed
volume participation, round-trip costs and daily-loss headroom after M15 approval.
Aggression scales requested risk by 0.5/0.75/1.0 and cannot enlarge a hard limit.
The example capital, costs and fully funded unit contract are simulation
assumptions; no real broker cash, margin or liquidity is inferred. Tests cover
caps, depleted cash, missing volume, daily losses and the kill switch.

Gate 5: the existing PaperBroker now restores durable checkpoints. One account
transaction closes observed positions, saves net outcomes, consumes causal M11
strategy effectiveness, ranks through M13, evaluates earlier proposals through
M14/M15 and commits fills, account state and ranking together. The configured
web API and both opportunity displays read that committed ranking, without the
retired scanner or in-memory fallback. Pause blocks entries, not risk-reducing
exits. Policy and durable fill record IDs are account-scoped.

Acceptance: focused paper/storage/causality tests pass on SQLite and the
PostgreSQL behavioral fixture. Native PostgreSQL 18 in a disposable loopback-only
cluster passes additive migration, competing exactly-once entry, failed-cycle
rollback, outcome, re-migration and separate-process recovery. Repeated native
validation exposed a cross-account exit-fill ID collision; account-scoped record
IDs and a two-account close regression correct it. No existing DB was migrated.

Full safe suite: 664 tests passed with sockets and dotenv disabled. All 54
protected artifacts match their manifest/baseline. JavaScript syntax and diff
whitespace checks pass. Provider probes, paid AI, live broker calls, remote
deployment and profitability tests were not run. See PAPER_LOOP_RUNBOOK.md for
activation steps and exact remaining scope boundaries.
