"""Immutable experiment records and append-only scientific registry."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Protocol

from domain.contracts.trade import MetricContext

VERSION = "experiment-registry-v1"
SECRET_KEYS = {"password", "api_key", "secret", "token", "cst", "x-security-token", "cookie", "authorization"}


def utc(value, name):
    if value.tzinfo is None or value.utcoffset() is None: raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def clean_mapping(value, name):
    data = dict(value)
    if any(str(key).lower() in SECRET_KEYS for key in data): raise ValueError(f"{name} contains forbidden secret field")
    return MappingProxyType(data)


def configuration_hash(value: Mapping[str, object]) -> str:
    safe = dict(clean_mapping(value, "configuration"))
    return sha256(json.dumps(safe, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class ExperimentMode(str, Enum): CONFIRMATORY="CONFIRMATORY"; RETROSPECTIVE="RETROSPECTIVE"; EXPLORATORY="EXPLORATORY"
class ExperimentStage(str, Enum):
    DRAFT="DRAFT"; REGISTERED="REGISTERED"; IN_SAMPLE="IN_SAMPLE"; VALIDATION="VALIDATION"; OUT_OF_SAMPLE="OUT_OF_SAMPLE"; WALK_FORWARD="WALK_FORWARD"; SHADOW="SHADOW"; FORWARD_DEMO="FORWARD_DEMO"; REJECTED="REJECTED"; INCONCLUSIVE="INCONCLUSIVE"; ACCEPTED_FOR_NEXT_STAGE="ACCEPTED_FOR_NEXT_STAGE"; CLOSED="CLOSED"
class DecisionType(str, Enum): REJECT="REJECT"; INCONCLUSIVE="INCONCLUSIVE"; ACCEPT_FOR_NEXT_STAGE="ACCEPT_FOR_NEXT_STAGE"; CLOSE_NO_PROMOTION="CLOSE_NO_PROMOTION"; SUPERSEDED="SUPERSEDED"


@dataclass(frozen=True)
class ArtifactReference:
    artifact_id: str; uri: str; sha256: str | None; media_type: str; commit: str | None = None


@dataclass(frozen=True)
class DataBoundary:
    dataset_id: str; dataset_version: str; data_grade: str; as_of: datetime
    train_start: datetime | None = None; train_end: datetime | None = None
    validation_start: datetime | None = None; validation_end: datetime | None = None
    oos_start: datetime | None = None; oos_end: datetime | None = None
    forward_start: datetime | None = None; forward_end: datetime | None = None
    provenance: str = ""
    def __post_init__(self):
        if not self.dataset_id or not self.dataset_version or not self.data_grade or not self.provenance: raise ValueError("data identity, grade and provenance required")
        for name in ("as_of","train_start","train_end","validation_start","validation_end","oos_start","oos_end","forward_start","forward_end"):
            value=getattr(self,name)
            if value is not None: object.__setattr__(self,name,utc(value,name))
        for start,end in ((self.train_start,self.train_end),(self.validation_start,self.validation_end),(self.oos_start,self.oos_end),(self.forward_start,self.forward_end)):
            if (start is None) != (end is None) or (start and end <= start): raise ValueError("data intervals require ordered start and end")
        if self.train_end and self.oos_start and self.train_end >= self.oos_start: raise ValueError("OOS interval overlaps training boundary")
        if self.as_of < max((x for x in (self.train_end,self.validation_end,self.oos_end,self.forward_end) if x), default=self.as_of): raise ValueError("as_of precedes declared data boundary")


@dataclass(frozen=True)
class Factor:
    name: str; levels: tuple[str,...]
    def __post_init__(self):
        if not self.name or len(self.levels)<2 or len(set(self.levels)) != len(self.levels): raise ValueError("factor requires unique named levels")


@dataclass(frozen=True)
class FactorialDesign:
    factors: tuple[Factor,...]; interaction_interpretation: str; sample_evidence_plan: str
    def __post_init__(self):
        if len(self.factors)<2 or not self.interaction_interpretation or not self.sample_evidence_plan: raise ValueError("explicit factorial design requires factors, interactions and evidence plan")


@dataclass(frozen=True)
class ExperimentDefinition:
    experiment_id: str; experiment_version: str; created_at: datetime; created_by: str; mode: ExperimentMode
    strategy_family: str; instrument_scope: tuple[str,...]; horizon_scope: tuple[str,...]
    baseline_id: str; baseline_version: str; baseline_commit: str
    baseline_artifacts: tuple[ArtifactReference,...]; baseline_evidence_references: tuple[str,...]
    observed_deficiency: str; deficiency_evidence: tuple[str,...]; primary_hypothesis: str
    expected_mechanism: str; falsifiable_prediction: str; treatment_description: str
    changed_components: tuple[str,...]; treatment_version: str; treatment_config_hash: str
    unchanged_components: tuple[str,...]; control_reference: str
    strategy_target_id: str; strategy_target_version: str; intended_metric_ids: tuple[str,...]
    data_boundaries: tuple[DataBoundary,...]; factorial_design: FactorialDesign | None = None
    registry_version: str = VERSION
    def __post_init__(self):
        required=(self.experiment_id,self.experiment_version,self.created_by,self.strategy_family,self.baseline_id,self.baseline_version,self.baseline_commit,self.observed_deficiency,self.primary_hypothesis,self.expected_mechanism,self.falsifiable_prediction,self.treatment_description,self.treatment_version,self.treatment_config_hash,self.control_reference,self.strategy_target_id,self.strategy_target_version)
        if any(not x for x in required): raise ValueError("complete experiment identity and scientific definition required")
        object.__setattr__(self,"created_at",utc(self.created_at,"created_at"))
        if not self.instrument_scope or not self.horizon_scope or not self.deficiency_evidence or not self.unchanged_components or not self.intended_metric_ids or not self.data_boundaries: raise ValueError("explicit scope, evidence, control, metrics and data required")
        if self.factorial_design is None and len(self.changed_components)!=1: raise ValueError("single-treatment experiment requires exactly one changed component")
        if self.factorial_design is not None and len(self.changed_components)<2: raise ValueError("factorial design requires multiple changed components")


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str; experiment_id: str; experiment_version: str; started_at: datetime; completed_at: datetime
    git_commit: str; code_version: str; environment: str; dataset_versions: Mapping[str,str]
    feature_versions: tuple[str,...]; regime_version: str | None; cost_model_version: str | None
    random_seed: int | None; configuration_hash: str; causal_cutoff: datetime; stage: ExperimentStage
    def __post_init__(self):
        if not all((self.run_id,self.experiment_id,self.experiment_version,self.git_commit,self.code_version,self.environment,self.configuration_hash)): raise ValueError("complete run provenance required")
        object.__setattr__(self,"started_at",utc(self.started_at,"started_at")); object.__setattr__(self,"completed_at",utc(self.completed_at,"completed_at")); object.__setattr__(self,"causal_cutoff",utc(self.causal_cutoff,"causal_cutoff"))
        if self.completed_at < self.started_at: raise ValueError("run completion precedes start")
        object.__setattr__(self,"dataset_versions",clean_mapping(self.dataset_versions,"dataset versions"))


@dataclass(frozen=True)
class ExperimentResult:
    result_id: str; run_id: str; recorded_at: datetime; metrics: Mapping[str,float|int|bool|None]
    metric_contexts: Mapping[str,MetricContext]; strategy_target_id: str; strategy_target_version: str
    target_assessment_reference: str | None; sample_counts: Mapping[str,float|int]
    uncertainty: Mapping[str,object]; regime_breakdown: Mapping[str,object]; cost_sensitivity: Mapping[str,object]
    evidence_stage: ExperimentStage; artifacts: tuple[ArtifactReference,...]; negative_evidence: tuple[str,...]
    warnings: tuple[str,...]; data_quality_limitations: tuple[str,...]
    canonical_metrics: tuple["MetricResult",...] = ()
    def __post_init__(self):
        if not self.result_id or not self.run_id or not self.strategy_target_id or not self.strategy_target_version: raise ValueError("result, run and target identity required")
        object.__setattr__(self,"recorded_at",utc(self.recorded_at,"recorded_at"))
        for name in ("metrics","metric_contexts","sample_counts","uncertainty","regime_breakdown","cost_sensitivity"):
            object.__setattr__(self,name,clean_mapping(getattr(self,name),name))
        if any(not isinstance(value,MetricContext) for value in self.metric_contexts.values()): raise ValueError("every metric context must be canonical")
        from .metrics import MetricResult
        if any(not isinstance(value,MetricResult) for value in self.canonical_metrics): raise ValueError("canonical metrics must use MetricResult")


@dataclass(frozen=True)
class ExperimentDecision:
    decision_id: str; experiment_id: str; experiment_version: str; decided_at: datetime
    decision: DecisionType; authority: str; rationale: str; supporting_result_ids: tuple[str,...]
    failed_hard_target_criteria: tuple[str,...]; unresolved_evidence: tuple[str,...]
    next_allowed_stage: ExperimentStage | None; successor_baseline_id: str | None = None
    def __post_init__(self):
        if not all((self.decision_id,self.experiment_id,self.experiment_version,self.authority,self.rationale)) or not self.supporting_result_ids: raise ValueError("decision authority, rationale and results required")
        object.__setattr__(self,"decided_at",utc(self.decided_at,"decided_at"))
        if self.successor_baseline_id and self.decision is not DecisionType.ACCEPT_FOR_NEXT_STAGE: raise ValueError("baseline succession requires explicit accepted-for-next-stage decision")


class ExperimentRepository(Protocol):
    def register_definition(self,definition:ExperimentDefinition)->ExperimentDefinition: ...
    def record_run(self,run:ExperimentRun)->ExperimentRun: ...
    def record_result(self,result:ExperimentResult)->ExperimentResult: ...
    def record_decision(self,decision:ExperimentDecision)->ExperimentDecision: ...
    def get_experiment(self,experiment_id:str,experiment_version:str): ...
    def list_experiments(self)->tuple[ExperimentDefinition,...]: ...
    def get_lineage(self,baseline_id:str)->tuple[ExperimentDecision,...]: ...


class InMemoryExperimentRepository:
    """Append-only reference implementation; no database or runtime dependency."""
    def __init__(self): self._definitions={}; self._runs={}; self._results={}; self._decisions={}
    def register_definition(self,d):
        key=(d.experiment_id,d.experiment_version)
        if key in self._definitions: raise ValueError("experiment definition is immutable; create a new version")
        self._definitions[key]=d; return d
    def record_run(self,r):
        definition=self._definitions.get((r.experiment_id,r.experiment_version))
        if definition is None: raise KeyError("experiment definition must be registered first")
        if definition.mode is ExperimentMode.CONFIRMATORY and r.started_at < definition.created_at: raise ValueError("confirmatory run predates preregistration")
        if r.run_id in self._runs: raise ValueError("run records are append-only")
        self._runs[r.run_id]=r; return r
    def record_result(self,r):
        run=self._runs.get(r.run_id)
        if run is None: raise KeyError("run must exist before result")
        definition=self._definitions[(run.experiment_id,run.experiment_version)]
        if (r.strategy_target_id,r.strategy_target_version)!=(definition.strategy_target_id,definition.strategy_target_version): raise ValueError("StrategyTarget identity/version mismatch")
        if r.evidence_stage is ExperimentStage.OUT_OF_SAMPLE and not any(x.oos_start for x in definition.data_boundaries): raise ValueError("OOS result requires declared non-overlapping OOS boundary")
        if r.result_id in self._results: raise ValueError("results are append-only")
        self._results[r.result_id]=r; return r
    def record_decision(self,d):
        if (d.experiment_id,d.experiment_version) not in self._definitions: raise KeyError("unknown experiment")
        if any(x not in self._results for x in d.supporting_result_ids): raise KeyError("decision references unknown result")
        if d.decision_id in self._decisions: raise ValueError("decisions are append-only")
        self._decisions[d.decision_id]=d; return d
    def get_experiment(self,e,v):
        d=self._definitions[(e,v)]; runs=tuple(x for x in self._runs.values() if (x.experiment_id,x.experiment_version)==(e,v)); ids={x.run_id for x in runs}; results=tuple(x for x in self._results.values() if x.run_id in ids); decisions=tuple(x for x in self._decisions.values() if (x.experiment_id,x.experiment_version)==(e,v)); return {"definition":d,"runs":runs,"results":results,"decisions":decisions}
    def list_experiments(self): return tuple(self._definitions.values())
    def get_lineage(self,b): return tuple(x for x in self._decisions.values() if x.successor_baseline_id==b)
    def find(self,*,component=None,decision=None,dataset_version=None,stage=None):
        output=[]
        for d in self._definitions.values():
            bundle=self.get_experiment(d.experiment_id,d.experiment_version)
            if component and component not in d.changed_components: continue
            if decision and not any(x.decision is decision for x in bundle["decisions"]): continue
            if dataset_version and not any(dataset_version in x.dataset_versions.values() for x in bundle["runs"]): continue
            if stage and not any(x.stage is stage for x in bundle["runs"]): continue
            output.append(d)
        return tuple(output)

__all__=["ArtifactReference","DataBoundary","DecisionType","ExperimentDecision","ExperimentDefinition","ExperimentMode","ExperimentRepository","ExperimentResult","ExperimentRun","ExperimentStage","Factor","FactorialDesign","InMemoryExperimentRepository","VERSION","configuration_hash"]
