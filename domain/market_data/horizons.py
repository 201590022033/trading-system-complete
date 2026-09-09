"""Canonical, non-colliding intraday and daily horizon contracts."""

from dataclasses import dataclass
from datetime import timedelta

from intraday_data import utc
from intraday_horizons import HORIZONS, IntradayHorizon, get_horizon, primary_horizon

VERSION = "canonical-market-horizons-v1"


@dataclass(frozen=True)
class IntradayDurationHorizon:
    """A duration measured in intraday minutes, never in trading sessions."""

    horizon_id: str
    minutes: int
    version: str = VERSION

    def __post_init__(self):
        if not self.horizon_id.startswith("intraday_") or self.minutes <= 0:
            raise ValueError("Intraday duration horizon requires a positive duration")

    def target(self, decision_time, session):
        decision = utc(decision_time)
        if not session.open_time <= decision < session.close_time:
            return None
        target = decision + timedelta(minutes=self.minutes)
        if target > session.close_time or any(decision < end and target > start for start, end in session.breaks):
            return None
        return target


@dataclass(frozen=True)
class DailySessionHorizon:
    """A horizon ending at a session close, distinct from intraday minutes."""

    horizon_id: str = "daily_session_eod"
    version: str = VERSION

    def __post_init__(self):
        if not self.horizon_id.startswith("daily_"):
            raise ValueError("Daily session horizon requires a daily identity")

    def target(self, decision_time, session):
        decision = utc(decision_time)
        return session.close_time if session.open_time <= decision < session.close_time else None


__all__ = [
    "DailySessionHorizon", "HORIZONS", "IntradayDurationHorizon", "IntradayHorizon",
    "VERSION", "get_horizon", "primary_horizon",
]
