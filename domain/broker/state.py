"""Immutable broker-neutral read-only account and position snapshots."""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite

VERSION="broker-state-v1"
class Freshness(str,Enum): FRESH="FRESH"; STALE="STALE"; UNAVAILABLE="UNAVAILABLE"
def utc(value):
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None: raise ValueError("timezone-aware snapshot required")
    return value.astimezone(timezone.utc)
def number(value,name):
    if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value)): raise ValueError(f"{name} must be finite or unavailable")

@dataclass(frozen=True)
class BrokerAccountState:
    broker:str; environment:str; account_id:str; account_name:str|None; account_type:str|None
    preferred:bool|None; account_currency:str|None; balance:float|None; equity:float|None
    available_funds:float|None; deposit:float|None; profit_loss:float|None; unrealized_pnl:float|None
    margin_used:float|None; margin_available:float|None; margin_requirement:float|None
    account_status:str|None; enabled:bool|None; retrieved_at:datetime; freshness:Freshness
    source_endpoint:str="GET /accounts"; source_version:str="1"; normalization_version:str=VERSION
    def __post_init__(self):
        object.__setattr__(self,"retrieved_at",utc(self.retrieved_at))
        if not self.broker or not self.environment or not self.account_id: raise ValueError("account identity required")
        for name in ("balance","equity","available_funds","deposit","profit_loss","unrealized_pnl","margin_used","margin_available","margin_requirement"): number(getattr(self,name),name)

@dataclass(frozen=True)
class BrokerPositionState:
    broker:str; environment:str; account_id:str; broker_position_id:str; instrument_id:str|None
    mapping_status:str; epic:str; execution_symbol:str; direction:str; quantity:float
    open_level:float; current_level:float|None; stop_level:float|None; limit_level:float|None
    unrealized_pnl:float|None; pnl_currency:str|None; opened_at:datetime|None; retrieved_at:datetime
    contract_size:float|None; currency:str|None; market_status:str|None
    source_endpoint:str="GET /positions"; source_version:str="2"; normalization_version:str=VERSION
    def __post_init__(self):
        object.__setattr__(self,"retrieved_at",utc(self.retrieved_at))
        if self.opened_at is not None: object.__setattr__(self,"opened_at",utc(self.opened_at))
        if not all((self.broker,self.environment,self.account_id,self.broker_position_id,self.epic,self.execution_symbol)): raise ValueError("position identity required")
        if self.direction not in {"LONG","SHORT"} or self.mapping_status not in {"RESOLVED","UNRESOLVED_INSTRUMENT_MAPPING"}: raise ValueError("invalid direction or mapping")
        for name in ("quantity","open_level","current_level","stop_level","limit_level","unrealized_pnl","contract_size"): number(getattr(self,name),name)
        if self.quantity<=0 or self.open_level<=0: raise ValueError("positive quantity and open level required")

@dataclass(frozen=True)
class BrokerStateSnapshot:
    broker:str; environment:str; account:BrokerAccountState; positions:tuple[BrokerPositionState,...]
    positions_available:bool; position_count:int; retrieved_at:datetime; freshness:Freshness
    error:str|None=None; normalization_version:str=VERSION
    def __post_init__(self):
        object.__setattr__(self,"retrieved_at",utc(self.retrieved_at))
        if not self.positions_available and self.positions: raise ValueError("unavailable positions cannot contain records")
        if self.position_count!=len(self.positions): raise ValueError("position count mismatch")

__all__=["BrokerAccountState","BrokerPositionState","BrokerStateSnapshot","Freshness","VERSION"]
