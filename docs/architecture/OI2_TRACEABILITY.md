# OI2 Requirement Traceability

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

The current dashboard has six sections including backend-populated Trading Strategies and the canonical Top-5. Older multi-agent/mock/merge designs remain historical context; they do not describe the default ranking path. Paper/connected cash and self-reported trades stay separate. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

| Requirement | Implementation | Verification |
|---|---|---|
| Canonical identities | `instrument_registry.py` | Alias tests |
| Run/component contract | `operational_intelligence.py` | API and partial-state tests |
| Real legacy benchmark | HR7 history + `legacy_technical_score` | Legacy/OI2 tests |
| Exactly 30 gates | `confidence_gates.py` | Count and result tests |
| Separate operations | market/technical/news/analysis/scan routes | Flask client tests |
| Maintainable UI | template, CSS and JavaScript assets | page hierarchy test |
| Research isolation | research endpoint and non-actionable decision | safety tests |
| No live orders | rejecting manual route, disabled UI | 409 boundary test |
| Graceful degradation | explicit `UNAVAILABLE` and `PARTIAL` | missing-news test |
| Runtime proof | local port 5055 health and SOL analysis | HTTP 200 smoke |

The current-public network smoke was not required to establish offline
operation. Network retrieval is explicit in the UI and reports provider failure
without substituting mock evidence.
