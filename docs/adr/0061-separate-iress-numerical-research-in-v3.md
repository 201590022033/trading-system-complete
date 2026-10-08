# ADR 0061 — Separate IRESS numerical research in the OST v3 dataset

Date: 8 October 2026. Status: accepted following three independent investigations and reviewer reconciliation.

## Problem

OST's observed native daily history export has Closing, High, Low and Volume, but no Opening column. Its parser correctly preserves the absent Open. IRESS has an observed daily Open, yet candidate registration was separate from collection: the v3 collector sent only OST charts, the research selector chose those same charts, and v3 normalization discarded an added research chart. The previous v2 supplemental path therefore stopped supplying Sasol Open after the OST v3 cutover.

## Decision

Extend v3 with one optional `research_charts.SASOL` full IRESS daily history. Reuse existing bar and supplemental receipt validation. The local collector derives it from hash-matched archived raw bytes, reparses at the actual acquisition time, and checks full equality with the saved candidate. It preserves provider, exact symbol, raw SHA-256, acquisition, unresolved adjustment/volume/historical-availability definitions, freshness and completed-session restrictions. A saved live row cannot become completed merely because its archive is reread later.

The separate chart survives validation, normalized storage and authenticated upload. `UploadedFetcher.get_chart` continues to use canonical OST. `get_research_chart` supplies the complete IRESS series only to numerical technical shadow calculations. No IRESS field is copied into an OST bar. The hosted read-only source audit can compare the two uploaded whole charts without a second audit store.

Source comparison uses integer cents and whole reported volume units. Every actual discrepancy is retained by session and field, including one-cent differences formerly miscounted by binary float tolerance. The independent raw integer comparison was preserved before repair. Volume eligibility remains unverified; it is not inferred from agreement.

## Boundaries and consequences

Historical v3 AI research retains its pre-model `OST_SOURCE_SEMANTICS_UNVERIFIED` hard stop. B5 remains PARTIAL_CLOSED with real-data admission false. Default strategy, paper accounting, canonical source identity, schedules and broker execution are unchanged. Existing same-session decisions are immutable; IRESS cannot relabel old OST decisions. New later-session IRESS decisions may mature only against consistent IRESS observations.

An expired IRESS receipt cannot supply Open. The existing worker may then retain partial canonical OST technical features, with Open/ATR unavailable; this is not a complete OHLC fallback. New upload observation times never renew acquisition timestamps. Missing/misaligned benchmarks leave the feature state PARTIAL. Full numerical availability is descriptive research, not verified historical availability or a trading signal.

Acceptance evidence: [R11 operating record](../research/IRESS_OPEN_ROUTING_R11.md). Existing source and historical gates are not weakened.
