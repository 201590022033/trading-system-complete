"""Adapter from market observations to multi-agent shadow intelligence context."""

from __future__ import annotations

from typing import Dict

from adaptive_fusion import AdaptiveFactor, AdaptiveFusionEngine
from market_profiles import DEFAULT_PROFILE_REGISTRY, ProfileRegistry
from regime_engine import classify_regime
from signal_pipeline import legacy_technical_score


def build_agent_context(
    ticker: str,
    observation,
    *,
    profile_registry: ProfileRegistry = DEFAULT_PROFILE_REGISTRY,
    fusion: AdaptiveFusionEngine | None = None,
) -> Dict:
    """Build explainable context without changing the observation's signals."""
    profile = profile_registry.select(ticker)
    prices = [float(value) for value in observation.recent_prices]
    try:
        regime = classify_regime(prices) if len(prices) >= 2 else None
    except ValueError:
        regime = None
    technical = legacy_technical_score(observation)
    sentiment = float(observation.news_sentiment_score)
    legacy_score = 0.60 * technical + 0.30 * sentiment
    legacy_action = "buy" if legacy_score > 0.35 else "sell" if legacy_score < -0.35 else "hold"
    adaptive = (fusion or AdaptiveFusionEngine()).fuse(
        (
            AdaptiveFactor("legacy_technical", "technical", technical, 0.65),
            AdaptiveFactor("aggregate_sentiment", "sentiment", sentiment, 0.35),
        ),
        legacy_score=round(legacy_score, 6), legacy_action=legacy_action,
        profile=profile, regime=regime,
    )
    return {
        "profile": adaptive.profile,
        "regime": adaptive.regime,
        "legacy": {"score": round(legacy_score, 6), "action": legacy_action},
        "adaptive": adaptive.to_dict(),
        "shadow_only": True,
    }


def disagreement_telemetry(context: Dict, bull, bear, general) -> Dict:
    legacy_action = context.get("legacy", {}).get("action", "unavailable")
    adaptive_action = context.get("adaptive", {}).get("action", "unavailable")
    research_scores = {
        "bull": bull.confidence if bull.stance == "bullish" else -bull.confidence,
        "bear": -bear.confidence if bear.stance == "bearish" else bear.confidence,
        "general": general.confidence if general.stance == "bullish" else (
            -general.confidence if general.stance == "bearish" else 0.0
        ),
    }
    research_consensus = sum(research_scores.values()) / 3.0
    legacy_direction = {"buy": 1, "sell": -1, "hold": 0}.get(legacy_action, 0)
    adaptive_direction = {"buy": 1, "sell": -1, "hold": 0}.get(adaptive_action, 0)
    research_direction = 1 if research_consensus > 0.3 else -1 if research_consensus < -0.3 else 0
    return {
        "legacy_action": legacy_action,
        "adaptive_action": adaptive_action,
        "legacy_adaptive_disagree": legacy_direction != adaptive_direction,
        "legacy_adaptive_opposed": legacy_direction * adaptive_direction == -1,
        "bull_bear_high_confidence": bull.confidence >= 0.5 and bear.confidence >= 0.5,
        "research_consensus": round(research_consensus, 6),
        "research_legacy_opposed": research_direction * legacy_direction == -1,
        "research_scores": research_scores,
    }
