"""Deterministic Fibonacci and contextual candlestick research features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from research_indicators import DataCapabilities, MarketBar


STRUCTURE_VERSION = "structure-patterns-v1"
FIBONACCI_LEVELS = (0.236, 0.382, 0.5, 0.618, 0.786)


@dataclass(frozen=True)
class StructureSnapshot:
    available: bool
    values: dict
    reason: str = ""
    version: str = STRUCTURE_VERSION
    shadow_only: bool = True


def _arrays(bars: Sequence[MarketBar], end: int):
    history = list(bars[:end + 1])
    if any(bar.open is None or bar.high is None or bar.low is None for bar in history):
        raise ValueError("OHLC capability requires open/high/low on every bar")
    return tuple(np.asarray([getattr(bar, field) for bar in history], dtype=float) for field in ("open", "high", "low", "close"))


def calculate_fibonacci_context(
    bars: Sequence[MarketBar], capabilities: DataCapabilities,
    as_of_index: Optional[int] = None, *, swing_window: int = 60,
) -> StructureSnapshot:
    if not bars:
        raise ValueError("at least one bar is required")
    end = len(bars) - 1 if as_of_index is None else as_of_index
    if end < 0 or end >= len(bars):
        raise ValueError("as_of_index is outside supplied bars")
    if not capabilities.has_ohlc:
        return StructureSnapshot(False, {}, "requires OHLC capability")
    if end < 19:
        return StructureSnapshot(False, {}, "requires 20 OHLC bars")
    opens, highs, lows, closes = _arrays(bars, end)
    start = max(0, end - swing_window)
    # Exclude the decision bar: the preceding swing must already be defined.
    prior_highs, prior_lows = highs[start:end], lows[start:end]
    high_offset, low_offset = int(np.argmax(prior_highs)), int(np.argmin(prior_lows))
    high_index, low_index = start + high_offset, start + low_offset
    swing_high, swing_low = float(highs[high_index]), float(lows[low_index])
    if swing_high <= swing_low or high_index == low_index:
        return StructureSnapshot(False, {}, "preceding swing range is undefined")
    direction = "upswing" if low_index < high_index else "downswing"
    span = swing_high - swing_low
    if direction == "upswing":
        levels = {str(level): swing_high - level * span for level in FIBONACCI_LEVELS}
    else:
        levels = {str(level): swing_low + level * span for level in FIBONACCI_LEVELS}
    close = float(closes[end])
    nearest_name, nearest_value = min(levels.items(), key=lambda item: abs(close - item[1]))
    returns = np.diff(closes[-15:]) / closes[-15:-1]
    realized_volatility = float(np.std(returns)) if len(returns) else 0.0
    support, resistance = float(np.min(lows[max(0, end - 20):end])), float(np.max(highs[max(0, end - 20):end]))
    tolerance = max(close * 0.005, close * realized_volatility)
    values = {
        "swing_direction": direction, "swing_high": swing_high, "swing_low": swing_low,
        "swing_high_index": high_index, "swing_low_index": low_index,
        "levels": levels, "nearest_level": float(nearest_name),
        "nearest_level_price": nearest_value,
        "distance_to_level_ratio": (close - nearest_value) / close,
        "near_level": abs(close - nearest_value) <= tolerance,
        "trend_confluence": (direction == "upswing" and close >= float(np.mean(closes[-20:]))) or (direction == "downswing" and close <= float(np.mean(closes[-20:]))),
        "support_resistance_confluence": abs(nearest_value - support) <= tolerance or abs(nearest_value - resistance) <= tolerance,
        "realized_volatility_14": realized_volatility,
        "volume_confirmation": None,
        "automatic_action": None,
    }
    if capabilities.has_volume:
        volumes = np.asarray([bar.volume for bar in bars[:end + 1]], dtype=float)
        values["volume_confirmation"] = bool(volumes[end] > np.mean(volumes[max(0, end - 20):end]))
    return StructureSnapshot(True, values)


def _geometry(o, h, l, c):
    span = max(h - l, 1e-12)
    body = abs(c - o)
    return body, span, h - max(o, c), min(o, c) - l


def calculate_candlestick_context(
    bars: Sequence[MarketBar], capabilities: DataCapabilities,
    as_of_index: Optional[int] = None, *, pattern_index: Optional[int] = None,
) -> StructureSnapshot:
    if not bars:
        raise ValueError("at least one bar is required")
    end = len(bars) - 1 if as_of_index is None else as_of_index
    target = end if pattern_index is None else pattern_index
    if target > end:
        raise ValueError("pattern_index cannot be after as_of_index")
    if not capabilities.has_ohlc:
        return StructureSnapshot(False, {}, "requires OHLC capability")
    if target < 2:
        return StructureSnapshot(False, {}, "requires three OHLC bars")
    opens, highs, lows, closes = _arrays(bars, end)
    o, h, l, c = (float(values[target]) for values in (opens, highs, lows, closes))
    body, span, upper, lower = _geometry(o, h, l, c)
    preceding_start = max(0, target - 5)
    preceding_change = float(closes[target - 1] / closes[preceding_start] - 1.0) if target - 1 > preceding_start else 0.0
    uptrend, downtrend = preceding_change > 0.02, preceding_change < -0.02
    small_body = body / span <= 0.35
    long_lower, long_upper = lower >= 2 * max(body, span * 0.05), upper >= 2 * max(body, span * 0.05)
    doji = body / span <= 0.10
    po, ph, pl, pc = (float(values[target - 1]) for values in (opens, highs, lows, closes))
    pbody = abs(pc - po)
    bullish_engulfing = pc < po and c > o and o <= pc and c >= po
    bearish_engulfing = pc > po and c < o and o >= pc and c <= po
    first_o, first_c = float(opens[target - 2]), float(closes[target - 2])
    middle_body = abs(pc - po)
    first_body = abs(first_c - first_o)
    morning_star = first_c < first_o and middle_body <= first_body * 0.5 and c > o and c >= (first_o + first_c) / 2
    evening_star = first_c > first_o and middle_body <= first_body * 0.5 and c < o and c <= (first_o + first_c) / 2
    harami = body < pbody and max(o, c) <= max(po, pc) and min(o, c) >= min(po, pc)
    midpoint = (po + pc) / 2
    patterns = {
        "hanging_man": bool(uptrend and small_body and long_lower and upper <= max(body, span * .1)),
        "hammer": bool(downtrend and small_body and long_lower and upper <= max(body, span * .1)),
        "inverted_hammer": bool(downtrend and small_body and long_upper and lower <= max(body, span * .1)),
        "shooting_star": bool(uptrend and small_body and long_upper and lower <= max(body, span * .1)),
        "doji": bool(doji),
        "dragonfly_doji": bool(doji and lower / span >= .6 and upper / span <= .1),
        "gravestone_doji": bool(doji and upper / span >= .6 and lower / span <= .1),
        "bullish_engulfing": bool(bullish_engulfing),
        "bearish_engulfing": bool(bearish_engulfing),
        "morning_star": bool(morning_star),
        "evening_star": bool(evening_star),
        "harami": bool(harami),
        "piercing_line": bool(pc < po and c > o and o < pc and midpoint < c < po),
        "dark_cloud_cover": bool(pc > po and c < o and o > pc and po < c < midpoint),
        "three_white_soldiers": bool(all(closes[i] > opens[i] for i in range(target - 2, target + 1)) and closes[target - 2] < closes[target - 1] < closes[target]),
        "three_black_crows": bool(all(closes[i] < opens[i] for i in range(target - 2, target + 1)) and closes[target - 2] > closes[target - 1] > closes[target]),
    }
    prior_start = max(0, target - 20)
    resistance = float(np.max(highs[prior_start:target]))
    support = float(np.min(lows[prior_start:target]))
    returns = np.diff(closes[max(0, target - 14):target + 1]) / closes[max(0, target - 14):target]
    volatility = float(np.std(returns)) if len(returns) else 0.0
    tolerance = max(c * .005, c * volatility)
    confirmation = None
    if target < end:
        direction = 1 if any(patterns[name] for name in ("hammer", "inverted_hammer", "bullish_engulfing", "morning_star", "piercing_line", "three_white_soldiers")) else -1 if any(patterns[name] for name in ("hanging_man", "shooting_star", "bearish_engulfing", "evening_star", "dark_cloud_cover", "three_black_crows")) else 0
        confirmation = bool(direction and direction * (closes[target + 1] / closes[target] - 1.0) > 0)
    volume_confirmation = None
    if capabilities.has_volume and target >= 20:
        volumes = np.asarray([bar.volume for bar in bars[:end + 1]], dtype=float)
        volume_confirmation = bool(volumes[target] > np.mean(volumes[target - 20:target]))
    return StructureSnapshot(True, {
        "patterns": patterns, "preceding_trend": "up" if uptrend else "down" if downtrend else "range",
        "near_resistance": abs(c - resistance) <= tolerance,
        "near_support": abs(c - support) <= tolerance,
        "body_ratio": body / span, "upper_wick_ratio": upper / span,
        "lower_wick_ratio": lower / span, "realized_volatility_14": volatility,
        "volume_confirmation": volume_confirmation,
        "next_bar_confirmation": confirmation,
        "confirmation_available": target < end,
        "automatic_action": None,
    })
