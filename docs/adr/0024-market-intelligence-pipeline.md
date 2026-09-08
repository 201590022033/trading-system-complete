# ADR 0024: Configurable market-intelligence pipeline

## Status
Accepted for OI4 / market-intelligence UI redesign on 2026-09-08.

## Context
The existing research system already has:
- normalized `EvidenceRecord` provenance (`evidence.py`);
- a policy-aware specialist source catalogue (`source_catalog.py`);
- a regime engine, adaptive ensemble and risk/execution boundaries;
- a Flask dashboard that exposes public feeds and simulated decisions.

What it lacks is a configurable, auditable market-intelligence layer that:
1. lets users see and manage information sources;
2. ingests and analyses structured content (including PDFs) safely;
3. produces a structured market narrative with explicit provenance;
4. recommends instruments for *investigation* only, never as executable trades;
5. feeds those recommendations into the existing technical/ensemble/risk pipeline.

## Decision
Introduce a new `market_intelligence` package that is strictly additive and
research/shadow-only. It will provide:

- Frozen, serialisable schemas for `SourceEvidence`, `MarketTheme`,
  `InstrumentCandidate`, `MarketNarrative` and `TickerSelection`.
- A SQLite-backed `MarketIntelligenceStore` with versioned migrations,
  append-only evidence/narratives/ticker selections and an audit log.
- A persisted `SourceRegistry` that seeds from the existing
  `source_catalog.DEFAULT_SOURCE_POLICIES` and allows runtime enable/disable,
  editing and user-added sources.
- A `MarketSource` abstract base so future ingestion implementations (RSS,
  HTML, PDF archive, API) plug in rather than duplicate.
- Explicit separation between **source content** and **LLM interpretation** in
  storage and in UI presentation.

The pipeline rule remains:

```
news/content → Market AI → themes → candidates → AI watchlist
→ technical/regime/signal analysis → ensemble → risk → trade candidate
→ human review / broker execution
```

No LLM or news item may directly generate an executable trade. The existing
signal contract, ensemble and risk gates are preserved unchanged.

## Consequences
- Source configuration is now persistent and auditable instead of in-memory only.
- New sources (including Efficient Group / Dawie Roodt material) can be added
  through the registry without altering existing collectors.
- Document hashing and deduplication prevent repeated LLM analysis of the same
  PDF.
- UI tabs for Market AI/News, Technical Intelligence and Portfolio/Trade Summary
  can be built on top of these schemas in later phases.
- Broker/execution integration remains prepare-only; no live-order route is
  introduced.

## Boundary conditions
- `market_intelligence` must not replace `evidence.py`, `source_catalog.py`,
  `reliability_store.py`, the regime engine or the adaptive ensemble.
- Source enable/disable is a configuration change, not a signal change.
- All market-intelligence output is research/shadow-only until explicit
  walk-forward evidence justifies promotion.
