"""Canonical instrument suitability evaluation; research output only."""

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean

from intraday_instruments import DataGrade, InstrumentDefinition

VERSION = "instrument-suitability-v1"


@dataclass(frozen=True)
class SuitabilityEvidence:
    data_status: str
    data_grade: DataGrade | None
    source_type: str
    resolution: str
    history_depth: int
    missingness: float | None = None
    timestamp_quality: str = "UNKNOWN"
    coverage_period: str | None = None


@dataclass(frozen=True)
class CostEvidence:
    status: str
    expected_cost_bps: float | None = None
    basis: str = "UNKNOWN"


@dataclass(frozen=True)
class LiquidityEvidence:
    status: str
    observed: bool = False
    reason: str = ""


@dataclass(frozen=True)
class InstrumentSuitability:
    instrument_id: str
    horizon_id: str
    evaluated_at: datetime
    suitability_version: str
    overall_status: str
    overall_score: float | None
    hard_eligible: bool
    research_suitability: str
    execution_suitability: str
    data_status: str
    execution_status: str
    cost_status: str
    liquidity_status: str
    feature_evidence_status: str
    regime_coverage_status: str
    history_depth: int
    evidence_sample_count: int
    learned_feature_count: int
    insufficient_feature_count: int
    positive_evidence_count: int
    negative_evidence_count: int
    stability_status: str
    expected_cost_bps: float | None
    blockers: tuple[str, ...]
    reasons: tuple[str, ...]
    provenance: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if self.overall_status not in {"SUITABLE", "CONDITIONALLY_SUITABLE", "INSUFFICIENT_EVIDENCE", "UNSUPPORTED", "BLOCKED"}:
            raise ValueError("invalid suitability status")
        if self.overall_score is not None and not 0 <= self.overall_score <= 1:
            raise ValueError("suitability score must be bounded")


@dataclass(frozen=True)
class DiscoveredInstrument:
    """Unresolved candidates never enter the canonical production registry."""

    instrument_id: str
    display_name: str
    source: str
    resolved: bool = False
    human_permitted: bool = False
    candidate_state: str = "CANDIDATE / RESEARCH"


def _feature_summary(records):
    records = tuple(records)
    learned = tuple(item for item in records if item.status == "LEARNED")
    insufficient = tuple(item for item in records if item.status == "INSUFFICIENT_EVIDENCE")
    positive = tuple(item for item in learned if item.expected_return_net is not None and item.expected_return_net > 0)
    negative = tuple(item for item in learned if item.expected_return_net is not None and item.expected_return_net < 0)
    return records, learned, insufficient, positive, negative


def evaluate_suitability(instrument: InstrumentDefinition, horizon_id: str, evaluated_at: datetime,
                         *, data: SuitabilityEvidence, features=(), costs=None, liquidity=None,
                         execution_required=False, human_permitted=True, manually_blocked=False,
                         regime_coverage="UNKNOWN", provenance=None) -> InstrumentSuitability:
    """Evaluate hard eligibility first, then report independent soft dimensions."""
    if not isinstance(instrument, InstrumentDefinition):
        raise TypeError("canonical InstrumentDefinition required")
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("evaluated_at must be timezone-aware")
    intraday = horizon_id.startswith("intraday_")
    blockers, reasons = [], []
    if manually_blocked:
        blockers.append("MANUALLY_BLOCKED")
    if not human_permitted:
        blockers.append("HUMAN_PERMISSION_REQUIRED")
    if intraday and not instrument.supports_intraday:
        blockers.append("UNSUPPORTED_HORIZON")
    if not instrument.supports_historical_data:
        blockers.append("NO_HISTORICAL_DATA_CAPABILITY")
    if data.data_status in {"UNAVAILABLE", "MISSING"} or data.history_depth <= 0:
        blockers.append("DATA_UNAVAILABLE")
    if data.data_grade is None:
        blockers.append("DATA_GRADE_UNKNOWN")
    if execution_required:
        if not instrument.execution_symbol:
            blockers.append("MISSING_EXECUTION_SYMBOL")
        if any(getattr(instrument, field) is None for field in ("contract_multiplier", "tick_size", "lot_size")):
            blockers.append("INCOMPLETE_EXECUTION_METADATA")
    hard_eligible = not blockers
    if data.missingness is not None and data.missingness > 0:
        reasons.append("DATA_MISSINGNESS_REPORTED")
    if intraday and data.data_grade != DataGrade.EXECUTION:
        reasons.append("INTRADAY_NOT_EXECUTION_GRADE")
    records, learned, insufficient, positive, negative = _feature_summary(features)
    if not records:
        feature_status = "UNAVAILABLE"
    elif learned:
        feature_status = "SUPPORTED" if not insufficient else "PARTIAL"
    else:
        feature_status = "INSUFFICIENT_EVIDENCE"
    if not learned:
        reasons.append("FEATURE_EVIDENCE_INSUFFICIENT")
    if insufficient:
        reasons.append("SPARSE_FEATURE_CELLS_RETAINED")
    cost_status = costs.status if costs else "UNKNOWN"
    liquidity_status = liquidity.status if liquidity else "UNKNOWN"
    execution_status = "SUPPORTED" if instrument.execution_symbol and not execution_required is False else (
        "RESEARCH_ONLY" if not execution_required else "UNAVAILABLE")
    if costs and costs.status == "ASSUMED":
        reasons.append("COSTS_ASSUMED")
    if liquidity is None or not liquidity.observed:
        reasons.append("LIQUIDITY_UNAVAILABLE")
    if regime_coverage == "UNKNOWN":
        reasons.append("REGIME_COVERAGE_UNKNOWN")
    stability = "INSUFFICIENT" if len(learned) < 2 else "SUPPORTED"
    soft = [1.0 if feature_status == "SUPPORTED" else .5 if feature_status == "PARTIAL" else 0.0,
            1.0 if cost_status == "OBSERVED" else .5 if cost_status == "ASSUMED" else 0.0,
            1.0 if liquidity_status in {"OBSERVED", "GOOD"} else 0.0,
            1.0 if stability == "SUPPORTED" else 0.0]
    score = mean(soft) if soft else None
    if not hard_eligible:
        status = "BLOCKED" if manually_blocked or not human_permitted else "UNSUPPORTED"
    elif not learned or data.data_status in {"PARTIAL", "UNKNOWN"}:
        status = "INSUFFICIENT_EVIDENCE"
    elif score is not None and score >= .75:
        status = "SUITABLE"
    else:
        status = "CONDITIONALLY_SUITABLE"
    return InstrumentSuitability(
        instrument.instrument_id, horizon_id, evaluated_at, VERSION, status, score, hard_eligible,
        "RESEARCH-SUITABLE" if hard_eligible else "NOT_RESEARCH-SUITABLE",
        "EXECUTION-SUITABLE" if execution_required and hard_eligible and instrument.execution_symbol else "RESEARCH-ONLY",
        data.data_status, execution_status, cost_status, liquidity_status, feature_status, regime_coverage,
        data.history_depth, len(records), len(learned), len(insufficient), len(positive), len(negative),
        stability, costs.expected_cost_bps if costs else None, tuple(blockers), tuple(dict.fromkeys(reasons)),
        {"instrument_registry_version": instrument.version, "data_source": data.source_type,
         "candidate": False, **(provenance or {})},
    )


__all__ = ["CostEvidence", "DiscoveredInstrument", "InstrumentSuitability", "LiquidityEvidence",
           "SuitabilityEvidence", "VERSION", "evaluate_suitability"]
