"""Explicit FX/gold research products: no broker imports or share-volume gate."""
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from domain.backtest.data import number as N
from domain.evaluation.experiment import utc


@dataclass(frozen=True)
class Conversion:
    session: str
    available_at: datetime
    account_per_quote: Decimal

    def __post_init__(self):
        object.__setattr__(self,'available_at',utc(self.available_at,'available_at'))
        object.__setattr__(self,'account_per_quote',N(self.account_per_quote))
        if self.account_per_quote<=0: raise ValueError('positive conversion required')


@dataclass(frozen=True)
class MarginProduct:
    """Quote-currency P&L converted at settlement; daily carry on entry notional.

    Carry uses actual calendar-day distance, including weekends. Caller supplies
    product/session-specific rates; a broker triple-roll convention requires its
    own adapter, and must not be inferred from this model.
    """
    account_currency: str
    quote_currency: str
    calendar_id: str
    sessions: tuple
    conversions: tuple[Conversion,...]
    long_financing_bps_per_day: Decimal
    short_financing_bps_per_day: Decimal
    multiplier: Decimal
    lot: Decimal
    margin_fraction: Decimal
    version: str = 'explicit-margin-product-v1'
    allow_short: bool = True
    activity_required: bool = False

    def __post_init__(self):
        for name in ('long_financing_bps_per_day','short_financing_bps_per_day','multiplier','lot','margin_fraction'):
            object.__setattr__(self,name,N(getattr(self,name)))
        if self.multiplier<=0 or self.lot<=0 or not 0<self.margin_fraction<1:
            raise ValueError('explicit multiplier/lot/margin required')
        if self.account_currency not in ('ZAR','USD') or self.quote_currency not in ('ZAR','USD') or not self.calendar_id:
            raise ValueError('supported currency and calendar identity required')
        if not isinstance(self.sessions,tuple) or not isinstance(self.conversions,tuple): raise ValueError('immutable inputs required')
        if len({c.session for c in self.conversions})!=len(self.conversions): raise ValueError('duplicate conversion')
        keys={s.key for s in self.sessions}
        if any(c.session not in keys for c in self.conversions): raise ValueError('conversion outside calendar')
        for c in self.conversions:
            if c.available_at>next(s.open_at for s in self.sessions if s.key==c.session):
                raise ValueError('conversion must be known before session open')

    def validate(self,m):
        if m.currency!=self.quote_currency or m.calendar_id!=self.calendar_id or m.sessions!=self.sessions:
            raise ValueError('product quote/session identity mismatch')
        if m.action_basis!='NONE_VERIFIED': raise ValueError('margin action treatment unsupported')

    def rate(self,session):
        if self.account_currency==self.quote_currency: return Decimal(1)
        matches=[c for c in self.conversions if c.session==session]
        if len(matches)!=1: raise ValueError('required conversion unavailable')
        return matches[0].account_per_quote

    def financing(self,p,session,previous):
        current=next(s for s in self.sessions if s.key==session)
        prior=next(s for s in self.sessions if s.key==previous)
        days=(current.open_at.date()-prior.open_at.date()).days
        bps=self.long_financing_bps_per_day if p['signal'].side==1 else self.short_financing_bps_per_day
        return p['entry']*p['qty']*self.multiplier*self.rate(session)*bps*days/10000

    def configuration(self): return asdict(self)


@dataclass(frozen=True)
class Forex(MarginProduct):
    pair: str = 'USD/ZAR'
    version: str = 'usd-zar-margin-v1'

    def validate(self,m):
        super().validate(m)
        if m.product!='FX' or self.pair!='USD/ZAR' or self.quote_currency!='ZAR':
            raise ValueError('USD/ZAR quote direction and FX identity required')
        if m.activity_basis not in ('NONE','PROVIDER_TICKS','EXCHANGE_CONTRACTS'):
            raise ValueError('FX activity must not impersonate traded shares')


@dataclass(frozen=True)
class Gold(MarginProduct):
    vehicle: str = 'SPOT_CFD'
    contract_id: str = 'XAU/USD'
    version: str = 'gold-product-margin-v1'

    def validate(self,m):
        super().validate(m)
        if m.product!='GOLD' or self.vehicle not in ('SPOT_CFD','FUTURE_CONTRACT'):
            raise ValueError('executable fixed gold product required, theoretical/continuous prices refused')
        if m.instrument!=self.contract_id:
            raise ValueError('exact gold contract identity required; roll requires separate close/reopen')
        allowed=('NONE','PROVIDER_TICKS') if self.vehicle=='SPOT_CFD' else ('NONE','EXCHANGE_CONTRACTS')
        if m.activity_basis not in allowed: raise ValueError('gold activity/product mismatch')


def reciprocal_bid_ask(bid,ask):
    bid,ask=N(bid),N(ask)
    if not 0<bid<=ask: raise ValueError('ordered positive bid/ask required')
    return Decimal(1)/ask,Decimal(1)/bid


def theoretical_rand_gold(usd_gold,usd_zar,*,gold_at,fx_at):
    gold_at=utc(gold_at,'gold_at'); fx_at=utc(fx_at,'fx_at')
    if gold_at!=fx_at or min(N(usd_gold),N(usd_zar))<=0:
        raise ValueError('positive exactly aligned quotes required')
    return {'value':str(N(usd_gold)*N(usd_zar)),'at':gold_at.isoformat(),
            'product':'XAU_ZAR_THEORETICAL','executable':False}

@dataclass(frozen=True)
class GoldListed:
    """Cash-funded listed gold units, independent venue sessions/activity."""
    account_currency: str
    quote_currency: str
    calendar_id: str
    sessions: tuple
    conversions: tuple[Conversion,...]
    instrument: str
    version: str = 'gold-listed-cash-v1'
    multiplier: Decimal = Decimal(1)
    lot: Decimal = Decimal(1)
    margin_fraction: Decimal = Decimal(1)
    allow_short: bool = False
    activity_required: bool = False

    def __post_init__(self):
        if self.account_currency not in ('USD','ZAR') or self.quote_currency not in ('USD','ZAR'):
            raise ValueError('explicit listed product currency required')
        if not isinstance(self.sessions,tuple) or not isinstance(self.conversions,tuple) or not self.instrument:
            raise ValueError('immutable instrument/session inputs required')
        if self.multiplier!=1 or self.lot!=1 or self.margin_fraction!=1 or self.allow_short or self.activity_required:
            raise ValueError('cash LONG listed units without share-volume gate required')
        if len({c.session for c in self.conversions})!=len(self.conversions): raise ValueError('duplicate conversion')
        for c in self.conversions:
            matches=[s for s in self.sessions if s.key==c.session]
            if len(matches)!=1 or c.available_at>matches[0].open_at: raise ValueError('listed conversion unavailable before open')

    def validate(self,m):
        if m.product!='GOLD_ETF' or m.instrument!=self.instrument or m.currency!=self.quote_currency or m.sessions!=self.sessions or m.calendar_id!=self.calendar_id:
            raise ValueError('actual listed vehicle identity/session required')
        if m.activity_basis not in ('NONE','TRADED_UNITS'): raise ValueError('listed units are not underlying spot/futures activity')

    def rate(self,session):
        if self.account_currency==self.quote_currency: return Decimal(1)
        values=[c.account_per_quote for c in self.conversions if c.session==session]
        if len(values)!=1: raise ValueError('listed conversion required')
        return values[0]

    def financing(self,p,session,previous): return Decimal(0)
    def configuration(self): return asdict(self)
