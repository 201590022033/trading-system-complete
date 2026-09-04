"""Canonical instrument identities used by the operational UI and adapters."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Instrument:
    instrument_id: str
    display_symbol: str
    research_symbol: str
    yahoo_symbol: str
    finnhub_symbol: str
    name: str
    sector: str
    currency: str = "ZAR"
    exchange: str = "XJSE"

    def to_dict(self):
        value = asdict(self)
        value["aliases"] = sorted(ALIASES_FOR[self.instrument_id])
        value["capabilities"] = {"historical": True, "yahoo": True,
                                  "news": True, "broker_execution": False}
        return value


INSTRUMENTS = {
    row.instrument_id: row for row in (
        Instrument("NPN", "NPN", "NPN", "NPN.JO", "NPN.XJSE", "Naspers", "Technology"),
        Instrument("SOL", "SOL", "SASOL", "SOL.JO", "SOL.XJSE", "Sasol", "Energy"),
        Instrument("BHP", "BHP", "BHP", "BHG.JO", "BHP.XJSE", "BHP Group", "Mining"),
        Instrument("IMP", "IMP", "IMPJ", "IMP.JO", "IMP.XJSE", "Impala Platinum", "Mining"),
        Instrument("SHP", "SHP", "SHPJ", "SHP.JO", "SHP.XJSE", "Shoprite", "Retail"),
        Instrument("ABG", "ABG", "ABSPJ", "ABG.JO", "ABG.XJSE", "Absa Group", "Financial Services"),
    )
}

ALIASES_FOR = {
    "NPN": {"NPN", "NPN.JO", "NPN.XJSE"},
    "SOL": {"SOL", "SASOL", "SOL.JO", "SOL.XJSE"},
    "BHP": {"BHP", "BHG.JO", "BHP.XJSE"},
    "IMP": {"IMP", "IMPJ", "IMP.JO", "IMP.XJSE"},
    "SHP": {"SHP", "SHPJ", "SHP.JO", "SHP.XJSE"},
    "ABG": {"ABG", "ABSPJ", "ABG.JO", "ABG.XJSE"},
}
ALIAS_INDEX = {alias.upper(): key for key, aliases in ALIASES_FOR.items() for alias in aliases}


def resolve_instrument(value: str) -> Instrument:
    key = ALIAS_INDEX.get((value or "").strip().upper())
    if not key:
        raise KeyError(f"unsupported instrument: {value}")
    return INSTRUMENTS[key]


def instrument_list():
    return [item.to_dict() for item in INSTRUMENTS.values()]
