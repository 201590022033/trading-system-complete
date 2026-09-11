"""Deterministic, in-memory PAPER-only execution simulator."""
from dataclasses import dataclass,replace
from datetime import datetime,timezone
from enum import Enum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Mapping
from domain.risk import RiskEvaluation,RiskStatus
from .adapter import UnsupportedBrokerCapability

VERSION='paper-broker-v1';FILL_VERSION='paper-supplied-observation-v1'
class PaperBrokerError(RuntimeError):pass
class OrderState(str,Enum):CREATED='CREATED';VALIDATED='VALIDATED';PENDING='PENDING';FILLED='FILLED';CANCELLED='CANCELLED';REJECTED='REJECTED';EXPIRED='EXPIRED'
class PositionState(str,Enum):FLAT='FLAT';LONG='LONG';SHORT='SHORT'
def utc(x,n):
 if x.tzinfo is None or x.utcoffset() is None:raise ValueError(f'{n} must be timezone-aware')
 return x.astimezone(timezone.utc)

@dataclass(frozen=True)
class PaperExecutionConfig:
 config_id:str;slippage_per_unit:float|None;commission_per_fill:float|None;currency:str;zero_cost_test_fixture:bool=False;fill_model_version:str=FILL_VERSION
 def __post_init__(self):
  if not self.config_id or len(self.currency)!=3:raise ValueError('explicit paper config identity/currency required')
  for x in (self.slippage_per_unit,self.commission_per_fill):
   if x is not None and (not isfinite(x) or x<0):raise ValueError('cost/slippage must be nonnegative')
  if (self.slippage_per_unit==0 or self.commission_per_fill==0) and not self.zero_cost_test_fixture:raise ValueError('zero costs allowed only for explicit test fixture')

@dataclass(frozen=True)
class CanonicalOrderIntent:
 order_intent_id:str;created_at:datetime;broker:str;instrument_id:str;execution_symbol:str;direction:str;quantity:float;order_type:str;requested_entry:float|None;stop_price:float|None;target_price:float|None;time_in_force:str;risk_evaluation_id:str;allow_reversal:bool;provenance:Mapping[str,object]
 def __post_init__(self):
  object.__setattr__(self,'created_at',utc(self.created_at,'created_at'))
  if not all((self.order_intent_id,self.instrument_id,self.execution_symbol,self.risk_evaluation_id)) or self.broker!='PAPER':raise ValueError('complete PAPER intent identity required')
  if self.direction not in {'LONG','SHORT'} or self.order_type!='MARKET' or self.time_in_force not in {'DAY','IOC'}:raise ValueError('only broker-neutral PAPER market intents are supported')
  if not isfinite(self.quantity) or self.quantity<=0:raise ValueError('positive finite quantity required')
  object.__setattr__(self,'provenance',MappingProxyType(dict(self.provenance)))

@dataclass(frozen=True)
class MarketObservation:
 instrument_id:str;price:float;observed_at:datetime;source:str
 def __post_init__(self):
  object.__setattr__(self,'observed_at',utc(self.observed_at,'observed_at'))
  if not self.instrument_id or not self.source or not isfinite(self.price) or self.price<=0:raise ValueError('causal positive market observation required')

@dataclass(frozen=True)
class PaperOrder:
 order_id:str;intent_id:str;instrument_id:str;direction:str;quantity:float;state:OrderState;created_at:datetime;updated_at:datetime;rejection_reason:str|None=None
@dataclass(frozen=True)
class PaperFill:
 fill_id:str;order_id:str;intent_id:str;instrument_id:str;direction:str;quantity:float;observed_price:float;fill_price:float;slippage:float;transaction_cost:float;net_cash_effect:float;filled_at:datetime;fill_model_version:str;observation_source:str
@dataclass(frozen=True)
class PaperPosition:
 position_id:str;instrument_id:str;execution_symbol:str;state:PositionState;quantity:float;average_entry_price:float;opened_at:datetime;last_mark:float|None;unrealized_pnl:float;realized_pnl:float;originating_order_ids:tuple[str,...];fill_ids:tuple[str,...]
@dataclass(frozen=True)
class PaperAccount:
 broker:str;mode:str;currency:str;starting_cash:float;available_cash:float;equity:float;realized_pnl:float;unrealized_pnl:float;margin_used:float|None;position_count:int;open_order_count:int
@dataclass(frozen=True)
class AuditEvent:
 sequence:int;event_type:str;recorded_at:datetime;reference_id:str;detail:str
@dataclass(frozen=True)
class ReconciliationResult:
 reconciled_at:datetime;clean:bool;discrepancies:tuple[str,...];orders:int;fills:int;positions:int

class PaperBroker:
 broker='PAPER';mode='PAPER'
 def __init__(self,starting_cash,config:PaperExecutionConfig):
  if not isfinite(starting_cash) or starting_cash<0:raise ValueError('starting cash must be nonnegative')
  self.config=config;self.starting_cash=float(starting_cash);self.cash=float(starting_cash);self.realized=0.;self._orders={};self._fills=[];self._positions={};self._audit=[];self._marks={}
 @property
 def capabilities(self):return {'historical_data':False,'streaming':False,'account_state':True,'positions':True,'order_preview':True,'order_submission':True,'amend':False,'cancel':True,'close':True,'reconcile':True}
 def _unsupported(self,*a,**k):raise UnsupportedBrokerCapability('capability unsupported by PaperBroker')
 authenticate=_unsupported;search_markets=_unsupported;get_instrument=_unsupported;get_historical_prices=_unsupported;subscribe_prices=_unsupported;amend_order=_unsupported
 def _event(self,t,ref,detail,at):self._audit.append(AuditEvent(len(self._audit)+1,t,utc(at,'audit time'),ref,detail))
 def preview_order(self,intent):return {'broker':'PAPER','mode':'PAPER','intent_id':intent.order_intent_id,'quantity':intent.quantity,'fill_model':self.config.fill_model_version,'executable':False}
 def place_order(self,intent:CanonicalOrderIntent,*,risk:RiskEvaluation,observation:MarketObservation|None=None):
  if intent.order_intent_id in {x.intent_id for x in self._orders.values()}:raise PaperBrokerError('duplicate active or historical order intent')
  now=intent.created_at;oid='paper-order:'+sha256(intent.order_intent_id.encode()).hexdigest();reason=None
  if risk.evaluation_id!=intent.risk_evaluation_id or risk.status not in {RiskStatus.APPROVED,RiskStatus.REDUCED}:reason='VALID_RISK_APPROVAL_REQUIRED'
  elif risk.approved_position_size is None or risk.approved_loss_budget is None:reason='APPROVED_SIZE_AND_LOSS_BUDGET_REQUIRED'
  elif intent.quantity>risk.approved_position_size:reason='QUANTITY_EXCEEDS_RISK_APPROVAL'
  elif risk.instrument_id!=intent.instrument_id:reason='RISK_INSTRUMENT_MISMATCH'
  existing=self._positions.get(intent.instrument_id)
  if not reason and existing and existing.state.value!=intent.direction and intent.quantity>existing.quantity:reason='REVERSAL_REQUIRES_CLOSE_THEN_SEPARATE_ORDER'
  if reason:
   order=PaperOrder(oid,intent.order_intent_id,intent.instrument_id,intent.direction,intent.quantity,OrderState.REJECTED,now,now,reason);self._orders[oid]=order;self._event('REJECTED',oid,reason,now);return order
  order=PaperOrder(oid,intent.order_intent_id,intent.instrument_id,intent.direction,intent.quantity,OrderState.PENDING,now,now);self._orders[oid]=order;self._event('VALIDATED',oid,'risk-approved PAPER intent',now)
  if observation is None:return order
  return self._fill(order,intent,observation)
 def _fill(self,order,intent,obs):
  if self.config.slippage_per_unit is None or self.config.commission_per_fill is None:raise PaperBrokerError('paper slippage and transaction costs are unconfigured')
  if obs.instrument_id!=intent.instrument_id or obs.observed_at<intent.created_at:raise PaperBrokerError('causal matching market observation required')
  sign=1 if intent.direction=='LONG' else -1;fp=obs.price+sign*self.config.slippage_per_unit;slip=intent.quantity*self.config.slippage_per_unit;cost=self.config.commission_per_fill;cash_effect=-sign*intent.quantity*fp-cost
  fill=PaperFill('paper-fill:'+sha256((order.order_id+obs.observed_at.isoformat()).encode()).hexdigest(),order.order_id,intent.order_intent_id,intent.instrument_id,intent.direction,intent.quantity,obs.price,fp,slip,cost,cash_effect,obs.observed_at,self.config.fill_model_version,obs.source)
  self.cash+=cash_effect;self._fills.append(fill);self._orders[order.order_id]=replace(order,state=OrderState.FILLED,updated_at=obs.observed_at);self._apply(fill,intent.execution_symbol);self._marks[intent.instrument_id]=obs.price;self._event('FILL',fill.fill_id,self.config.fill_model_version,obs.observed_at);return self._orders[order.order_id]
 def _apply(self,f,symbol):
  p=self._positions.get(f.instrument_id);sign=1 if f.direction=='LONG' else -1
  if not p:
   self._positions[f.instrument_id]=PaperPosition('paper-position:'+f.instrument_id,f.instrument_id,symbol,PositionState.LONG if sign>0 else PositionState.SHORT,f.quantity,f.fill_price,f.filled_at,f.observed_price,0.,0.,(f.order_id,),(f.fill_id,));return
  psign=1 if p.state is PositionState.LONG else -1
  if psign==sign:
   q=p.quantity+f.quantity;avg=(p.average_entry_price*p.quantity+f.fill_price*f.quantity)/q;self._positions[f.instrument_id]=replace(p,quantity=q,average_entry_price=avg,last_mark=f.observed_price,originating_order_ids=p.originating_order_ids+(f.order_id,),fill_ids=p.fill_ids+(f.fill_id,));return
  q=p.quantity-f.quantity;profit=f.quantity*(f.fill_price-p.average_entry_price)*psign;self.realized+=profit
  if q==0:del self._positions[f.instrument_id]
  else:self._positions[f.instrument_id]=replace(p,quantity=q,last_mark=f.observed_price,realized_pnl=p.realized_pnl+profit,originating_order_ids=p.originating_order_ids+(f.order_id,),fill_ids=p.fill_ids+(f.fill_id,))
 def mark(self,observation):
  p=self._positions.get(observation.instrument_id)
  if p:
   sign=1 if p.state is PositionState.LONG else -1;u=(observation.price-p.average_entry_price)*p.quantity*sign;self._positions[p.instrument_id]=replace(p,last_mark=observation.price,unrealized_pnl=u);self._marks[p.instrument_id]=observation.price
 def close_position(self,position_id,*,observation,risk):
  p=next((x for x in self._positions.values() if x.position_id==position_id),None)
  if not p:raise KeyError('position not found')
  intent=CanonicalOrderIntent('close:'+position_id+':'+observation.observed_at.isoformat(),observation.observed_at,'PAPER',p.instrument_id,p.execution_symbol,'SHORT' if p.state is PositionState.LONG else 'LONG',p.quantity,'MARKET',None,None,None,'IOC',risk.evaluation_id,False,{'close_position_id':position_id})
  return self.place_order(intent,risk=risk,observation=observation)
 def cancel_order(self,order_id,at=None):
  o=self._orders[order_id]
  if o.state is not OrderState.PENDING:raise PaperBrokerError('only pending orders may be cancelled')
  at=utc(at or datetime.now(timezone.utc),'cancel time');o=replace(o,state=OrderState.CANCELLED,updated_at=at);self._orders[order_id]=o;self._event('CANCELLED',order_id,'operator cancellation',at);return o
 def get_order_status(self,order_id):return self._orders[order_id]
 def get_positions(self):return tuple(self._positions.values())
 def get_account(self):
  unreal=sum(p.unrealized_pnl for p in self._positions.values());equity=self.cash+sum((1 if p.state is PositionState.LONG else -1)*p.quantity*(p.last_mark or p.average_entry_price) for p in self._positions.values());return PaperAccount('PAPER','PAPER',self.config.currency,self.starting_cash,self.cash,equity,self.realized,unreal,None,len(self._positions),sum(o.state is OrderState.PENDING for o in self._orders.values()))
 def audit_trail(self):return tuple(self._audit)
 def fills(self):return tuple(self._fills)
 def reconcile(self,at=None):
  d=[]
  if any(f.order_id not in self._orders or self._orders[f.order_id].state is not OrderState.FILLED for f in self._fills):d.append('FILL_WITHOUT_FILLED_ORDER')
  known={f.fill_id for f in self._fills}
  if any(fid not in known for p in self._positions.values() for fid in p.fill_ids):d.append('POSITION_REFERENCES_UNKNOWN_FILL')
  expected=self.starting_cash+sum(f.net_cash_effect for f in self._fills)
  if abs(expected-self.cash)>1e-9:d.append('CASH_LEDGER_MISMATCH')
  r=ReconciliationResult(utc(at or datetime.now(timezone.utc),'reconcile time'),not d,tuple(d),len(self._orders),len(self._fills),len(self._positions));self._event('RECONCILIATION','PAPER',','.join(d) if d else 'CLEAN',r.reconciled_at);return r

__all__=['AuditEvent','CanonicalOrderIntent','MarketObservation','OrderState','PaperAccount','PaperBroker','PaperBrokerError','PaperExecutionConfig','PaperFill','PaperOrder','PaperPosition','PositionState','ReconciliationResult','VERSION']
