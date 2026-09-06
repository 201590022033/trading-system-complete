"""Point-in-time adapters extending the existing technical feature registry."""
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd
from intraday_data import as_of,TIMEFRAMES,utc
from research_indicators import MarketBar,DataCapabilities,_ema
from asset_specific_technicals import build_asset_features
from technical_feature_registry import RegistryComputation,TechnicalFeatureDefinition,build_default_registry

VERSION='intraday-features-v1'
FRAMES=('5m','15m','30m','60m','1d')


def _result(name,values,reason=''):
    clean={k:v for k,v in values.items() if v is not None and (not isinstance(v,(float,np.floating)) or math.isfinite(v))}
    return RegistryComputation(name,bool(clean),clean,reason if not clean else '',VERSION)


def _continuous(bars,caps,index,benchmark):
    bars=bars[:index+1];n=len(bars);closes=np.array([b.close for b in bars]);values={}
    # Reuse HR7's established causal RSI and SMA math; no daily regimes or thresholds imported.
    frame=pd.DataFrame([dict(event_time=pd.Timestamp('2000-01-01',tz='UTC')+pd.Timedelta(minutes=5*i),
        available_time=pd.Timestamp('2000-01-01',tz='UTC')+pd.Timedelta(minutes=5*i),
        close=b.close,open=b.open,high=b.high,low=b.low,volume=b.volume) for i,b in enumerate(bars)])
    old=build_asset_features(frame,'adapter','research','explicit').iloc[-1]
    for key in ('rsi','sma_fast','sma_slow'):values[key]=old[key]
    if n>=26:values.update(ema_fast=_ema(closes,12),ema_slow=_ema(closes,26),ema_spread=_ema(closes,12)/_ema(closes,26)-1)
    if n>=21:
        returns=closes[1:]/closes[:-1]-1
        values['realized_volatility_20']=float(np.std(returns[-20:]))
        if n>=41:
            previous=float(np.std(returns[-40:-20]))
            if previous>0:values['volatility_change']=float(np.std(returns[-20:]))/previous-1
    if caps.has_ohlc:
        if n>=14:
            def stochastic(part):
                high=max(b.high for b in part);low=min(b.low for b in part)
                return 100*(part[-1].close-low)/(high-low) if high>low else None
            values['stochastic_k']=stochastic(bars[-14:])
            if n>=16:
                ks=[stochastic(bars[n-16+i:n-2+i]) for i in range(3)]
                if all(k is not None for k in ks):values['stochastic_d']=sum(ks)/3
        if n>=21:
            prior=bars[-21:-1];high=max(b.high for b in prior);low=min(b.low for b in prior)
            values.update(donchian_high=high,donchian_low=low,support=low,resistance=high,
                distance_support=closes[-1]/low-1,distance_resistance=closes[-1]/high-1)
            if high>low:values['channel_position']=(closes[-1]-low)/(high-low)
        if n>=5:
            # A pivot at i is known only once the two right-side bars have completed.
            highs=[i for i in range(2,n-2) if bars[i].high>max(b.high for b in bars[i-2:i]+bars[i+1:i+3])]
            lows=[i for i in range(2,n-2) if bars[i].low<min(b.low for b in bars[i-2:i]+bars[i+1:i+3])]
            if highs:values['confirmed_swing_high']=bars[highs[-1]].high
            if lows:values['confirmed_swing_low']=bars[lows[-1]].low
    return _result('intraday_continuous',values,'WARMUP_OR_MISSING_CAPABILITY')


def extend_registry(session_bars=(),prior_session_bars=(),session_complete=False,prior_complete=False):
    registry=build_default_registry()
    registry.register(TechnicalFeatureDefinition('intraday_continuous','multi_family',('close','optional_ohlc'),
        {'rsi':14,'sma':(5,20),'ema':(12,26),'stochastic':14,'volatility':20,'channel':20,'swing_confirmation':2},
        5,FRAMES,('rsi','sma_fast','sma_slow','ema_fast','ema_slow','ema_spread','stochastic_k','stochastic_d',
        'realized_volatility_20','volatility_change','donchian_high','donchian_low','channel_position',
        'support','resistance','distance_support','distance_resistance','confirmed_swing_high','confirmed_swing_low'),
        'Windows measured in completed bars, not daily calibration. Partial fields explicitly absent.',
        (),VERSION,'intraday_features.py + asset_specific_technicals.py','implemented'),_continuous)
    def session_calculator(bars,caps,index,benchmark):
        values={};current=session_bars
        if session_complete and current and all(b.high is not None and b.low is not None for b in current):
            values.update(session_high=max(b.high for b in current),session_low=min(b.low for b in current))
            if len(current)>=3:values.update(opening_range_high=max(b.high for b in current[:3]),opening_range_low=min(b.low for b in current[:3]))
            if all(b.volume is not None and b.close is not None for b in current) and sum(b.volume for b in current)>0:
                values['session_vwap']=sum((b.high+b.low+b.close)/3*b.volume for b in current)/sum(b.volume for b in current)
        if prior_complete and prior_session_bars and all(b.high is not None and b.low is not None for b in prior_session_bars):
            values.update(prior_session_high=max(b.high for b in prior_session_bars),prior_session_low=min(b.low for b in prior_session_bars))
            if session_complete and current and current[0].open is not None and prior_session_bars[-1].close is not None:
                values['gap_return']=current[0].open/prior_session_bars[-1].close-1
        return _result('intraday_session',values,'MISSING_COMPLETE_SESSION_PREFIX_OR_VOLUME')
    registry.register(TechnicalFeatureDefinition('intraday_session','session_structure',('session_calendar','ohlc','optional_volume'),
        {'opening_range_bars':3},1,FRAMES,('session_high','session_low','opening_range_high','opening_range_low','session_vwap',
        'prior_session_high','prior_session_low','gap_return'),'Current-session prefix only; VWAP needs observed positive volume.',
        ('intraday',),VERSION,'intraday_features.py','implemented'),session_calculator)
    return registry


@dataclass(frozen=True)
class FeatureSnapshot:
    instrument_id: str
    timeframe: str
    decision_time: object
    values: dict
    unavailable: dict
    input_record_ids: tuple
    version: str=VERSION


def compute_features(bars,decision_time,sessions=(),benchmark_closes=None):
    known=as_of(bars,decision_time)
    if not known:raise ValueError('No available observations')
    if len({(b.instrument_id,b.timeframe) for b in known})!=1:raise ValueError('One instrument/timeframe required')
    # Refuse to compress missing or stale observations into a deceptively contiguous window.
    if any(b.close is None or b.stale for b in known):
        return FeatureSnapshot(known[-1].instrument_id,known[-1].timeframe,utc(decision_time),{}, {'all':'MISSING_OR_STALE_PRICES'},tuple(b.record_id for b in known))
    gaps=any(a.session_id==b.session_id and a.event_time!=b.interval_start for a,b in zip(known,known[1:]))
    if gaps:return FeatureSnapshot(known[-1].instrument_id,known[-1].timeframe,utc(decision_time),{}, {'all':'INCOMPLETE_BAR_SEQUENCE'},tuple(b.record_id for b in known))
    current=tuple(b for b in known if b.session_id==known[-1].session_id)
    windows=sorted(sessions,key=lambda s:s.open_time);window=next((s for s in windows if s.session_id==current[-1].session_id),None)
    previous=next((s for s in reversed(windows) if window and s.close_time<=window.open_time),None)
    prior=tuple(b for b in known if previous and b.session_id==previous.session_id)
    complete=bool(window and current[0].interval_start==window.open_time)
    prior_complete=bool(previous and prior and prior[0].interval_start==previous.open_time and prior[-1].event_time==previous.close_time)
    registry=extend_registry(current,prior,complete,prior_complete)
    caps=DataCapabilities(all(all(getattr(b,k) is not None for k in ('open','high','low')) for b in known),
        all(b.volume is not None for b in known),benchmark_closes is not None,True,known[-1].timeframe)
    raw=[MarketBar(b.close,b.high,b.low,b.open,b.volume) for b in known]
    values={};unavailable={}
    names=('macd','bollinger','atr','adx_dmi','relative_strength','relative_volume','ichimoku','fibonacci_context','candlestick_patterns','intraday_continuous','intraday_session')
    for name in names:
        if name=='relative_volume' and (len(raw)<21 or not caps.has_volume or sum(b.volume for b in raw[-21:-1])<=0):
            unavailable[name]='MISSING_VOLUME_OR_WARMUP';continue
        result=registry.compute(name,raw,caps,len(raw)-1,benchmark_closes)
        if result.available:values.update(result.values)
        else:unavailable[name]=result.reason
    if 'median_dollar_volume' in values:values['median_quote_notional_volume']=values.pop('median_dollar_volume')
    return FeatureSnapshot(known[-1].instrument_id,known[-1].timeframe,utc(decision_time),values,unavailable,tuple(b.record_id for b in known))
