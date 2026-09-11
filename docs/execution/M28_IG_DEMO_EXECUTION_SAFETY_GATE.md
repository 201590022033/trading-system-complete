# M28 — IG Demo Execution Safety Gate

M28 is an immutable authorization-checking layer. It answers whether every
declared prerequisite for a future IG Demo submission is satisfied. A PASS means
only “eligible for a later submission attempt”; this module has no transport,
broker payload, order call or execution authority.

`ExecutionSafetyContext`, `ExecutionSafetyConfig`, `ExecutionSafetyCheck` and
`ExecutionSafetyDecision` preserve decision identity, time, account, intent,
every check, deterministic blocker and provenance. Individual states are PASS,
FAIL, UNRESOLVED or NOT_CONFIGURED. Every mandatory check must PASS before the
derived boolean can be true; later facts create a new immutable decision.

The gate requires exact `broker=IG` and `environment=DEMO`. The execution flag
defaults disabled, and human permission is separately explicit; neither an AI
recommendation nor risk approval can grant it. The existing adapter capability
remains false, so repository state cannot currently pass.

The causal identity/version chain must align opportunity → policy → M15 risk →
intent/order-intent. M15 must be APPROVED or REDUCED with positive approved size
and loss budget. M14 must be ready for risk review with resolved stop price and
distance. Current unresolved M14/M15 records remain non-executable.

A factual enabled account, matching account ID, fresh M26 snapshot and available
positions response are mandatory. Zero positions passes availability; endpoint
failure does not. Exact canonical ID/execution symbol/EPIC identity is required.
No fuzzy mapping exists.

Market state must be TRADEABLE and quote freshness explicit. M27 reconciliation
must exist with no critical discrepancy; whether warnings block is configured,
never assumed. Stable intent identity must not already be pending/accepted.
Opposing or unresolved exposure fails; same-direction exposure requires an
explicit blocking policy. Reversal is never netted or silently permitted.

An active kill switch fails and an unknown switch is unresolved. Currency must
match or have explicit FX evidence. Required margin metadata must be factual;
available cash is not substituted. Deterministic blockers are produced without
LLM text.

No Flask route or GUI control was added. External read-only evaluation was not
run because credentials are unavailable. A future check may retrieve account,
positions, market metadata and reconciliation, but must make no POST/PUT/DELETE
request. With current unresolved M14 stop geometry and disabled capability, its
expected result is FAIL/UNRESOLVED.

M25 external empirical HR11 validation remains pending/inconclusive.
