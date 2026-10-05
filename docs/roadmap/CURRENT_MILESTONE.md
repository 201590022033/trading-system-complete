# Current milestone — B5 external-data acceptance

Date: 5 October 2026. Status: BLOCKED_EXTERNAL_DATA. Local software, reproducible examples and read-only audit delivered; no implementation milestone remains ACTIVE. B1–B4 completed in separate commits. Full engine acceptance is not claimed.

Final checks: 900 safe tests passed (86.320s), 31 added local tests, seven assertion-killed mutants, 54 protected artifacts. Synthetic equity/FX/gold cash oracles and indicator restart reproducibility passed. Existing checkout, default strategy profiles, ranking, running pipeline, schedules and broker boundaries preserved.

External gates unresolved: verified session calendars; raw OHLC/action/unit consistency; historical instrument/universe identity; point-in-time availability evidence/declared reconstruction; real costs/liquidity/fill envelope; real intraday ordering comparison; and FX/gold conversion/financing/margin/roll/product validation. Local archive audit found 883 inconsistent OHLC bars out of 5271; prior IG manifest has zero admitted intraday bars. No data was invented, repaired with display estimates or used for real-performance claims.

Stop at integration review/data evidence acquisition. See [operating guide](../research/LOCAL_BACKTEST_OPERATING_GUIDE.md) and [implementation record](../research/LOCAL_BACKTEST_IMPLEMENTATION.md). The adaptive feedback/dashboard programme has not started.
