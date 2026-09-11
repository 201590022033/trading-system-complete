# M19 Canonical Opportunity / TradeIntent API

M19 adds a framework-neutral `OpportunityService` and a thin read-only Flask
adapter. The service consumes injected canonical M13 `ResearchOpportunity`, M14
`TradePolicy`, and M15 `RiskEvaluation` records; its default source is empty, so
it never fabricates production opportunities or scrapes dashboard state.

The following routes coexist with all legacy endpoints:

- `GET /api/v1/opportunities[?limit=N]`
- `GET /api/v1/opportunities/<opportunity_id>`
- `GET /api/v1/opportunities/<opportunity_id>/policy`
- `GET /api/v1/opportunities/<opportunity_id>/risk`
- `GET /api/v1/opportunities/<opportunity_id>/intent`

Top-N orders by canonical rank and returns fewer records when fewer exist. IDs
are source IDs, never array indexes. Opportunity responses retain rank,
`ranking_score`, direction, evidence/suitability, uncertainty, reasons, blockers,
timestamps and version provenance. The score semantic is always “comparative
research score; not probability of profit”; no probability/confidence-percent
alias is emitted.

Policy serialization preserves entry, invalidation, target/exit and stop states.
An absent stop is explicitly `UNRESOLVED` with null distance/price. Risk output
preserves M15 status and null approved size; failure is never converted into a
positive presentation state.

`TradeIntentPreview` is an immutable, non-executable planning DTO. It references
opportunity, policy and risk identities plus factual broker mapping, direction,
entry, stop, risk, exit, invalidation, blockers and provenance. Readiness is one
of `READY_FOR_PREVIEW`, `NOT_READY`, `BLOCKED`, or `UNRESOLVED`. Current M14
policies have no stop and therefore remain unresolved. Even ready previews carry
`executable: false`; no generic or broker-native `OrderIntent` is created.

Serialization is explicit rather than `__dict__`-based, converts enums and aware
timestamps predictably, retains nulls, and excludes credentials, tokens, headers,
cookies, and account secrets. Structured errors use 404 for unknown opportunity,
409 for unresolved intent prerequisites, 422 for invalid query input, and 503
for unavailable upstream policy/risk state.

Existing `/api/opportunities` and operational dashboard routes remain
`LEGACY / NON-CANONICAL` and unchanged. M19 does not switch the production GUI,
activate paper routing, call IG dealing endpoints, submit orders, mutate
positions, or enable runtime execution. M20 GUI consumption and later order
contracts remain deferred.
