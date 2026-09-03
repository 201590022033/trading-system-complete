"""Multi-horizon, segmented walk-forward evaluation for legacy and shadow signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean, median
from types import SimpleNamespace
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from adaptive_fusion import AdaptiveFactor, AdaptiveFusionEngine
from data_pipeline import SignalGenerator
from market_profiles import DEFAULT_PROFILE_REGISTRY, ProfileRegistry
from regime_engine import classify_regime
from signal_pipeline import legacy_technical_score


EVALUATION_VERSION = "walk-forward-evaluation-v1"
MODEL_NAMES = ("legacy", "technical_only", "macro_only", "source_only", "adaptive")


@dataclass(frozen=True)
class CostAssumptions:
    spread_bps: float = 0.0
    fees_bps: float = 0.0
    slippage_bps: float = 0.0

    @property
    def total_bps(self) -> float:
        return self.spread_bps + self.fees_bps + self.slippage_bps


@dataclass(frozen=True)
class EvaluationRow:
    ticker: str
    model: str
    horizon: int
    segment_type: str
    segment: str
    sample_count: int
    wins: int
    losses: int
    win_rate: float
    win_rate_ci_low: float
    win_rate_ci_high: float
    mean_aligned_return: float
    median_aligned_return: float
    mean_net_return: float
    max_drawdown: float
    mean_mfe: float
    mean_mae: float
    turnover: float
    insufficient_sample: bool


@dataclass
class _DecisionOutcome:
    model: str
    horizon: int
    trend: str
    volatility: str
    profile: str
    position: int
    aligned_return: float
    net_return: float
    mfe: float
    mae: float
    turnover: float


def _position(score: float, threshold: float = 0.35) -> int:
    return 1 if score > threshold else -1 if score < -threshold else 0


def _metric_row(
    ticker: str,
    model: str,
    horizon: int,
    segment_type: str,
    segment: str,
    outcomes: Sequence[_DecisionOutcome],
    minimum_sample: int,
) -> EvaluationRow:
    active = [item for item in outcomes if item.position]
    aligned = [item.aligned_return for item in active]
    net = [item.net_return for item in outcomes if item.position or item.turnover]
    wins = sum(value > 0 for value in aligned)
    losses = sum(value < 0 for value in aligned)
    count = len(active)
    win_rate = wins / count if count else 0.0
    if count:
        z = 1.96
        denominator = 1.0 + z * z / count
        centre = (win_rate + z * z / (2.0 * count)) / denominator
        margin = z * sqrt((win_rate * (1.0 - win_rate) / count) + z * z / (4.0 * count * count)) / denominator
        ci_low, ci_high = max(0.0, centre - margin), min(1.0, centre + margin)
    else:
        ci_low, ci_high = 0.0, 1.0

    equity = peak = 1.0
    max_drawdown = 0.0
    for item in outcomes:
        equity *= max(0.0, 1.0 + item.net_return)
        peak = max(peak, equity)
        if peak:
            max_drawdown = min(max_drawdown, equity / peak - 1.0)

    return EvaluationRow(
        ticker, model, horizon, segment_type, segment, count, wins, losses,
        round(win_rate, 6), round(ci_low, 6), round(ci_high, 6),
        round(mean(aligned), 8) if aligned else 0.0,
        round(median(aligned), 8) if aligned else 0.0,
        round(mean(net), 8) if net else 0.0,
        round(max_drawdown, 8),
        round(mean(item.mfe for item in active), 8) if active else 0.0,
        round(mean(item.mae for item in active), 8) if active else 0.0,
        round(sum(item.turnover for item in outcomes), 4),
        count < minimum_sample,
    )


def evaluate_walk_forward(
    ticker: str,
    prices: Sequence[float],
    *,
    horizons: Iterable[int] = (1, 3, 5, 20),
    sentiment_scores: Optional[Sequence[float]] = None,
    macro_scores: Optional[Sequence[float]] = None,
    source_scores: Optional[Sequence[float]] = None,
    costs: CostAssumptions = CostAssumptions(),
    profile_registry: ProfileRegistry = DEFAULT_PROFILE_REGISTRY,
    minimum_sample: int = 30,
) -> Dict:
    """Evaluate signals using only the price/context prefix at each decision."""
    values = [float(value) for value in prices]
    if len(values) < 2 or any(value <= 0 for value in values):
        raise ValueError("prices require at least two positive values")
    context_series = {
        "sentiment": sentiment_scores,
        "macro": macro_scores,
        "source": source_scores,
    }
    for name, series in context_series.items():
        if series is not None and len(series) != len(values):
            raise ValueError(f"{name}_scores must align with prices")

    horizons = tuple(sorted(set(int(value) for value in horizons)))
    if not horizons or any(value <= 0 for value in horizons):
        raise ValueError("horizons must contain positive integers")
    profile = profile_registry.select(ticker)
    fusion = AdaptiveFusionEngine()
    outcomes: List[_DecisionOutcome] = []

    for horizon in horizons:
        generator = SignalGenerator(buffer_size=max(100, len(values)))
        previous = {model: 0 for model in MODEL_NAMES}
        for index, price in enumerate(values):
            generator.add_vwap(ticker, price)
            if index + horizon >= len(values):
                break
            indicators = generator.generate_indicators(ticker)
            technical = legacy_technical_score(SimpleNamespace(indicators=indicators))
            sentiment = float(sentiment_scores[index]) if sentiment_scores is not None else 0.0
            macro = float(macro_scores[index]) if macro_scores is not None else 0.0
            source = float(source_scores[index]) if source_scores is not None else 0.0
            regime = classify_regime(values[:index + 1]) if index else None
            legacy = 0.60 * technical + 0.30 * sentiment + 0.15 * macro
            adaptive = fusion.fuse(
                (
                    AdaptiveFactor("technical", "technical", technical, 0.45),
                    AdaptiveFactor(
                        "sentiment", "sentiment", sentiment, 0.15,
                        available=sentiment_scores is not None,
                    ),
                    AdaptiveFactor(
                        "macro", "macro", macro, 0.20,
                        available=macro_scores is not None,
                    ),
                    AdaptiveFactor(
                        "source", "authoritative_event", source, 0.20,
                        available=source_scores is not None,
                    ),
                ),
                legacy_score=legacy,
                legacy_action="research",
                profile=profile,
                regime=regime,
            ).score
            scores = {
                "legacy": legacy,
                "technical_only": technical,
                "macro_only": macro,
                "source_only": source,
                "adaptive": adaptive,
            }
            future_returns = [(future / price) - 1.0 for future in values[index + 1:index + horizon + 1]]
            forward_return = future_returns[-1]
            for model, score in scores.items():
                position = _position(score)
                turnover = abs(position - previous[model])
                previous[model] = position
                aligned = position * forward_return
                path = [position * value for value in future_returns]
                cost = turnover * costs.total_bps / 10000.0
                outcomes.append(_DecisionOutcome(
                    model, horizon,
                    regime.trend if regime else "unavailable",
                    regime.volatility if regime else "unavailable",
                    profile.profile_id, position, aligned, aligned - cost,
                    max([0.0] + path), min([0.0] + path), turnover,
                ))

    rows: List[EvaluationRow] = []
    for horizon in horizons:
        for model in MODEL_NAMES:
            base = [item for item in outcomes if item.horizon == horizon and item.model == model]
            rows.append(_metric_row(ticker, model, horizon, "overall", "all", base, minimum_sample))
            for segment_type, attribute in (("trend", "trend"), ("volatility", "volatility"), ("profile", "profile")):
                for segment in sorted({getattr(item, attribute) for item in base}):
                    subset = [item for item in base if getattr(item, attribute) == segment]
                    rows.append(_metric_row(
                        ticker, model, horizon, segment_type, segment, subset, minimum_sample
                    ))

    return {
        "version": EVALUATION_VERSION,
        "method": "walk-forward; context and indicators at t, outcome through t+horizon",
        "cost_assumptions": asdict(costs),
        "minimum_sample": minimum_sample,
        "rows": [asdict(row) for row in rows],
    }
