"""Strict HR11 adapters to established profile names and macro definitions."""
from dataclasses import dataclass
from market_profiles import DEFAULT_PROFILE_REGISTRY,MarketProfile,MacroSensitivity
VERSION='intraday-profiles-v1'

@dataclass(frozen=True)
class IntradayProfile:
    profile_id: str
    base_profile: MarketProfile
    factors: tuple[str,...]
    requires_volume: bool
    minimum_bars: int=26
    minimum_relative_volume: float=0.2
    maximum_spread_bps: float=30
    version: str=VERSION
    shadow_only: bool=True

# The gold and energy names already exist in HR7; platinum is an explicit extension.
_EXTENSIONS={name:MarketProfile(name,sector,'research_proxy',tuple(MacroSensitivity(f,0) for f in factors))
    for name,sector,factors in [('gold','gold',('USDZAR','JSE_INDEX')),('energy','energy',('USDZAR','GOLD')),('platinum','pgm',('USDZAR','GOLD'))]}
_FACTORS={
    'usdzar':('GOLD','BRENT','JSE_INDEX'), 'index_derivative':('USDZAR','GOLD','BRENT','PLATINUM'),
    'offshore_earner':('USDZAR','JSE_INDEX'), 'energy_sasol':('BRENT','USDZAR','JSE_INDEX'),
    'diversified_mining':('PLATINUM','GOLD','USDZAR','JSE_INDEX'), 'banks_financials':('USDZAR','JSE_INDEX'),
    'gold':('USDZAR','JSE_INDEX'), 'energy':('USDZAR','GOLD'), 'platinum':('USDZAR','GOLD'),
}

def get_profile(instrument):
    factors=_FACTORS[instrument.profile_id] # Unknown definitions intentionally raise.
    base=_EXTENSIONS[instrument.profile_id] if instrument.profile_id in _EXTENSIONS else DEFAULT_PROFILE_REGISTRY.get(instrument.profile_id)
    return IntradayProfile(instrument.profile_id,base,factors,instrument.instrument_type=='cash_equity')
