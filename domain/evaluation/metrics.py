"""Canonical, context-explicit research metrics. No strategy/runtime integration."""
from dataclasses import dataclass, field
from math import isfinite, sqrt
from statistics import mean, stdev
from types import MappingProxyType
from typing import Callable, Mapping
from domain.contracts.trade import MetricContext

VERSION="canonical-metrics-v1"; LEGACY_VERSION="legacy-tstat-like-v1"

@dataclass(frozen=True)
class MetricResult:
 metric_id:str; metric_version:str; value:float|None; context:MetricContext
 sample_count:int; effective_sample_count:float; minimum_required_sample:int
 status:str; warnings:tuple[str,...]=(); provenance:Mapping[str,object]=field(default_factory=dict)
 def __post_init__(self):
  if self.status not in {'VALID','INSUFFICIENT_EVIDENCE','INVALID_CONTEXT','UNAVAILABLE'}: raise ValueError('invalid metric status')
  if self.value is not None and (isinstance(self.value,bool) or not isfinite(self.value)): raise ValueError('metric value must be finite or unavailable')
  if self.sample_count<0 or self.effective_sample_count<0 or self.minimum_required_sample<0: raise ValueError('sample depths must be nonnegative')
  if self.status!='VALID' and self.value is not None: raise ValueError('invalid/unavailable metrics cannot carry numeric zero or value')
  object.__setattr__(self,'provenance',MappingProxyType(dict(self.provenance)))
 def to_dict(self): return {'metric_id':self.metric_id,'metric_version':self.metric_version,'value':self.value,'context':self.context.to_dict(),'sample_count':self.sample_count,'effective_sample_count':self.effective_sample_count,'minimum_required_sample':self.minimum_required_sample,'status':self.status,'warnings':list(self.warnings),'provenance':dict(self.provenance)}

@dataclass(frozen=True)
class MetricDefinition:
 metric_id:str; version:str; required_context:tuple[str,...]; required_inputs:tuple[str,...]; output_unit:str; valid_scopes:tuple[str,...]; calculator:Callable

class MetricRegistry:
 def __init__(self,definitions=()): self._items={d.metric_id:d for d in definitions}
 def register(self,d):
  if d.metric_id in self._items: raise ValueError('metric identity already registered')
  self._items[d.metric_id]=d; return d
 def get(self,metric_id): return self._items[metric_id]
 def definitions(self): return tuple(self._items[k] for k in sorted(self._items))

def _result(mid,ctx,values,status='VALID',value=None,warnings=(),minimum=1,version=VERSION,effective=None):
 n=len(values); return MetricResult(mid,version,value,ctx,n,float(n if effective is None else effective),minimum,status,tuple(warnings),{'library_version':VERSION})
def _finite(values): return tuple(float(x) for x in values if x is not None and isfinite(float(x)))
def _context(ctx,mid,*,unit=None,periodic=False):
 if not isinstance(ctx,MetricContext) or ctx.metric_id not in {None,mid} or ctx.metric_version not in {None,VERSION,LEGACY_VERSION}: return False
 if unit and ctx.return_unit!=unit:return False
 if periodic and (ctx.sampling_basis!='PERIODIC_CALENDAR' or not ctx.period_duration or not ctx.trading_calendar):return False
 return ctx.aggregation_scope in {'PER_TRADE','STRATEGY','PORTFOLIO'}

def expectancy(values,ctx,*,gross=False,minimum_sample=1,weights=None):
 mid='GROSS_EXPECTANCY' if gross else ('WEIGHTED_NET_EXPECTANCY' if weights is not None else 'NET_EXPECTANCY'); vals=_finite(values)
 expected='GROSS' if gross else 'NET'
 if not _context(ctx,mid) or ctx.return_basis!=expected:return _result(mid,ctx,vals,'INVALID_CONTEXT',minimum=minimum_sample)
 if len(vals)<minimum_sample:return _result(mid,ctx,vals,'INSUFFICIENT_EVIDENCE',minimum=minimum_sample)
 if weights is None:return _result(mid,ctx,vals,value=mean(vals),minimum=minimum_sample)
 w=tuple(float(x) for x in weights)
 if len(w)!=len(vals) or any(x<0 or not isfinite(x) for x in w) or sum(w)<=0:return _result(mid,ctx,vals,'INVALID_CONTEXT',minimum=minimum_sample,version='weighted-expectancy-v1')
 effective=sum(w)**2/sum(x*x for x in w); value=sum(x*y for x,y in zip(vals,w))/sum(w)
 return _result(mid,ctx,vals,value=value,minimum=minimum_sample,version='weighted-expectancy-v1',effective=effective)

def hit_rate(outcomes,ctx,minimum_sample=1):
 resolved=tuple(float(x) for x in outcomes if x is not None and isfinite(float(x)))
 if not _context(ctx,'HIT_RATE',unit='FRACTION'):return _result('HIT_RATE',ctx,resolved,'INVALID_CONTEXT',minimum=minimum_sample)
 if len(resolved)<minimum_sample:return _result('HIT_RATE',ctx,resolved,'INSUFFICIENT_EVIDENCE',minimum=minimum_sample)
 return _result('HIT_RATE',ctx,resolved,value=sum(x>0 for x in resolved)/len(resolved),minimum=minimum_sample,warnings=(f'NEUTRAL_OUTCOMES:{sum(x==0 for x in resolved)}',f'UNRESOLVED_EXCLUDED:{sum(x is None for x in outcomes)}'))

def payoff_metrics(outcomes,ctx):
 vals=_finite(outcomes); wins=[x for x in vals if x>0]; losses=[x for x in vals if x<0]
 aw=_result('AVERAGE_WIN',ctx,wins,value=mean(wins) if wins else None,status='VALID' if wins else 'UNAVAILABLE')
 al=_result('AVERAGE_LOSS',ctx,losses,value=mean(losses) if losses else None,status='VALID' if losses else 'UNAVAILABLE')
 ratio=_result('PAYOFF_RATIO',ctx,vals,value=mean(wins)/abs(mean(losses)) if wins and losses else None,status='VALID' if wins and losses else 'UNAVAILABLE',warnings=() if losses else ('ZERO_LOSS_DENOMINATOR',))
 return aw,al,ratio

def canonical_sharpe(values,ctx,minimum_sample=2):
 vals=_finite(values); mid='CANONICAL_ANNUALIZED_SHARPE'
 valid=_context(ctx,mid,unit='DECIMAL_RETURN',periodic=True) and ctx.return_basis in {'NET','GROSS'} and ctx.is_overlapping is False and ctx.annualization_factor and ctx.annualization_factor>0 and ctx.risk_free_rate_annualized is not None
 if not valid:return _result(mid,ctx,vals,'INVALID_CONTEXT',minimum=minimum_sample)
 if len(vals)<minimum_sample:return _result(mid,ctx,vals,'INSUFFICIENT_EVIDENCE',minimum=minimum_sample)
 excess=[x-ctx.risk_free_rate_annualized/ctx.annualization_factor for x in vals]; sd=stdev(excess)
 if sd==0:return _result(mid,ctx,vals,'UNAVAILABLE',warnings=('ZERO_VOLATILITY',),minimum=minimum_sample)
 return _result(mid,ctx,vals,value=mean(excess)/sd*sqrt(ctx.annualization_factor),minimum=minimum_sample)

def legacy_tstat_like_v1(values,ctx):
 vals=_finite(values);mid='LEGACY_TSTAT_LIKE_V1'
 if not _context(ctx,mid):return _result(mid,ctx,vals,'INVALID_CONTEXT',version=LEGACY_VERSION,minimum=2)
 if len(vals)<2 or stdev(vals)==0:return _result(mid,ctx,vals,'UNAVAILABLE',version=LEGACY_VERSION,minimum=2)
 return _result(mid,ctx,vals,value=mean(vals)/stdev(vals)*sqrt(len(vals)),version=LEGACY_VERSION,minimum=2)

def sortino(values,ctx,*,target_return=None):
 vals=_finite(values);mid='CANONICAL_ANNUALIZED_SORTINO'
 if target_return is None or not (_context(ctx,mid,unit='DECIMAL_RETURN',periodic=True) and ctx.annualization_factor and ctx.is_overlapping is False):return _result(mid,ctx,vals,'INVALID_CONTEXT',minimum=2)
 if len(vals)<2:return _result(mid,ctx,vals,'INSUFFICIENT_EVIDENCE',minimum=2)
 downside=sqrt(sum(min(0,x-target_return)**2 for x in vals)/len(vals))
 if downside==0:return _result(mid,ctx,vals,'UNAVAILABLE',warnings=('ZERO_DOWNSIDE_DEVIATION',),minimum=2)
 return _result(mid,ctx,vals,value=(mean(vals)-target_return)/downside*sqrt(ctx.annualization_factor),minimum=2)

def drawdown(equity,ctx):
 vals=_finite(equity);mid='MAX_DRAWDOWN'
 if not _context(ctx,mid) or ctx.return_unit!='FRACTION':return _result(mid,ctx,vals,'INVALID_CONTEXT')
 if not vals:return _result(mid,ctx,vals,'UNAVAILABLE')
 peak=vals[0];maxdd=0.;duration=longest=0
 for x in vals: peak=max(peak,x);dd=0 if peak==0 else (peak-x)/peak;maxdd=max(maxdd,dd);duration=duration+1 if x<peak else 0;longest=max(longest,duration)
 return _result(mid,ctx,vals,value=maxdd,warnings=(f'MAX_DRAWDOWN_DURATION_PERIODS:{longest}',))

def volatility(values,ctx,annualized=False):
 vals=_finite(values);mid='ANNUALIZED_VOLATILITY' if annualized else 'PERIODIC_VOLATILITY'
 if not _context(ctx,mid,unit='DECIMAL_RETURN',periodic=True) or (annualized and not ctx.annualization_factor):return _result(mid,ctx,vals,'INVALID_CONTEXT',minimum=2)
 if len(vals)<2:return _result(mid,ctx,vals,'INSUFFICIENT_EVIDENCE',minimum=2)
 sd=stdev(vals)
 return _result(mid,ctx,vals,value=sd*(sqrt(ctx.annualization_factor) if annualized else 1),minimum=2)

def turnover(positions,ctx):
 vals=tuple(float(x) for x in positions); sides=sum(abs(b-a) for a,b in zip((0.,)+vals,vals))
 return _result('POSITION_STATE_TURNOVER',ctx,vals,value=sides)

def cost_decomposition(gross,transaction_costs,slippage,ctx):
 if any(not isfinite(float(x)) for x in (gross,transaction_costs,slippage)) or transaction_costs<0 or slippage<0:return _result('NET_RETURN',ctx,(),'INVALID_CONTEXT')
 return {'gross_return':float(gross),'transaction_costs':float(transaction_costs),'slippage':float(slippage),'net_return':float(gross-transaction_costs-slippage)}

def profit_factor(values,ctx):
 vals=_finite(values);profit=sum(x for x in vals if x>0);loss=-sum(x for x in vals if x<0)
 if loss==0:return _result('PROFIT_FACTOR',ctx,vals,'UNAVAILABLE',warnings=('ZERO_GROSS_LOSS_DENOMINATOR',))
 return _result('PROFIT_FACTOR',ctx,vals,value=profit/loss)

def calmar(annualized_return,max_drawdown,ctx):
 if not _context(ctx,'CALMAR') or not ctx.annualization_factor:return _result('CALMAR',ctx,(),'INVALID_CONTEXT')
 if max_drawdown<=0:return _result('CALMAR',ctx,(),'UNAVAILABLE',warnings=('ZERO_DRAWDOWN_DENOMINATOR',))
 return _result('CALMAR',ctx,(annualized_return,),value=annualized_return/max_drawdown)

def exposure(positions,ctx):
 vals=tuple(float(x) for x in positions)
 if not vals:return _result('TIME_IN_MARKET',ctx,(),'UNAVAILABLE')
 return {'time_in_market':sum(x!=0 for x in vals)/len(vals),'gross_exposure':mean(abs(x) for x in vals),'net_exposure':mean(vals),'unit':ctx.return_unit}

METRIC_REGISTRY=MetricRegistry()
for _id,_unit,_calc in [('NET_EXPECTANCY','context-defined',expectancy),('GROSS_EXPECTANCY','context-defined',expectancy),('HIT_RATE','FRACTION',hit_rate),('CANONICAL_ANNUALIZED_SHARPE','RATIO',canonical_sharpe),('LEGACY_TSTAT_LIKE_V1','LEGACY_RATIO',legacy_tstat_like_v1),('MAX_DRAWDOWN','FRACTION',drawdown),('POSITION_STATE_TURNOVER','SIDES',turnover),('PROFIT_FACTOR','RATIO',profit_factor)]: METRIC_REGISTRY.register(MetricDefinition(_id,LEGACY_VERSION if _id.startswith('LEGACY') else VERSION,('MetricContext',),('observations',),_unit,('PER_TRADE','STRATEGY','PORTFOLIO'),_calc))
