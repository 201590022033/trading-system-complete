"""Explainable adaptive signal fusion operating strictly in shadow mode."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, Optional, Tuple

from market_profiles import MarketProfile
from regime_engine import MarketRegime


FUSION_VERSION = "adaptive-fusion-v1"


@dataclass(frozen=True)
class AdaptiveFactor:
    name: str
    category: str
    score: float
    base_weight: float
    available: bool = True
    reliability: float = 0.5
    reliability_samples: int = 0


@dataclass(frozen=True)
class FactorContribution:
    name: str
    category: str
    score: float
    base_weight: float
    regime_multiplier: float
    profile_multiplier: float
    reliability_multiplier: float
    effective_weight: float
    normalized_weight: float
    contribution: float


@dataclass(frozen=True)
class AdaptiveFusionResult:
    score: float
    action: str
    legacy_score: float
    legacy_action: str
    contributions: Tuple[FactorContribution, ...]
    regime: Dict
    profile: Dict
    version: str = FUSION_VERSION
    shadow_only: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)


class AdaptiveFusionEngine:
    """Configurable contextual weighting with conservative reliability gates."""

    def __init__(self, minimum_reliability_samples: int = 20) -> None:
        self.minimum_reliability_samples = minimum_reliability_samples

    @staticmethod
    def _regime_multiplier(category: str, regime: Optional[MarketRegime]) -> float:
        if regime is None:
            return 1.0
        multiplier = 1.0
        if category == "technical":
            multiplier *= 0.85 if regime.trend == "range" else 1.10
            if regime.volatility == "high":
                multiplier *= 0.80
        elif category in ("macro", "authoritative_event") and regime.risk == "risk_off":
            multiplier *= 1.10
        elif category == "community" and regime.volatility == "high":
            multiplier *= 0.75
        return multiplier

    @staticmethod
    def _profile_multiplier(category: str, profile: MarketProfile) -> float:
        contextual_sectors = {
            "financials", "gold_mining", "pgm_mining", "diversified_mining",
            "energy", "retail_consumer", "agriculture", "foreign_exchange",
        }
        if category == "macro" and profile.sector in contextual_sectors:
            return 1.10
        if category == "technical" and profile.instrument_type == "index_future_or_cfd":
            return 1.05
        return 1.0

    def _reliability_multiplier(self, factor: AdaptiveFactor) -> float:
        if factor.reliability_samples < self.minimum_reliability_samples:
            return 1.0
        return max(0.5, min(1.5, factor.reliability / 0.5))

    def fuse(
        self,
        factors: Iterable[AdaptiveFactor],
        *,
        legacy_score: float,
        legacy_action: str,
        profile: MarketProfile,
        regime: Optional[MarketRegime] = None,
    ) -> AdaptiveFusionResult:
        weighted = []
        for factor in factors:
            if not factor.available or factor.base_weight <= 0:
                continue
            if factor.category not in {
                "technical", "macro", "authoritative_event", "community", "sentiment"
            }:
                raise ValueError(f"Unsupported factor category: {factor.category}")
            score = max(-1.0, min(1.0, float(factor.score)))
            regime_multiplier = self._regime_multiplier(factor.category, regime)
            profile_multiplier = self._profile_multiplier(factor.category, profile)
            reliability_multiplier = self._reliability_multiplier(factor)
            effective_weight = (
                factor.base_weight * regime_multiplier * profile_multiplier * reliability_multiplier
            )
            weighted.append((factor, score, regime_multiplier, profile_multiplier,
                             reliability_multiplier, effective_weight))

        total_weight = sum(item[-1] for item in weighted)
        contributions = []
        score = 0.0
        for factor, factor_score, regime_mult, profile_mult, reliability_mult, weight in weighted:
            normalized = weight / total_weight if total_weight else 0.0
            contribution = factor_score * normalized
            score += contribution
            contributions.append(FactorContribution(
                factor.name, factor.category, round(factor_score, 6), factor.base_weight,
                round(regime_mult, 6), round(profile_mult, 6), round(reliability_mult, 6),
                round(weight, 6), round(normalized, 6), round(contribution, 6),
            ))

        action = "buy" if score > 0.35 else "sell" if score < -0.35 else "hold"
        regime_data = regime.to_dict() if regime is not None else {"status": "unavailable"}
        profile_data = {
            "id": profile.profile_id,
            "sector": profile.sector,
            "instrument_type": profile.instrument_type,
            "version": profile.version,
        }
        return AdaptiveFusionResult(
            score=round(score, 6), action=action,
            legacy_score=float(legacy_score), legacy_action=legacy_action,
            contributions=tuple(contributions), regime=regime_data, profile=profile_data,
        )
