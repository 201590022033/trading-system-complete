"""Versioned completed-bar and provenance contract for offline intraday research."""
from dataclasses import asdict,dataclass
from datetime import datetime,timezone,date
import hashlib
import json
import math
from pathlib import Path

from intraday_instruments import DataGrade

VERSION='intraday-market-data-v1'
TIMEFRAMES={'5m':300,'15m':900,'30m':1800,'60m':3600,'1d':86400}


def utc(value):
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Timezone-aware timestamp required')
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    authority_tier: int
    access_mode: str
    data_grade: DataGrade
    max_age_seconds: int
    availability_basis: str = 'observed'
    status: str = 'RESEARCH_ONLY'
    version: str = 'intraday-source-policy-v1'

    def __post_init__(self):
        if not self.source_id or not 1 <= self.authority_tier <= 4 or not math.isfinite(self.max_age_seconds) or self.max_age_seconds <= 0:
            raise ValueError('Explicit source identity, tier and freshness required')
        if self.access_mode not in {'licensed','public_delayed','manual_research'}:
            raise ValueError('Unsupported access mode')
        if self.availability_basis not in {'observed','historical_publication'}:
            raise ValueError('Unknown timestamp semantics')
        if not isinstance(self.data_grade,DataGrade): raise ValueError('Explicit source grade required')
        if self.data_grade == DataGrade.EXECUTION and self.access_mode != 'licensed':
            raise ValueError('Only verified licensed policy can declare execution grade')


@dataclass(frozen=True)
class IntradayBar:
    instrument_id: str
    interval_start: datetime
    event_time: datetime
    available_time: datetime
    decision_time: datetime
    ingestion_timestamp: datetime
    session_id: str
    session_date: str
    timeframe: str
    source: SourcePolicy
    close: float | None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    bid: float | None = None
    ask: float | None = None
    trade_count: int | None = None
    vwap: float | None = None
    source_timestamp: datetime | None = None
    currency: str | None = None
    delayed: bool = False
    stale: bool = False
    market_state: str = 'OPEN'
    input_record_ids: tuple[str,...] = ()
    version: str = VERSION

    def __post_init__(self):
        for name in ('interval_start','event_time','available_time','decision_time','ingestion_timestamp'):
            object.__setattr__(self,name,utc(getattr(self,name)))
        if self.source_timestamp is not None:
            object.__setattr__(self,'source_timestamp',utc(self.source_timestamp))
        if not self.instrument_id or not self.session_id or self.timeframe not in TIMEFRAMES:
            raise ValueError('Explicit identity/session/timeframe required')
        date.fromisoformat(self.session_date)
        if not self.interval_start < self.event_time <= self.available_time <= self.decision_time:
            raise ValueError('Bar end <= availability <= decision; interval must be positive')
        duration=(self.event_time-self.interval_start).total_seconds()
        if self.timeframe != '1d' and duration != TIMEFRAMES[self.timeframe]:
            raise ValueError('Partial bars cannot masquerade as complete timeframes')
        if self.source.availability_basis == 'observed' and self.ingestion_timestamp > self.available_time:
            raise ValueError('Observed availability cannot predate ingestion')
        if self.ingestion_timestamp < self.event_time:
            raise ValueError('Complete bars cannot be ingested before their end')
        if self.source_timestamp is not None and self.source_timestamp > self.available_time:
            raise ValueError('Source timestamp is later than availability')
        if self.delayed and self.source.data_grade == DataGrade.EXECUTION:
            raise ValueError('Delayed records cannot declare execution grade')
        for name in ('open','high','low','close','bid','ask','vwap'):
            value=getattr(self,name)
            if value is not None and (isinstance(value,bool) or not math.isfinite(value) or value <= 0):
                raise ValueError('Prices must be positive finite or unavailable')
        for name in ('volume','trade_count'):
            value=getattr(self,name)
            if value is not None and (isinstance(value,bool) or not math.isfinite(value) or value < 0):
                raise ValueError('Volume/count must be nonnegative finite or unavailable')
        if self.trade_count is not None and not isinstance(self.trade_count,int):
            raise ValueError('Trade count must be an integer')
        if self.high is not None and self.low is not None:
            if self.high < self.low or any(x is not None and not self.low <= x <= self.high for x in (self.open,self.close)):
                raise ValueError('Inconsistent OHLC range')
        if (self.bid is None) != (self.ask is None): raise ValueError('Bid/ask must be supplied together')
        if self.bid is not None and self.bid > self.ask: raise ValueError('Crossed quote')
        if self.market_state not in {'OPEN','CLOSED','HALTED','UNKNOWN'}: raise ValueError('Invalid market state')
        if not isinstance(self.input_record_ids,tuple): raise ValueError('Lineage must be immutable')

    @property
    def mid(self): return None if self.bid is None else (self.bid+self.ask)/2
    @property
    def spread(self): return None if self.bid is None else self.ask-self.bid
    @property
    def data_grade(self): return self.source.data_grade

    def to_dict(self):
        result=asdict(self)
        for key in ('interval_start','event_time','available_time','decision_time','ingestion_timestamp','source_timestamp'):
            value=getattr(self,key);result[key]=None if value is None else value.isoformat()
        return result

    @property
    def record_id(self):
        values=self.to_dict();values.pop('decision_time')
        return hashlib.sha256(json.dumps(values,sort_keys=True,allow_nan=False).encode()).hexdigest()

    @classmethod
    def from_dict(cls,value):
        value=dict(value)
        for key in ('interval_start','event_time','available_time','decision_time','ingestion_timestamp','source_timestamp'):
            if value.get(key) is not None:value[key]=datetime.fromisoformat(value[key])
        source=dict(value['source']);source['data_grade']=DataGrade(source['data_grade'])
        value['source']=SourcePolicy(**source)
        value['input_record_ids']=tuple(value.get('input_record_ids',()))
        return cls(**value)


def canonical_bars(bars):
    values=tuple(bars)
    keys=[(b.instrument_id,b.timeframe,b.event_time) for b in values]
    if len(set(keys)) != len(keys):raise ValueError('Duplicate bars/revisions need a new dataset version')
    ordered=tuple(sorted(values,key=lambda b:(b.instrument_id,b.timeframe,b.event_time)))
    previous={}
    for bar in ordered:
        key=(bar.instrument_id,bar.timeframe)
        if key in previous and bar.interval_start < previous[key]:raise ValueError('Overlapping input bars')
        previous[key]=bar.event_time
    return ordered


def as_of(bars,decision_time,instrument_id=None,timeframe=None):
    cutoff=utc(decision_time)
    return tuple(b for b in canonical_bars(bars) if b.available_time <= cutoff and b.decision_time <= cutoff
                 and (instrument_id is None or b.instrument_id==instrument_id)
                 and (timeframe is None or b.timeframe==timeframe))


def load_jsonl(path):
    with Path(path).open() as handle:
        return canonical_bars(IntradayBar.from_dict(json.loads(line)) for line in handle if line.strip())


def fetch_canonical(loader):
    """Provider-boundary adapter; no provider imports or fabricated fallback."""
    try:
        records=canonical_bars(loader())
        return {'state':'AVAILABLE' if records else 'UNAVAILABLE','records':records,'reason':None if records else 'No bars supplied'}
    except Exception as exc:
        return {'state':'UNAVAILABLE','records':(), 'reason':f'Input failed ({type(exc).__name__})'}
