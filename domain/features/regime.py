"""Versioned regime contracts with isolated legacy and candidate models.

This module is deliberately additive. The reference implementations remain in
``regime_engine`` and ``intraday_signals``; candidate output is research-only.
"""

from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from typing import Mapping, Sequence

from regime_engine import MarketRegime as LegacyMarketRegime
from regime_engine import REGIME_VERSION, classify_regime

VERSION = "canonical-regime-contract-v1"
UNKNOWN = "UNKNOWN"
UNAVAILABLE = "UNAVAILABLE"
_STATES = {
    "trend": {UNKNOWN, UNAVAILABLE, "bull", "bear", "range", "up", "down"},
    "volatility": {UNKNOWN, UNAVAILABLE, "high", "normal", "low", "expanding", "contracting", "stable"},
    "macro_risk": {UNKNOWN, UNAVAILABLE, "risk_on", "risk_off", "neutral"},
    "liquidity": {UNKNOWN, UNAVAILABLE, "thin", "normal", "liquid"},
}


@dataclass(frozen=True)
class MarketRegime:
    evaluated_at: datetime
    regime_version: str
    trend_state: str = UNKNOWN
    volatility_state: str = UNKNOWN
    macro_risk_state: str = UNKNOWN
    liquidity_state: str = UNKNOWN
    metrics: Mapping[str, float] = field(default_factory=dict)
    feature_ids: tuple[str, ...] = ()
    confidence: float | None = None
    availability: str = "AVAILABLE"
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        for name in ("trend_state", "volatility_state", "macro_risk_state", "liquidity_state"):
            if getattr(self, name) not in _STATES[name.removesuffix("_state")]:
                raise ValueError(f"invalid {name}")
        if self.availability not in {"AVAILABLE", UNKNOWN, UNAVAILABLE}:
            raise ValueError("invalid availability state")
        if self.confidence is not None and (not isfinite(self.confidence) or not 0 <= self.confidence <= 1):
            raise ValueError("confidence must be between zero and one")
        if not isinstance(self.feature_ids, tuple):
            raise ValueError("feature_ids must be immutable")

    @property
    def version(self):
        return self.regime_version

    def to_dict(self):
        return {
            "evaluated_at": self.evaluated_at.isoformat(),
            "regime_version": self.regime_version,
            "trend_state": self.trend_state,
            "volatility_state": self.volatility_state,
            "macro_risk_state": self.macro_risk_state,
            "liquidity_state": self.liquidity_state,
            "metrics": dict(self.metrics),
            "feature_ids": list(self.feature_ids),
            "confidence": self.confidence,
            "availability": self.availability,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class RegimeParameters:
    """Candidate thresholds; values are configuration, not architecture truth."""

    trend_threshold: float
    high_volatility: float
    low_volatility: float
    trend_window: int = 20
    volatility_window: int = 20
    version: str = "regime-candidate-v2"

    def __post_init__(self):
        if self.trend_window < 1 or self.volatility_window < 2:
            raise ValueError("regime windows must be positive")
        if not all(isfinite(value) and value >= 0 for value in
                   (self.trend_threshold, self.high_volatility, self.low_volatility)):
            raise ValueError("regime thresholds must be finite and nonnegative")
        if self.high_volatility < self.low_volatility:
            raise ValueError("high volatility threshold must not be below low threshold")


@dataclass(frozen=True)
class RegimeDefinition:
    regime_id: str
    version: str
    required_inputs: tuple[str, ...]
    parameters: Mapping[str, object]
    supported_timeframes: tuple[str, ...]
    supported_asset_classes: tuple[str, ...]
    governance_state: str
    implementation: str


LEGACY_DAILY = RegimeDefinition(
    "regime_legacy_daily", REGIME_VERSION,
    ("close",), {"trend_window": 20, "volatility_window": 20, "trend_threshold": .02,
                   "high_volatility": .025, "low_volatility": .008},
    ("daily",), ("equity",), "REFERENCE / LEGACY", "regime_engine.classify_regime",
)
LEGACY_INTRADAY = RegimeDefinition(
    "regime_intraday_hr11", "intraday-signals-v1",
    ("ema_spread", "volatility_change", "relative_volume"), {},
    ("intraday",), ("equity",), "REFERENCE / LEGACY", "intraday_signals.regimes",
)
CANDIDATE_V2 = RegimeDefinition(
    "regime_candidate_multidimensional", "regime-candidate-v2",
    ("close",), {"thresholds": "RegimeParameters supplied per evaluation"},
    ("daily", "intraday"), ("equity",), "RESEARCH / CANDIDATE", "domain.features.regime.classify_candidate",
)


class RegimeRegistry:
    def __init__(self, definitions=(LEGACY_DAILY, LEGACY_INTRADAY, CANDIDATE_V2)):
        self._definitions = {(item.regime_id, item.version): item for item in definitions}

    def get(self, regime_id, version):
        return self._definitions[(regime_id, version)]

    def definitions(self):
        return tuple(self._definitions.values())


DEFAULT_REGIME_REGISTRY = RegimeRegistry()


def legacy_daily(prices: Sequence[float], **kwargs) -> LegacyMarketRegime:
    """Exact reference adapter; delegates without changing legacy semantics."""
    return classify_regime(list(prices), **kwargs)


def classify_candidate(prices: Sequence[float], evaluated_at: datetime,
                       parameters: RegimeParameters, *, available_times=None,
                       spread=None, volume=None, macro_risk=None) -> MarketRegime:
    """Classify a causal candidate regime using explicitly supplied parameters."""
    if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
        raise ValueError("evaluated_at must be timezone-aware")
    values = tuple(float(value) for value in prices)
    if available_times is not None:
        if len(available_times) != len(values):
            raise ValueError("each regime input requires an availability timestamp")
        pairs = tuple((value, time) for value, time in zip(values, available_times)
                      if time <= evaluated_at)
        values = tuple(value for value, _ in pairs)
    required = max(parameters.trend_window + 1, parameters.volatility_window + 1)
    if len(values) < required or any(value <= 0 or not isfinite(value) for value in values):
        return MarketRegime(evaluated_at, parameters.version, availability=UNAVAILABLE,
                            trend_state=UNKNOWN, volatility_state=UNKNOWN,
                            macro_risk_state=UNKNOWN, liquidity_state=UNKNOWN)
    reference = classify_regime(values, trend_window=parameters.trend_window,
                                volatility_window=parameters.volatility_window,
                                trend_threshold=parameters.trend_threshold,
                                high_volatility=parameters.high_volatility,
                                low_volatility=parameters.low_volatility)
    liquidity = UNKNOWN
    if spread is not None and volume is not None:
        liquidity = "normal" if spread >= 0 and volume >= 0 else UNAVAILABLE
    risk = macro_risk if macro_risk in _STATES["macro_risk"] else UNKNOWN
    metrics = dict(reference.features)
    if spread is not None: metrics["spread"] = float(spread)
    if volume is not None: metrics["volume"] = float(volume)
    return MarketRegime(evaluated_at, parameters.version, reference.trend, reference.volatility,
                        risk, liquidity, metrics, ("close",), reference.confidence,
                        "AVAILABLE", {"source": "candidate-close-series"})


__all__ = ["CANDIDATE_V2", "DEFAULT_REGIME_REGISTRY", "LEGACY_DAILY", "LEGACY_INTRADAY",
           "MarketRegime", "RegimeDefinition", "RegimeParameters", "RegimeRegistry",
           "UNKNOWN", "UNAVAILABLE", "classify_candidate", "legacy_daily"]
