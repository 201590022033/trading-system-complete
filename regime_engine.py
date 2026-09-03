"""Transparent, research-only market regime classification.

Version 1 uses trailing close prices only. It deliberately emits multiple
orthogonal labels instead of collapsing market context into one opaque class.
No output from this module changes production signal weights.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import Dict, List

REGIME_VERSION = "regime-v1"


@dataclass(frozen=True)
class MarketRegime:
    trend: str
    volatility: str
    risk: str
    confidence: float
    version: str
    features: Dict[str, float]

    def to_dict(self) -> Dict:
        return asdict(self)


def _returns(prices: List[float]) -> List[float]:
    return [
        (prices[index] - prices[index - 1]) / prices[index - 1]
        for index in range(1, len(prices))
        if prices[index - 1] > 0
    ]


def classify_regime(
    prices: List[float],
    *,
    trend_window: int = 20,
    volatility_window: int = 20,
    trend_threshold: float = 0.02,
    high_volatility: float = 0.025,
    low_volatility: float = 0.008,
) -> MarketRegime:
    """Classify trailing context without using future observations.

    Trend is the total return over the trailing window. Volatility is the
    population standard deviation of trailing one-period returns. Thresholds
    are explicit v1 defaults and must be calibrated with walk-forward evidence
    before being used to alter signal weights.
    """
    if len(prices) < 2:
        raise ValueError("at least two positive prices are required")
    if any(price <= 0 for price in prices):
        raise ValueError("prices must be positive")

    trend_prices = prices[-(trend_window + 1):]
    trend_return = (trend_prices[-1] - trend_prices[0]) / trend_prices[0]
    returns = _returns(prices[-(volatility_window + 1):])
    realized_volatility = pstdev(returns) if len(returns) > 1 else 0.0

    if trend_return >= trend_threshold:
        trend = "bull"
    elif trend_return <= -trend_threshold:
        trend = "bear"
    else:
        trend = "range"

    if realized_volatility >= high_volatility:
        volatility = "high"
    elif realized_volatility <= low_volatility:
        volatility = "low"
    else:
        volatility = "normal"

    # Risk is a transparent composite, not a claim about an investable index.
    if volatility == "high" or (trend == "bear" and realized_volatility > low_volatility):
        risk = "risk_off"
    elif trend == "bull" and volatility != "high":
        risk = "risk_on"
    else:
        risk = "neutral"

    # Confidence reflects data sufficiency and distance from thresholds.
    data_factor = min(1.0, len(prices) / max(trend_window + 1, volatility_window + 1))
    trend_distance = min(1.0, abs(trend_return) / max(trend_threshold, 1e-9))
    vol_threshold = high_volatility if volatility == "high" else low_volatility
    vol_distance = min(1.0, realized_volatility / max(vol_threshold, 1e-9))
    confidence = min(0.95, max(0.2, data_factor * (0.5 + 0.25 * trend_distance + 0.25 * vol_distance)))

    return MarketRegime(
        trend=trend,
        volatility=volatility,
        risk=risk,
        confidence=round(confidence, 4),
        version=REGIME_VERSION,
        features={
            "trend_return": round(trend_return, 8),
            "realized_volatility": round(realized_volatility, 8),
            "observations": float(len(prices)),
        },
    )
