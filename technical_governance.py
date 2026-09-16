"""Evidence-gated governance for candidate technical indicators.

This module is deliberately separate from production scoring: implementing a
feature never makes it contributing or production eligible.
"""
from dataclasses import dataclass
from enum import Enum

class IndicatorStatus(str, Enum):
    RESEARCH_ONLY="RESEARCH_ONLY"; CANDIDATE="CANDIDATE"; VALIDATED="VALIDATED"
    INSUFFICIENT_EVIDENCE="INSUFFICIENT_EVIDENCE"; REJECTED="REJECTED"; PRODUCTION_ELIGIBLE="PRODUCTION_ELIGIBLE"

@dataclass(frozen=True)
class IndicatorGovernance:
    indicator: str
    status: IndicatorStatus
    instrument: str | None = None
    horizon: str | None = None
    regime: str | None = None
    sample_count: int = 0
    reliability: float | None = None
    production: bool = False
    reason: str = ""

def assess(indicator: str, *, sample_count: int, reliability: float | None = None, instrument=None, horizon=None, regime=None) -> IndicatorGovernance:
    if sample_count < 30: status=IndicatorStatus.INSUFFICIENT_EVIDENCE
    elif reliability is None: status=IndicatorStatus.CANDIDATE
    elif reliability <= 0: status=IndicatorStatus.REJECTED
    else: status=IndicatorStatus.VALIDATED
    return IndicatorGovernance(indicator,status,instrument,horizon,regime,sample_count,reliability,False,"Evidence-gated research state")
