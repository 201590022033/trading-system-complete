# Technical indicator inventory

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
