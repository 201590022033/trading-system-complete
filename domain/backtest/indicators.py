"""Bounded causal indicator catalogue reusing existing EMA/Wilder RSI seeds."""
from dataclasses import dataclass
from decimal import Decimal
from domain.features.technical import _ema, candidate_rsi_wilder
from domain.backtest.data import number as N


@dataclass(frozen=True)
class Indicator:
    id: str
    version: str
    role: str
    lookback: int
    inputs: tuple[str,...]
    markets: tuple[str,...]
    formula: str


CATALOGUE=(
    Indicator('ROC3','roc3-v1','MOMENTUM',4,('close',),('EQUITY','FX','GOLD'),'close / close[-4] - 1'),
    Indicator('EMA3','ema3-first-seed-v1','MOMENTUM',3,('close',),('EQUITY','FX','GOLD'),'close / EMA3(first-close seed) - 1'),
    Indicator('RSI14','wilder14-existing-v1','MOMENTUM',15,('close',),('EQUITY','FX','GOLD'),'existing Wilder14 seed and smoothing'),
    Indicator('VOLUME20','prior20-volume-v1','ACTIVITY',21,('activity',),('EQUITY',),'current shares / prior20 mean shares'),
)


def feature(id,bars,product):
    plugin=next((p for p in CATALOGUE if p.id==id),None)
    if plugin is None or product not in plugin.markets: raise ValueError('indicator/market not registered')
    if len(bars)<plugin.lookback: return None
    closes=[N(b.close) for b in bars]
    if id=='ROC3': return closes[-1]/closes[-4]-1
    if id=='EMA3': return closes[-1]/Decimal(str(_ema([float(x) for x in closes],3)))-1
    if id=='RSI14':
        r=candidate_rsi_wilder([float(x) for x in closes])
        return Decimal(str(r.value)) if r.available else None
    values=[N(b.activity) if b.activity is not None else None for b in bars[-21:]]
    if None in values or any(x<0 for x in values) or sum(values[:-1])<=0: return None
    return values[-1]/(sum(values[:-1])/20)
