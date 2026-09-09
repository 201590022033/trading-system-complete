"""Canonical, broker-neutral instrument identity registry.

This module reconciles existing identity metadata without changing any legacy
lookup or scanner behavior. Execution symbols remain unresolved unless an
authoritative broker mapping is supplied.
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

from instrument_registry import ALIASES_FOR, INSTRUMENTS
from intraday_instruments import DEFAULT_REGISTRY as HR11_REGISTRY


class GovernanceState(str, Enum):
    MANDATORY = "MANDATORY"
    PRODUCTION = "PRODUCTION"
    SHADOW = "SHADOW"
    RESEARCH = "RESEARCH"
    DISABLED = "DISABLED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CanonicalInstrument:
    instrument_id: str
    display_name: str
    asset_class: str
    underlying_id: str
    signal_target_id: str
    data_symbol: Optional[str]
    execution_symbol: Optional[str]
    exchange: Optional[str]
    quote_currency: Optional[str]
    timezone: str
    calendar_reference: Optional[str]
    contract_multiplier: Optional[float]
    tick_size: Optional[float]
    tick_value: Optional[float]
    lot_size: Optional[float]
    margin_requirement: Optional[float]
    leverage: Optional[float]
    governance_state: GovernanceState
    aliases: tuple[str, ...]
    enabled_horizons: tuple[str, ...]
    capabilities: tuple[str, ...]
    source_reference: str
    instrument_type: str = "unknown"
    sector: str = "unspecified"

    def __post_init__(self) -> None:
        required = (self.instrument_id, self.display_name, self.underlying_id,
                    self.signal_target_id, self.timezone, self.source_reference)
        if any(not value or not value.strip() for value in required):
            raise ValueError("instrument identity and provenance are required")
        ZoneInfo(self.timezone)
        if not isinstance(self.governance_state, GovernanceState):
            raise ValueError("explicit governance state required")
        if not isinstance(self.aliases, tuple) or not isinstance(self.enabled_horizons, tuple):
            raise ValueError("aliases and horizons must be immutable tuples")
        for value in (self.contract_multiplier, self.tick_size, self.tick_value, self.lot_size, self.leverage):
            if value is not None and (isinstance(value, bool) or not math.isfinite(value) or value <= 0):
                raise ValueError("known contract values must be positive and finite")
        if self.margin_requirement is not None and (not math.isfinite(self.margin_requirement) or self.margin_requirement < 0):
            raise ValueError("margin requirement must be non-negative and finite")
        if all(value is not None for value in (self.contract_multiplier, self.tick_size, self.tick_value)):
            if not math.isclose(self.tick_value, self.contract_multiplier * self.tick_size):
                raise ValueError("tick value inconsistent with multiplier and tick size")
        if self.quote_currency is not None and (len(self.quote_currency) != 3 or not self.quote_currency.isupper()):
            raise ValueError("quote currency must be an uppercase ISO-style code or None")

    def to_dict(self) -> dict[str, Any]:
        return {"instrument_id": self.instrument_id, "display_name": self.display_name,
                "asset_class": self.asset_class, "underlying_id": self.underlying_id,
                "signal_target_id": self.signal_target_id, "data_symbol": self.data_symbol,
                "execution_symbol": self.execution_symbol, "exchange": self.exchange,
                "quote_currency": self.quote_currency, "timezone": self.timezone,
                "calendar_reference": self.calendar_reference, "contract_multiplier": self.contract_multiplier,
                "tick_size": self.tick_size, "tick_value": self.tick_value, "lot_size": self.lot_size,
                "margin_requirement": self.margin_requirement, "leverage": self.leverage,
                "governance_state": self.governance_state.value, "aliases": list(self.aliases),
                "enabled_horizons": list(self.enabled_horizons), "capabilities": list(self.capabilities),
                "source_reference": self.source_reference, "instrument_type": self.instrument_type,
                "sector": self.sector, "live_execution_available": False}


class CanonicalInstrumentRegistry:
    version = "canonical-instrument-registry-v1"

    def __init__(self, instruments: Iterable[CanonicalInstrument]) -> None:
        items = tuple(instruments)
        if len({item.instrument_id for item in items}) != len(items):
            raise ValueError("duplicate canonical instrument ID")
        aliases: dict[str, str] = {}
        for item in items:
            for alias in item.aliases:
                key = alias.strip().upper()
                if not key or (key in aliases and aliases[key] != item.instrument_id):
                    raise ValueError("duplicate instrument alias")
                aliases[key] = item.instrument_id
        self._items = {item.instrument_id: item for item in items}
        self._aliases = aliases

    def get(self, instrument_id: str) -> CanonicalInstrument:
        return self._items[instrument_id]

    def resolve(self, value: str) -> CanonicalInstrument:
        return self.get(self._aliases[(value or "").strip().upper()])

    def instruments(self, enabled_only: bool = False) -> tuple[CanonicalInstrument, ...]:
        disabled = {GovernanceState.DISABLED, GovernanceState.BLOCKED}
        return tuple(item for item in self._items.values()
                     if not enabled_only or item.governance_state not in disabled)

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "instruments": [item.to_dict() for item in self.instruments()]}


def _legacy_item(key: str, *, canonical_id: str, target: str, state: GovernanceState) -> CanonicalInstrument:
    old = INSTRUMENTS[key]
    return CanonicalInstrument(
        canonical_id, old.name, "equity", old.research_symbol, target, old.yahoo_symbol, None,
        old.exchange, old.currency, "Africa/Johannesburg", "JSE", None, None, None, None, None, None,
        state, tuple(sorted(ALIASES_FOR[key])), ("1d",), ("historical", "yahoo", "news"),
        "instrument_registry.py", "cash_equity", old.sector)


def build_default_registry() -> CanonicalInstrumentRegistry:
    legacy = (
        _legacy_item("NPN", canonical_id="EQ_ZAR_NASPERS", target="NPN", state=GovernanceState.MANDATORY),
        _legacy_item("SOL", canonical_id="EQ_ZAR_SASOL", target="SASOL", state=GovernanceState.MANDATORY),
        _legacy_item("BHP", canonical_id="EQ_ZAR_BHP", target="BHP", state=GovernanceState.MANDATORY),
        _legacy_item("IMP", canonical_id="EQ_ZAR_IMPLATS", target="IMPJ", state=GovernanceState.MANDATORY),
        _legacy_item("SHP", canonical_id="EQ_ZAR_SHOPRITE", target="SHPJ", state=GovernanceState.MANDATORY),
        _legacy_item("ABG", canonical_id="EQ_ZAR_ABSA", target="ABSPJ", state=GovernanceState.MANDATORY),
    )
    reconciled = []
    legacy_aliases = {alias.upper() for item in legacy for alias in item.aliases}
    for item in HR11_REGISTRY.instruments():
        aliases = tuple(alias for alias in (item.instrument_id, item.signal_target_id, item.data_symbol)
                        if alias and alias.upper() not in legacy_aliases)
        reconciled.append(CanonicalInstrument(
            item.instrument_id, item.display_name, item.asset_class, item.underlying_id,
            item.signal_target_id, item.data_symbol, item.execution_symbol, item.exchange,
            item.quote_currency, item.timezone, item.session_calendar, item.contract_multiplier,
            item.tick_size, item.tick_value, item.lot_size, item.margin_requirement, item.leverage,
            GovernanceState.RESEARCH if item.enabled else GovernanceState.DISABLED,
            tuple(dict.fromkeys(aliases)), ("5m", "15m", "30m", "60m", "1d") if item.supports_intraday else ("1d",),
            tuple(filter(None, ("historical" if item.supports_historical_data else None,
                                "volume" if item.supports_volume else None,
                                "intraday" if item.supports_intraday else None))),
            "intraday_instruments.py", item.instrument_type, item.sector))
    return CanonicalInstrumentRegistry(legacy + tuple(reconciled))


DEFAULT_INSTRUMENT_REGISTRY = build_default_registry()


def discovery_mapping(symbols: Iterable[str]) -> dict[str, Optional[str]]:
    """Map discovery keys without inventing identities for unknown tickers."""
    result = {}
    for symbol in symbols:
        try:
            result[symbol] = DEFAULT_INSTRUMENT_REGISTRY.resolve(symbol).instrument_id
        except KeyError:
            result[symbol] = None
    return result
