# Current milestone — engine-first feedback design

Date: 5 October 2026. Starting branch/HEAD: `master@8a0e7c11a1b2714cd7ffcdd5cbfe0e013e74b148`. Status: COMPLETED — documentation/planning only. This is B0 in the engine plan; B1 implementation has not started. No implementation milestone is ACTIVE.

Deliverables: [feedback and indicator review design](../research/ADAPTIVE_SWING_FEEDBACK_LOOP.md), [engine requirements, independent verification matrix and B1–B5 plan](../research/LOCAL_BACKTEST_ENGINE_SPEC.md), [ADR 0046](../adr/0046-backtest-engine-before-adaptive-loop.md), and navigation/roadmap/current-state updates.

Acceptance: inspect current replay/registry/metrics and limitations, check all introduced document links and documentation-only diff, run full offline safe suite and protected-artifact verifier; commit milestone-sized documentation. Record results before completion. No actual backtest, engine build, strategy accuracy, provider/model call, deployment or trading change is claimed.

Results: all 869 safe software tests passed in 60.949 seconds; all 54 protected artifacts passed; 272 relative targets across eleven changed/new Markdown documents resolved; `git diff --check` passed. Source inspection confirmed current replay's observed-session, fixed-LONG and hypothetical-cost limitations, and existing experiment/metric contracts. Documentation-only review passed; no new runtime tests were added for this planning task. These results establish repository/document safety, not acceptance of the proposed engine or evidence of an edge.

## Previous completed milestone — source-backed Swing hypothesis refinement

Date: 5 October 2026. Starting branch/HEAD: `master@a9d9185460613fb8b0b8f798406d131d0f8e7c57`. Status: COMPLETED. This is a proposal/documentation milestone, not an infrastructure implementation. No implementation milestone is ACTIVE.

Deliverable: [rule refinement 0.2](../research/SWING_RULE_REFINEMENT.md), linked into the six hypotheses, target architecture, current state, roadmap and document index. Primary South African studies are cited with scope/limits; no per-sector accuracy is fabricated. [ADR 0045](../adr/0045-swing-rule-research-contract.md) preserves isolation from installed profile versions and safety boundaries.

Acceptance: validate new document links/diffs, run the full safe suite and protected-artifact verifier, and verify only Markdown changes. The plan specifies separate entry setups, causal delayed trails, 3/4/5-session exits, volume ablations/weights, pooled personalities and nested chronological testing. No actual backtest or strategy promotion is claimed.

Results: 869 software tests passed in 61.120 seconds; all 54 protected artifacts passed; introduced relative links/document index checks passed and the diff is documentation-only. These checks establish repository safety, not strategy accuracy. Provider/model calls, data collection, ranking weights, hosted settings and broker permissions were unchanged.

## Previous completed milestone — project documentation reconciliation

Date: 5 October 2026. Starting code/branch: `master`, `c2ef802ef31ae087915ad73c76e075df09310a4a`. Status: COMPLETED. No milestone is currently ACTIVE; the next research milestone remains proposed. Earlier accumulated milestone notes are preserved in [the checkpoint archive](../history/CURRENT_MILESTONE_PRE_2026-10-05.md).

## Scope and result

Reconcile all tracked project documents and the ten authored workspace Markdown guides/reports with the recent implementation history. Rewrite living entry points, architecture, operating guides and roadmap; retain historical decisions/checkpoints with explicit temporal framing. Index every original document, including eleven protected Markdown artifacts that must not be edited. Preserve benchmark evidence and immutable decision records.

The authoritative snapshot is [CURRENT_STATE](../CURRENT_STATE.md); [DOCUMENTATION_INDEX](../DOCUMENTATION_INDEX.md) records coverage. [ADR 0044](../adr/0044-documentation-reconciliation.md) explains the distinction between current guidance and historical evidence. The owner's six-family workflow is a proposal, not an implemented or validated strategy.

## Acceptance

- Baseline: 869 safe tests passed on the starting code.
- Required final checks: complete inventory coverage, relative links introduced by this task, protected-artifact verification, full safe suite, diff/secret review.
- No runtime source, broker mutation, ranking weights, scheduled settings or persistence schema changes in this task.
- Recommended next work: six-family hypothesis/data contracts, then local causal backtests and real-data radar/event admission.

Final acceptance: all 178 existing documents indexed; 167 updated, eleven protected Markdown documents unchanged, 30 new guidance/archive records and ten workspace Markdown documents reconciled. Baseline and final full suites each passed 869 tests; the final run took 60.920 seconds. All 54 protected artifacts passed. The documentation checker verifies index coverage, original archive preservation, introduced relative targets and zero runtime-file changes. Current-document `git diff --check`, documentation-only staged-file review and concrete-token secret screening passed before commit. The 24 archives preserve original text, including inherited trailing whitespace; archive checking allows that historical whitespace only. All 197 staged files are Markdown; no protected file is staged. No new feature milestone is activated by completing this documentation task.
