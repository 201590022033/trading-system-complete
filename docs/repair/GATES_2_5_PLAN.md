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
