"""Availability-time joins with event-age limits and traceable source observations."""
from dataclasses import dataclass
import math
from intraday_data import utc,as_of
VERSION='intraday-cross-asset-v1'

@dataclass(frozen=True)
class FactorObservation:
    factor: str
    value: float
    event_time: object
    available_time: object
    source_id: str
    record_ids: tuple
    max_age_seconds: float
    version: str=VERSION
    def __post_init__(self):
        for field in ('event_time','available_time'):object.__setattr__(self,field,utc(getattr(self,field)))
        if not self.factor or not self.source_id or not self.record_ids or not isinstance(self.record_ids,tuple):raise ValueError('Factor provenance required')
        if self.event_time>self.available_time or not math.isfinite(self.value) or not math.isfinite(self.max_age_seconds) or self.max_age_seconds<=0:raise ValueError('Invalid factor clocks/value/age')

@dataclass(frozen=True)
class CrossAssetSnapshot:
    decision_time: object
    values: dict
    unavailable: dict
    lineage: dict
    version: str=VERSION


def join_factors(observations,decision_time,required_factors):
    cutoff=utc(decision_time);values={};missing={};lineage={}
    for factor in required_factors:
        eligible=[o for o in observations if o.factor==factor and o.available_time<=cutoff and o.event_time<=cutoff]
        if not eligible:missing[factor]='MISSING_ASOF';continue
        observation=max(eligible,key=lambda o:(o.event_time,o.available_time,o.source_id,o.record_ids))
        age=(cutoff-observation.event_time).total_seconds()
        if age>observation.max_age_seconds:missing[factor]='STALE';continue
        values[factor]=observation.value
        lineage[factor]=dict(source_id=observation.source_id,record_ids=observation.record_ids,event_time=observation.event_time.isoformat(),
            available_time=observation.available_time.isoformat(),age_seconds=age,max_age_seconds=observation.max_age_seconds)
    return CrossAssetSnapshot(cutoff,values,missing,lineage)


def factor_return(bars,factor,decision_time):
    known=as_of(bars,decision_time)
    if len(known)<2:return None
    a,b=known[-2:]
    if (a.instrument_id,a.timeframe,a.source)!=(b.instrument_id,b.timeframe,b.source):raise ValueError('One factor instrument/timeframe/source required')
    if a.close is None or b.close is None or a.stale or b.stale or a.session_id!=b.session_id or a.event_time!=b.interval_start:return None
    return FactorObservation(factor,b.close/a.close-1,b.event_time,max(a.available_time,b.available_time),b.source.source_id,
        (a.record_id,b.record_id),b.source.max_age_seconds)
