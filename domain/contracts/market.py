"""Canonical market-data contracts."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Optional, Tuple


class DataGrade(str, Enum):
    RESEARCH = "RESEARCH_DATA"
    DELAYED_PUBLIC = "DELAYED_PUBLIC"
    EXECUTION_GRADE = "EXECUTION_GRADE"


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


def utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware UTC timestamp required")
    return value.astimezone(timezone.utc)


def finite(value: float, field: str, *, minimum: Optional[float] = None) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    authority_tier: int
    access_mode: str
    data_grade: DataGrade
    max_age_seconds: int
    status: str

    def __post_init__(self) -> None:
        if not self.source_id or self.authority_tier not in {1, 2, 3, 4}:
            raise ValueError("source identity and authority tier are required")
        if self.access_mode not in {"licensed", "public_rss", "manual"}:
            raise ValueError("unsupported source access mode")
        if not isinstance(self.data_grade, DataGrade) or self.max_age_seconds <= 0:
            raise ValueError("source grade and positive freshness are required")
        if not self.status:
            raise ValueError("source status is required")


@dataclass(frozen=True)
class CanonicalBar:
    instrument_id: str
    timeframe: str
    interval_start: datetime
    event_time: datetime
    available_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    source_policy: SourcePolicy
    input_record_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("interval_start", "event_time", "available_time"):
            object.__setattr__(self, name, utc_timestamp(getattr(self, name)))
        if not self.instrument_id or not self.timeframe or not isinstance(self.source_policy, SourcePolicy):
            raise ValueError("bar identity, timeframe and source policy are required")
        if not self.interval_start < self.event_time <= self.available_time:
            raise ValueError("bar timestamps must satisfy start < event <= available")
        for name in ("open", "high", "low", "close"):
            finite(getattr(self, name), name, minimum=0.0)
        if self.high < self.low or not self.low <= self.open <= self.high or not self.low <= self.close <= self.high:
            raise ValueError("OHLC values must be internally consistent")
        for name in ("volume", "bid", "ask"):
            value = getattr(self, name)
            if value is not None:
                finite(value, name, minimum=0.0)
        if (self.bid is None) != (self.ask is None) or (self.bid is not None and self.bid > self.ask):
            raise ValueError("bid and ask must be paired and non-crossed")
        if not isinstance(self.input_record_ids, tuple):
            raise ValueError("input record lineage must be a tuple")

    def to_dict(self) -> dict[str, Any]:
        result = {
            "instrument_id": self.instrument_id, "timeframe": self.timeframe,
            "interval_start": self.interval_start.isoformat(), "event_time": self.event_time.isoformat(),
            "available_time": self.available_time.isoformat(), "open": self.open, "high": self.high,
            "low": self.low, "close": self.close, "volume": self.volume, "bid": self.bid, "ask": self.ask,
            "source_policy": {"source_id": self.source_policy.source_id,
                              "authority_tier": self.source_policy.authority_tier,
                              "access_mode": self.source_policy.access_mode,
                              "data_grade": self.source_policy.data_grade.value,
                              "max_age_seconds": self.source_policy.max_age_seconds,
                              "status": self.source_policy.status},
            "input_record_ids": list(self.input_record_ids),
        }
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CanonicalBar":
        data = dict(value)
        source = dict(data["source_policy"])
        source["data_grade"] = DataGrade(source["data_grade"])
        data["source_policy"] = SourcePolicy(**source)
        data["input_record_ids"] = tuple(data.get("input_record_ids", ()))
        for name in ("interval_start", "event_time", "available_time"):
            data[name] = datetime.fromisoformat(data[name])
        return cls(**data)
