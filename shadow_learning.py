"""Validated, broker-independent contracts for the persistent shadow loop."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import math
import hashlib
import json
from typing import Any

def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)

def _aware(value: str) -> None:
    timestamp(value)

def _normalize(record, *names):
    for name in names:
        value = getattr(record, name)
        if value:
            object.__setattr__(record, name, timestamp(value).isoformat())

def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite numeric value required")

def stable_id(kind, *parts):
    encoded=json.dumps(parts,ensure_ascii=True,separators=(",",":"))
    return kind+":"+hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def canonical_instrument(value):
    from instrument_registry import resolve_instrument
    if not isinstance(value,str) or not value.strip():
        raise ValueError("instrument required")
    try: return resolve_instrument(value).instrument_id
    except KeyError: return value.strip().upper()

def evidence_key(evidence, lookup):
    dimensions=(evidence.instrument,str(evidence.horizon),evidence.regime,evidence.profile)
    legacy="|".join(dimensions)
    previous=lookup(legacy)
    # Preserve identity of valid pre-repair contributions without rewriting data.
    if previous and tuple(str(previous[n]) for n in ('instrument','horizon','regime','profile'))==dimensions:
        return legacy
    return stable_id("cell",*dimensions)

def causal_metadata(value, cutoff):
    """Reject outcome data and future-dated metadata at the observation boundary."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"exit_price", "forward_return", "net_return", "outcome", "outcome_label"}:
                raise ValueError("outcome data is not observation context")
            if key in {"event_time", "available_time", "observed_at", "published_at", "available_at"} and item:
                if timestamp(item) > cutoff:
                    raise ValueError("future observation context")
            causal_metadata(item, cutoff)
    elif isinstance(value, (list, tuple)):
        for item in value:
            causal_metadata(item, cutoff)
    elif isinstance(value, float):
        _finite(value)

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
        object.__setattr__(self,"instrument",canonical_instrument(self.instrument))
        object.__setattr__(self,"horizon",str(self.horizon))
        _normalize(self, "observed_at", "created_at")
        for value in (self.market_data, self.production_context, self.research_context):
            causal_metadata(value, timestamp(self.observed_at))
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
    horizon_context: dict[str, Any] = field(default_factory=dict)
    previous_signal: float = 0.0
    provenance: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"instrument",canonical_instrument(self.instrument))
        object.__setattr__(self,"horizon",str(self.horizon))
        _normalize(self, "decided_at")
        if self.action not in {"BUY", "HOLD", "SELL"}: raise ValueError("invalid action")
        if self.previous_signal not in {-1, 0, 1}: raise ValueError("invalid previous signal")
        if self.outcome_status not in {"PENDING_OUTCOME", "LABELLED", "OUTCOME_DATA_UNAVAILABLE"}:
            raise ValueError("invalid outcome status")
        causal_metadata(self.research_context, timestamp(self.decided_at))
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class OutcomeLabel:
    outcome_id: str
    decision_id: str
    matured_at: str
    label: str
    entry_price: float | None
    exit_price: float | None = None
    gross_return: float | None = None
    net_return: float | None = None
    cost_model: str = "existing"
    data_quality: str = "COMPLETE"
    evaluated_at: str = ""
    entry_at: str = ""
    exit_at: str = ""
    entry_available_at: str = ""
    exit_available_at: str = ""
    def __post_init__(self):
        _normalize(self, "matured_at", "evaluated_at", "entry_at", "exit_at", "entry_available_at", "exit_available_at")
        if self.label not in {"WIN", "LOSS", "HOLD", "OUTCOME_DATA_UNAVAILABLE"}:
            raise ValueError("unsupported label")
        for value in (self.entry_price, self.exit_price, self.gross_return, self.net_return):
            if value is not None: _finite(value)
        for price in (self.entry_price, self.exit_price):
            if price is not None and price <= 0: raise ValueError("price must be positive")
        if self.label != "OUTCOME_DATA_UNAVAILABLE":
            if self.data_quality != "COMPLETE" or any(v is None for v in (self.entry_price, self.exit_price, self.gross_return, self.net_return)):
                raise ValueError("label requires complete prices and returns")
        elif self.gross_return is not None or self.net_return is not None:
            raise ValueError("unavailable data cannot carry returns")
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
    def __post_init__(self):
        object.__setattr__(self,"instrument",canonical_instrument(self.instrument))
        object.__setattr__(self,"horizon",str(self.horizon))
        _normalize(self,"updated_at")
        if self.mean_net_return is not None: _finite(self.mean_net_return)
        if self.governance_state != "SHADOW_ADAPTIVE_EVIDENCE": raise ValueError("shadow governance required")
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
    def __post_init__(self):
        _normalize(self,"target_time","last_updated")
        if self.status not in {"PENDING","RUNNING","COMPLETED","FAILED"} or self.attempt_count < 0:
            raise ValueError("invalid durable job state")
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
