# ADR 0023 — Gate 1 canonical opportunity input bundle

Status: accepted locally, 2026-09-19.

Correction: ADR 0024 completes the causal learned-ranking and durable worker/UI
connections. This checkpoint's provenance bundle alone was not a closed loop.

The canonical M13 ResearchOpportunity now carries an immutable factual input
bundle alongside its existing ranked components. This reconciles the existing
public-share refresh with the repository's causal regime, news/macro and
shadow-learning boundaries without creating another ranker.

The bundle is descriptive input provenance, not a new score. The existing M13
ranker remains the only ranking implementation. M13 filters future-dated
effectiveness and input evidence at evaluation time; unavailable inputs remain
explicitly unavailable. The legacy scanner is retained as a benchmark only,
and the compatibility /api/opportunities route reads the canonical service.

No live broker call, new provider, new indicator, migration, or production
adaptive-weight promotion is part of this decision.
