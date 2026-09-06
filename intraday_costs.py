"""Explicit instrument-unit turnover costs; no silent proxy contract assumptions."""
from dataclasses import dataclass,asdict
import math
VERSION='intraday-costs-v1'

@dataclass(frozen=True)
class CostSchedule:
    schedule_id: str
    instrument_id: str
    currency: str
    commission_bps: float
    minimum_commission: float
    spread_bps: float
    slippage_ticks: float
    exchange_fee_per_unit: float
    broker_fee_per_order: float
    annual_long_financing: float
    annual_short_financing: float
    assumptions: tuple[str,...]
    verified: bool=False
    version: str=VERSION
    def __post_init__(self):
        if not self.schedule_id or not self.instrument_id or len(self.currency)!=3:raise ValueError('Cost identity/currency required')
        for key,value in asdict(self).items():
            if key in ('commission_bps','minimum_commission','spread_bps','slippage_ticks','exchange_fee_per_unit',
                       'broker_fee_per_order','annual_long_financing','annual_short_financing'):
                if isinstance(value,bool) or not math.isfinite(value) or value<0:raise ValueError('Invalid cost '+key)
        if not isinstance(self.assumptions,tuple) or (not self.verified and not self.assumptions):raise ValueError('Unverified costs need explicit assumptions')

@dataclass(frozen=True)
class CostResult:
    available: bool
    total: float | None
    currency: str | None
    turnover_units: float
    components: dict
    reasons: tuple
    schedule_id: str | None
    assumptions: tuple
    version: str=VERSION


def missing_cost_metadata(instrument,schedule):
    reasons=[]
    if schedule is None:reasons.append('MISSING_COST_SCHEDULE')
    else:
        if schedule.instrument_id!=instrument.instrument_id:reasons.append('COST_INSTRUMENT_MISMATCH')
        if schedule.currency!=instrument.currency:reasons.append('COST_CURRENCY_MISMATCH')
    for field in ('currency','contract_multiplier','tick_size','lot_size','minimum_trade_size','financing_applicable'):
        if getattr(instrument,field) is None:reasons.append('UNKNOWN_'+field.upper())
    return tuple(reasons)


def transition_cost(instrument,schedule,previous_units,target_units,price,holding_seconds=0):
    if any(not math.isfinite(x) for x in (previous_units,target_units,price,holding_seconds)) or price<=0 or holding_seconds<0:raise ValueError('Invalid position/price/time')
    reasons=list(missing_cost_metadata(instrument,schedule));turnover=abs(target_units-previous_units)
    if min(previous_units,target_units)<0 and not instrument.supports_short:reasons.append('SHORT_UNSUPPORTED')
    if instrument.lot_size is not None:
        for units in (previous_units,target_units):
            if units and (abs(units)<instrument.minimum_trade_size if instrument.minimum_trade_size is not None else False):reasons.append('BELOW_MINIMUM_SIZE')
            if not math.isclose(units/instrument.lot_size,round(units/instrument.lot_size),abs_tol=1e-8):reasons.append('INVALID_LOT_SIZE')
    if reasons:return CostResult(False,None,instrument.currency,turnover,{},tuple(dict.fromkeys(reasons)),getattr(schedule,'schedule_id',None),getattr(schedule,'assumptions',()))
    notional=turnover*price*instrument.contract_multiplier
    # Reversal is two sides of turnover; a single net order incurs one minimum commission.
    components=dict(commission=max(schedule.minimum_commission,notional*schedule.commission_bps/10000) if turnover else 0,
        spread=notional*schedule.spread_bps/20000,
        slippage=turnover*math.ceil(schedule.slippage_ticks)*instrument.tick_size*instrument.contract_multiplier,
        exchange=turnover*schedule.exchange_fee_per_unit,broker=schedule.broker_fee_per_order if turnover else 0,
        financing=0.)
    if instrument.financing_applicable and previous_units:
        rate=schedule.annual_long_financing if previous_units>0 else schedule.annual_short_financing
        components['financing']=abs(previous_units)*price*instrument.contract_multiplier*rate*holding_seconds/(365*86400)
    return CostResult(True,sum(components.values()),instrument.currency,turnover,components,(),schedule.schedule_id,schedule.assumptions)
