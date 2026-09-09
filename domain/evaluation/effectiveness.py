"""Causal contextual feature-effectiveness estimates for research only."""

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite, sqrt
from statistics import mean

VERSION = "contextual-effectiveness-v1"


@dataclass(frozen=True)
class EffectivenessConfig:
    minimum_sample: int = 30
    prior_strength: float = 20.0
    prior_return: float = 0.0
    recency_half_life_seconds: float | None = None
    version: str = VERSION

    def __post_init__(self):
        if self.minimum_sample < 1 or self.prior_strength < 0:
            raise ValueError("invalid effectiveness evidence configuration")
        if not isfinite(self.prior_return):
            raise ValueError("prior return must be finite")
        if self.recency_half_life_seconds is not None and self.recency_half_life_seconds <= 0:
            raise ValueError("recency half-life must be positive")


@dataclass(frozen=True)
class FeatureOutcome:
    feature_id: str
    feature_version: str
    feature_family: str
    instrument_id: str
    horizon_id: str
    regime_version: str | None
    regime_state: str | None
    signal_state: int | None
    evaluated_at: datetime
    available_time: datetime
    outcome_maturity: datetime
    gross_return: float
    net_return: float
    record_id: str = ""

    def __post_init__(self):
        for name in ("evaluated_at", "available_time", "outcome_maturity"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if not self.available_time <= self.evaluated_at < self.outcome_maturity:
            raise ValueError("outcome clocks must be feature-available, then mature")
        if not all(isfinite(value) for value in (self.gross_return, self.net_return)):
            raise ValueError("outcomes must be finite")
        if self.signal_state not in (-1, 0, 1, None):
            raise ValueError("invalid signal state")


@dataclass(frozen=True)
class FeatureEffectiveness:
    feature_id: str
    feature_version: str
    feature_family: str
    instrument_id: str
    horizon_id: str
    regime_version: str | None
    regime_state: str | None
    evaluated_at: datetime
    matured_through: datetime | None
    sample_count: int
    effective_sample_count: float
    positive_outcomes: int
    negative_outcomes: int
    neutral_outcomes: int
    expected_return_gross: float | None
    expected_return_net: float | None
    hit_rate: float | None
    dispersion: float | None
    uncertainty: float | None
    confidence: float | None
    evidence_grade: str
    status: str
    fallback_level: str
    raw_estimate: float | None
    prior_estimate: float
    shrinkage_strength: float
    recency_half_life_seconds: float | None
    configuration_version: str
    lineage: tuple[str, ...] = field(default_factory=tuple)


def _finite_mean(values):
    return mean(values) if values else None


def _std_error(values):
    if len(values) < 2:
        return None
    average = mean(values)
    return sqrt(sum((value - average) ** 2 for value in values) / (len(values) - 1)) / sqrt(len(values))


class ContextualEffectivenessLearner:
    """Estimate attributable feature outcomes with causal hierarchical fallback."""

    def __init__(self, config=EffectivenessConfig()):
        self.config = config

    def _eligible(self, outcomes, evaluated_at):
        return tuple(sorted((outcome for outcome in outcomes
                             if outcome.available_time <= outcome.evaluated_at < evaluated_at
                             and outcome.outcome_maturity <= evaluated_at),
                            key=lambda outcome: (outcome.outcome_maturity, outcome.record_id)))

    @staticmethod
    def _levels(instrument_id, horizon_id, regime_state):
        exact = (instrument_id, horizon_id, regime_state)
        return ((exact, "instrument+horizon+regime"),
                ((instrument_id, horizon_id, None), "instrument+horizon"),
                ((instrument_id, None, None), "instrument"),
                ((None, None, None), "global"))

    def estimate(self, outcomes, *, feature_id, evaluated_at, instrument_id=None,
                 horizon_id=None, regime_state=None, regime_version=None):
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        all_eligible = tuple(item for item in self._eligible(outcomes, evaluated_at)
                             if item.feature_id == feature_id and
                             (regime_version is None or item.regime_version == regime_version))
        selected = ()
        fallback = "none"
        for (instrument, horizon, regime), level in self._levels(instrument_id, horizon_id, regime_state):
            selected = tuple(item for item in all_eligible
                             if (instrument is None or item.instrument_id == instrument) and
                             (horizon is None or item.horizon_id == horizon) and
                             (regime is None or item.regime_state == regime))
            if len(selected) >= self.config.minimum_sample or level == "global":
                fallback = level
                break
        if selected:
            feature_version = selected[0].feature_version
            family = selected[0].feature_family
        else:
            feature_version, family = "unknown", "unknown"
        gross = [item.gross_return for item in selected]
        net = [item.net_return for item in selected]
        weights = self._weights(selected, evaluated_at)
        effective_n = sum(weights)
        raw = sum(value * weight for value, weight in zip(net, weights)) / effective_n if net else None
        positive = sum(value > 0 for value in net)
        negative = sum(value < 0 for value in net)
        neutral = len(net) - positive - negative
        prior = self.config.prior_return
        shrink = self.config.prior_strength
        posterior = ((raw * effective_n + prior * shrink) / (effective_n + shrink)
                     if raw is not None else prior)
        status = "LEARNED" if len(selected) >= self.config.minimum_sample else "INSUFFICIENT_EVIDENCE"
        return FeatureEffectiveness(
            feature_id, feature_version, family, instrument_id or "", horizon_id or "",
            regime_version, regime_state, evaluated_at, max((item.outcome_maturity for item in selected), default=None),
            len(selected), effective_n, positive, negative, neutral,
            _finite_mean(gross), posterior if selected else None, positive / len(selected) if selected else None,
            _std_error(net), _std_error(net), min(1.0, len(selected) / self.config.minimum_sample) if selected else 0.0,
            "SUFFICIENT" if status == "LEARNED" else "INSUFFICIENT",
            status, fallback, raw, prior, shrink, self.config.recency_half_life_seconds,
            self.config.version, tuple(item.record_id for item in selected),
        )

    def _weights(self, outcomes, evaluated_at):
        half_life = self.config.recency_half_life_seconds
        if half_life is None:
            return (1.0,) * len(outcomes)
        return tuple(2 ** (-max(0.0, (evaluated_at - item.outcome_maturity).total_seconds()) / half_life)
                     for item in outcomes)


def learn_effectiveness(outcomes, **kwargs):
    """Convenience boundary; produces research records and no runtime weights."""
    return ContextualEffectivenessLearner().estimate(outcomes, **kwargs)


__all__ = ["ContextualEffectivenessLearner", "EffectivenessConfig", "FeatureEffectiveness",
           "FeatureOutcome", "VERSION", "learn_effectiveness"]
