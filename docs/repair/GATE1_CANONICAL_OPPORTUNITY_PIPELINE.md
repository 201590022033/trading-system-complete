# Gate 1 — Canonical opportunity pipeline

Status: implemented locally, paper/shadow-only, 2026-09-19.

Correction/continuation: ADR 0024 and GATES_2_5_PLAN.md supersede this checkpoint's
completion claim. Provenance alone did not wire learned evidence into ranking;
the later repair supplies causal strategy outcomes and migrates the remaining
discovery display. Legacy aggregates remain context, not fabricated skill.

## Repair objective

There must be one authoritative opportunity path:

public market inputs -> factual evidence bundle -> causal M11/M12 inputs -> M13 ranker -> canonical ResearchOpportunity -> Top 5 API/UI

The old opportunity_scanner.py remains available only as a characterized legacy
benchmark for its existing unit tests. It is not an application/API data source.
operational_intelligence.py, signal_pipeline.py, adaptive_fusion.py, and the
shadow-learning worker remain separate research/benchmark boundaries; their
inputs are not silently substituted into M13.

## Findings reconciled

- opportunity_scanner.py calculated a separate 70/30 technical/news score.
- dashboard_feeds.py exposed that score through /api/opportunities.
- application/opportunities/public_research.py already built M11/M12/M10
  inputs for the M13 ranker, but dropped regime and current news/macro context.
- M13 already enforced causal effectiveness, divergence and suitability clocks.
- Shadow learning persisted evidence, but Gate 1 had no explicit input slot for
  its factual, matured state.
- M14/M15 and broker adapters are downstream read-only previews and are not
  prerequisites for the research Top 5.

## Implementation decisions

1. Add an immutable input_evidence bundle to the canonical candidate and
   ResearchOpportunity record. It carries technical facts, a causal regime
   record, dated news/macro facts, and learned-effectiveness context.
2. Build regime context from the same dated close series used by the candidate;
   availability timestamps are passed into the regime classifier.
3. Treat missing news/macro or persisted learning as UNAVAILABLE, never as a
   neutral score or fabricated fallback.
4. Apply the M13 evaluation cutoff to input evidence before exposing it. Future
   learned context cannot affect an earlier rank.
5. Make /api/opportunities a compatibility read model over the canonical
   service. The Top 5 UI continues to use /api/v1/opportunities; neither path
   invokes the simplified scanner.
6. Preserve the existing M13 score semantics, PostgreSQL/shadow durability
   contracts, and all broker safety gates. No live execution capability is
   added.

## Acceptance checks

- The compatibility endpoint remains canonical when the legacy scanner is
  unavailable.
- A canonical record exposes technical, regime, news/macro and learned input
  evidence.
- Future learned evidence is absent from an earlier evaluated record.
- Public-data failures remain unavailable and are not ranked.
- Existing focused tests and the full safe suite are green.

## Explicitly deferred

Gate 2 autonomous scheduling/outcomes, Gate 3 trade geometry, Gate 4
portfolio/aggression sizing, and Gate 5 PaperBroker closed-loop orchestration
are not connected by this repair. Live execution remains disabled.
