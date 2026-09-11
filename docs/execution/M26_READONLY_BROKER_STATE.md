# M26 — Read-only Broker Account and Position State

M26 adds an immutable broker-neutral snapshot boundary and a GET-only IG Demo
service. It calls only `/accounts` v1 and `/positions` v2 after the existing M12A
session. No POST, PUT or DELETE route exists in the service, and all IG execution
capabilities remain false.

`BrokerAccountState` preserves broker/environment/account identity, name, type,
preferred/status/enabled state, account currency, broker balance, available
funds, deposit and profit/loss. Equity, unrealized P&L and margin fields remain
null when `/accounts` does not supply them. Balance is never equated to equity;
IG documents balance, available, deposit and profitLoss as distinct values.

`BrokerPositionState` preserves deal ID, EPIC, LONG/SHORT direction mapped
explicitly from BUY/SELL, positive broker quantity, opening level, optional stop
and limit, contract size/currency, opened time and factual market status. The
current close-side indicative level is bid for LONG and offer for SHORT; it is
not a fill or valuation guarantee. Unrealized P&L is retained only if IG supplies
`profitLoss`/`upl`; it is not calculated. Products remain EPIC-specific.

Explicit supplied `IGMapping` records resolve canonical IDs. Unknown EPICs stay
in the snapshot with `UNRESOLVED_INSTRUMENT_MAPPING`; no closest-symbol guess is
made. `BrokerStateSnapshot` distinguishes a successful empty positions response
(`positions_available=true`, count zero) from an endpoint exception.

Every record includes endpoint/version, normalization version and timezone-aware
retrieval time. A caller must configure a positive staleness threshold; snapshot
freshness is FRESH or STALE. State is transient and no historical database was
created.

IG state (`broker=IG`, `environment=DEMO`) is not a `PaperAccount`, ViewPoint
state, legacy CSV/dashboard portfolio, cached application portfolio or M15
`PortfolioRiskState`. Nothing overwrites or merges those stores. M26 performs no
FX conversion, risk sizing, approval, reconciliation mutation or GUI integration.
Read-only API exposure is deferred because the canonical service can be added to
M19-style routes later without placing provider normalization in Flask.

External validation was not run because credentials are unavailable in this
workspace. A future bounded check may authenticate, call the two GET endpoints,
mask account IDs in display output, report whether zero positions is available,
and end. It must never print session credentials or call dealing endpoints.

M25 external empirical HR11 validation remains pending and inconclusive until a
real dataset and factual session/calendar context are supplied.

References: [IG REST guide](https://labs.ig.com/rest-trading-api-guide.html) and
[IG REST reference](https://labs.ig.com/rest-trading-api-reference.html).
