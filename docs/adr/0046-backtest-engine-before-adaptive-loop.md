# ADR 0046 — prove the local replay engine before adaptive feedback

Date: 5 October 2026. Status: Accepted for documentation/design; implementation pending.

## Context

The owner wants six independent 3–5-session hypotheses, their own indicators/tests, explicit indicator reconsideration and local historical computation with selective cloud evidence. Existing daily shadow replay and retrospective cloud comparisons do not constitute a complete local multi-market backtest engine. Trustworthy outcome accounting is a dependency of learning.

## Decision

Specify and verify a deterministic local event-driven engine before implementing the broader feedback loop or dashboard rewire. Extend existing causal snapshots, frozen replay benchmarks, strategy attribution, experiment registry and metric contexts through explicit adapters. Keep event-study outcomes distinct from capital-constrained portfolio replay. Give FX and gold separate execution, activity, session and cost contracts.

Use independent arithmetic fixtures, causality/accounting invariants, controlled defect checks, locked chronological evaluation and independently audited real-data slices. A new general-purpose framework is deferred until semantics and reuse gaps are established; duplicating the old legacy paths or changing installed replay rules in place is rejected.

See [engine contract and gates B0–B5](../research/LOCAL_BACKTEST_ENGINE_SPEC.md) and [feedback loop](../research/ADAPTIVE_SWING_FEEDBACK_LOOP.md). B0 does not authorize or start the subsequent implementation gates. No broad persistence migration is required for this documentation milestone.

## Consequences

More verification before feature rollout; clean separation between software correctness, retrospective strategy evidence and prospective validation. “Bulletproof” is bounded testable correctness, not guaranteed profitability. Real-data/provider limitations can block execution-ready acceptance without blocking offline fixture development. Current canonical workflow, local uploads, cloud comparisons, protected benchmarks and broker gates remain unchanged.
