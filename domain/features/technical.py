"""Legacy reference and disconnected candidate technical features.

The legacy functions intentionally reproduce ``data_pipeline.SignalGenerator``
semantics. Candidate functions are research-only and use distinct IDs.
"""

from math import isfinite
from typing import Sequence

from data_pipeline import SignalGenerator
from domain.registry.feature import (FeatureStatus, FeatureValue,
                                     TechnicalFeatureDefinition,
                                     TechnicalFeatureRegistry)


def _legacy_generator(values: Sequence[float]) -> SignalGenerator:
    generator = SignalGenerator(buffer_size=max(100, len(values)))
    for value in values:
        generator.add_vwap("fixture", value)
    return generator


def legacy_rsi(values: Sequence[float]) -> FeatureValue:
    if len(values) < 15:
        return FeatureValue(False, reason="requires 15 closes")
    return FeatureValue(True, _legacy_generator(values).calculate_rsi_signal("fixture")[0])


def legacy_sma_signal(values: Sequence[float]) -> FeatureValue:
    if len(values) < 20:
        return FeatureValue(False, reason="requires 20 closes")
    return FeatureValue(True, _legacy_generator(values).calculate_sma_signal("fixture"))


def legacy_breakout_signal(values: Sequence[float]) -> FeatureValue:
    if len(values) < 20:
        return FeatureValue(False, reason="requires 20 closes")
    return FeatureValue(True, _legacy_generator(values).calculate_breakout_signal("fixture"))


def legacy_stochastic(values: Sequence[float]) -> FeatureValue:
    if len(values) < 14:
        return FeatureValue(False, reason="requires 14 closes")
    window = values[-14:]
    high, low, close = max(window), min(window), window[-1]
    result = 50.0 if high == low else 100.0 * (close - low) / (high - low)
    return FeatureValue(True, result)


def _ema(values: Sequence[float], period: int) -> float:
    alpha = 2.0 / (period + 1.0)
    result = float(values[0])
    for value in values[1:]:
        result = alpha * float(value) + (1 - alpha) * result
    return result


def candidate_rsi_wilder(values: Sequence[float]) -> FeatureValue:
    if len(values) < 15:
        return FeatureValue(False, reason="requires 15 closes")
    deltas = [float(values[i]) - float(values[i - 1]) for i in range(1, len(values))]
    gains = [max(delta, 0.0) for delta in deltas]
    losses = [max(-delta, 0.0) for delta in deltas]
    avg_gain = sum(gains[:14]) / 14
    avg_loss = sum(losses[:14]) / 14
    for gain, loss in zip(gains[14:], losses[14:]):
        avg_gain = (avg_gain * 13 + gain) / 14
        avg_loss = (avg_loss * 13 + loss) / 14
    return FeatureValue(True, 100.0 if avg_loss == 0 and avg_gain else
                        50.0 if avg_loss == 0 else 100.0 - 100.0 / (1 + avg_gain / avg_loss))


def candidate_donchian(values: Sequence[float]) -> FeatureValue:
    if len(values) < 21:
        return FeatureValue(False, reason="requires 21 closes")
    prior = values[-21:-1]
    current = values[-1]
    return FeatureValue(True, 1 if current > max(prior) else -1 if current < min(prior) else 0)


def candidate_macd_line_signal(values: Sequence[float]) -> FeatureValue:
    if len(values) < 35:
        return FeatureValue(False, reason="requires 35 closes")
    macd_series = []
    for end in range(26, len(values) + 1):
        sample = values[:end]
        macd_series.append(_ema(sample, 12) - _ema(sample, 26))
    if len(macd_series) < 9:
        return FeatureValue(False, reason="requires 9 MACD values")
    macd = macd_series[-1]
    signal = _ema(macd_series[-9:], 9)
    return FeatureValue(True, {"line": macd, "signal": signal, "histogram": macd - signal})


def candidate_bollinger(values: Sequence[float]) -> FeatureValue:
    if len(values) < 20:
        return FeatureValue(False, reason="requires 20 closes")
    window = [float(item) for item in values[-20:]]
    middle = sum(window) / 20
    std = (sum((item - middle) ** 2 for item in window) / 20) ** 0.5
    return FeatureValue(True, {"middle": middle, "upper": middle + 2 * std,
                               "lower": middle - 2 * std,
                               "zscore": (window[-1] - middle) / std if std else 0.0})


def build_default_registry() -> TechnicalFeatureRegistry:
    registry = TechnicalFeatureRegistry()
    definitions = (
        ("feat_rsi_legacy_v1", "RSI", "momentum", ("close",), 15, "data_pipeline.SignalGenerator.calculate_rsi_signal", legacy_rsi),
        ("feat_sma_legacy_v1", "SMA trend", "trend", ("close",), 20, "data_pipeline.SignalGenerator.calculate_sma_signal", legacy_sma_signal),
        ("feat_breakout_close_legacy_v1", "Close breakout", "structure", ("close",), 20, "data_pipeline.SignalGenerator.calculate_breakout_signal", legacy_breakout_signal),
        ("feat_stoch_close_legacy_v1", "Close stochastic", "momentum", ("close",), 14, "data_pipeline.SignalGenerator.generate_indicators", legacy_stochastic),
    )
    for feature_id, display, family, fields, warmup, reference, calculator in definitions:
        registry.register(TechnicalFeatureDefinition(feature_id, "legacy-v1", display, family, {}, fields, warmup,
                                                      ("daily", "intraday"), ("equity",), reference, FeatureStatus.LEGACY), calculator)
    candidates = (
        ("feat_rsi_wilder_v2", "Wilder RSI", "momentum", ("close",), 15, candidate_rsi_wilder),
        ("feat_donchian_break_v2", "Donchian breakout", "structure", ("close",), 21, candidate_donchian),
        ("feat_macd_line_signal_v2", "MACD line and signal", "trend", ("close",), 35, candidate_macd_line_signal),
        ("feat_bollinger_v2", "Bollinger bands", "volatility", ("close",), 20, candidate_bollinger),
    )
    for feature_id, display, family, fields, warmup, calculator in candidates:
        registry.register(TechnicalFeatureDefinition(feature_id, "candidate-v2", display, family, {}, fields, warmup,
                                                      ("daily", "intraday"), ("equity",),
                                                      "domain.features.technical candidate implementation", FeatureStatus.CANDIDATE), calculator)
    return registry


DEFAULT_FEATURE_REGISTRY = build_default_registry()
