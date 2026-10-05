# ADR 0035 — Versioned trading strategy profiles, foundation first

## Current context — 5 October 2026

This is a dated decision record. Its original rationale/status is retained; it is not a complete current capability inventory. Later additive decisions and the current snapshot determine deployed scope.

Canonical Swing remains pinned to 1.0.1 with exact new-record attribution. Separate 1.1.0 technical, 1.2.0 policy and 1.3.0 AI research do not replace M13 ranking/M14 policy/M15 veto. M16 targets are evaluation requirements, not execution approval; Live remains disabled. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Accepted 2026-10-03 under the owner's architecture mandate; bounded delivery
within the sole active operational demo workspace. See the complete
[implementation audit](../architecture/STRATEGY_PROFILE_IMPLEMENTATION_AUDIT.md).

Add an immutable domain `StrategyProfile` and exact `(strategy_profile_id,
strategy_profile_version)` reference, with explicit strategy family, universe,
decision timeframe, intended holding horizons, lifecycle/capability declarations
and limitations. Keep MarketProfile, HR11 context profiles, policy families,
operator aggression and StrategyTarget distinct. Registry definitions cannot
overwrite the same identity/version; current versions are explicitly pinned,
not inferred from lexicographic version order. Future writers must pin the exact
reference before generating evidence, not resolve "current" when reading history.

Register JSE Swing Trader 3–5 Day (active research/paper direction), Intraday CFD
(development/data validation) and Long-Term Investment (development). Lifecycle
means declared development priority, not validated profitability or execution
permission. All responses disclose foundation-only attribution and disabled
strategy execution/LIVE. No LIVE mode can be declared in these contracts.

Expose read-only list/current/exact-version discovery, with no DB, provider,
worker, broker or LLM invocation. Add Trading Strategies cards driven by those
DTOs. Swing links the existing canonical Top 5 workspace; no duplicate scorer,
DOM, account state or generated recommendation. Placeholders link no trading
workflow. The existing one-day ranking/three-session paper horizon mismatch is
visible and preserved for a separately tested change.

No schema migration or historical relabelling occurs now. Attribution through
M13–M16, durable paper and learning is the NEXT planned vertical slice, with
nullable legacy readers, chain equality, IDs/idempotency namespaces, exact
version pool isolation and explicit both-backend migrations. StrategyTarget
remains an evaluation requirement object referenced by a later exact-version
binding; it is not a trading profile or runtime gate.

No optimized weights, new technical signals, risk changes, fees, account sizing,
portfolio writes, broker activation or automatic promotion. Existing cost/
data/validation limitations remain explicit. Rollback is removing the additive
discovery API/tab; existing ledgers and trading outputs are unchanged.
