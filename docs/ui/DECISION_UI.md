# Decision dashboard — current user-facing behavior

Reviewed 5 October 2026. [Current state](../CURRENT_STATE.md) is the capability snapshot. Earlier UI designs and mock-price descriptions are retained in [the previous UI document](../history/DECISION_UI_PRE_2026-10-05.md).

| Section | What the user sees | Truthfulness boundary |
| --- | --- | --- |
| Portfolio & demo | Durable paper account, separate connected balances, controls, printable worksheet, manual Demo journal | Simulator capital is not available cash; journal capture is self-reported |
| Trading Strategies | Backend registry cards and current capability/limitation state | Clicking does not activate rules/orders; two profiles are development placeholders |
| Canonical Top-5 | Committed M13 canonical opportunities with policy/risk context | Read-only refresh; unavailable/stale evidence is visible |
| Market AI / News | Source feeds, sentiment context, source controls, Monday brief and research cases | Briefs are unverified leads; corroboration gates attention flags |
| Technical Intelligence | Public chart/technical context and data-quality diagnostics | Estimated bars are explicit display-only; no validated entry-refinement claim |
| System | Health, persistence and operational state | Service health is not strategy performance |

Public quotes/charts are now backed by cached provider reads, not the old blanket random-walk description. Canonical ranking remains separate from legacy diagnostic analyses. Printable worksheets leave actual execution details for the operator to record, and do not submit orders.

Existing Portfolio controls unlock protected journal/brief imports. Read-only profile/status endpoints need no broker mutation. IG connected balances distinguish Demo/Live and original currency with dated conversion. No card, news flag, estimated price or aggression control may override risk veto or enable Live execution.

Weekly research displays import time, model/scan state, referenced publisher cases and waiting/failure states. The first two accepted cases were single-publisher and earned zero boosts/flags. The future local six-hypothesis/radar workflow needs its own interface milestone; it is not already hidden behind the cards.
