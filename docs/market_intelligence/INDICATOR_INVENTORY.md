# Technical indicator inventory

## Current context — 5 October 2026

The original feature/profile contract below is retained as its delivery checkpoint. Existing regime and feature registries are reused. Separate Swing 1.1.0 now adds EMA20/50, Wilder RSI/ATR14, relative volume and independent 3/4/5-session labels; 1.2.0 adds cash-only daily policy replay and 1.3.0 adds bounded AI hypothesis comparisons. These are research lanes and do not change default ranking weights. Invalid OHLC, verified sector/FX/commodity context, actual event availability and prospective evaluation remain admission gates. The complete local six-family engine and 30-minute radar are proposed. See [current state](../CURRENT_STATE.md), [Swing readiness](../research/SWING_NARRATIVE_READINESS.md) and [document index](../DOCUMENTATION_INDEX.md).


---

This inventory records the repository's existing implementation; the UI does
not add or recompute technical mathematics.

| Family | Status | Evidence |
|---|---|---|
| SMA / moving averages | IMPLEMENTED | `data_pipeline.py`, legacy scorer |
| RSI | IMPLEMENTED | operational and research signal paths |
| Stochastic | IMPLEMENTED | operational and research signal paths |
| Breakout | IMPLEMENTED | operational and research signal paths |
| MACD | RESEARCH-ONLY | `research_indicators.py`, HR9 artifacts |
| Bollinger / z-score | RESEARCH-ONLY | `research_indicators.py`, HR9 artifacts |
| ATR | RESEARCH-ONLY | capability-gated research features |
| ADX / DMI | RESEARCH-ONLY | capability-gated research features |
| Relative volume / liquidity | RESEARCH-ONLY | requires volume capability |
| Ichimoku | RESEARCH-ONLY | HR5 shadow feature; not production UI scoring |
| Fibonacci | RESEARCH-ONLY | HR6 shadow feature; no automatic action |
| Candlestick patterns | RESEARCH-ONLY | HR6 deterministic shadow features |
| Hanging Man | RESEARCH-ONLY | candlestick family; no production action |

## Admission process

New indicators enter as research candidates, receive unit and causality tests,
are registered with an implementation/version and capability requirements, and
are evaluated with existing cost-aware walk-forward evidence by instrument,
horizon, profile and regime. The governance state remains
`INSUFFICIENT_EVIDENCE`, `CANDIDATE`, `VALIDATED` or `REJECTED` until evidence
supports a later `PRODUCTION_ELIGIBLE` decision. No UI or LLM can promote a
feature or alter production weights.

Unavailable indicators are shown as unavailable rather than inferred from
other values. Technical Intelligence remains an explainability surface and
does not alter signal, adaptive, regime, risk, or broker behaviour.
