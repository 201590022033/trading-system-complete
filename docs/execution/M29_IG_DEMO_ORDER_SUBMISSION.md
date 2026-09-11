# M29 — IG Demo Order Submission

M29 adds an explicitly invoked IG Demo-only submission adapter. Coding this
boundary did not authorize an external order, so none was sent. The adapter
cannot be constructed for LIVE and validates environment before building a
mutation request.

Every request contains a canonical `OrderIntent`, immutable M28 PASS decision,
and matching M15 `RiskEvaluation`. Account, order/intent, instrument, EPIC,
policy, risk evaluation and opportunity/policy/risk/intent versions must match.
The execution flag defaults false and independent human Demo permission defaults
false. Current unresolved M14 stop/M15 state cannot submit.

Only MARKET is supported. The adapter maps exact EPIC, BUY/SELL direction and
the exact approved M15 size to IG `/positions/otc` v2. Size must equal—not merely
fit beneath—the approval and is never rounded or recalculated. Stop level must
equal the approved risk stop. Expiry and force-open semantics must be explicitly
supplied. M29 supports only non-guaranteed stops. Currency is omitted when
unavailable; price, limit, distance, trailing and other fields are not invented.

Stable submission identity derives from OrderIntent identity. States distinguish
pending, request accepted, broker confirmed, broker rejected and unknown outcome.
Once any mutation attempt begins, that OrderIntent is retained and cannot be
retried. Network failure, malformed/unknown response or server failure after send
becomes `UNKNOWN_OUTCOME`; there is no automatic mutation retry.

HTTP acceptance must include IG's deal reference but is not confirmation. The
adapter performs one read-only `/confirms/{dealReference}` v1 lookup. ACCEPTED
becomes broker-confirmed, REJECTED retains the broker reason, and pending or
unavailable confirmation remains request-accepted. Deal reference and supplied
deal ID are distinct from internal IDs. No fill price, position, or internal
portfolio state is fabricated. Later state comparison remains M27's job.

The in-memory append-only audit records request, safety validation, idempotency,
mutation attempt, broker response, confirmation, rejection or unknown outcome.
Configured credentials and session tokens never enter results or audit details.
Durable cross-worker idempotency is not implemented and is a material limitation
before deployment.

Capabilities report `demo_order_submission=IMPLEMENTED_DISABLED` while ordinary
`order_submission` remains false. No Flask route, GUI button, stream trigger,
opportunity orchestration or LIVE path was added.

External Demo submission: **NOT RUN — EXPLICIT ORDER TEST AUTHORIZATION NOT
PROVIDED**. A later single-order test requires a separate direct operator command,
valid exact Demo state, deliberate flags/permission and an M28 PASS decision.

M25 external empirical HR11 validation remains pending/inconclusive.

Official contract references: [IG REST reference](https://labs.ig.com/rest-trading-api-reference.html)
and [IG trading basics](https://labs.ig.com/trading-basics.html).
