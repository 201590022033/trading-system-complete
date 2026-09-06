"""Modular metadata and capability registry for shadow technical research."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from research_indicators import DataCapabilities, MarketBar, calculate_expanded_indicators
from ichimoku_features import calculate_ichimoku
from structure_pattern_features import calculate_candlestick_context, calculate_fibonacci_context


REGISTRY_VERSION = "technical-feature-registry-v1"


@dataclass(frozen=True)
class TechnicalFeatureDefinition:
    name: str
    family: str
    required_inputs: tuple[str, ...]
    parameters: dict
    minimum_warmup: int
    supported_timeframes: tuple[str, ...]
    output_fields: tuple[str, ...]
    interpretation_notes: str
    capability_requirements: tuple[str, ...]
    version: str
    implementation_source: str
    implementation_status: str


@dataclass(frozen=True)
class RegistryComputation:
    name: str
    available: bool
    values: dict
    reason: str
    version: str
    shadow_only: bool = True


Calculator = Callable[[list[MarketBar], DataCapabilities, int, Optional[list[float]]], RegistryComputation]


class TechnicalFeatureRegistry:
    def __init__(self):
        self._definitions: dict[str, TechnicalFeatureDefinition] = {}
        self._calculators: dict[str, Calculator] = {}

    def register(self, definition: TechnicalFeatureDefinition, calculator: Optional[Calculator] = None) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"duplicate technical feature: {definition.name}")
        if definition.implementation_status == "implemented" and calculator is None:
            raise ValueError("implemented features require a calculator")
        if definition.implementation_status != "implemented" and calculator is not None:
            raise ValueError("non-implemented features cannot register a calculator")
        self._definitions[definition.name] = definition
        if calculator:
            self._calculators[definition.name] = calculator

    def definition(self, name: str) -> TechnicalFeatureDefinition:
        return self._definitions[name]

    def definitions(self) -> tuple[TechnicalFeatureDefinition, ...]:
        return tuple(self._definitions[name] for name in sorted(self._definitions))

    def compute(self, name: str, bars: Iterable[MarketBar], capabilities: DataCapabilities, as_of_index: int, benchmark_closes: Optional[list[float]] = None) -> RegistryComputation:
        definition = self.definition(name)
        if name not in self._calculators:
            return RegistryComputation(
                name, False, {}, f"{definition.implementation_status}: {definition.implementation_source}", definition.version
            )
        values = list(bars)
        if as_of_index < 0 or as_of_index >= len(values):
            raise ValueError("as_of_index is outside supplied bars")
        return self._calculators[name](values, capabilities, as_of_index, benchmark_closes)

    def to_dict(self) -> dict:
        return {"registry_version": REGISTRY_VERSION, "features": [asdict(item) for item in self.definitions()]}


def _existing_adapter(name: str, output_fields: tuple[str, ...]) -> Calculator:
    def calculate(bars: list[MarketBar], capabilities: DataCapabilities, as_of_index: int, benchmark_closes: Optional[list[float]]) -> RegistryComputation:
        snapshot = calculate_expanded_indicators(
            bars, capabilities, benchmark_closes=benchmark_closes, as_of_index=as_of_index
        )
        selected = {field: snapshot.features[field] for field in output_fields}
        unavailable = [field for field, value in selected.items() if not value.available]
        return RegistryComputation(
            name=name,
            available=not unavailable,
            values={field: value.value for field, value in selected.items() if value.available},
            reason="; ".join(snapshot.features[field].reason for field in unavailable),
            version=snapshot.version,
        )
    return calculate


def _ichimoku_adapter(bars, capabilities, as_of_index, benchmark_closes):
    snapshot = calculate_ichimoku(bars, capabilities, as_of_index)
    return RegistryComputation("ichimoku", snapshot.available, snapshot.values, snapshot.reason, snapshot.version)


def _fibonacci_adapter(bars, capabilities, as_of_index, benchmark_closes):
    snapshot = calculate_fibonacci_context(bars, capabilities, as_of_index)
    return RegistryComputation("fibonacci_context", snapshot.available, snapshot.values, snapshot.reason, snapshot.version)


def _candlestick_adapter(bars, capabilities, as_of_index, benchmark_closes):
    snapshot = calculate_candlestick_context(bars, capabilities, as_of_index)
    return RegistryComputation("candlestick_patterns", snapshot.available, snapshot.values, snapshot.reason, snapshot.version)


def _definition(
    name: str, family: str, inputs: tuple[str, ...], warmup: int,
    outputs: tuple[str, ...], notes: str, *, parameters: Optional[dict] = None,
    capabilities: tuple[str, ...] = (), status: str = "planned",
    source: str = "scheduled for HR5/HR6 deterministic implementation",
) -> TechnicalFeatureDefinition:
    return TechnicalFeatureDefinition(
        name, family, inputs, parameters or {}, warmup, ("daily", "intraday"),
        outputs, notes, capabilities, "v1", source, status,
    )


def build_default_registry() -> TechnicalFeatureRegistry:
    registry = TechnicalFeatureRegistry()
    existing = (
        _definition("macd", "trend", ("close",), 26, ("macd",), "EMA12 minus EMA26; no signal line yet.", status="implemented", source="research_indicators.py"),
        _definition("bollinger", "volatility", ("close",), 20, ("bollinger_middle", "bollinger_upper", "bollinger_lower", "close_zscore"), "Twenty-close population bands at two standard deviations.", status="implemented", source="research_indicators.py"),
        _definition("atr", "volatility", ("high", "low", "close"), 15, ("atr",), "Mean true range; not a directional signal.", capabilities=("has_ohlc",), status="implemented", source="research_indicators.py"),
        _definition("adx_dmi", "trend", ("high", "low", "close"), 29, ("adx", "plus_di", "minus_di"), "Trend strength and directional movement.", capabilities=("has_ohlc",), status="implemented", source="research_indicators.py"),
        _definition("relative_strength", "momentum", ("close", "benchmark_close"), 15, ("relative_strength",), "Asset return minus aligned benchmark return.", capabilities=("has_benchmark",), status="implemented", source="research_indicators.py"),
        _definition("relative_volume", "volume_flow", ("close", "volume"), 21, ("relative_volume", "median_dollar_volume"), "Current volume relative to prior twenty and liquidity proxy.", capabilities=("has_volume",), status="implemented", source="research_indicators.py"),
        _definition("session_context", "structure", ("high", "low", "close", "volume"), 5, ("session_vwap", "opening_range_high", "opening_range_low"), "Intraday-only session VWAP and opening range.", capabilities=("has_ohlc", "has_volume", "intraday"), status="implemented", source="research_indicators.py"),
    )
    for item in existing:
        registry.register(item, _existing_adapter(item.name, item.output_fields))

    planned = (
        _definition("sma_structure", "trend", ("close",), 20, ("sma_fast", "sma_slow", "sma_spread"), "Continuous moving-average structure; legacy state remains separate."),
        _definition("ema_structure", "trend", ("close",), 26, ("ema_fast", "ema_slow", "ema_spread"), "EMA levels and relative spread."),
        _definition("aroon", "trend", ("high", "low"), 25, ("aroon_up", "aroon_down"), "Time since rolling high/low.", capabilities=("has_ohlc",)),
        _definition("supertrend", "trend", ("high", "low", "close"), 15, ("supertrend", "direction"), "ATR-derived trailing structure.", capabilities=("has_ohlc",)),
        _definition("parabolic_sar", "trend", ("high", "low"), 3, ("sar", "direction"), "Deterministic stop-and-reverse state.", capabilities=("has_ohlc",)),
        _definition("rsi", "momentum", ("close",), 15, ("rsi",), "Continuous RSI feature; legacy threshold signal remains separate."),
        _definition("stochastic", "momentum", ("high", "low", "close"), 14, ("stochastic_k", "stochastic_d"), "OHLC stochastic rather than legacy close-only simplification.", capabilities=("has_ohlc",)),
        _definition("roc", "momentum", ("close",), 21, ("roc_20",), "Rate of change."),
        _definition("williams_r", "momentum", ("high", "low", "close"), 14, ("williams_r",), "Range-relative momentum.", capabilities=("has_ohlc",)),
        _definition("cci", "momentum", ("high", "low", "close"), 20, ("cci",), "Typical-price deviation.", capabilities=("has_ohlc",)),
        _definition("keltner", "volatility", ("high", "low", "close"), 21, ("keltner_middle", "keltner_upper", "keltner_lower"), "EMA and ATR channel.", capabilities=("has_ohlc",)),
        _definition("realized_volatility", "volatility", ("close",), 21, ("realized_volatility_20", "volatility_change"), "Close-return volatility and expansion/contraction."),
        _definition("obv", "volume_flow", ("close", "volume"), 2, ("obv",), "Cumulative signed volume.", capabilities=("has_volume",)),
        _definition("mfi", "volume_flow", ("high", "low", "close", "volume"), 15, ("mfi",), "Money Flow Index.", capabilities=("has_ohlc", "has_volume")),
        _definition("chaikin_money_flow", "volume_flow", ("high", "low", "close", "volume"), 20, ("cmf",), "Location-weighted volume flow.", capabilities=("has_ohlc", "has_volume")),
        _definition("accumulation_distribution", "volume_flow", ("high", "low", "close", "volume"), 1, ("ad_line",), "Cumulative accumulation/distribution.", capabilities=("has_ohlc", "has_volume")),
        _definition("donchian", "structure", ("high", "low", "close"), 20, ("donchian_high", "donchian_low", "channel_position"), "Rolling channel and breakout distance.", capabilities=("has_ohlc",)),
        _definition("support_resistance", "structure", ("high", "low", "close"), 20, ("support", "resistance", "distance_support", "distance_resistance"), "Rolling extrema context.", capabilities=("has_ohlc",)),
        _definition("swing_structure", "structure", ("high", "low", "close"), 7, ("swing_high", "swing_low", "structure_state"), "Confirmed local swings using only available bars.", capabilities=("has_ohlc",)),
        _definition("price_gap", "structure", ("open", "close"), 2, ("gap_return",), "Current open versus prior close.", capabilities=("has_ohlc",)),
    )
    for item in planned:
        registry.register(item)
    ichimoku = _definition(
        "ichimoku", "trend", ("high", "low", "close"), 78,
        ("tenkan", "kijun", "current_senkou_a", "current_senkou_b",
         "future_senkou_a_known_at_t", "future_senkou_b_known_at_t",
         "price_cloud_state", "cloud_thickness_ratio", "future_cloud_direction",
         "tenkan_kijun_spread_ratio", "distance_from_kijun",
         "chikou_vs_historical_price_26", "cloud_breakout", "tk_cross",
         "tk_cross_strength", "regime_consistency"),
        "Full displaced point-in-time cloud, TK and Chikou context; never uses future bars.",
        capabilities=("has_ohlc",), status="implemented", source="ichimoku_features.py",
    )
    registry.register(ichimoku, _ichimoku_adapter)
    fibonacci = _definition(
        "fibonacci_context", "fibonacci", ("high", "low", "close"), 20,
        ("swing_direction", "swing_high", "swing_low", "levels", "nearest_level",
         "distance_to_level_ratio", "trend_confluence", "support_resistance_confluence"),
        "Contextual levels from a defined preceding swing; automatic_action is always null.",
        capabilities=("has_ohlc",), status="implemented", source="structure_pattern_features.py",
    )
    candles = _definition(
        "candlestick_patterns", "candlestick", ("open", "high", "low", "close"), 3,
        ("patterns", "preceding_trend", "near_resistance", "near_support", "body_ratio",
         "upper_wick_ratio", "lower_wick_ratio", "realized_volatility_14",
         "volume_confirmation", "next_bar_confirmation", "confirmation_available"),
        "Deterministic patterns plus context; confirmation only after its bar is available.",
        capabilities=("has_ohlc",), status="implemented", source="structure_pattern_features.py",
    )
    registry.register(fibonacci, _fibonacci_adapter)
    registry.register(candles, _candlestick_adapter)
    return registry


DEFAULT_TECHNICAL_REGISTRY = build_default_registry()


def write_registry(path: Path | str) -> None:
    Path(path).write_text(json.dumps(DEFAULT_TECHNICAL_REGISTRY.to_dict(), indent=2) + "\n", encoding="utf-8")


def build_intraday_registry(**session_context) -> TechnicalFeatureRegistry:
    """Add HR11 entries without altering the daily/default registry contract."""
    from intraday_features import extend_registry
    return extend_registry(**session_context)
