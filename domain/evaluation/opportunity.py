"""Transparent, causal opportunity ranking for research investigation only."""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Mapping

from domain.broker.ig import IGMapping
from domain.evaluation.effectiveness import FeatureEffectiveness
from domain.evaluation.suitability import InstrumentSuitability
from domain.features.divergence import DivergenceFeature
from domain.features.regime import MarketRegime
from domain.registry.instrument import CanonicalInstrument, GovernanceState

VERSION = "opportunity-ranking-v1"
SCORE_SEMANTICS = "COMPARATIVE_RESEARCH_RANKING_SCORE_NOT_A_PROBABILITY_OR_EXPECTED_RETURN"


def causal_input_evidence(bundle, cutoff):
    # Shared adapter validates nested clocks using UTC instants, not lexical ISO ordering.
    from application.opportunities.evidence import causal_bundle
    return causal_bundle(bundle, cutoff)


@dataclass(frozen=True)
class RankingConfig:
    """Declared defaults; these weights were not fitted to historical returns."""

    suitability_weight: float = .25
    effectiveness_weight: float = .20
    evidence_depth_weight: float = .15
    stability_weight: float = .10
    directional_weight: float = .10
    regime_context_weight: float = .08
    divergence_weight: float = .07
    data_quality_weight: float = .05
    uncertainty_penalty_weight: float = .10
    cost_penalty_weight: float = .05
    evidence_target: int = 30
    cost_penalty_cap_bps: float = 50.0
    version: str = VERSION

    def __post_init__(self):
        values = tuple(getattr(self, name) for name in self.__dataclass_fields__
                       if name.endswith("_weight"))
        if any(not isfinite(value) or value < 0 for value in values):
            raise ValueError("ranking weights must be finite and nonnegative")
        if not isclose(sum(values[:8]), 1.0):
            raise ValueError("positive ranking weights must sum to one")
        if self.evidence_target < 1 or self.cost_penalty_cap_bps <= 0:
            raise ValueError("ranking evidence and cost bounds must be positive")


def isclose(left, right, tolerance=1e-12):
    return abs(left - right) <= tolerance


@dataclass(frozen=True)
class OpportunityCandidate:
    instrument: CanonicalInstrument
    suitability: InstrumentSuitability
    divergence: DivergenceFeature | None
    effectiveness: tuple[FeatureEffectiveness, ...]
    regime: MarketRegime | None
    data_grade: str
    broker_mapping: IGMapping | None = None
    input_evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.instrument, CanonicalInstrument):
            raise TypeError("canonical M3 instrument required")
        if not isinstance(self.suitability, InstrumentSuitability):
            raise TypeError("canonical M12 suitability required")
        if not isinstance(self.effectiveness, tuple) or any(
                not isinstance(item, FeatureEffectiveness) for item in self.effectiveness):
            raise TypeError("canonical M11 effectiveness tuple required")
        if not isinstance(self.data_grade, str) or not self.data_grade:
            raise ValueError("explicit factual data grade required")


@dataclass(frozen=True)
class FeatureEvidenceSummary:
    learned_count: int
    insufficient_count: int
    positive_count: int
    negative_count: int
    sample_count: int
    effective_sample_count: float
    evidence_confidence: float | None
    fallback_levels: tuple[str, ...]
    negative_feature_ids: tuple[str, ...]


@dataclass(frozen=True)
class ResearchOpportunity:
    opportunity_id: str
    evaluated_at: datetime
    opportunity_version: str
    instrument_id: str
    horizon_id: str
    broker: str | None
    market_mapping_status: str
    ig_epic: str | None
    direction: str
    evidence_status: str
    feature_evidence_summary: FeatureEvidenceSummary
    divergence_summary: Mapping[str, object]
    regime_context: Mapping[str, object]
    suitability_status: str
    research_suitability: str
    execution_suitability: str
    data_status: str
    cost_status: str
    liquidity_status: str
    data_grade: str
    sample_count: int
    effective_evidence_count: float
    uncertainty: tuple[str, ...]
    ranking_score: float | None
    ranking_score_semantics: str
    ranking_components: Mapping[str, float]
    rank: int | None
    eligibility_status: str
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    input_feature_versions: tuple[str, ...]
    regime_version: str | None
    suitability_version: str
    effectiveness_version: str | None
    ranking_version: str
    provenance: Mapping[str, object] = field(default_factory=dict)
    input_evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if self.direction not in {"LONG", "SHORT", "WATCH", "UNKNOWN"}:
            raise ValueError("invalid research direction")
        if self.eligibility_status not in {
                "ELIGIBLE", "WATCH", "INSUFFICIENT_EVIDENCE", "BLOCKED", "UNSUPPORTED"}:
            raise ValueError("invalid opportunity status")
        if self.ranking_score is not None and not 0 <= self.ranking_score <= 100:
            raise ValueError("ranking score must be between zero and 100")
        if self.rank is not None and (self.ranking_score is None or self.rank < 1):
            raise ValueError("only scored opportunities may have positive ranks")
        for name in ("divergence_summary", "regime_context", "ranking_components", "provenance"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))
        object.__setattr__(self, "input_evidence", causal_input_evidence(self.input_evidence, self.evaluated_at))

    def to_dict(self):
        return {
            "opportunity_id": self.opportunity_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "opportunity_version": self.opportunity_version,
            "instrument_id": self.instrument_id,
            "horizon_id": self.horizon_id,
            "broker": self.broker,
            "market_mapping_status": self.market_mapping_status,
            "ig_epic": self.ig_epic,
            "direction": self.direction,
            "evidence_status": self.evidence_status,
            "feature_evidence_summary": self.feature_evidence_summary.__dict__,
            "divergence_summary": dict(self.divergence_summary),
            "regime_context": dict(self.regime_context),
            "suitability_status": self.suitability_status,
            "research_suitability": self.research_suitability,
            "execution_suitability": self.execution_suitability,
            "data_status": self.data_status,
            "cost_status": self.cost_status,
            "liquidity_status": self.liquidity_status,
            "data_grade": self.data_grade,
            "sample_count": self.sample_count,
            "effective_evidence_count": self.effective_evidence_count,
            "uncertainty": self.uncertainty,
            "ranking_score": self.ranking_score,
            "ranking_score_semantics": self.ranking_score_semantics,
            "ranking_components": dict(self.ranking_components),
            "rank": self.rank,
            "eligibility_status": self.eligibility_status,
            "reasons": self.reasons,
            "blockers": self.blockers,
            "input_feature_versions": self.input_feature_versions,
            "regime_version": self.regime_version,
            "suitability_version": self.suitability_version,
            "effectiveness_version": self.effectiveness_version,
            "ranking_version": self.ranking_version,
            "provenance": dict(self.provenance),
            "input_evidence": dict(self.input_evidence),
        }


@dataclass(frozen=True)
class OpportunityRanking:
    evaluated_at: datetime
    ranking_version: str
    top_n: int
    top_opportunities: tuple[ResearchOpportunity, ...]
    opportunities: tuple[ResearchOpportunity, ...]


def _summary(records):
    learned = tuple(item for item in records if item.status == "LEARNED")
    insufficient = tuple(item for item in records if item.status != "LEARNED")
    positive = tuple(item for item in learned if (item.expected_return_net or 0) > 0)
    negative = tuple(item for item in learned if (item.expected_return_net or 0) < 0)
    return FeatureEvidenceSummary(
        len(learned), len(insufficient), len(positive), len(negative),
        sum(item.sample_count for item in records),
        sum(item.effective_sample_count for item in records),
        (sum(item.confidence for item in learned if item.confidence is not None) /
         sum(item.confidence is not None for item in learned)
         if any(item.confidence is not None for item in learned) else None),
        tuple(sorted({item.fallback_level for item in records})),
        tuple(sorted(item.feature_id for item in negative)),
    )


def _direction(divergence):
    if divergence is None or divergence.state in {"LOW_EVIDENCE", "UNAVAILABLE"}:
        return "UNKNOWN"
    if divergence.dominant_direction == 1:
        return "LONG"
    if divergence.dominant_direction == -1:
        return "SHORT"
    return "WATCH"


def _divergence_component(divergence):
    return {"HIGH_AGREEMENT": 1.0, "DOMINANT_WITH_CONFLICT": .7,
            "HIGH_DISAGREEMENT": .3, "LOW_EVIDENCE": .1,
            "UNAVAILABLE": 0.0}.get(getattr(divergence, "state", "UNAVAILABLE"), 0.0)


class OpportunityRanker:
    """Rank canonical research candidates without producing any trade intent."""

    def __init__(self, config=RankingConfig()):
        self.config = config

    def _evaluate(self, candidate, evaluated_at):
        instrument, suitability = candidate.instrument, candidate.suitability
        blockers = list(suitability.blockers)
        reasons = list(suitability.reasons)
        if instrument.instrument_id != suitability.instrument_id:
            blockers.append("INSTRUMENT_IDENTITY_MISMATCH")
        if candidate.broker_mapping is not None and (
                candidate.broker_mapping.canonical_instrument_id != instrument.instrument_id):
            blockers.append("BROKER_MAPPING_IDENTITY_MISMATCH")
        if instrument.governance_state in {GovernanceState.BLOCKED, GovernanceState.DISABLED}:
            blockers.append("INSTRUMENT_GOVERNANCE_BLOCK")
        if suitability.evaluated_at > evaluated_at:
            blockers.append("FUTURE_SUITABILITY_INPUT")
        if suitability.overall_status in {"BLOCKED", "UNSUPPORTED"} or not suitability.hard_eligible:
            status = "BLOCKED" if suitability.overall_status == "BLOCKED" else "UNSUPPORTED"
        elif blockers:
            status = "BLOCKED" if "INSTRUMENT_GOVERNANCE_BLOCK" in blockers else "UNSUPPORTED"
        else:
            status = None

        effectiveness = tuple(item for item in candidate.effectiveness
                              if item.evaluated_at <= evaluated_at
                              and (item.matured_through is None or item.matured_through <= evaluated_at)
                              and item.instrument_id == suitability.instrument_id
                              and item.horizon_id == suitability.horizon_id)
        divergence = candidate.divergence
        if divergence is not None and (divergence.evaluated_at > evaluated_at or
                                       divergence.instrument_id != suitability.instrument_id or
                                       divergence.horizon_id != suitability.horizon_id):
            divergence = None
            reasons.append("DIVERGENCE_UNAVAILABLE_AT_EVALUATION")
        regime = candidate.regime
        if regime is not None and regime.evaluated_at > evaluated_at:
            regime = None
            reasons.append("REGIME_UNAVAILABLE_AT_EVALUATION")
        summary = _summary(effectiveness)
        if status is None and (suitability.overall_status == "INSUFFICIENT_EVIDENCE" or
                               not summary.learned_count):
            status = "INSUFFICIENT_EVIDENCE"
            blockers.append("REQUIRED_EFFECTIVENESS_EVIDENCE_ABSENT")

        direction = _direction(divergence)
        if status is None:
            status = "WATCH" if direction in {"WATCH", "UNKNOWN"} else "ELIGIBLE"

        uncertainty = []
        if summary.sample_count < self.config.evidence_target:
            uncertainty.append("LIMITED_SAMPLE_DEPTH")
        if any(level != "instrument+horizon+regime" for level in summary.fallback_levels):
            uncertainty.append("BROADER_EFFECTIVENESS_FALLBACK")
        if suitability.liquidity_status == "UNKNOWN":
            uncertainty.append("LIQUIDITY_UNKNOWN")
        if suitability.cost_status == "UNKNOWN":
            uncertainty.append("COST_UNKNOWN")
        if regime is None or regime.availability != "AVAILABLE":
            uncertainty.append("REGIME_UNAVAILABLE")
        if divergence is None or divergence.state in {"LOW_EVIDENCE", "UNAVAILABLE"}:
            uncertainty.append("DIRECTIONAL_EVIDENCE_WEAK")
        elif divergence.state in {"HIGH_DISAGREEMENT", "DOMINANT_WITH_CONFLICT"}:
            uncertainty.append("DIVERGENCE_CONFLICT_PRESENT")
        if candidate.data_grade != "EXECUTION_GRADE_DATA":
            uncertainty.append("DATA_NOT_EXECUTION_GRADE")

        suitability_component = suitability.overall_score or 0.0
        effectiveness_component = ((summary.positive_count + .5 *
                                    (summary.learned_count - summary.positive_count - summary.negative_count)) /
                                   summary.learned_count if summary.learned_count else 0.0)
        depth_component = min(1.0, summary.effective_sample_count / self.config.evidence_target)
        stability_component = 1.0 if suitability.stability_status == "SUPPORTED" else .25
        directional_component = getattr(divergence, "dominance_margin", None) or 0.0
        exact_regime = tuple(item for item in effectiveness if
                             item.fallback_level == "instrument+horizon+regime" and regime is not None and
                             item.regime_state == regime.trend_state)
        regime_component = (sum((item.expected_return_net or 0) >= 0 for item in exact_regime) /
                            len(exact_regime) if exact_regime else .5 if regime is not None else 0.0)
        divergence_component = _divergence_component(divergence)
        data_component = 1.0 if candidate.data_grade == "EXECUTION_GRADE_DATA" else (
            .75 if candidate.data_grade == "RESEARCH_DATA" and suitability.data_status == "AVAILABLE" else .25)
        uncertainty_penalty = min(1.0, len(uncertainty) / 6)
        cost_penalty = (min(1.0, suitability.expected_cost_bps / self.config.cost_penalty_cap_bps)
                        if suitability.expected_cost_bps is not None else 0.0)
        components = {
            "suitability": suitability_component,
            "effectiveness_support": effectiveness_component,
            "evidence_depth": depth_component,
            "stability": stability_component,
            "directional_strength": directional_component,
            "regime_context": regime_component,
            "divergence_state": divergence_component,
            "data_quality": data_component,
            "uncertainty_penalty": uncertainty_penalty,
            "cost_penalty": cost_penalty,
        }
        score = None
        if status in {"ELIGIBLE", "WATCH"}:
            positive = sum(components[name] * getattr(self.config, name + "_weight") for name in (
                "suitability", "evidence_depth", "stability"))
            positive += components["effectiveness_support"] * self.config.effectiveness_weight
            positive += components["directional_strength"] * self.config.directional_weight
            positive += components["regime_context"] * self.config.regime_context_weight
            positive += components["divergence_state"] * self.config.divergence_weight
            positive += components["data_quality"] * self.config.data_quality_weight
            score = round(100 * max(0.0, min(1.0, positive -
                components["uncertainty_penalty"] * self.config.uncertainty_penalty_weight -
                components["cost_penalty"] * self.config.cost_penalty_weight)), 6)
        if summary.negative_count:
            reasons.append("NEGATIVE_EFFECTIVENESS_REDUCES_SUPPORT")
        if divergence is not None:
            reasons.append("DIVERGENCE_" + divergence.state)
        if direction == "UNKNOWN":
            reasons.append("NO_SUPPORTED_CURRENT_DIRECTION")
        mapping = candidate.broker_mapping
        if mapping is None:
            reasons.append("EXECUTION_MAPPING_UNAVAILABLE_RESEARCH_ONLY")
        identity = f"{instrument.instrument_id}|{suitability.horizon_id}|{evaluated_at.isoformat()}|{self.config.version}"
        opportunity_id = "opp:" + sha256(identity.encode()).hexdigest()
        divergence_summary = ({"state": divergence.state,
                               "dominant_direction": divergence.dominant_direction,
                               "dominance_margin": divergence.dominance_margin,
                               "disagreement_ratio": divergence.disagreement_ratio,
                               "agreement_strength": divergence.agreement_strength,
                               "evidence_coverage": divergence.evidence_coverage}
                              if divergence else {"state": "UNAVAILABLE"})
        regime_context = ({"trend": regime.trend_state, "volatility": regime.volatility_state,
                           "macro_risk": regime.macro_risk_state, "liquidity": regime.liquidity_state,
                           "availability": regime.availability} if regime else {"availability": "UNAVAILABLE"})
        versions = tuple(sorted({item.feature_version for item in effectiveness} |
                                ({divergence.feature_version} if divergence else set())))
        effectiveness_versions = {item.configuration_version for item in effectiveness}
        return ResearchOpportunity(
            opportunity_id, evaluated_at.astimezone(timezone.utc), self.config.version,
            instrument.instrument_id, suitability.horizon_id,
            mapping.broker if mapping else None, mapping.mapping_status if mapping else "UNAVAILABLE",
            mapping.epic if mapping else None, direction,
            "SUFFICIENT" if summary.learned_count else "INSUFFICIENT", summary, divergence_summary,
            regime_context, suitability.overall_status, suitability.research_suitability,
            suitability.execution_suitability, suitability.data_status, suitability.cost_status,
            suitability.liquidity_status, candidate.data_grade, summary.sample_count,
            summary.effective_sample_count, tuple(dict.fromkeys(uncertainty)), score,
            SCORE_SEMANTICS, components, None, status,
            tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(blockers)), versions,
            regime.regime_version if regime else None, suitability.suitability_version,
            next(iter(effectiveness_versions)) if len(effectiveness_versions) == 1 else
            "MIXED" if effectiveness_versions else None, self.config.version,
            {"instrument_registry_version": "canonical-instrument-registry-v1",
             "divergence_configuration_version": getattr(divergence, "configuration_version", None),
             "broker_mapping_version": getattr(mapping, "version", None)},
            input_evidence=causal_input_evidence(candidate.input_evidence, evaluated_at),
        )

    def rank(self, candidates, *, evaluated_at, top_n=5):
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if not isinstance(top_n, int) or top_n < 1:
            raise ValueError("top_n must be a positive integer")
        evaluated = tuple(self._evaluate(item, evaluated_at) for item in candidates)
        rankable = sorted((item for item in evaluated if item.ranking_score is not None),
                          key=lambda item: (-item.ranking_score, item.instrument_id,
                                            item.horizon_id, item.opportunity_id))
        ranked = tuple(replace(item, rank=index) for index, item in enumerate(rankable, 1))
        ranks = {item.opportunity_id: item for item in ranked}
        unranked = sorted((item for item in evaluated if item.ranking_score is None),
                          key=lambda item: (item.eligibility_status, item.instrument_id, item.horizon_id))
        all_items = tuple(ranks.get(item.opportunity_id, item) for item in rankable) + tuple(unranked)
        return OpportunityRanking(evaluated_at.astimezone(timezone.utc), self.config.version, top_n,
                                  ranked[:top_n], all_items)


def rank_opportunities(candidates, *, evaluated_at, top_n=5, config=RankingConfig()):
    return OpportunityRanker(config).rank(candidates, evaluated_at=evaluated_at, top_n=top_n)


__all__ = ["FeatureEvidenceSummary", "OpportunityCandidate", "OpportunityRanker",
           "OpportunityRanking", "RankingConfig", "ResearchOpportunity", "SCORE_SEMANTICS",
           "VERSION", "rank_opportunities"]
