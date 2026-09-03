# ADR 0007: Policy-aware specialist source catalogue

## Status
Accepted for M8 on 2026-09-03.

## Context
Named specialist/community sources differ materially in licensing, API access,
content permissions and authority. Adding opportunistic page scrapers would
create compliance risk and duplicate existing Moneyweb/SENS collectors.

## Decision
Add an explicit source-policy catalogue with independent enable flags, access
status, authority tier, minimum polling interval and provenance normalization.
Enable only the existing Moneyweb RSS and Moneyweb-hosted SENS routes. Disable
unauthenticated Reddit JSON access and require approved OAuth API access.

## Consequences
- Disabled/unlicensed sources cannot be mistaken for live integrations.
- Source policy flows into evidence metadata and the reliability registry.
- TradingView is excluded under its current non-display terms.
- API/licence/manual sources can be activated later without changing evidence
  contracts, after their access prerequisites are met.
