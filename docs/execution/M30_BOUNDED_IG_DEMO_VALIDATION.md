# M30 — Bounded IG Demo Execution Validation

## Outcome

M30 implementation is complete as a manually invoked, two-phase IG Demo
validation boundary. Phase A was validated locally. Phase B was not authorized,
so no external order or other broker mutation was performed.

M25 empirical HR11 validation remains **INCONCLUSIVE / EXTERNAL RUN PENDING**.

## Two-phase boundary

Phase A constructs the exact M29 payload from an isolated synthetic chain and
reports what would be sent. Its default is non-mutating and reports
`NOT_AUTHORIZED`. Credentials, an enabled adapter, or coding authorization do
not grant Phase B permission.

Phase B requires `external_demo_order_authorized=true` in a separately assembled
factual plan. The safe status CLI deliberately cannot construct that plan or
submit an order. Before the one permitted mutation, the harness re-reads the
exact Demo account and positions, requires an enabled account, verifies the
position count has not changed, and reruns M27. A critical reconciliation result
fails closed.

## Synthetic fixture and factual inputs

The fixture label is exactly `M30 DEMO VALIDATION FIXTURE`. It carries matching
canonical intent, M15 APPROVED/REDUCED risk, resolved stop, approved loss budget,
M28 PASS, instrument mapping and version provenance. It is operational test data,
never research evidence, and does not modify ordinary M13–M15 records.

An eventual Phase B operator must obtain these facts immediately before use:

- exact enabled IG Demo account;
- one exact permitted EPIC and canonical mapping;
- `TRADEABLE` market status and a quote inside the configured freshness limit;
- broker minimum deal size, used without scaling;
- a correctly oriented stop satisfying current broker distance constraints and
  the approved-risk fixture;
- readable account and position state, a clear kill switch, a deliberate
  execution flag, explicit human Demo permission, and M27 with zero critical
  discrepancies.

No instrument, EPIC, size, stop, or market status was claimed in the checked-in
Phase A artifact because no external factual preflight was run. Existing Brent
mapping is only a candidate and must not be treated as interchangeable with
another Brent product.

## Mutation, confirmation, and readback

The harness permits at most one opening mutation in one process. M29's
idempotency remains process-local: do not use multiple workers, Railway,
concurrent attempts, or a process restart during submission. A timeout,
transport interruption, malformed acknowledgement, or uncertain confirmation
becomes `UNKNOWN_OUTCOME`; it is never retried.

Request transmission, HTTP acknowledgement/deal reference, confirmation status,
broker reason, and deal ID are recorded separately. After submission the harness
only reads account and positions through M26 and runs M27. A newly visible
broker-only position may be reported as a discrepancy; nothing is fabricated or
auto-repaired.

Opening permission never grants closing permission. There is no close operation
in the harness and no automatic cleanup.

## Output and artifacts

`python -m scripts.m30_demo_validation` is the safe local command. It reports
`EXTERNAL MUTATION: NOT PERFORMED` semantically. Supplying its authorization flag
exits with an error because Phase B requires a separately controlled factual
plan; this prevents a bare CLI switch from becoming an order button.

The append-only manifest is
`artifacts/execution/m30_demo_validation/run_manifest.json`. Reports contain only
safe operational identity, masked account identity, payload fields, bounded
status/readback/reconciliation summaries, warnings, authorization state and the
unknown-outcome flag. Secrets, session tokens, cookies and auth headers are
excluded.

## Guarantees and limitations

- DEMO identity is enforced before M29 request mapping; M29 itself has no LIVE
  construction path.
- No GUI control or streaming-to-submission orchestration was added.
- No external broker path was exercised in this workspace.
- Current market metadata, minimum size, stop constraints, account eligibility,
  and post-submit propagation remain externally unverified.
- Durable distributed idempotency and any separately authorized close validation
  remain outside M30.
