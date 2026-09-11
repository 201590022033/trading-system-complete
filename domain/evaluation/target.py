"""Versioned strategy research targets and non-promoting requirement assessment."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite, sqrt
from statistics import mean, stdev
from types import MappingProxyType
from typing import Mapping

from domain.contracts.trade import MetricContext


VERSION = "strategy-target-v1"


class TargetStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class RequirementLevel(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"


class EvidenceStage(str, Enum):
    IN_SAMPLE = "IN_SAMPLE"
    VALIDATION = "VALIDATION"
    OUT_OF_SAMPLE = "OUT_OF_SAMPLE"
    WALK_FORWARD = "WALK_FORWARD"
    FORWARD_DEMO = "FORWARD_DEMO"
    LIVE = "LIVE"


class Comparison(str, Enum):
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"
    REQUIRED_TRUE = "REQUIRED_TRUE"


class MetricIdentity(str, Enum):
    NET_EXPECTANCY = "NET_EXPECTANCY"
    GROSS_EXPECTANCY = "GROSS_EXPECTANCY"
    TOTAL_SAMPLE_COUNT = "TOTAL_SAMPLE_COUNT"
    EFFECTIVE_SAMPLE_COUNT = "EFFECTIVE_SAMPLE_COUNT"
    OOS_SAMPLE_COUNT = "OOS_SAMPLE_COUNT"
    FORWARD_SAMPLE_COUNT = "FORWARD_SAMPLE_COUNT"
    CANONICAL_ANNUALIZED_SHARPE = "CANONICAL_ANNUALIZED_SHARPE"
    LEGACY_TSTAT_LIKE_V1 = "LEGACY_TSTAT_LIKE_V1"
    SORTINO = "SORTINO"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    MAX_LOSS_PER_TRADE = "MAX_LOSS_PER_TRADE"
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"
    MAX_PORTFOLIO_OPEN_RISK = "MAX_PORTFOLIO_OPEN_RISK"
    OOS_NET_EXPECTANCY = "OOS_NET_EXPECTANCY"
    WALK_FORWARD_STABILITY = "WALK_FORWARD_STABILITY"
    REGIME_ROBUSTNESS = "REGIME_ROBUSTNESS"
    COST_STRESS_EXPECTANCY = "COST_STRESS_EXPECTANCY"
    SLIPPAGE_SENSITIVITY = "SLIPPAGE_SENSITIVITY"
    PARAMETER_STABILITY = "PARAMETER_STABILITY"
    STRESS_SURVIVAL = "STRESS_SURVIVAL"
    FORWARD_DURATION_DAYS = "FORWARD_DURATION_DAYS"
    FORWARD_NET_EXPECTANCY = "FORWARD_NET_EXPECTANCY"
    FORWARD_DRAWDOWN = "FORWARD_DRAWDOWN"
    OPERATIONAL_STABILITY = "OPERATIONAL_STABILITY"
    MAX_HISTORICAL_FORWARD_DIVERGENCE = "MAX_HISTORICAL_FORWARD_DIVERGENCE"
    MAX_GEARING = "MAX_GEARING"
    MARGIN_FEASIBLE = "MARGIN_FEASIBLE"
    LIQUIDITY_TRADABLE = "LIQUIDITY_TRADABLE"
    MINIMUM_DATA_GRADE = "MINIMUM_DATA_GRADE"


@dataclass(frozen=True)
class TargetCriterion:
    criterion_id: str
    metric_id: MetricIdentity
    level: RequirementLevel
    comparison: Comparison
    threshold: float | bool | str | None
    context: MetricContext
    evidence_stage: EvidenceStage
    required_regimes: tuple[str, ...] = ()
    allowed_specialization: tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self):
        if not self.criterion_id or not isinstance(self.context, MetricContext):
            raise ValueError("criterion identity and metric context are required")
        if isinstance(self.threshold, float) and not isfinite(self.threshold):
            raise ValueError("numeric threshold must be finite")
        if self.comparison is Comparison.REQUIRED_TRUE and self.threshold not in {None, True}:
            raise ValueError("required-true criterion threshold must be true or unset")
        if self.metric_id is MetricIdentity.CANONICAL_ANNUALIZED_SHARPE:
            if (self.context.annualization_factor is None or self.context.annualization_factor <= 0 or
                    self.context.sampling_basis != "PERIODIC_CALENDAR" or
                    self.context.is_overlapping is not False or
                    self.context.return_unit != "DECIMAL_RETURN" or
                    self.context.return_basis not in {"NET", "GROSS"} or
                    self.context.risk_free_rate_annualized is None):
                raise ValueError("canonical Sharpe threshold requires complete annualization context")

    @property
    def configured(self) -> bool:
        return self.threshold is not None


@dataclass(frozen=True)
class StrategyTarget:
    target_id: str
    target_version: str
    created_at: datetime
    strategy_family: str
    instrument_scope: tuple[str, ...]
    horizon_scope: tuple[str, ...]
    status: TargetStatus
    criteria: tuple[TargetCriterion, ...]
    author_governance: str
    rationale: str
    version_history: tuple[str, ...]
    applicable_experiment_family: str

    def __post_init__(self):
        if not all((self.target_id, self.target_version, self.strategy_family,
                    self.author_governance, self.rationale, self.applicable_experiment_family)):
            raise ValueError("target identity, family, governance and rationale are required")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("target creation time must be timezone-aware")
        object.__setattr__(self, "created_at", self.created_at.astimezone(timezone.utc))
        if not self.instrument_scope or not self.horizon_scope:
            raise ValueError("instrument and horizon scopes must be explicit")
        identifiers = [item.criterion_id for item in self.criteria]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("criterion identifiers must be unique")

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id, "target_version": self.target_version,
            "created_at": self.created_at.isoformat(), "strategy_family": self.strategy_family,
            "instrument_scope": list(self.instrument_scope), "horizon_scope": list(self.horizon_scope),
            "status": self.status.value, "criteria": [{
                "criterion_id": c.criterion_id, "metric_id": c.metric_id.value,
                "level": c.level.value, "comparison": c.comparison.value,
                "threshold": c.threshold, "context": c.context.to_dict(),
                "evidence_stage": c.evidence_stage.value,
                "required_regimes": list(c.required_regimes),
                "allowed_specialization": list(c.allowed_specialization), "rationale": c.rationale,
            } for c in self.criteria], "author_governance": self.author_governance,
            "rationale": self.rationale, "version_history": list(self.version_history),
            "applicable_experiment_family": self.applicable_experiment_family,
        }


@dataclass(frozen=True)
class MetricObservation:
    criterion_id: str
    metric_id: MetricIdentity
    evidence_stage: EvidenceStage
    value: float | bool | str | None
    context: MetricContext
    observed_at: datetime
    provenance: Mapping[str, object]

    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observation time must be timezone-aware")
        if isinstance(self.value, float) and not isfinite(self.value):
            raise ValueError("observation value must be finite")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(timezone.utc))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True)
class CriterionAssessment:
    criterion_id: str
    level: RequirementLevel
    status: str
    observed_value: float | bool | str | None
    threshold: float | bool | str | None
    reason: str


@dataclass(frozen=True)
class TargetAssessment:
    target_id: str
    target_version: str
    status: str
    criteria: tuple[CriterionAssessment, ...]
    promotion_authorized: bool = False

    def __post_init__(self):
        if self.promotion_authorized:
            raise ValueError("M16 cannot authorize promotion")


def assess_target(target: StrategyTarget, observations: tuple[MetricObservation, ...]) -> TargetAssessment:
    """Compare declared requirements only; never promotes or changes a strategy."""
    indexed = {item.criterion_id: item for item in observations}
    results = []
    for criterion in target.criteria:
        observation = indexed.get(criterion.criterion_id)
        if not criterion.configured:
            results.append(CriterionAssessment(criterion.criterion_id, criterion.level, "NOT_CONFIGURED", None, None,
                                               "TARGET_THRESHOLD_UNSET"))
            continue
        if observation is None:
            results.append(CriterionAssessment(criterion.criterion_id, criterion.level, "UNAVAILABLE", None,
                                               criterion.threshold, "EVIDENCE_UNAVAILABLE"))
            continue
        if (observation.metric_id is not criterion.metric_id or observation.evidence_stage is not criterion.evidence_stage or
                observation.context != criterion.context):
            results.append(CriterionAssessment(criterion.criterion_id, criterion.level, "INVALID_CONTEXT",
                                               observation.value, criterion.threshold, "METRIC_CONTEXT_OR_STAGE_MISMATCH"))
            continue
        if observation.value is None:
            passed = False
        elif criterion.comparison is Comparison.MINIMUM:
            passed = observation.value >= criterion.threshold
        elif criterion.comparison is Comparison.MAXIMUM:
            passed = observation.value <= criterion.threshold
        else:
            passed = observation.value is True
        results.append(CriterionAssessment(criterion.criterion_id, criterion.level,
                                           "SATISFIED" if passed else "FAILED", observation.value,
                                           criterion.threshold, "THRESHOLD_SATISFIED" if passed else "THRESHOLD_FAILED"))
    hard = [item for item in results if item.level is RequirementLevel.HARD]
    if any(item.status == "FAILED" for item in hard):
        status = "HARD_REQUIREMENTS_FAILED"
    elif any(item.status == "INVALID_CONTEXT" for item in hard):
        status = "INVALID_EVIDENCE_CONTEXT"
    elif any(item.status == "NOT_CONFIGURED" for item in hard):
        status = "NOT_CONFIGURED"
    elif any(item.status == "UNAVAILABLE" for item in hard):
        status = "EVIDENCE_INCOMPLETE"
    else:
        status = "REQUIREMENTS_SATISFIED_FOR_REVIEW"
    return TargetAssessment(target.target_id, target.target_version, status, tuple(results))


@dataclass(frozen=True)
class MetricComputation:
    metric_id: MetricIdentity
    status: str
    value: float | None
    reason: str | None = None


def canonical_annualized_sharpe(returns, context: MetricContext) -> MetricComputation:
    valid = (context.annualization_factor is not None and context.annualization_factor > 0 and
             context.sampling_basis == "PERIODIC_CALENDAR" and context.is_overlapping is False and
             context.return_unit == "DECIMAL_RETURN" and context.return_basis in {"NET", "GROSS"} and
             context.risk_free_rate_annualized is not None)
    if not valid:
        return MetricComputation(MetricIdentity.CANONICAL_ANNUALIZED_SHARPE, "INVALID_CONTEXT", None,
                                 "EXPLICIT_PERIODICITY_ANNUALIZATION_AND_RETURN_CONTEXT_REQUIRED")
    values = tuple(float(value) for value in returns)
    if len(values) < 2 or any(not isfinite(value) for value in values) or stdev(values) == 0:
        return MetricComputation(MetricIdentity.CANONICAL_ANNUALIZED_SHARPE, "UNAVAILABLE", None,
                                 "INSUFFICIENT_NONCONSTANT_PERIODIC_RETURNS")
    periodic_rf = context.risk_free_rate_annualized / context.annualization_factor
    value = mean(value - periodic_rf for value in values) / stdev(values) * sqrt(context.annualization_factor)
    return MetricComputation(MetricIdentity.CANONICAL_ANNUALIZED_SHARPE, "AVAILABLE", value)


def legacy_tstat_like_v1(returns) -> MetricComputation:
    """Preserve HR10 mean/sample-std*sqrt(n); this is not canonical Sharpe."""
    values = tuple(float(value) for value in returns)
    if len(values) < 2 or any(not isfinite(value) for value in values) or stdev(values) == 0:
        return MetricComputation(MetricIdentity.LEGACY_TSTAT_LIKE_V1, "UNAVAILABLE", None,
                                 "INSUFFICIENT_NONCONSTANT_TRADE_RETURNS")
    return MetricComputation(MetricIdentity.LEGACY_TSTAT_LIKE_V1, "AVAILABLE",
                             mean(values) / stdev(values) * sqrt(len(values)))


__all__ = ["Comparison", "CriterionAssessment", "EvidenceStage", "MetricComputation",
           "MetricIdentity", "MetricObservation", "RequirementLevel", "StrategyTarget",
           "TargetAssessment", "TargetCriterion", "TargetStatus", "VERSION", "assess_target",
           "canonical_annualized_sharpe", "legacy_tstat_like_v1"]
