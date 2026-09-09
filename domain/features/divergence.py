"""Causal, unweighted disagreement features for research use only."""

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite, sqrt
from statistics import mean
from typing import Mapping

VERSION = "divergence-v1"
UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class SignalEvidence:
    feature_id: str
    feature_version: str
    state: int | None
    available_time: datetime | None
    value: float | None = None
    instrument_id: str = ""
    horizon_id: str = ""
    category: str = ""

    def __post_init__(self):
        if self.state not in (-1, 0, 1, None):
            raise ValueError("signal state must be -1, 0, 1 or unavailable")
        if self.available_time is not None and (self.available_time.tzinfo is None or self.available_time.utcoffset() is None):
            raise ValueError("available_time must be timezone-aware")
        if self.value is not None and not isfinite(self.value):
            raise ValueError("signal value must be finite")


@dataclass(frozen=True)
class DivergenceConfig:
    expected_signal_count: int
    minimum_active_count: int = 1
    version: str = VERSION

    def __post_init__(self):
        if self.expected_signal_count < 1 or self.minimum_active_count < 0:
            raise ValueError("evidence requirements must be positive")


@dataclass(frozen=True)
class DivergenceFeature:
    feature_version: str
    evaluated_at: datetime
    instrument_id: str
    horizon_id: str
    state: str
    active_signal_count: int
    positive_signal_count: int
    negative_signal_count: int
    neutral_signal_count: int
    unavailable_signal_count: int
    directional_balance: float | None
    disagreement_ratio: float | None
    agreement_strength: float | None
    signal_dispersion: float | None
    bullish_intensity: float | None
    bearish_intensity: float | None
    dominant_direction: int | None
    dominance_margin: float | None
    evidence_coverage: float
    contributing_feature_ids: tuple[str, ...] = ()
    contributing_feature_versions: tuple[str, ...] = ()
    input_availability: tuple[str, ...] = ()
    regime_version: str | None = None
    regime_state: Mapping[str, str] = field(default_factory=dict)
    configuration_version: str = VERSION

    def __post_init__(self):
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        if self.state not in {"LOW_EVIDENCE", "HIGH_AGREEMENT", "HIGH_DISAGREEMENT", "DOMINANT_WITH_CONFLICT", UNAVAILABLE}:
            raise ValueError("invalid divergence state")
        if not 0 <= self.evidence_coverage <= 1:
            raise ValueError("evidence coverage must be between zero and one")

    def to_dict(self):
        result = self.__dict__.copy()
        result["evaluated_at"] = self.evaluated_at.isoformat()
        result["regime_state"] = dict(self.regime_state)
        return result


def _dispersion(values):
    if len(values) < 2:
        return 0.0 if values else None
    average = mean(values)
    return sqrt(mean((value - average) ** 2 for value in values))


def _build(evidence, evaluated_at, config, *, instrument_id="", horizon_id="", regime=None):
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("evaluated_at must be timezone-aware")
    evidence = tuple(evidence)
    usable = tuple(item for item in evidence if item.available_time is not None and item.available_time <= evaluated_at)
    # Inputs published after evaluation are outside the feature's evidence set;
    # they must not alter counts, coverage or provenance for the earlier state.
    unavailable = sum(item.state is None for item in usable)
    positives = sum(item.state == 1 for item in usable)
    negatives = sum(item.state == -1 for item in usable)
    neutrals = sum(item.state == 0 for item in usable)
    active = positives + negatives
    coverage = len(usable) / config.expected_signal_count
    balance = (positives - negatives) / active if active else None
    opposition = 2 * min(positives, negatives) / active if active else None
    agreement = max(positives, negatives) / active if active else None
    values = tuple(item.value for item in usable if item.value is not None)
    state = UNAVAILABLE if not usable else "LOW_EVIDENCE" if active < config.minimum_active_count else (
        "HIGH_DISAGREEMENT" if positives == negatives else
        "DOMINANT_WITH_CONFLICT" if positives and negatives else "HIGH_AGREEMENT")
    dominant = 1 if positives > negatives else -1 if negatives > positives else None
    margin = abs(balance) if balance is not None else None
    regime_version = getattr(regime, "regime_version", None)
    regime_state = ({
        "trend": regime.trend_state,
        "volatility": regime.volatility_state,
        "macro_risk": regime.macro_risk_state,
        "liquidity": regime.liquidity_state,
    } if regime is not None else {})
    return DivergenceFeature(
        VERSION, evaluated_at, instrument_id, horizon_id, state, active, positives, negatives, neutrals,
        unavailable, balance, opposition, agreement, _dispersion(values),
        positives / active if active else None, negatives / active if active else None,
        dominant, margin, min(1.0, coverage),
        tuple(item.feature_id for item in usable),
        tuple(item.feature_version for item in usable),
        tuple(item.available_time.isoformat() for item in usable), regime_version, regime_state,
        config.version,
    )


def summarize(evidence, evaluated_at, config, *, instrument_id="", horizon_id="", regime=None):
    """Summarize causal signal evidence without learned or implicit weights."""
    return _build(evidence, evaluated_at, config, instrument_id=instrument_id,
                  horizon_id=horizon_id, regime=regime)


def pairwise(left, right, evaluated_at, config, *, instrument_id="", horizon_id="", regime=None):
    """Return a two-input disagreement feature while retaining each input ID."""
    return summarize((left, right), evaluated_at, config, instrument_id=instrument_id,
                     horizon_id=horizon_id, regime=regime)


def grouped(groups, evaluated_at, config, *, instrument_id="", horizon_id="", regime=None):
    """Summarize named groups; group names remain in provenance IDs."""
    evidence = tuple(item for name, values in groups.items() for item in values)
    return summarize(evidence, evaluated_at, config, instrument_id=instrument_id,
                     horizon_id=horizon_id, regime=regime)


__all__ = ["DivergenceConfig", "DivergenceFeature", "SignalEvidence", "VERSION",
           "grouped", "pairwise", "summarize"]
