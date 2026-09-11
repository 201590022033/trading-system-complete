# M24 — Real-time Market Streaming

M24 is a data-only canonical streaming layer. M12A/M12B superseded the old M22
IG discovery and M23 IG history placeholders. Unfinished HR11 real-data
validation remains M25 and was not performed here.

IG's official contract uses the Lightstreamer endpoint returned by `/session`
v2, the active account identifier as user, and in-memory
`CST-<token>|XST-<token>` credentials. Price items are
`PRICE:{account}:{epic}` in MERGE mode. `IGMarketStream` provides an injectable
transport boundary with explicit mapped subscribe/unsubscribe, multiple isolated
subscriptions and bounded reconnect with restoration. LIVE is rejected.

Raw updates normalize to immutable canonical observations retaining canonical
ID, EPIC, execution/data symbol, subscription, broker, source and receipt times,
bid, ask, optional last, market status, quality, ordering and provenance. Bid and
ask remain separate. Mid uses only `(bid + ask) / 2` under
`ig-bid-ask-mid-v1`; spread is `ask - bid` and is not total execution cost.
Incomplete, crossed or nonfinite prices are rejected without fallback.

UTM epoch milliseconds normalize to UTC. Without UTM, source time stays null and
the basis is `RECEIPT_TIME_ONLY`; UPDATE_TIME is not assigned an invented date or
timezone. Source sequences are preserved if present and never invented.
Duplicate, repeated and out-of-order updates are explicit. Configurable
staleness and health distinguish LIVE, STALE, DISCONNECTED and RECONNECTING.
Errors are sanitized and reconnect attempts are bounded.

IG Demo quotes remain `RESEARCH_DATA`. Market status is preserved factually.
No candle engine was added; M8 completed-bar causality is unchanged. There is no
tick persistence or unbounded buffer. Incoming data triggers no PaperBroker
fill, opportunity, policy, risk evaluation, TradeIntent or order. Railway remains
compatible but unvalidated.

External validation was not run: credentials/production Lightstreamer transport
were unavailable to this workspace. Any later validator must be DEMO-only,
bounded by update count/time, sanitized, and disconnect cleanly.

References: [IG guide](https://labs.ig.com/streaming-api-guide.html) and
[IG reference](https://labs.ig.com/streaming-api-reference.html).
