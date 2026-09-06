"""HR11 adapter to authoritative signals and sample-gated, prior-only reliability."""
from dataclasses import dataclass
from datetime import timedelta
import math
import pandas as pd
from technical_signals import technical_signal_frame,SIGNAL_DEFINITION_VERSION
from indicator_effectiveness import ReliabilityAccumulator,MINIMUM_SAMPLE
from intraday_data import utc
VERSION='intraday-signals-v1'


def signal_values(snapshot,close):
    v=snapshot.values;nan=float('nan')
    rsi=v.get('rsi',nan);slow=v.get('sma_slow',nan);fast=v.get('sma_fast',nan);stoch=v.get('stochastic_k',nan)
    high=v.get('donchian_high',nan);low=v.get('donchian_low',nan)
    row=dict(rsi=rsi,rsi_signal=1 if rsi<30 else -1 if rsi>70 else 0,sma_slow=slow,
        sma_signal=1 if fast/slow>1.001 else -1 if fast/slow<.999 else 0,
        technical_warmup_complete=math.isfinite(high) and math.isfinite(low),
        breakout_signal=1 if close>high else -1 if close<low else 0,
        stochastic=stoch,stochastic_signal=1 if stoch<20 else -1 if stoch>80 else 0,
        macd=v.get('macd',nan),bollinger_zscore=v.get('close_zscore',nan),adx=v.get('adx',nan),
        dmi_direction=(1 if v['plus_di']>v['minus_di'] else -1 if v['plus_di']<v['minus_di'] else 0) if 'plus_di' in v and 'minus_di' in v else nan,
        ichimoku_direction={'above':1,'below':-1,'inside':0}.get(v.get('price_cloud_state'),nan))
    result=technical_signal_frame(pd.DataFrame([row])).iloc[0]
    return {name:float(value) if pd.notna(value) else None for name,value in result.items()}


def regimes(snapshot):
    v=snapshot.values;spread=v.get('ema_spread');change=v.get('volatility_change');volume=v.get('relative_volume')
    return ('unknown' if spread is None else 'up' if spread>.001 else 'down' if spread<-.001 else 'range',
        'unknown' if change is None else 'expanding' if change>.25 else 'contracting' if change<-.25 else 'stable',
        'unknown' if volume is None else 'thin' if volume<.2 else 'normal')


def cell_key(instrument,timeframe,horizon,regime):
    return (instrument.instrument_id,instrument.instrument_type,timeframe,horizon,instrument.profile_id,*regime)

@dataclass(frozen=True)
class EvidenceOutcome:
    cell: tuple
    indicator: str
    decision_time: object
    label_end: object
    available_time: object
    net_return: float
    gross_return: float
    def __post_init__(self):
        for name in ('decision_time','label_end','available_time'):object.__setattr__(self,name,utc(getattr(self,name)))
        if not self.decision_time<self.label_end<=self.available_time or not all(math.isfinite(x) for x in (self.net_return,self.gross_return)):raise ValueError('Invalid evidence')

@dataclass(frozen=True)
class EnsembleDecision:
    decision_time: object
    cell: tuple
    score: float | None
    signals: dict
    explanations: dict
    version: str=VERSION
    signal_definition_version: str=SIGNAL_DEFINITION_VERSION
    shadow_only: bool=True


def ensemble(snapshot,close,cell,evidence=(),purge=timedelta(minutes=60),embargo=timedelta(minutes=5)):
    if purge<timedelta(0) or embargo<timedelta(0):raise ValueError('Negative purge/embargo')
    values=signal_values(snapshot,close);explanations={};weighted=0.;denominator=0.
    for name,value in values.items():
        accumulator=ReliabilityAccumulator();end=None
        eligible=sorted((e for e in evidence if e.cell==cell and e.indicator==name and
            e.available_time+embargo<snapshot.decision_time and e.label_end+purge<snapshot.decision_time),key=lambda e:e.decision_time)
        for outcome in eligible:
            if end is not None and outcome.decision_time<end:continue
            accumulator.update(outcome.net_return,outcome.gross_return);end=outcome.label_end
        weight=accumulator.weight()
        explanations[name]=dict(available=value is not None,value=value,weight=weight if value is not None else None,
            contribution=value*weight if value is not None else None,evidence_sample_count=accumulator.count,
            reason='UNAVAILABLE' if value is None else 'DEFAULT_SMALL_SAMPLE' if accumulator.count<MINIMUM_SAMPLE else 'PRIOR_ONLY_SHRUNK_RELIABILITY')
        if value is not None:weighted+=value*weight;denominator+=weight
    return EnsembleDecision(snapshot.decision_time,cell,weighted/denominator if denominator else None,values,explanations)
