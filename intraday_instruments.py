"""HR11 immutable research identities; no executable broker capabilities."""
from dataclasses import asdict, dataclass
from enum import Enum
import math
from zoneinfo import ZoneInfo

from instrument_registry import resolve_instrument

VERSION = 'intraday-instrument-registry-v1'


class DataGrade(str, Enum):
    RESEARCH = 'RESEARCH_DATA'
    DELAYED = 'DELAYED_LIVE_DATA'
    EXECUTION = 'EXECUTION_GRADE_DATA'


@dataclass(frozen=True)
class InstrumentDefinition:
    instrument_id: str
    display_name: str
    underlying_id: str
    signal_target_id: str
    asset_class: str
    instrument_type: str
    currency: str | None
    profile_id: str
    data_symbol: str | None = None
    exchange: str | None = None
    base_currency: str | None = None
    quote_currency: str | None = None
    timezone: str = 'UTC'
    session_calendar: str | None = None
    trading_hours: tuple[str, ...] = ()
    contract_multiplier: float | None = None
    tick_size: float | None = None
    tick_value: float | None = None
    lot_size: float | None = None
    minimum_trade_size: float | None = None
    margin_type: str | None = None
    margin_requirement: float | None = None
    leverage: float | None = None
    financing_applicable: bool | None = None
    commission_model: str | None = None
    spread_model: str | None = None
    slippage_model: str | None = None
    exchange_fee_model: str | None = None
    financing_model: str | None = None
    liquidity_class: str = 'UNVERIFIED'
    benchmark_symbol: str | None = None
    execution_symbol: str | None = None
    sector: str = 'unspecified'
    region: str = 'ZA'
    supports_intraday: bool = True
    supports_short: bool = False
    supports_volume: bool = False
    supports_bid_ask: bool = False
    supports_live_data: bool = False
    supports_historical_data: bool = True
    data_grade: DataGrade = DataGrade.RESEARCH
    data_status: str = 'INTRADAY_HISTORY_UNAVAILABLE'
    version: str = VERSION
    enabled: bool = True
    notes: str = 'Research identity only; source and contract capabilities need verification.'

    def __post_init__(self):
        if any(not value.strip() for value in (self.instrument_id,self.display_name,self.underlying_id,
                                               self.signal_target_id,self.profile_id,self.version)):
            raise ValueError('Required identity fields cannot be blank')
        if self.instrument_type not in {'cash_equity','index','future','single_stock_future','cfd','fx','commodity','proxy'}:
            raise ValueError('Unknown instrument type')
        if not isinstance(self.data_grade,DataGrade):
            raise ValueError('Explicit DataGrade required')
        ZoneInfo(self.timezone)
        for name in ('currency','base_currency','quote_currency'):
            currency = getattr(self,name)
            if currency is not None and (len(currency) != 3 or not currency.isalpha() or not currency.isupper()):
                raise ValueError('Currency must be an uppercase code or None (unknown)')
        for name in ('contract_multiplier','tick_size','tick_value','lot_size','minimum_trade_size','leverage'):
            value = getattr(self,name)
            if value is not None and (isinstance(value,bool) or not math.isfinite(value) or value <= 0):
                raise ValueError(f'{name} must be positive and finite or unknown')
        if self.margin_requirement is not None and (not math.isfinite(self.margin_requirement) or self.margin_requirement < 0):
            raise ValueError('Invalid margin requirement')
        if all(x is not None for x in (self.contract_multiplier,self.tick_size,self.tick_value)):
            if not math.isclose(self.tick_value,self.contract_multiplier*self.tick_size):
                raise ValueError('Tick value inconsistent with multiplier and tick size')
        if not isinstance(self.trading_hours,tuple):
            raise ValueError('Trading hours must be immutable')

    def to_dict(self):
        result = asdict(self)
        result['live_execution_available'] = False
        result['cost_availability'] = 'UNAVAILABLE' if not self.commission_model else 'REQUIRES_COST_SCHEDULE'
        return result


class InstrumentRegistry:
    version = VERSION

    def __init__(self, definitions):
        items = tuple(definitions)
        self._items = {i.instrument_id:i for i in items}
        if len(items) != len(self._items):
            raise ValueError('Duplicate instrument ID')

    def get(self, instrument_id):
        # No fallback from an unknown contract to an equity or proxy.
        return self._items[instrument_id]

    def instruments(self, enabled_only=False):
        return tuple(i for i in self._items.values() if i.enabled or not enabled_only)

    def for_target(self, signal_target):
        return tuple(i for i in self.instruments(True) if i.signal_target_id == signal_target)


def default_registry():
    items = []
    for name,symbol,asset,profile,currency in (
        ('USDZAR','ZAR=X','fx','usdzar','ZAR'),
        ('JSE_INDEX','^J203.JO','equity_index','index_derivative',None),
        ('GOLD','GC=F','commodity','gold','USD'),
        ('BRENT','BZ=F','commodity','energy','USD'),
        ('PLATINUM','PL=F','commodity','platinum','USD')):
        items.append(InstrumentDefinition(name+'_PROXY',name+' research proxy',name,name,asset,'proxy',
            currency,profile,data_symbol=symbol,base_currency='USD' if name=='USDZAR' else None,
            quote_currency=currency,notes='Public research proxy, not a verified FX/futures execution contract.'))
    for symbol,profile in (('NPN','offshore_earner'),('SOL','energy_sasol'),('BHP','diversified_mining'),('ABG','banks_financials')):
        old = resolve_instrument(symbol)
        items.append(InstrumentDefinition(symbol+'_CASH',old.name,old.research_symbol,old.research_symbol,
            'equity','cash_equity',old.currency,profile,data_symbol=old.yahoo_symbol,exchange=old.exchange,
            timezone='Africa/Johannesburg',contract_multiplier=1,financing_applicable=False,
            supports_volume=True,benchmark_symbol='^J203.JO',sector=old.sector))
    for name,symbol in (('PALLADIUM','PA=F'),('SP500','^GSPC')):
        items.append(InstrumentDefinition(name+'_PROXY',name+' future extension',name,name,'context','proxy',
            'USD','future_extension',data_symbol=symbol,enabled=False,supports_intraday=False))
    for kind in ('cfd','single_stock_future'):
        items.append(InstrumentDefinition('SASOL_'+kind.upper(),'Sasol '+kind,'SASOL','SASOL','equity',kind,
            'ZAR','energy_sasol',enabled=False,supports_intraday=False,supports_historical_data=False))
    return InstrumentRegistry(items)


DEFAULT_REGISTRY = default_registry()
