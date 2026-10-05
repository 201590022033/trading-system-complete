# Swing strategy readiness — implemented research versus evidence gaps

Reviewed 5 October 2026. The intended holding window is 3–5 observed trading sessions. A profile name does not make all existing one-day ranking evidence a five-day policy. See [current state](../CURRENT_STATE.md) and [the original readiness checkpoint](../history/SWING_NARRATIVE_READINESS_PRE_2026-10-05.md).

| Element | Current implementation | Remaining gate |
| --- | --- | --- |
| Canonical ranking/policy/risk | M13/M14/M15, default profile 1.0.1; attributed new paper evidence | Real liquidity/account feasibility and validation |
| Daily technical indicators | Separate 1.1.0 EMA20/50, Wilder RSI/ATR14, prior-volume and structure; 3/4/5-session labels | Admissible OHLCV; sector-aware evidence; indicator effectiveness |
| Entry / stop / target | Separate 1.2.0 cash LONG replay; later completed close, fixed structure/ATR stop, 2R target | Actual fill/spread/fees, exchange calendars and corporate actions |
| Volume | Prior-real-session daily relative volume and paper capacity constraint | Verified share-volume quality and same-slot 30-minute source |
| Exit | Independent 3/4/5-session replay exits; ambiguous bars stop-first, conservative gaps | Prospective testing; executable portfolio and trailing research |
| AI hypothesis comparison | Separate 1.3.0 bounded cloud proposals and chronological replay | Zero closed first holdout samples; prospective walk-forward evidence |
| News/event context | Existing feeds; manual Monday briefs; local Ollama cases and gated archive screen | Historic SENS/economic retrieval, publication availability, independent sources |
| Six hypothesis families | Documented owner proposal | Local engine, dated universe/benchmarks, testable frozen contracts |

Daily replay costs of 10/25/50 bps are hypothetical sensitivity scenarios, not broker quotes. The policy does not authorize trading or override M15. Index ETFs are included in 1.1.0 technical research but not the 1.2.0 cash policy.

Some real closes remain usable for older ranking while invalid OHLC blocks ATR/structure replay. Estimated bars are labelled display-only and cannot unblock admission. IG login works but the tested JSE history request is not entitled; Alpha Vantage probes did not verify coverage. Do not claim the missing data has been solved.

No winning-indicator, accuracy or profitability claim is supported yet. Next: freeze the [six hypotheses](SIX_SWING_HYPOTHESES.md), establish real daily/optional intraday data admission and dated event contracts, then implement local causal backtests and controls before promotion.
