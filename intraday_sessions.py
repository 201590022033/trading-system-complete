"""Deterministic aggregation using supplied, versioned exchange session intervals."""
from dataclasses import dataclass,replace
from datetime import datetime,timedelta,date
from intraday_data import utc,TIMEFRAMES,IntradayBar,as_of

VERSION='intraday-sessions-v1'

@dataclass(frozen=True)
class SessionWindow:
    session_id: str
    session_date: str
    open_time: datetime
    close_time: datetime
    calendar_version: str
    breaks: tuple = ()

    def __post_init__(self):
        object.__setattr__(self,'open_time',utc(self.open_time))
        object.__setattr__(self,'close_time',utc(self.close_time))
        if not self.session_id or not self.calendar_version or self.close_time<=self.open_time:
            raise ValueError('Explicit valid session interval/version required')
        date.fromisoformat(self.session_date)
        object.__setattr__(self,'breaks',tuple((utc(a),utc(b)) for a,b in self.breaks))
        previous=self.open_time
        for start,end in self.breaks:
            start,end=utc(start),utc(end)
            if not previous <= start < end <= self.close_time:raise ValueError('Invalid session break')
            previous=end

    def contains(self,start,end):
        start,end=utc(start),utc(end)
        return (self.open_time<=start<end<=self.close_time and
                not any(start<b and end>a for a,b in self.breaks))

    def trading_seconds(self):
        return (self.close_time-self.open_time).total_seconds()-sum((b-a).total_seconds() for a,b in self.breaks)


def validate_sessions(sessions):
    sessions=tuple(sorted(sessions,key=lambda s:s.open_time))
    if len({s.session_id for s in sessions})!=len(sessions):raise ValueError('Duplicate session identity')
    if any(a.close_time>b.open_time for a,b in zip(sessions,sessions[1:])):raise ValueError('Overlapping sessions')
    return sessions


def validate_bar_session(bar,session):
    if bar.session_id!=session.session_id or bar.session_date!=session.session_date:
        raise ValueError('Bar session identity mismatch')
    full_day=bar.timeframe=='1d' and bar.interval_start==session.open_time and bar.event_time==session.close_time
    if not full_day and not session.contains(bar.interval_start,bar.event_time):raise ValueError('Bar outside session or inside break')


@dataclass(frozen=True)
class AggregationResult:
    bars: tuple
    warnings: tuple
    version: str=VERSION


def aggregate(bars,sessions,timeframe,decision_time):
    if timeframe not in TIMEFRAMES:raise ValueError('Unsupported timeframe')
    sessions=validate_sessions(sessions)
    known=as_of(bars,decision_time)
    if not known:return AggregationResult((),('NO_AVAILABLE_BARS',))
    if len({(b.instrument_id,b.timeframe) for b in known})!=1:raise ValueError('Aggregate one instrument/source timeframe at a time')
    source_frame=known[0].timeframe
    if source_frame=='1d' and timeframe!='1d':raise ValueError('Cannot invent intraday data from daily bars')
    step=TIMEFRAMES[source_frame]
    if timeframe!='1d' and TIMEFRAMES[timeframe]%step:raise ValueError('Target must be a multiple of source timeframe')
    window_by_id={s.session_id:s for s in sessions}
    for bar in known:
        if bar.session_id not in window_by_id:raise ValueError('Missing session metadata')
        validate_bar_session(bar,window_by_id[bar.session_id])
    result,warnings=[],[]
    for session in sessions:
        selected=[b for b in known if b.session_id==session.session_id]
        if not selected:
            if session.close_time<=utc(decision_time):warnings.append(session.session_id+':MISSING_SESSION')
            continue
        if source_frame==timeframe:
            result.extend(selected);continue
        start=session.open_time
        while start<session.close_time:
            end=session.close_time if timeframe=='1d' else start+timedelta(seconds=TIMEFRAMES[timeframe])
            if end>session.close_time:
                warnings.append(session.session_id+':PARTIAL_FINAL_INTERVAL');break
            if end>utc(decision_time):break
            expected=[];point=start
            while point<end:
                next_point=point+timedelta(seconds=step)
                if next_point<=end and session.contains(point,next_point):expected.append(point)
                point=next_point
            chunk=[b for b in selected if start<=b.interval_start and b.event_time<=end]
            # Incomplete bars or unexplained gaps never become complete research bars.
            if not expected or len(chunk)!=len(expected) or [b.interval_start for b in chunk]!=expected:
                warnings.append(session.session_id+':INCOMPLETE:'+end.isoformat())
            elif timeframe!='1d' and not session.contains(start,end):
                warnings.append(session.session_id+':SESSION_BREAK')
            else:
                if len({b.source for b in chunk})!=1 or len({b.currency for b in chunk})!=1:
                    raise ValueError('Cannot mix providers, policies or currencies in an aggregate')
                def complete(name,fn):
                    values=[getattr(b,name) for b in chunk]
                    return fn(values) if all(v is not None for v in values) else None
                open_values=[b.open for b in chunk if b.open is not None]
                close_values=[b.close for b in chunk if b.close is not None]
                missing_prices=any(any(getattr(b,n) is None for n in ('open','high','low','close')) for b in chunk)
                if missing_prices:warnings.append(session.session_id+':MISSING_OHLC')
                result.append(replace(chunk[-1],interval_start=start,event_time=end,
                    available_time=max(b.available_time for b in chunk),decision_time=max(b.decision_time for b in chunk),
                    ingestion_timestamp=max(b.ingestion_timestamp for b in chunk),timeframe=timeframe,
                    open=open_values[0] if open_values else None,close=close_values[-1] if close_values else None,
                    high=complete('high',max),low=complete('low',min),volume=complete('volume',sum),
                    bid=None,ask=None,vwap=None,trade_count=complete('trade_count',sum),
                    delayed=any(b.delayed for b in chunk),stale=any(b.stale for b in chunk) or missing_prices,
                    source_timestamp=None,input_record_ids=tuple(b.record_id for b in chunk)))
            start=end
    return AggregationResult(tuple(result),tuple(warnings))
