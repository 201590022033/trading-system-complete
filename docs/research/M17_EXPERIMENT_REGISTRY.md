# M17 Experiment Registry

M17 implements `experiment-registry-v1`, an immutable scientific record from
baseline and deficiency through hypothesis, treatment, causal evidence, and an
explicit research decision. It does not optimize, rerun research, promote a
strategy, change a baseline automatically, or connect to runtime/brokers.

`ExperimentDefinition` records identity and governance, strategy/instrument/
horizon scope, baseline ID/version/commit plus artifact/evidence references,
observed deficiency and evidence, one falsifiable primary hypothesis and
mechanism, treatment/configuration identity, unchanged controls, exact M16
StrategyTarget ID/version, intended metrics, and versioned data boundaries.
Large CSV/Parquet/JSON/report artifacts are referenced by `ArtifactReference`,
not copied or overwritten.

Confirmatory definitions must precede their runs. Historical or after-the-fact
work is explicitly `RETROSPECTIVE` or `EXPLORATORY`; HR7–HR11 remain immutable
`LEGACY / PRE-REGISTRY` research and are not falsely presented as preregistered.

The default attribution rule permits exactly one changed component. Multiple
components require an explicit `FactorialDesign` with named factors, unique
levels, interaction interpretation, and sample/evidence plan. Undeclared bundled
treatments are rejected.

`ExperimentRun` preserves timestamps, commit/code/environment, dataset and
feature versions, regime/cost versions, seed, deterministic configuration hash,
causal cutoff, and stage. Secret-named fields are rejected. `DataBoundary`
preserves train, validation, OOS, forward, maturity/as-of and provenance; an OOS
interval may not overlap training.

`ExperimentResult` retains metrics with exact `MetricContext`, StrategyTarget
version and assessment reference, sample counts, uncertainty, regime breakdown,
cost sensitivity, stage, artifacts, negative evidence, warnings, and data-quality
limitations. It never collapses evidence to PASS/FAIL. Results are append-only.

`ExperimentDecision` supports `REJECT`, `INCONCLUSIVE`,
`ACCEPT_FOR_NEXT_STAGE`, `CLOSE_NO_PROMOTION`, and `SUPERSEDED`, with authority,
rationale, result references, failed hard criteria, unresolved evidence, and
next permitted stage. Rejected and inconclusive evidence stays queryable.
Accepting a next stage does not alter production.

A successor baseline can appear only on an explicit accepted-for-next-stage
decision, preserving `baseline A → experiment X → decision → baseline B`.
Inconclusive evidence leaves the baseline unchanged. Changing hypothesis,
treatment, target, or material data boundaries requires a new version because a
registered definition cannot be replaced.

`ExperimentRepository` defines registration, append, retrieval, listing, and
lineage operations. `InMemoryExperimentRepository` is the safe local reference
implementation and supports audit queries by component, decision, dataset
version, and stage. Durable persistence is deliberately deferred: the existing
SQLite/PostgreSQL repositories have entity-specific schemas, and adding only one
backend or an unrelated database would violate the canonical boundary. A future
additive migration can implement this protocol for both backends.

No production status exists, no automatic promotion is possible, and no target
threshold, parameter search, historical rewrite, runtime mutation, or broker
execution was added.
