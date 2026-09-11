"""Canonical market-data contracts backed by the preserved HR11 semantics."""

from .aggregation import AggregationResult, aggregate
from .cross_asset import CrossAssetSnapshot, FactorObservation, factor_return, join_factors
from .horizons import DailySessionHorizon, HORIZONS, IntradayDurationHorizon, get_horizon
from .sessions import SessionWindow, validate_bar_session, validate_sessions
from .streaming import (CanonicalMarketObservation, MarketStreamSubscription,
                        OrderingState, RawMarketUpdate, StreamHealth, StreamStatus)

__all__ = [
    "AggregationResult", "aggregate", "CrossAssetSnapshot", "FactorObservation",
    "factor_return", "join_factors", "DailySessionHorizon", "HORIZONS",
    "IntradayDurationHorizon", "get_horizon", "SessionWindow",
    "validate_bar_session", "validate_sessions", "CanonicalMarketObservation",
    "MarketStreamSubscription", "OrderingState", "RawMarketUpdate", "StreamHealth", "StreamStatus",
]
