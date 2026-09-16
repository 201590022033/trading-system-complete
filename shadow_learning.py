"""Validated, broker-independent contracts for the persistent shadow loop."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

def _aware(value: str) -> None:
    if not isinstance(value, str) or not value.endswith(("+00:00", "Z")):
        raise ValueError("timestamps must be UTC")

@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    instrument: str
    observed_at: str
    horizon: str
    market_data: dict[str, Any]
    production_context: dict[str, Any] = field(default_factory=dict)
    research_context: dict[str, Any] = field(default_factory=dict)
    source_version: str = "unknown"
    pipeline_version: str = "unknown"
    created_at: str = ""
    def __post_init__(self):
        if not self.instrument or not self.horizon: raise ValueError("instrument and horizon are required")
        _aware(self.observed_at)
        if self.created_at: _aware(self.created_at)
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ShadowDecision:
    decision_id: str
    observation_id: str
    instrument: str
    decided_at: str
    horizon: str
    action: str
    production_assessment: dict[str, Any]
    research_context: dict[str, Any] = field(default_factory=dict)
    pipeline_version: str = "unknown"
    outcome_status: str = "PENDING_OUTCOME"
    def __post_init__(self):
        _aware(self.decided_at)
        if self.action not in {"BUY", "HOLD", "SELL"}: raise ValueError("invalid action")
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class OutcomeLabel:
    outcome_id: str
    decision_id: str
    matured_at: str
    label: str
    entry_price: float
    exit_price: float | None = None
    gross_return: float | None = None
    net_return: float | None = None
    cost_model: str = "existing"
    data_quality: str = "COMPLETE"
    def __post_init__(self): _aware(self.matured_at)
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class AdaptiveEvidence:
    evidence_id: str
    instrument: str
    horizon: str
    regime: str
    profile: str
    sample_count: int
    wins: int
    losses: int
    mean_net_return: float | None
    reliability_state: str
    governance_state: str = "SHADOW_ADAPTIVE_EVIDENCE"
    updated_at: str = ""
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class JobCheckpoint:
    job_key: str
    job_type: str
    target_time: str
    status: str = "PENDING"
    worker_id: str | None = None
    attempt_count: int = 0
    checkpoint: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    error_category: str | None = None
    last_updated: str = ""
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class LearningStatus:
    observations: dict[str, int]
    shadow_decisions: dict[str, int]
    labelled_outcomes: dict[str, int]
    pending_outcomes: int
    adaptive_updates: dict[str, int]
    latest_timestamps: dict[str, str | None]
    worker_status: dict[str, Any]
    database_backend: str
    database_state: str
