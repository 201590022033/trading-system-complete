# ADR 0001: Additive Evidence and Provenance Contract

- **Status:** Accepted
- **Date:** 2026-09-03

## Context

The repository already has collectors and a `NewsItem` model. Future source reliability and adaptive fusion work needs stable provenance, but replacing `NewsItem` immediately would risk breaking existing collectors and signal behavior.

## Decision

Add `evidence.py` with an immutable `EvidenceRecord` and conversion helpers:

- `normalize_news_item()` wraps existing `NewsItem` values without changing their meaning;
- `evidence_id()` creates a stable SHA-256-derived deduplication key from source, headline, publication time and URL;
- records carry source identity/class/tier, publication/observation/ingestion times, ticker/asset/sector mappings, sentiment/score/confidence, horizon and parser version;
- `deduplicate_evidence()` preserves first-seen order;
- source tiers follow the existing market-intelligence hierarchy, with community sources treated conservatively.

## Consequences

- Existing collectors remain compatible and can migrate one at a time.
- Reliability and learning engines have a stable contract for future outcomes.
- URL and fine-grained provenance remain optional until collectors provide them.
- No production signal weights change as part of this decision.

## Rejected alternatives

- Replacing `NewsItem` immediately: unnecessary migration risk.
- Using raw headline text as the only deduplication key: fails when syndicated items have different timestamps/URLs.
- Treating all sources equally: conflicts with the documented authority hierarchy.
