"""Read-only market chart identities outside the canonical cash-share universe."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MarketChartInstrument:
    instrument_id: str
    display_symbol: str
    name: str
    asset_class: str
    instrument_type: str
    data_symbol: str
    source: str
    chart_basis: str
    note: str

    def to_dict(self):
        return {**asdict(self), "capabilities": {"public_chart": True,
                "canonical_ranking": False, "broker_execution": False}}


MARKET_CHART_INSTRUMENTS = {
    item.instrument_id: item for item in (
        MarketChartInstrument(
            "ETF_STX40", "STX40", "Satrix 40 ETF", "index_etf", "etf",
            "STX40.JO", "Yahoo Finance", "LISTED_SECURITY",
            "Actual JSE-listed ETF price; not yet admitted to canonical ranking or sizing."),
        MarketChartInstrument(
            "ETF_STXFIN", "STXFIN", "Satrix FINI ETF", "index_etf", "etf",
            "STXFIN.JO", "Yahoo Finance", "LISTED_SECURITY",
            "Actual JSE-listed ETF price; not yet admitted to canonical ranking or sizing."),
        MarketChartInstrument(
            "ETF_STXRES", "STXRES", "Satrix RESI ETF", "index_etf", "etf",
            "STXRES.JO", "Yahoo Finance", "LISTED_SECURITY",
            "Actual JSE-listed ETF price; not yet admitted to canonical ranking or sizing."),
        MarketChartInstrument(
            "ETF_STXIND", "STXIND", "Satrix INDI ETF", "index_etf", "etf",
            "STXIND.JO", "Yahoo Finance", "LISTED_SECURITY",
            "Actual JSE-listed ETF price; not yet admitted to canonical ranking or sizing."),
        MarketChartInstrument(
            "CFD_REF_BRENT", "BRENT REF", "Brent CFD reference", "cfd_reference", "proxy",
            "BZ=F", "Yahoo Finance", "UNDERLYING_FUTURES_PROXY",
            "Public Brent futures proxy; not an IG CFD quote and excludes spread and financing."),
        MarketChartInstrument(
            "CFD_REF_GOLD", "GOLD REF", "Gold CFD reference", "cfd_reference", "proxy",
            "GC=F", "Yahoo Finance", "UNDERLYING_FUTURES_PROXY",
            "Public gold futures proxy; not an IG CFD quote and excludes spread and financing."),
        MarketChartInstrument(
            "CFD_REF_USDZAR", "USD/ZAR REF", "USD/ZAR CFD reference", "cfd_reference", "proxy",
            "ZAR=X", "Yahoo Finance", "SPOT_PROXY",
            "Public USD/ZAR reference; not an IG CFD quote and excludes spread and financing."),
        MarketChartInstrument(
            "CFD_REF_JSE", "JSE REF", "JSE index CFD reference", "cfd_reference", "proxy",
            "^J203.JO", "Yahoo Finance", "INDEX_PROXY",
            "Public JSE All Share proxy; not an IG index CFD quote or Top 40 contract."),
    )
}


def resolve_market_chart(value):
    return MARKET_CHART_INSTRUMENTS[value]


def market_chart_list():
    return [item.to_dict() for item in MARKET_CHART_INSTRUMENTS.values()]

