# ADR 0022 — Standard Bank ViewPoint prepare-only boundary

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
