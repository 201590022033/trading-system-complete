"""Full deterministic point-in-time Ichimoku feature model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from research_indicators import DataCapabilities, MarketBar


ICHIMOKU_VERSION = "ichimoku-v1"


@dataclass(frozen=True)
class IchimokuSnapshot:
    available: bool
    values: dict
    reason: str = ""
    version: str = ICHIMOKU_VERSION
    shadow_only: bool = True


def _midpoint(highs: np.ndarray, lows: np.ndarray, end: int, period: int) -> float:
    start = end - period + 1
    return (float(np.max(highs[start:end + 1])) + float(np.min(lows[start:end + 1]))) / 2.0


def calculate_ichimoku(
    bars: Sequence[MarketBar],
    capabilities: DataCapabilities,
    as_of_index: Optional[int] = None,
    *, conversion_period: int = 9,
    base_period: int = 26,
    span_b_period: int = 52,
    displacement: int = 26,
) -> IchimokuSnapshot:
    if not bars:
        raise ValueError("at least one bar is required")
    end = len(bars) - 1 if as_of_index is None else as_of_index
    if end < 0 or end >= len(bars):
        raise ValueError("as_of_index is outside supplied bars")
    if not capabilities.has_ohlc:
        return IchimokuSnapshot(False, {}, "requires OHLC capability")
    history = list(bars[:end + 1])
    if any(bar.high is None or bar.low is None for bar in history):
        raise ValueError("has_ohlc requires high and low on every bar")
    required = span_b_period + displacement
    if len(history) < required:
        return IchimokuSnapshot(False, {}, f"requires {required} OHLC bars")
    highs = np.asarray([bar.high for bar in history], dtype=float)
    lows = np.asarray([bar.low for bar in history], dtype=float)
    closes = np.asarray([bar.close for bar in history], dtype=float)

    tenkan = _midpoint(highs, lows, end, conversion_period)
    kijun = _midpoint(highs, lows, end, base_period)
    future_a = (tenkan + kijun) / 2.0
    future_b = _midpoint(highs, lows, end, span_b_period)

    cloud_source = end - displacement
    source_tenkan = _midpoint(highs, lows, cloud_source, conversion_period)
    source_kijun = _midpoint(highs, lows, cloud_source, base_period)
    current_a = (source_tenkan + source_kijun) / 2.0
    current_b = _midpoint(highs, lows, cloud_source, span_b_period)
    cloud_top, cloud_bottom = max(current_a, current_b), min(current_a, current_b)
    close = float(closes[end])
    price_cloud_state = "above" if close > cloud_top else "below" if close < cloud_bottom else "inside"

    previous_end = end - 1
    previous_source = previous_end - displacement
    previous_close = float(closes[previous_end])
    if previous_source + 1 < span_b_period:
        breakout = "unavailable_at_first_full_cloud"
    else:
        previous_a = (
            _midpoint(highs, lows, previous_source, conversion_period)
            + _midpoint(highs, lows, previous_source, base_period)
        ) / 2.0
        previous_b = _midpoint(highs, lows, previous_source, span_b_period)
        previous_top, previous_bottom = max(previous_a, previous_b), min(previous_a, previous_b)
        if previous_close <= previous_top and close > cloud_top:
            breakout = "bullish"
        elif previous_close >= previous_bottom and close < cloud_bottom:
            breakout = "bearish"
        else:
            breakout = "none"

    previous_tenkan = _midpoint(highs, lows, previous_end, conversion_period)
    previous_kijun = _midpoint(highs, lows, previous_end, base_period)
    tk_spread = tenkan - kijun
    previous_tk_spread = previous_tenkan - previous_kijun
    tk_cross = "bullish" if previous_tk_spread <= 0 < tk_spread else "bearish" if previous_tk_spread >= 0 > tk_spread else "none"
    if tk_cross == "bullish":
        tk_strength = "strong" if tenkan > cloud_top else "weak" if tenkan < cloud_bottom else "neutral"
    elif tk_cross == "bearish":
        tk_strength = "strong" if tenkan < cloud_bottom else "weak" if tenkan > cloud_top else "neutral"
    else:
        tk_strength = "none"

    direction = "bullish" if future_a > future_b else "bearish" if future_a < future_b else "flat"
    agreement = (
        "bullish" if price_cloud_state == "above" and tenkan > kijun and direction == "bullish"
        else "bearish" if price_cloud_state == "below" and tenkan < kijun and direction == "bearish"
        else "mixed"
    )
    values = {
        "tenkan": tenkan, "kijun": kijun,
        "current_senkou_a": current_a, "current_senkou_b": current_b,
        "future_senkou_a_known_at_t": future_a, "future_senkou_b_known_at_t": future_b,
        "price_cloud_state": price_cloud_state,
        "cloud_thickness_ratio": abs(current_a - current_b) / close,
        "future_cloud_direction": direction,
        "tenkan_kijun_spread_ratio": tk_spread / close,
        "distance_from_kijun": close / kijun - 1.0,
        "chikou_vs_historical_price_26": close / float(closes[end - displacement]) - 1.0,
        "cloud_breakout": breakout, "tk_cross": tk_cross,
        "tk_cross_strength": tk_strength, "regime_consistency": agreement,
    }
    return IchimokuSnapshot(True, values)
