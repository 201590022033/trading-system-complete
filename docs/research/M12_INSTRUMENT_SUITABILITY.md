# M12 — Instrument Selection & Suitability Learning

## Status

**COMPLETE — 2026-09-09**

M12 adds a canonical suitability evaluator around the existing HR11
`InstrumentDefinition` registry and M11 effectiveness records. It does not
create a second identity system or rank current opportunities.

## Contract and eligibility

`InstrumentSuitability` reports separate hard eligibility, research suitability,
execution suitability, data, cost, liquidity, feature-evidence and regime
coverage states, plus history depth, samples, stability, blockers, reasons and
provenance. Hard eligibility is evaluated before soft evidence and cannot be
outweighed by a score. Manual blocks, missing permission, unsupported horizons,
missing data and required execution metadata produce explicit blockers.

Research suitability does not require live broker mapping. Execution suitability
requires an execution symbol and known contract multiplier, tick size and lot
size when execution is explicitly requested. Unknown live capability remains
unknown; it is never assumed.

## Data, costs and liquidity

Data evidence records source, resolution, history depth, missingness and grade.
Intraday public/research data is not labelled execution-grade. Cost evidence
distinguishes observed from assumed burden and retains the stated basis; no
broker fees are invented. Liquidity evidence distinguishes observed quality
from unavailable/unknown spread or volume. Unknown liquidity is not equivalent
to poor liquidity.

## Feature evidence and stability

M11 `FeatureEffectiveness` records are summarized without becoming strategy
weights. Learned, insufficient, positive and negative evidence counts remain
visible. Stability is marked insufficient when evidence is shallow rather than
manufactured. Redundancy is not used to alter eligibility or portfolio weights
in M12.

## Governance and discovered instruments

Human permission and manual blocks remain authoritative over learned evidence.
`DiscoveredInstrument` is explicitly `CANDIDATE / RESEARCH` and is not added to
the canonical production registry automatically. Identity, data validation,
execution mapping and permission remain prerequisites for later promotion.

## Runtime boundary and limitations

No suitability output is connected to dashboard recommendations, Buy/Hold/Sell,
opportunity ranking, TradePolicy, risk, Railway, brokers or portfolio
allocation. No historical return, Sharpe, feature weight, instrument subset or
portfolio optimization occurred. The safe suite passes 307 tests and all 39
immutable research artifacts remain unchanged. Current opportunity ranking is
deferred to M13.
