"""Canonical session API; implementation remains the verified HR11 contract."""

from intraday_sessions import AggregationResult, SessionWindow, aggregate, validate_bar_session, validate_sessions

__all__ = ["AggregationResult", "SessionWindow", "aggregate", "validate_bar_session", "validate_sessions"]
