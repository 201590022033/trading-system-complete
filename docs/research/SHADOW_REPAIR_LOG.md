# Shadow-learning forensic repair log

Baseline: `ea3f3a7ef229f333832d2b68ebd7b3370d117379`. Local repairs only; no push
or deployment is authorized. One web service, one bounded worker, PostgreSQL.

## Batch 1 — causal inputs and outcomes

`OperationalIntelligence.analyze` accepts an optional as-of and observation
history context. It retains the existing scoring formula and default UI path.
Historical rows must have both event and availability timestamps at/before the
cutoff. Live/news retrieval is forbidden for as-of assessment. Missing causal
news remains unavailable. Research metadata is not a scoring input. Shadow
records retain component provenance and gates.

Shadow's default horizon is `5` (five supplied trading sessions), not the UI
label `swing`. Daily horizons use the existing 1/3/5/20 session definitions;
intraday uses the existing horizon/session resolver. Callers must supply the
complete versioned session sequence; there is no inferred holiday calendar.
Missing sessions, unsupported horizons and crossing a break fail closed.

Labels require exact entry/target price timestamps and causal availability.
Missing or stale prices produce `OUTCOME_DATA_UNAVAILABLE`, never zero prices.
Raw forward return is passed once to the existing `signal_outcome`, including
previous-position turnover. HOLD is not counted as a losing active sample.
The `existing` cost identity denotes that helper's 10bps turnover model, not a
claim of instrument-specific executable intraday spreads/slippage.

Both repositories validate persisted ancestry, canonical maturity/evaluation,
finite prices, complete returns and matching instrument/horizon before evidence
contribution. UTC offsets normalize at contract boundaries. Additive SQLite
insert guards and PostgreSQL NOT VALID foreign keys preserve old rows while
enforcing new relationships. Legacy invalid rows are rejected on contribution;
operators must review them rather than silently relabel them.

The PostgreSQL DB-API fixture emulates insert-side FK enforcement. It does not
prove native PostgreSQL migration, timestamp or concurrency behavior. Deployment
remains blocked pending real PostgreSQL validation and the remaining repair
batches. No protected research artifacts are regenerated.

## Batch 2 — transaction and identity repairs

Explicit repository transactions now own commits; nested operations use DB-API
savepoints. Outcome+status and contribution+aggregate writes roll back together.
PostgreSQL contributions lock the aggregate row and update sample/win/loss/net
statistics. Job updates now persist their state/checkpoints on PostgreSQL.
Direct writes of unbacked adaptive aggregates are rejected.

Immutable observation/decision/outcome conflicts are errors, not silent data
replacement. Exact reruns remain idempotent. Instrument aliases and offset
timestamps normalize; new evidence/contribution IDs use structured hashed
identities. Matching pre-repair evidence keys are retained without rewriting
old data. Status timestamp comparisons explicitly cast legacy PostgreSQL TEXT
timestamps; invalid legacy timestamps require operator review, never guessing.

Failure-injection tests cover marker-before-aggregate and label-before-status,
outer rollback, nested rollback, retry, and two SQLite connections. The local
PostgreSQL fixture removes FOR UPDATE and therefore cannot prove PostgreSQL row
locking. No Docker/postgres/initdb/pg_ctl executable was found on PATH. Native
PostgreSQL timestamp/DDL/concurrency validation is pending an operator-provided
disposable local environment; no software was installed or service contacted.

## Batch 3 — composition, bounded worker and migrations

Web source/MI operations now share the selected repository's store; PostgreSQL
uses the same database through a parameterized MI adapter, not local SQLite.
Source/evidence serialization remains the established implementation. The actual
heartbeat entrypoint runs bounded durable jobs and persists heartbeats. Claims
and completion use persisted state and compare-and-swap; recovery requires lease
expiry. Missing handlers fail explicitly, with no provider or broker fallback.

Native additive PostgreSQL migrations are versioned/checksummed and run under an
explicit transaction/advisory lock. The operator command and limitations are in
`docs/operations/SHADOW_MIGRATION_RUNBOOK.md`. Web import has no database writes.
SQLite migration initialization is also serialized and atomic: the full-suite
threaded UI test exposed an executescript/version-registration race, now fixed.
Decision replay excludes volatile retrieval timestamps from immutable provenance.

No PostgreSQL migration command was run against any external database. Native
SQL validation remains pending; the emulator cannot establish PostgreSQL locks.

## Batch 4 — bounded intelligence, reliability and status

MI consumes only the configured document bound and consults the durable
content/provider/model/schema/prompt cache before text loading. Document-ID
changes retain cached analysis and add provenance aliases. Successful processing
persists a deterministic snapshot and uses the existing watchlist selector;
replays cannot duplicate snapshots. Nested malformed provider collections and
nonfinite confidence values are rejected. Audit records contain static error
categories, never raw provider exception text. Failed refresh jobs remain failed.

The runtime handler accepts an explicitly supplied approved MI provider and text
loader. No network provider is selected implicitly, and the CLI default fails
such jobs closed until the host supplies those dependencies. This is an operator
configuration requirement, not authorization for continuous LLM calls or PDF
collection. No provider was called externally during validation.

Runtime reliability now uses the configured shared repository locally and on
PostgreSQL, including source registration. The original hit-rate, mean-return
and conservative-prior rounding semantics are preserved. Tuple identities are
collision-safe; summary aggregation stays in SQL. In-memory ReliabilityStore
remains available for isolated tests. The read-only reliability route and worker
use the same persistence composition.

LearningStatus excludes future records, counts unavailable outcomes separately,
uses evaluation timestamps for labels and contribution events for adaptive
updates, and reads persisted heartbeat timestamps. Safe projections exclude
arbitrary worker payloads. Health checks schema reachability, not just URL
presence. Connection/readiness errors produce a safe unavailable response.

## Batch 5 — acceptance quality and hardening

Full deterministic acceptance runs the actual production path (a synthetic
causal BUY, not a hand-written decision) through durable jobs, pending maturity,
label, exactly one contribution and persisted status. Uninterrupted, duplicate
reruns and multiple reconstructed SQLite/PG-fixture runs produce identical
domain records. Fingerprints cover real profile registry state, production
math files and all protected artifacts, rather than constants naming output
paths. A deliberate in-memory profile perturbation is detected and restored.

Behavioral parity now includes source policies, evidence, clusters, narrative
and snapshot serialization. Crash injection and competing SQLite connections
remain part of the acceptance suite. Nested ledger payloads are frozen and
dirty/nonfinite string prices rejected. Process dotenv opt-out is authoritative
even for explicit mappings. Only the synthetic loader test fixture changed for
IG; no IG implementation or credentials changed and no external authentication
occurred. Git and Docker exclusions cover secrets/runtime state without opening
real secrets. Error-category projection also rejects untrusted exception names.

The final expanded readiness test exposed a partial legacy SQLite v4 install
missing `reliability_outcomes`. Additive migration 8 repairs that missing table
without resetting any rows. An isolated populated upgrade fixture reproduces
the defect and verifies observation survival. Health fixtures use temporary
databases rather than depending on the user's runtime database contents.
Shadow assessments do not accumulate entries in the web service's in-memory
run cache; the durable decision is the authoritative record. Default web
analysis behavior is unchanged.

Protected checks use `python -m scripts.verify_protected_artifacts`: compare
manifest SHA256, baseline/HEAD/index Git blobs and normalized Windows worktree
bytes. All 54 protected entries pass; 15 require CRLF normalization only.

### Original finding disposition

| Finding | Local disposition | Evidence/remaining qualification |
| --- | --- | --- |
| 1 | FIXED | As-of canonical production path; future-data invariance. |
| 2 | FIXED | Explicit versioned session maturity; fail-closed unsupported calendars. |
| 3 | FIXED | Raw return once, BUY/SELL/HOLD and position-transition costs. |
| 4 | FIXED | Validated ancestry, complete/finite outcomes, immutable context. |
| 5 | FIXED | PostgreSQL legacy timestamp comparisons cast explicitly; native execution pending. |
| 6 | FIXED | Aggregate and job updates actually persist in DB-API behavioral tests. |
| 7 | FIXED | Transaction ownership, injected rollback and stranded-marker recovery. |
| 8 | FIXED | Normalized logical identities, conflicts and authoritative outcome status. |
| 9 | FIXED | Shared web/worker MI, shadow, status and reliability composition. |
| 10 | FIXED | Bounded due queries, CAS claims, lease expiry, real entrypoint. |
| 11 | FIXED | Bounded MI enumeration and durable cache before extraction. |
| 12 | FIXED | Nested provider validation, safe errors and failed-job semantics. |
| 13 | FIXED | Reliability API/rounding and collision-safe shared persistence. |
| 14 | FIXED | Bounded UTC status windows, event counts, safe worker/readiness state. |
| 15 | FIXED | Tracked additive atomic migrations and explicit operator runbook. |
| 16 | TEST-GAP-CLOSED | Actual state/artifact fingerprints with perturbation control. |
| 17 | LOCALLY VERIFIED | PostgreSQL 18 at 127.0.0.1:5433 passed native write/read, rollback, separate-process verification, and repeatable migrations. Railway/native production concurrency validation remains an external deployment prerequisite. |
| 18 | FIXED | Global dotenv opt-out documented and tested with mocked secrets only. |
| 19 | FIXED | Git/Docker secret/runtime exclusions; protected artifacts unchanged. |

PostgreSQL 17 and 18 are installed locally; PostgreSQL 18 listens on port 5433.
Native local validation passed without changing project credentials or Railway.
Approved MI provider/loader host configuration remains a deployment prerequisite.
Historical M7 Railway evidence does not validate this new release. Nothing was
deployed by this repair program.

## Final local verification — 2026-09-17

- Canonical `.venv\Scripts\python.exe` unittest runner: **638 passed**, with
  external Python socket connections blocked and dotenv loading disabled.
- Windows-compatible in-memory compile: **265 Python files passed**, no bytecode
  generated by the check.
- Protected artifacts: **54/54**, no checksum failures (15 CRLF-only worktree
  normalizations). No historical artifact was regenerated.
- Working/index diff whitespace checks passed. Accumulated repair boundary scan
  covered **58 changed files**; no secret/runtime DB/PDF/broker artifacts added.
- `.env` remains ignored and untracked. Broker implementations, production
  scoring/regime/risk/cost/slippage math and protected research outputs unchanged.
- No Railway access/deployment, external IG authentication, Standard
  Bank/ViewPoint interaction, or broker action occurred. Native PostgreSQL
  validation used only the local server on port 5433.

The initial remote-tracking checkpoint remains `ea3f3a7`. Native PostgreSQL
verification is now locally complete; Railway migration/deployment and its
external health/restart checks remain intentionally unperformed.
