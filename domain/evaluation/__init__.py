"""Canonical research evaluation contracts."""

from .opportunity import (OpportunityCandidate, OpportunityRanker, OpportunityRanking,
                          RankingConfig, ResearchOpportunity, rank_opportunities)

__all__ = ["OpportunityCandidate", "OpportunityRanker", "OpportunityRanking",
           "RankingConfig", "ResearchOpportunity", "rank_opportunities"]
