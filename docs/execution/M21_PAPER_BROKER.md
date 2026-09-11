# M21 Canonical PaperBroker

M21 adds a broker-neutral `BrokerAdapter` protocol and deterministic in-memory
`PaperBroker`. The identity and mode are always `PAPER`, distinct from IG Demo,
IG Live, ViewPoint, and MT5. It performs no network calls and is not wired to the
GUI or default runtime.

Capabilities truthfully report account state, positions, preview, paper order
submission, cancellation, close, and reconciliation. Historical data, streaming,
market discovery, authentication, and amendment fail explicitly as unsupported.
The existing preview-only `PaperExecutionProvider` and real broker adapters remain
unchanged.

`CanonicalOrderIntent` is the minimum broker-neutral execution record: identity,
timestamp, PAPER broker, canonical instrument and mapping, LONG/SHORT direction,
quantity, MARKET type, optional entry/stop/target references, time-in-force,
M15 risk-evaluation reference, reversal flag, and provenance. It contains no IG
fields. PaperBroker never accepts raw opportunity, policy, or preview objects.

Every intent must match an M15 `RiskEvaluation` with `APPROVED` or `REDUCED`
status, approved size, loss budget, instrument, and quantity ceiling. Invalid
risk becomes a retained rejected order/audit event. Current unresolved M14/M15
records therefore remain non-executable; synthetic valid fixtures exist only in
tests.

Only MARKET orders are implemented. They remain `PENDING` without a supplied
matching causal `MarketObservation`; no price is generated internally. The
versioned `paper-supplied-observation-v1` model applies configured adverse
per-unit slippage, records observed and fill prices separately, and deducts an
explicit commission separately. Zero cost/slippage is allowed only when an
explicit test-fixture flag is configured. Unconfigured cost models cannot fill.

Orders use CREATED/VALIDATED/PENDING/FILLED/CANCELLED/REJECTED/EXPIRED states
(partial fills are not implemented). Positions are FLAT by absence or explicit
LONG/SHORT records with quantity, weighted entry, mark, realized/unrealized P&L,
and originating order/fill lineage. Same-direction fills increase and re-average.
Opposite orders may reduce or close, but quantities crossing through flat are
rejected: reversal requires a separate later intent.

Explicit close requires a causal observation and produces a normal audited
opposite-side fill. Only pending orders may be cancelled. Duplicate intent IDs
are rejected across active and historical orders, preventing retry duplication.

Paper account state reports starting/available cash, mark-based equity,
realized/unrealized P&L, positions, and open orders. Margin is `None` because M21
does not invent a paper margin model. Long/short cash movements, slippage, and
transaction costs are ledgered per fill.

The append-only in-memory audit trail records validations, rejections, fills,
cancellations, closes through fills, and reconciliation. Reconciliation checks
fill/order references, position/fill lineage, and cash ledger equality; it reports
discrepancies without self-healing. Durable storage is deferred rather than
creating an isolated database.

M12A and M12B supersede the roadmap's old IG discovery/history placeholders.
Remaining IG work is streaming, account/position synchronization, Demo execution,
and reconciliation. None is started here. No GUI controls, IG/ViewPoint/MT5
execution, live-mode change, or later milestone is included.
