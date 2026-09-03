"""Expanded technical indicators with explicit data-capability gates.

This module is research/shadow-only. It consumes observations only through an
explicit ``as_of_index`` and never modifies the legacy ``SignalGenerator``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

import numpy as np


INDICATOR_VERSION = "expanded-indicators-v1"


@dataclass(frozen=True)
class DataCapabilities:
    has_ohlc: bool = False
    has_volume: bool = False
    has_benchmark: bool = False
    intraday: bool = False
    frequency: str = "daily"


@dataclass(frozen=True)
class MarketBar:
    close: float
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    volume: Optional[float] = None


@dataclass(frozen=True)
class FeatureValue:
    available: bool
    value: Optional[float] = None
    reason: str = ""


@dataclass(frozen=True)
class ExpandedIndicatorSnapshot:
    as_of_index: int
    version: str
    capabilities: DataCapabilities
    features: Dict[str, FeatureValue] = field(default_factory=dict)
    shadow_only: bool = True


def _unavailable(reason: str) -> FeatureValue:
    return FeatureValue(False, reason=reason)


def _value(value: float) -> FeatureValue:
    return FeatureValue(True, float(value))


def _ema(values: np.ndarray, period: int) -> float:
    alpha = 2.0 / (period + 1.0)
    result = float(values[0])
    for item in values[1:]:
        result = alpha * float(item) + (1.0 - alpha) * result
    return result


def calculate_expanded_indicators(
    bars: Sequence[MarketBar],
    capabilities: DataCapabilities,
    benchmark_closes: Optional[Sequence[float]] = None,
    as_of_index: Optional[int] = None,
    period: int = 14,
    opening_range_bars: int = 5,
) -> ExpandedIndicatorSnapshot:
    """Calculate only features supported by data available at ``as_of_index``."""
    if not bars:
        raise ValueError("At least one market bar is required")
    end = len(bars) - 1 if as_of_index is None else as_of_index
    if end < 0 or end >= len(bars):
        raise ValueError("as_of_index is outside the supplied bars")
    history = list(bars[: end + 1])
    closes = np.asarray([bar.close for bar in history], dtype=float)
    if not np.all(np.isfinite(closes)) or np.any(closes <= 0):
        raise ValueError("Close prices must be positive and finite")

    features: Dict[str, FeatureValue] = {}

    if len(closes) >= 26:
        features["macd"] = _value(_ema(closes, 12) - _ema(closes, 26))
    else:
        features["macd"] = _unavailable("requires 26 closes")

    if len(closes) >= 20:
        window = closes[-20:]
        middle = float(np.mean(window))
        std = float(np.std(window))
        features["bollinger_middle"] = _value(middle)
        features["bollinger_upper"] = _value(middle + 2.0 * std)
        features["bollinger_lower"] = _value(middle - 2.0 * std)
        features["close_zscore"] = _value((closes[-1] - middle) / std if std else 0.0)
    else:
        for name in ("bollinger_middle", "bollinger_upper", "bollinger_lower", "close_zscore"):
            features[name] = _unavailable("requires 20 closes")

    highs = lows = None
    if capabilities.has_ohlc:
        if any(bar.high is None or bar.low is None for bar in history):
            raise ValueError("has_ohlc requires high and low on every bar")
        highs = np.asarray([bar.high for bar in history], dtype=float)
        lows = np.asarray([bar.low for bar in history], dtype=float)
        previous = closes[:-1]
        true_ranges = np.maximum.reduce((
            highs[1:] - lows[1:],
            np.abs(highs[1:] - previous),
            np.abs(lows[1:] - previous),
        ))
        if len(true_ranges) >= period:
            features["atr"] = _value(np.mean(true_ranges[-period:]))
        else:
            features["atr"] = _unavailable(f"requires {period + 1} OHLC bars")

        if len(closes) >= (2 * period + 1):
            up_moves = np.diff(highs)
            down_moves = -np.diff(lows)
            plus_dm = np.where((up_moves > down_moves) & (up_moves > 0), up_moves, 0.0)
            minus_dm = np.where((down_moves > up_moves) & (down_moves > 0), down_moves, 0.0)
            dx_values = []
            for index in range(period - 1, len(true_ranges)):
                atr_sum = float(np.sum(true_ranges[index - period + 1:index + 1]))
                if atr_sum == 0:
                    dx_values.append(0.0)
                    continue
                plus_di = 100.0 * float(np.sum(plus_dm[index - period + 1:index + 1])) / atr_sum
                minus_di = 100.0 * float(np.sum(minus_dm[index - period + 1:index + 1])) / atr_sum
                denominator = plus_di + minus_di
                dx_values.append(100.0 * abs(plus_di - minus_di) / denominator if denominator else 0.0)
            features["adx"] = _value(np.mean(dx_values[-period:]))
            features["plus_di"] = _value(plus_di)
            features["minus_di"] = _value(minus_di)
        else:
            for name in ("adx", "plus_di", "minus_di"):
                features[name] = _unavailable(f"requires {2 * period + 1} OHLC bars")
    else:
        for name in ("atr", "adx", "plus_di", "minus_di"):
            features[name] = _unavailable("requires OHLC capability")

    if capabilities.has_benchmark and benchmark_closes is not None:
        benchmark = np.asarray(benchmark_closes[: end + 1], dtype=float)
        if len(closes) >= period + 1 and len(benchmark) == len(closes):
            asset_return = closes[-1] / closes[-period - 1] - 1.0
            benchmark_return = benchmark[-1] / benchmark[-period - 1] - 1.0
            features["relative_strength"] = _value(asset_return - benchmark_return)
        else:
            features["relative_strength"] = _unavailable(
                f"requires {period + 1} aligned asset and benchmark closes"
            )
    else:
        features["relative_strength"] = _unavailable("requires benchmark capability and data")

    volumes = None
    if capabilities.has_volume:
        if any(bar.volume is None or bar.volume < 0 for bar in history):
            raise ValueError("has_volume requires non-negative volume on every bar")
        volumes = np.asarray([bar.volume for bar in history], dtype=float)
        if len(volumes) >= 21:
            baseline = float(np.mean(volumes[-21:-1]))
            features["relative_volume"] = _value(volumes[-1] / baseline if baseline else 0.0)
            features["median_dollar_volume"] = _value(np.median(closes[-20:] * volumes[-20:]))
        else:
            features["relative_volume"] = _unavailable("requires 21 volume bars")
            features["median_dollar_volume"] = _unavailable("requires 21 volume bars")
    else:
        features["relative_volume"] = _unavailable("requires volume capability")
        features["median_dollar_volume"] = _unavailable("requires volume capability")

    if capabilities.intraday and capabilities.has_ohlc and capabilities.has_volume:
        assert highs is not None and lows is not None and volumes is not None
        total_volume = float(np.sum(volumes))
        typical = (highs + lows + closes) / 3.0
        features["session_vwap"] = _value(
            float(np.sum(typical * volumes) / total_volume) if total_volume else closes[-1]
        )
        if len(history) >= opening_range_bars:
            features["opening_range_high"] = _value(np.max(highs[:opening_range_bars]))
            features["opening_range_low"] = _value(np.min(lows[:opening_range_bars]))
        else:
            features["opening_range_high"] = _unavailable("opening range is incomplete")
            features["opening_range_low"] = _unavailable("opening range is incomplete")
    else:
        reason = "requires explicitly declared intraday OHLCV capability"
        for name in ("session_vwap", "opening_range_high", "opening_range_low"):
            features[name] = _unavailable(reason)

    return ExpandedIndicatorSnapshot(end, INDICATOR_VERSION, capabilities, features)
