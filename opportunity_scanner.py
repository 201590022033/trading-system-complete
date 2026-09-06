"""Current-data opportunity discovery for the OI3 dashboard.

This is deliberately separate from the frozen HR7 benchmark and the six-card
baseline watchlist. It ranks a permitted public JSE universe using available
Yahoo bars and the shared news report; it never creates an executable order.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from jse_adapter import JSE_TICKERS, YahooFinanceFetcher


# Broad public universe used for discovery, not a recommendation list.
DISCOVERY_UNIVERSE = {
    key: value for key, value in JSE_TICKERS.items()
    if key not in {"JSE"}
}


def _rsi(closes, period=14):
    if len(closes) <= period:
        return None
    gains, losses = [], []
    for previous, current in zip(closes[-period - 1:-1], closes[-period:]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    average_gain = sum(gains) / period
    average_loss = sum(losses) / period
    if average_loss == 0:
        return 100.0
    return 100 - (100 / (1 + average_gain / average_loss))


def _candidate(key, metadata, fetcher, news_tickers):
    try:
        chart = fetcher.get_chart(metadata["yahoo_symbol"], "3mo")
        closes = [bar["close"] for bar in chart["bars"]]
        if len(closes) < 21:
            return {"symbol": key, "name": metadata["name"], "state": "INSUFFICIENT_DATA",
                    "reason": "At least 21 public daily bars are required", "evidence": []}
        momentum = (closes[-1] / closes[-21] - 1) * 100
        rsi = _rsi(closes)
        news = news_tickers.get(key) or news_tickers.get(metadata.get("research_symbol", ""))
        news_score = float(news.get("score", 0)) if news else 0.0
        technical_score = max(-1.0, min(1.0, momentum / 10))
        combined = 0.7 * technical_score + 0.3 * news_score
        evidence = ["Yahoo 3-month daily bars"]
        if news:
            evidence.append(f"{news.get('mentions', 0)} current public news mention(s)")
        return {"symbol": key, "name": metadata["name"], "sector": metadata.get("sector"),
                "yahoo_symbol": metadata["yahoo_symbol"], "price": closes[-1],
                "momentum_20d_pct": round(momentum, 2), "rsi_14": round(rsi, 2) if rsi is not None else None,
                "technical_score": round(technical_score, 3), "news_score": round(news_score, 3),
                "combined_score": round(combined, 3), "news_mentions": news.get("mentions", 0) if news else 0,
                "state": "NEWS_AND_TECHNICAL" if news else "TECHNICAL_ONLY", "evidence": evidence,
                "as_of": chart.get("source_timestamp")}
    except Exception as exc:
        return {"symbol": key, "name": metadata["name"], "state": "UNAVAILABLE",
                "reason": f"Public data unavailable ({type(exc).__name__})", "evidence": []}


def discover(news_report=None, universe=None, fetcher=None):
    universe = universe or DISCOVERY_UNIVERSE
    fetcher = fetcher or YahooFinanceFetcher()
    news_tickers = (news_report or {}).get("tickers", {})
    results = []
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="opportunity") as pool:
        futures = [pool.submit(_candidate, key, metadata, fetcher, news_tickers)
                   for key, metadata in universe.items()]
        for future in as_completed(futures):
            results.append(future.result())
    available = [row for row in results if row["state"] not in {"UNAVAILABLE", "INSUFFICIENT_DATA"}]
    available.sort(key=lambda row: abs(row.get("combined_score", 0)), reverse=True)
    unavailable = [row for row in results if row not in available]
    return {"updated_at": datetime.now(timezone.utc).isoformat(),
            "universe_size": len(universe), "scanned": len(results),
            "opportunities": available[:10], "other_results": available[10:],
            "unavailable": unavailable, "execution_enabled": False,
            "method": "Yahoo public daily technicals plus current public-news impacts; research-only"}
