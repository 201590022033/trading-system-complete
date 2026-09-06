"""Causal timestamp walk-forward evaluation with one open position per research cell."""
from dataclasses import dataclass,asdict
from datetime import datetime,timedelta,timezone
import math
import statistics
from intraday_data import canonical_bars,as_of,utc
from intraday_costs import transition_cost
from intraday_sessions import validate_bar_session,validate_sessions
from intraday_signals import EvidenceOutcome
VERSION='intraday-evaluation-v1'

@dataclass(frozen=True)
class EvaluationPolicy:
    purge_seconds: int=3600
    embargo_seconds: int=300
    fold_seconds: int=7*86400
    score_threshold: float=.2
    units: float=1
    version: str='intraday-evaluation-policy-v1'
    def __post_init__(self):
        if self.purge_seconds<0 or self.embargo_seconds<0 or self.fold_seconds<=0 or not 0<self.score_threshold<=1 or not math.isfinite(self.units) or self.units<=0:raise ValueError('Invalid evaluation policy')
    def fold(self,decision_time):
        epoch=datetime(1970,1,5,tzinfo=timezone.utc)
        start=epoch+timedelta(seconds=((utc(decision_time)-epoch).total_seconds()//self.fold_seconds)*self.fold_seconds)
        return start,start+timedelta(seconds=self.fold_seconds)


def training_evidence(outcomes,test_start,policy):
    cutoff=utc(test_start)
    return tuple(e for e in outcomes if e.label_end+timedelta(seconds=policy.purge_seconds)<cutoff and
        e.available_time+timedelta(seconds=policy.embargo_seconds)<cutoff)

@dataclass(frozen=True)
class ResearchTrade:
    cell: tuple
    fold_id: str
    decision_time: object
    entry_time: object
    exit_time: object
    outcome_available_time: object
    side: int
    units: float
    entry_price: float
    exit_price: float
    gross_return: float
    net_return: float
    costs: float
    cost_fraction: float
    turnover_units: float
    mfe: float | None
    mae: float | None
    holding_seconds: float
    currency: str
    decision_explanations: dict
    record_ids: tuple
    version: str=VERSION
    def to_dict(self):
        result=asdict(self)
        for name in ('decision_time','entry_time','exit_time','outcome_available_time'):result[name]=getattr(self,name).isoformat()
        return result

@dataclass(frozen=True)
class EvaluationResult:
    instrument_id: str
    timeframe: str
    horizon_id: str
    trades: tuple
    decisions: tuple
    warnings: tuple
    metrics: dict
    policy: EvaluationPolicy
    version: str=VERSION


def metrics(trades,sample_count=0,span_seconds=None):
    trades=tuple(trades);net=[t.net_return for t in trades];gross=[t.gross_return for t in trades]
    equity=peak=1.;drawdown=0.
    for value in net:
        equity*=1+value;peak=max(peak,equity);drawdown=max(drawdown,1-equity/peak)
    positive=sum(x for x in net if x>0);negative=-sum(x for x in net if x<0)
    def avg(values):return statistics.mean(values) if values else None
    return dict(sample_count=sample_count,trade_count=len(trades),win_rate=avg([x>0 for x in net]),
        mean_aligned_return=avg(gross),median_aligned_return=statistics.median(gross) if gross else None,
        mean_net_return=avg(net),median_net_return=statistics.median(net) if net else None,
        cumulative_net_return=equity-1 if net else None,max_drawdown=drawdown if net else None,
        costs=sum(t.costs for t in trades) if trades else None,cost_currency=trades[0].currency if trades else None,
        turnover_units=sum(t.turnover_units for t in trades),mfe=avg([t.mfe for t in trades if t.mfe is not None]),
        mae=avg([t.mae for t in trades if t.mae is not None]),average_holding_seconds=avg([t.holding_seconds for t in trades]),
        exposure=sum(t.holding_seconds for t in trades)/span_seconds if span_seconds else None,
        profit_factor=positive/negative if negative else None,long_count=sum(t.side==1 for t in trades),short_count=sum(t.side==-1 for t in trades))


def evaluate(instrument,decision_bars,execution_bars,sessions,horizon,schedule,decision_builder,cutoff,policy=EvaluationPolicy()):
    cutoff=utc(cutoff);decisions_bars=as_of(decision_bars,cutoff);raw=as_of(execution_bars,cutoff)
    if any(b.instrument_id!=instrument.instrument_id for b in (*decisions_bars,*raw)):raise ValueError('Instrument mismatch')
    if len({b.timeframe for b in decisions_bars})>1 or len({b.timeframe for b in raw})>1:raise ValueError('Mixed timeframes')
    windows={s.session_id:s for s in validate_sessions(sessions)}
    for b in (*decisions_bars,*raw):
        if b.session_id not in windows:raise ValueError('Missing session')
        validate_bar_session(b,windows[b.session_id])
    trades=[];records=[];warnings=[];evidence=[];busy_until=None
    for current in sorted(decisions_bars,key=lambda b:(b.decision_time,b.event_time)):
        now=current.decision_time
        if busy_until is not None and now<busy_until:continue
        session=windows[current.session_id];fold_start,fold_end=policy.fold(now)
        prior=training_evidence(evidence,fold_start,policy)
        decision,gates=decision_builder(current,as_of(decisions_bars,now),prior)
        if decision.decision_time!=now:raise ValueError('Builder returned noncausal decision clock')
        record=dict(decision_time=now.isoformat(),cell=decision.cell,score=decision.score,gates=gates.checks,
            reasons=gates.reasons,signals=decision.explanations,fold_id=fold_start.isoformat(),training_outcomes=len(prior))
        records.append(record)
        if not gates.research_pass or decision.score is None or abs(decision.score)<policy.score_threshold:continue
        side=1 if decision.score>0 else -1
        if side<0 and not instrument.supports_short:warnings.append('SHORT_UNSUPPORTED');continue
        target=horizon.target(now,session)
        if target is None:warnings.append('HORIZON_OUTSIDE_SESSION');continue
        path=[b for b in raw if b.session_id==session.session_id and b.interval_start>=now and b.event_time<=target]
        if not path or path[0].interval_start!=now or path[-1].event_time!=target or any(a.event_time!=b.interval_start for a,b in zip(path,path[1:])):
            warnings.append('INCOMPLETE_OR_UNALIGNED_EXECUTION_WINDOW');continue
        if any(b.stale or b.market_state!='OPEN' or b.open is None or b.close is None for b in path):warnings.append('UNAVAILABLE_EXECUTION_PRICES');continue
        # These are realized research bars, never observations furnished to the decision builder.
        entry,exit_=path[0].open,path[-1].close;holding=(target-now).total_seconds();units=side*policy.units
        entry_cost=transition_cost(instrument,schedule,0,units,entry)
        exit_cost=transition_cost(instrument,schedule,units,0,exit_,holding)
        if not entry_cost.available or not exit_cost.available:warnings.append('UNAVAILABLE_COSTS');continue
        notional=abs(units)*entry*instrument.contract_multiplier
        cost=entry_cost.total+exit_cost.total;fraction=cost/notional;gross=side*(exit_/entry-1)
        extrema=all(b.high is not None and b.low is not None for b in path)
        favourable=[side*((b.high if side>0 else b.low)/entry-1) for b in path] if extrema else []
        adverse=[side*((b.low if side>0 else b.high)/entry-1) for b in path] if extrema else []
        maturity=max(b.available_time for b in path)
        trade=ResearchTrade(decision.cell,fold_start.isoformat(),now,path[0].interval_start,target,maturity,side,policy.units,entry,exit_,gross,gross-fraction,cost,fraction,
            entry_cost.turnover_units+exit_cost.turnover_units,max([0]+favourable) if extrema else None,min([0]+adverse) if extrema else None,
            holding,instrument.currency,decision.explanations,tuple(b.record_id for b in path))
        trades.append(trade);busy_until=target
        # Learning is conditioned on independently entered research trades. Neutral signals have no directional outcome.
        for indicator,value in decision.signals.items():
            if value in (-1,1) and (value>0 or instrument.supports_short):
                directional=value*(exit_/entry-1)
                signal_entry=transition_cost(instrument,schedule,0,value*policy.units,entry)
                signal_exit=transition_cost(instrument,schedule,value*policy.units,0,exit_,holding)
                if signal_entry.available and signal_exit.available:
                    signal_fraction=(signal_entry.total+signal_exit.total)/notional
                    evidence.append(EvidenceOutcome(decision.cell,indicator,now,target,maturity,directional-signal_fraction,directional))
    timeframe=decisions_bars[0].timeframe if decisions_bars else 'unknown'
    span=sum(s.trading_seconds() for s in windows.values() if s.open_time<cutoff)
    return EvaluationResult(instrument.instrument_id,timeframe,horizon.horizon_id,tuple(trades),tuple(records),tuple(sorted(set(warnings))),metrics(trades,len(records),span),policy)
