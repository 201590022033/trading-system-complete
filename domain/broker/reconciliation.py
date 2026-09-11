"""Pure read-only comparison of broker and explicitly adapted internal snapshots."""
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Mapping
from .state import BrokerStateSnapshot,Freshness

VERSION="broker-reconciliation-v1"
class Severity(str,Enum):INFO="INFO";WARNING="WARNING";CRITICAL="CRITICAL"
class DiscrepancyType(str,Enum):
    BROKER_ONLY_POSITION="BROKER_ONLY_POSITION";INTERNAL_ONLY_POSITION="INTERNAL_ONLY_POSITION";DIRECTION_MISMATCH="DIRECTION_MISMATCH";QUANTITY_MISMATCH="QUANTITY_MISMATCH";ENTRY_LEVEL_MISMATCH="ENTRY_LEVEL_MISMATCH";INSTRUMENT_MAPPING_UNRESOLVED="INSTRUMENT_MAPPING_UNRESOLVED";ACCOUNT_CURRENCY_MISMATCH="ACCOUNT_CURRENCY_MISMATCH";ACCOUNT_VALUE_MISMATCH="ACCOUNT_VALUE_MISMATCH";STALE_BROKER_SNAPSHOT="STALE_BROKER_SNAPSHOT";STALE_INTERNAL_SNAPSHOT="STALE_INTERNAL_SNAPSHOT";FIELD_UNAVAILABLE="FIELD_UNAVAILABLE";SEMANTICALLY_NOT_COMPARABLE="SEMANTICALLY_NOT_COMPARABLE";BROKER_UNAVAILABLE="BROKER_UNAVAILABLE";INTERNAL_UNAVAILABLE="INTERNAL_UNAVAILABLE"
def utc(x):
    if not isinstance(x,datetime) or x.tzinfo is None or x.utcoffset() is None:raise ValueError("timezone-aware timestamp required")
    return x.astimezone(timezone.utc)
def finite(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not isfinite(x) or x<0:raise ValueError(f"{name} must be nonnegative finite")

@dataclass(frozen=True)
class InternalAccountSnapshot:
    source:str;environment:str;account_id:str|None;currency:str|None;available_funds:float|None;balance:float|None;unrealized_pnl:float|None;as_of:datetime;freshness:Freshness;source_version:str
    def __post_init__(self):object.__setattr__(self,"as_of",utc(self.as_of))
@dataclass(frozen=True)
class InternalPositionSnapshot:
    internal_position_id:str;broker_position_id:str|None;instrument_id:str|None;epic:str|None;direction:str;quantity:float;quantity_unit:str|None;open_level:float|None;stop_level:float|None;limit_level:float|None;unrealized_pnl:float|None;pnl_currency:str|None
    def __post_init__(self):
        if self.direction not in {"LONG","SHORT"}:raise ValueError("invalid internal direction")
        finite(self.quantity,"quantity")
@dataclass(frozen=True)
class ReconciliationSnapshot:
    source:str;environment:str;account:InternalAccountSnapshot;positions:tuple[InternalPositionSnapshot,...];positions_available:bool;as_of:datetime;freshness:Freshness;source_version:str
    def __post_init__(self):
        object.__setattr__(self,"as_of",utc(self.as_of))
        if not self.positions_available and self.positions:raise ValueError("unavailable positions cannot be flat records")
@dataclass(frozen=True)
class ReconciliationConfig:
    quantity_tolerance:float;entry_level_tolerance:float;account_value_tolerance:float;pnl_tolerance:float;max_snapshot_skew_seconds:float;quantity_units:Mapping[str,str];account_comparisons:tuple[tuple[str,str],...]=(("account_currency","currency"),)
    def __post_init__(self):
        for name in ("quantity_tolerance","entry_level_tolerance","account_value_tolerance","pnl_tolerance","max_snapshot_skew_seconds"):finite(getattr(self,name),name)
        object.__setattr__(self,"quantity_units",MappingProxyType(dict(self.quantity_units)))
@dataclass(frozen=True)
class ReconciliationDiscrepancy:
    discrepancy_type:DiscrepancyType;severity:Severity;field:str;broker_value:object;internal_value:object;position_reference:str|None;message:str
@dataclass(frozen=True)
class PositionComparison:
    broker_position_id:str|None;internal_position_id:str|None;match_basis:str|None;discrepancies:tuple[ReconciliationDiscrepancy,...]
@dataclass(frozen=True)
class AccountComparison:
    compared_fields:tuple[str,...];discrepancies:tuple[ReconciliationDiscrepancy,...]
@dataclass(frozen=True)
class BrokerReconciliationResult:
    reconciliation_id:str;version:str;evaluated_at:datetime;broker_snapshot_reference:str;internal_snapshot_reference:str;account_comparison:AccountComparison;position_comparisons:tuple[PositionComparison,...];discrepancies:tuple[ReconciliationDiscrepancy,...];severity_summary:Mapping[str,int];clean:bool;warnings:tuple[str,...];provenance:str
    def __post_init__(self):
        object.__setattr__(self,"evaluated_at",utc(self.evaluated_at));object.__setattr__(self,"severity_summary",MappingProxyType(dict(self.severity_summary)))

def _d(kind,severity,field,b,i,ref,message):return ReconciliationDiscrepancy(kind,severity,field,b,i,ref,message)
def _match(broker,internal,used):
    candidates=[]
    if broker.broker_position_id:candidates=[x for x in internal if x.internal_position_id not in used and x.broker_position_id==broker.broker_position_id]
    if not candidates and broker.epic:candidates=[x for x in internal if x.internal_position_id not in used and x.epic==broker.epic and x.direction==broker.direction]
    if not candidates and broker.instrument_id:candidates=[x for x in internal if x.internal_position_id not in used and x.instrument_id==broker.instrument_id]
    return candidates[0] if len(candidates)==1 else None,("DEAL_ID" if candidates and candidates[0].broker_position_id==broker.broker_position_id else "EPIC_ACCOUNT_DIRECTION" if candidates and candidates[0].epic==broker.epic else "CANONICAL_INSTRUMENT" if candidates else None)

def reconcile(broker:BrokerStateSnapshot|None,internal:ReconciliationSnapshot|None,config:ReconciliationConfig,evaluated_at):
    evaluated_at=utc(evaluated_at);all_d=[];pcs=[];warnings=[]
    if broker is None:
        all_d.append(_d(DiscrepancyType.BROKER_UNAVAILABLE,Severity.CRITICAL,"snapshot",None,None,None,"broker snapshot unavailable"))
    if internal is None:
        all_d.append(_d(DiscrepancyType.INTERNAL_UNAVAILABLE,Severity.CRITICAL,"snapshot",None,None,None,"internal snapshot unavailable"))
    if broker is None or internal is None:return _result(broker,internal,evaluated_at,AccountComparison((),()),(),all_d,warnings)
    if not broker.positions_available:all_d.append(_d(DiscrepancyType.BROKER_UNAVAILABLE,Severity.CRITICAL,"positions",False,internal.positions_available,None,"broker positions unavailable"))
    if not internal.positions_available:all_d.append(_d(DiscrepancyType.INTERNAL_UNAVAILABLE,Severity.CRITICAL,"positions",broker.positions_available,False,None,"internal positions unavailable"))
    if broker.freshness is Freshness.STALE:all_d.append(_d(DiscrepancyType.STALE_BROKER_SNAPSHOT,Severity.WARNING,"freshness",broker.freshness.value,internal.freshness.value,None,"broker snapshot stale"))
    if internal.freshness is Freshness.STALE:all_d.append(_d(DiscrepancyType.STALE_INTERNAL_SNAPSHOT,Severity.WARNING,"freshness",broker.freshness.value,internal.freshness.value,None,"internal snapshot stale"))
    account_d=[];compared=[]
    for bf,inf in config.account_comparisons:
        bv=getattr(broker.account,bf);iv=getattr(internal.account,inf)
        if bv is None or iv is None:account_d.append(_d(DiscrepancyType.FIELD_UNAVAILABLE,Severity.INFO,bf,bv,iv,None,"account field unavailable"));continue
        compared.append(bf)
        mismatch=(bv!=iv) if not isinstance(bv,(int,float)) else abs(bv-iv)>config.account_value_tolerance
        if mismatch:account_d.append(_d(DiscrepancyType.ACCOUNT_CURRENCY_MISMATCH if "currency" in bf else DiscrepancyType.ACCOUNT_VALUE_MISMATCH,Severity.WARNING,bf,bv,iv,None,"comparable account field differs"))
    all_d.extend(account_d);used=set()
    if broker.positions_available and internal.positions_available:
        for bp in broker.positions:
            local,basis=_match(bp,internal.positions,used);pd=[]
            if bp.mapping_status=="UNRESOLVED_INSTRUMENT_MAPPING":pd.append(_d(DiscrepancyType.INSTRUMENT_MAPPING_UNRESOLVED,Severity.WARNING,"instrument_id",bp.epic,None,bp.broker_position_id,"broker EPIC unresolved"))
            if local is None:pd.append(_d(DiscrepancyType.BROKER_ONLY_POSITION,Severity.CRITICAL,"existence",True,False,bp.broker_position_id,"broker position has no unique internal match"))
            else:
                used.add(local.internal_position_id)
                if bp.direction!=local.direction:pd.append(_d(DiscrepancyType.DIRECTION_MISMATCH,Severity.CRITICAL,"direction",bp.direction,local.direction,bp.broker_position_id,"position directions differ"))
                unit=config.quantity_units.get(bp.epic)
                if unit is None or local.quantity_unit!=unit:pd.append(_d(DiscrepancyType.SEMANTICALLY_NOT_COMPARABLE,Severity.INFO,"quantity_unit",unit,local.quantity_unit,bp.broker_position_id,"explicit aligned quantity unit required"))
                elif abs(bp.quantity-local.quantity)>config.quantity_tolerance:pd.append(_d(DiscrepancyType.QUANTITY_MISMATCH,Severity.WARNING,"quantity",bp.quantity,local.quantity,bp.broker_position_id,"position quantities differ"))
                if bp.open_level is None or local.open_level is None:pd.append(_d(DiscrepancyType.FIELD_UNAVAILABLE,Severity.INFO,"open_level",bp.open_level,local.open_level,bp.broker_position_id,"entry level unavailable"))
                elif abs(bp.open_level-local.open_level)>config.entry_level_tolerance:pd.append(_d(DiscrepancyType.ENTRY_LEVEL_MISMATCH,Severity.WARNING,"open_level",bp.open_level,local.open_level,bp.broker_position_id,"entry levels differ"))
                for field in ("stop_level","limit_level"):
                    bv,iv=getattr(bp,field),getattr(local,field)
                    if (bv is None)!=(iv is None):pd.append(_d(DiscrepancyType.FIELD_UNAVAILABLE,Severity.INFO,field,bv,iv,bp.broker_position_id,f"{field} unavailable on one source"))
                    elif bv is not None and abs(bv-iv)>config.entry_level_tolerance:pd.append(_d(DiscrepancyType.ENTRY_LEVEL_MISMATCH,Severity.WARNING,field,bv,iv,bp.broker_position_id,f"{field} differs"))
                aligned_time=abs((broker.retrieved_at-internal.as_of).total_seconds())<=config.max_snapshot_skew_seconds
                if bp.unrealized_pnl is not None and local.unrealized_pnl is not None and bp.pnl_currency==local.pnl_currency and aligned_time:
                    if abs(bp.unrealized_pnl-local.unrealized_pnl)>config.pnl_tolerance:pd.append(_d(DiscrepancyType.ACCOUNT_VALUE_MISMATCH,Severity.WARNING,"unrealized_pnl",bp.unrealized_pnl,local.unrealized_pnl,bp.broker_position_id,"aligned P&L differs"))
                elif bp.unrealized_pnl is not None or local.unrealized_pnl is not None:pd.append(_d(DiscrepancyType.SEMANTICALLY_NOT_COMPARABLE,Severity.INFO,"unrealized_pnl",bp.unrealized_pnl,local.unrealized_pnl,bp.broker_position_id,"P&L currency/value/time unavailable or unaligned"))
            all_d.extend(pd);pcs.append(PositionComparison(bp.broker_position_id,local.internal_position_id if local else None,basis,tuple(pd)))
        for local in internal.positions:
            if local.internal_position_id not in used:
                d=_d(DiscrepancyType.INTERNAL_ONLY_POSITION,Severity.WARNING,"existence",False,True,local.internal_position_id,"internal position has no broker match");all_d.append(d);pcs.append(PositionComparison(None,local.internal_position_id,None,(d,)))
    return _result(broker,internal,evaluated_at,AccountComparison(tuple(compared),tuple(account_d)),tuple(pcs),all_d,warnings)

def _result(broker,internal,at,account,positions,discrepancies,warnings):
    bref="UNAVAILABLE" if broker is None else f"{broker.broker}:{broker.environment}:{broker.retrieved_at.isoformat()}";iref="UNAVAILABLE" if internal is None else f"{internal.source}:{internal.environment}:{internal.as_of.isoformat()}"
    rid="reconciliation:"+sha256((bref+iref+at.isoformat()).encode()).hexdigest();summary={s.value:sum(d.severity is s for d in discrepancies) for s in Severity}
    return BrokerReconciliationResult(rid,VERSION,at,bref,iref,account,positions,tuple(discrepancies),summary,not discrepancies,tuple(warnings),"read-only comparison; no repair or trade authorization")

__all__=["AccountComparison","BrokerReconciliationResult","DiscrepancyType","InternalAccountSnapshot","InternalPositionSnapshot","PositionComparison","ReconciliationConfig","ReconciliationDiscrepancy","ReconciliationSnapshot","Severity","VERSION","reconcile"]
