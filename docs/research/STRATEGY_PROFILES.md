# Strategy Profile contracts and versions

Reviewed 5 October 2026 against `domain/strategy/profile.py`, `registry.py`, `attribution.py` and `application/strategy_profiles.py`. See [current state](../CURRENT_STATE.md).

`StrategyProfile` is immutable descriptive metadata: identity/version, lifecycle, universe, decision timeframe, intended holding horizons, allowed research modes, capability states/references, limitations and navigation target. The registry resolves exact versions and pins a separate current version; it does not overwrite earlier definitions or infer a default from semantic version order.

| Profile ID | Default | Lifecycle / scope |
| --- | --- | --- |
| `jse_swing_3_5d` | 1.0.1 | ACTIVE_RESEARCH/PAPER; cash equities; default canonical workflow |
| `intraday_cfd` | 1.0.0 | DEVELOPMENT/DATA_VALIDATION_REQUIRED; no admitted intraday workflow |
| `long_term_investment` | 1.0.0 | DEVELOPMENT; intended weeks/months; investment model not configured |

Swing 1.0.0 remains the original foundation. Additive 1.0.1 wires canonical attribution. 1.1.0 adds separate cash/index-ETF technical shadow; 1.2.0 is cash-only daily policy replay; 1.3.0 is the isolated hypothesis research lane. None changes the default automatically.

Read-only API:

- `GET /api/v1/strategy-profiles`
- `GET /api/v1/strategy-profiles/<profile_id>`
- `GET /api/v1/strategy-profiles/<profile_id>/versions/<version>`

Unknown IDs/versions return 404. Responses declare read-only state and disabled Live execution; reads schedule no jobs and call no broker/provider. The dashboard Trading Strategies cards use backend capability/limitation state, not hard-coded validation claims.

New opportunity/policy/risk/paper/evaluation records retain the exact `strategy_profile_id` and `strategy_profile_version` pair through the existing persistence boundary. Missing legacy lineage remains `LEGACY_UNATTRIBUTED`; attribution does not silently mix horizons or promote evidence from another experiment. M16 StrategyTarget is an evaluation contract, not a second execution profile or risk override. No broad persistence migration was needed for this foundation.

Capability IMPLEMENTED_REUSABLE means the named component exists. It does not establish liquidity, statistical accuracy, actual account feasibility, data entitlement or permission to execute. See [Swing readiness](SWING_NARRATIVE_READINESS.md).
