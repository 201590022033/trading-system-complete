"""Broker-neutral, immutable real-time market observation contracts."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math

STREAM_VERSION = "canonical-market-stream-v1"

class StreamStatus(str, Enum):
    LIVE="LIVE"; STALE="STALE"; DISCONNECTED="DISCONNECTED"; RECONNECTING="RECONNECTING"; UNAVAILABLE="UNAVAILABLE"

class OrderingState(str, Enum):
    FIRST="FIRST"; IN_ORDER="IN_ORDER"; DUPLICATE="DUPLICATE"; REPEATED="REPEATED"; OUT_OF_ORDER="OUT_OF_ORDER"; SOURCE_SEQUENCE_UNAVAILABLE="SOURCE_SEQUENCE_UNAVAILABLE"

def _utc(value, name):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True)
class MarketStreamSubscription:
    subscription_id: str; instrument_id: str; execution_symbol: str; broker: str; epic: str
    fields: tuple[str,...] = ("BIDPRICE1","ASKPRICE1","TIMESTAMP","DLG_FLAG","DELAY")
    def __post_init__(self):
        if not all((self.subscription_id,self.instrument_id,self.execution_symbol,self.broker,self.epic)):
            raise ValueError("resolved canonical instrument mapping required")

@dataclass(frozen=True)
class RawMarketUpdate:
    subscription_id: str; epic: str; values: dict; received_at: datetime; source_sequence: str|None=None
    def __post_init__(self): object.__setattr__(self,"received_at",_utc(self.received_at,"received_at"))

@dataclass(frozen=True)
class CanonicalMarketObservation:
    instrument_id: str; execution_symbol: str; broker: str; epic: str; subscription_id: str
    source_timestamp: datetime|None; received_at: datetime; timestamp_basis: str
    bid: float|None; ask: float|None; mid: float|None; last: float|None; spread: float|None
    market_status: str|None; data_grade: str; stale: bool; ordering_state: OrderingState
    source_sequence: str|None; provenance: str; source_version: str=STREAM_VERSION
    delayed: bool|None=None
    def __post_init__(self):
        object.__setattr__(self,"received_at",_utc(self.received_at,"received_at"))
        if self.source_timestamp is not None: object.__setattr__(self,"source_timestamp",_utc(self.source_timestamp,"source_timestamp"))
        for name in ("bid","ask","mid","last","spread"):
            value=getattr(self,name)
            if value is not None and (isinstance(value,bool) or not math.isfinite(value) or value < 0): raise ValueError(f"invalid {name}")
        if (self.bid is None)!=(self.ask is None): raise ValueError("bid and ask must be paired")
        if self.bid is not None and self.bid > self.ask: raise ValueError("crossed quote")

@dataclass(frozen=True)
class StreamHealth:
    status: StreamStatus; connected: bool; last_message_at: datetime|None; last_valid_quote_at: datetime|None
    subscription_count: int; error: str|None; reconnect_attempts: int

__all__=["STREAM_VERSION","StreamStatus","OrderingState","MarketStreamSubscription","RawMarketUpdate","CanonicalMarketObservation","StreamHealth"]
