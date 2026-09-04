"""Authoritative versioned signal definitions for HR8+ technical research."""

from __future__ import annotations

import numpy as np
import pandas as pd


SIGNAL_DEFINITION_VERSION = "technical-signals-v1"
INDICATORS = (
    "rsi",
    "sma",
    "breakout",
    "stochastic",
    "macd",
    "bollinger_mean_reversion",
    "adx_dmi",
    "ichimoku",
)


def technical_signal_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return {-1, 0, 1, unavailable} signals without future observations."""
    result = pd.DataFrame(index=frame.index, columns=INDICATORS, dtype=float)
    result["rsi"] = frame["rsi_signal"].where(frame["rsi"].notna())
    result["sma"] = frame["sma_signal"].where(frame["sma_slow"].notna())
    result["breakout"] = frame["breakout_signal"].where(frame["technical_warmup_complete"])
    result["stochastic"] = frame["stochastic_signal"].where(frame["stochastic"].notna())
    result["macd"] = np.sign(frame["macd"]).where(frame["macd"].notna())
    result["bollinger_mean_reversion"] = pd.Series(
        np.select(
            [frame["bollinger_zscore"] <= -1.5, frame["bollinger_zscore"] >= 1.5],
            [1, -1],
            default=0,
        ),
        index=frame.index,
        dtype=float,
    ).where(frame["bollinger_zscore"].notna())
    result["adx_dmi"] = pd.Series(
        np.where(frame["adx"] >= 25, frame["dmi_direction"], 0),
        index=frame.index,
        dtype=float,
    ).where(frame["adx"].notna() & frame["dmi_direction"].notna())
    result["ichimoku"] = frame["ichimoku_direction"].where(frame["ichimoku_direction"].notna())
    return result
