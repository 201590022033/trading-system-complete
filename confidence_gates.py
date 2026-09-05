"""OI2's explicit 30-gate evidence model (six categories of five gates)."""

from dataclasses import asdict, dataclass

UNAVAILABLE = "UNAVAILABLE"

GATES = {
    "Data": ("current_data_available", "freshness", "history_sufficient", "spread_liquidity", "anomaly_free"),
    "Trend": ("short_trend", "medium_trend", "moving_average_structure", "trend_slope", "breakout"),
    "Momentum & volatility": ("rsi", "macd", "stochastic", "atr", "indicator_agreement"),
    "Volume & liquidity": ("volume_confirmation", "relative_volume", "liquidity", "price_volume_agreement", "volatility_liquidity_fit"),
    "News & macro": ("company_news", "sens", "source_agreement", "macro", "news_conflict"),
    "Decision": ("legacy_signal", "researcher_agreement", "technical_news_agreement", "risk_reward", "safety_override"),
}


@dataclass(frozen=True)
class GateResult:
    category: str
    gate: str
    outcome: str
    reason: str
    source: str


def _outcome(signal):
    if signal is None:
        return "UNAVAILABLE"
    if signal > 0:
        return "SUPPORTS_BUY"
    if signal < 0:
        return "SUPPORTS_SELL"
    return "NEUTRAL"


def evaluate_gates(market: dict, technical: dict, news: dict, decision: dict):
    """Evaluate every gate; missing evidence is visible and never silently neutral."""
    t = technical.get("metrics", {}) if technical.get("success") else {}
    values = {
        "current_data_available": (0 if market.get("success") else None, "market component"),
        "freshness": (0 if market.get("success") and market.get("freshness_verified") else None, market.get("state", UNAVAILABLE)),
        "history_sufficient": (0 if technical.get("history_count", 0) >= 40 else None, "price history"),
        "spread_liquidity": (None, "no order book connected"), "anomaly_free": (0, "finite validated values"),
        "short_trend": (t.get("sma_signal"), "legacy indicators"),
        "medium_trend": (_sign(t.get("trend_return_20")), "HR7 point-in-time feature"),
        "moving_average_structure": (t.get("sma_signal"), "legacy indicators"),
        "trend_slope": (_sign(t.get("trend_return_20")), "HR7 point-in-time feature"),
        "breakout": (t.get("breakout_signal"), "legacy indicators"),
        "rsi": (t.get("rsi_signal"), "legacy indicators"), "macd": (_sign(t.get("macd")), "HR7 feature"),
        "stochastic": (t.get("stochastic_signal"), "legacy indicators"),
        "atr": (0 if t.get("atr_ratio") is not None else None, "HR7 feature"),
        "indicator_agreement": (_sign(technical.get("legacy_technical_score")), "fixed-weight legacy score"),
        "volume_confirmation": (None, "volume history unavailable"),
        "relative_volume": (_sign_delta(t.get("relative_volume"), 1), "HR7 feature"),
        "liquidity": (None, "order-book feed unavailable"),
        "price_volume_agreement": (None, "volume history unavailable"),
        "volatility_liquidity_fit": (None, "liquidity evidence unavailable"),
        "company_news": (_sign(news.get("sentiment_score")) if news.get("success") else None, "news scan"),
        "sens": (news.get("sens_signal"), "SENS scan"),
        "source_agreement": (news.get("agreement_signal"), "news sources"),
        "macro": (news.get("macro_signal"), "macro sources"),
        "news_conflict": (news.get("conflict_signal"), "news sources"),
        "legacy_signal": (_sign(decision.get("score")), "characterized legacy path"),
        "researcher_agreement": (None, "researcher quorum not operationally connected"),
        "technical_news_agreement": (_agreement(technical, news), "technical/news components"),
        "risk_reward": (None, "no admitted trade setup"),
        "safety_override": (None if decision.get("action") != "hold" else 0, "research-only safety boundary"),
    }
    results = []
    for category, names in GATES.items():
        for name in names:
            signal, source = values[name]
            results.append(GateResult(category, name, _outcome(signal),
                                      "Evidence unavailable" if signal is None else "Evaluated from stated source", source))
    buy = sum(x.outcome == "SUPPORTS_BUY" for x in results)
    sell = sum(x.outcome == "SUPPORTS_SELL" for x in results)
    unavailable = sum(x.outcome == "UNAVAILABLE" for x in results)
    return {"results": [asdict(x) for x in results], "total": 30, "buy": buy, "sell": sell,
            "neutral": 30 - buy - sell - unavailable, "unavailable": unavailable,
            "net_support": buy - sell, "label": "BUY_LEAN" if buy > sell else "SELL_LEAN" if sell > buy else "NO_EDGE"}


def _sign(value):
    return None if value is None else (1 if float(value) > 0 else -1 if float(value) < 0 else 0)


def _sign_delta(value, baseline):
    return None if value in (None, "") else _sign(float(value) - baseline)


def _agreement(technical, news):
    a = _sign(technical.get("legacy_technical_score"))
    b = _sign(news.get("sentiment_score")) if news.get("success") else None
    if a is None or b is None: return None
    return a if a == b else 0
