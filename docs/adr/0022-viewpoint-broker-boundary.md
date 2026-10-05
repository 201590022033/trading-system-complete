# ADR 0022 — Standard Bank ViewPoint prepare-only boundary

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Connected IG account reads and a self-reported manual Demo journal exist, while entitlement-specific data and order safety remain separate gates. Standard Bank/ViewPoint/Shyft/MT5 are not verified automatic connections in this workflow. No research/card enables Live execution. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Status: accepted, 2026-09-06

ViewPoint is a new broker adapter behind a vendor-neutral observed-state
boundary. The surviving OST browser experiment remains historical and is not
renamed: its selectors and navigation are OST-specific, while ViewPoint
payloads, account semantics and identifiers are currently unverified.

The scaffold models accounts, cash, positions, orders, mappings and
reconciliation. Missing broker state is represented as unknown and prevents
preparation. `submit_order` always raises; the user must authenticate and
submit in ViewPoint. No credentials, captures, endpoints or selectors are
stored. Synthetic payloads, when used in tests, are explicitly test-only.
