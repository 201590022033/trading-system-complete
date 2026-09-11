"""Canonical research evaluation contracts."""

from .opportunity import (OpportunityCandidate, OpportunityRanker, OpportunityRanking,
                          RankingConfig, ResearchOpportunity, rank_opportunities)
from .target import (Comparison, EvidenceStage, MetricIdentity, MetricObservation,
                     RequirementLevel, StrategyTarget, TargetCriterion, TargetStatus,
                     assess_target, canonical_annualized_sharpe, legacy_tstat_like_v1)
from .experiment import (ExperimentDefinition, ExperimentRun, ExperimentResult,
                         ExperimentDecision, InMemoryExperimentRepository)

__all__ = ["OpportunityCandidate", "OpportunityRanker", "OpportunityRanking",
           "RankingConfig", "ResearchOpportunity", "rank_opportunities"]
__all__ += ["Comparison", "EvidenceStage", "MetricIdentity", "MetricObservation",
            "RequirementLevel", "StrategyTarget", "TargetCriterion", "TargetStatus",
            "assess_target", "canonical_annualized_sharpe", "legacy_tstat_like_v1"]
__all__ += ["ExperimentDefinition", "ExperimentRun", "ExperimentResult",
            "ExperimentDecision", "InMemoryExperimentRepository"]
