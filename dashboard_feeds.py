"""Shared, bounded public-feed cache for the existing dashboard adapters.

HTTP reads never wait for providers or an LLM. A single job per cache key
refreshes data, keeping last-good results visible on failure. No broker calls.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from time import monotonic

from instrument_registry import resolve_instrument


class DashboardFeeds:
    def __init__(self, chart_fetcher=None, scanner=None):
        self._chart_fetcher = chart_fetcher
        self._scanner = scanner
        self._lock = Lock()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="public-feed")
        self._entries = {}

    def _snapshot(self, key, ttl, loader):
        with self._lock:
            entry = self._entries.setdefault(key, {"data": None, "last_success": None,
                                                   "last_attempt": None, "next_poll": 0,
                                                   "refreshing": False, "error": None})
            if not entry["refreshing"] and monotonic() >= entry["next_poll"]:
                entry["refreshing"] = True
                entry["last_attempt"] = datetime.now(timezone.utc).isoformat()
                self._pool.submit(self._refresh, key, ttl, loader)
            result = deepcopy(entry)
        result.pop("next_poll")
        result["refresh_seconds"] = ttl
        result["state"] = ("STALE" if result["data"] and result["error"] else
                           "AVAILABLE" if result["data"] else
                           "UNAVAILABLE" if result["error"] else "LOADING")
        return result

    def _refresh(self, key, ttl, loader):
        try:
            data = loader()
            error = None
        except Exception as exc:
            # Never serialize provider exceptions containing request URLs/keys.
            data = None
            error = f"Provider refresh failed ({type(exc).__name__}); retrying automatically."
        with self._lock:
            entry = self._entries[key]
            if data is not None:
                entry["data"] = data
                if data.get("feed_state") == "UNAVAILABLE":
                    error = "News sources returned no usable feed; retained headlines may be stale."
                else:
                    entry["last_success"] = datetime.now(timezone.utc).isoformat()
            entry.update(error=error, refreshing=False, next_poll=monotonic() + ttl)

    def chart(self, symbol, period="3mo"):
        if period not in {"1d", "1mo", "3mo", "1y"}:
            raise ValueError("Choose 1d, 1mo, 3mo or 1y")
        yahoo_symbol = "^J203.JO" if symbol == "JSE" else resolve_instrument(symbol).yahoo_symbol

        def load():
            from jse_adapter import YahooFinanceFetcher
            fetcher = self._chart_fetcher or YahooFinanceFetcher()
            return fetcher.get_chart(yahoo_symbol, period)

        result = self._snapshot((yahoo_symbol, period), 60 if period == "1d" else 300, load)
        result.update(source="Yahoo Finance", symbol=symbol, provider_symbol=yahoo_symbol,
                      data_state="DELAYED_PUBLIC", note="Public bars may be delayed. Daily timestamps are session dates; intraday timestamps are bar starts. No ticks are simulated.")
        if result["data"]:
            stamp = datetime.fromisoformat(result["data"]["source_timestamp"])
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - stamp).total_seconds()
            if age > (1800 if period == "1d" else 4 * 86400):
                result["data_state"] = "STALE_OR_MARKET_CLOSED"
        return result

    def news(self):
        def load():
            from sentiment_analyzer import MacroSentimentScanner
            if self._scanner is None:
                self._scanner = MacroSentimentScanner(max_llm_items=8, retain_items=True)
            def publish(preview):
                data = self._news_report(preview)
                data["ai_pending"] = self._scanner.use_llm
                with self._lock:
                    self._entries["news"]["data"] = data

            report = self._scanner.scan(moneyweb_limit=20, sens_limit=15, on_progress=publish)
            return self._news_report(report)

        result = self._snapshot("news", 300, load)
        result.update(source="Moneyweb / SENS / configured NewsAPI", data_state="PUBLIC_NEWS")
        if result["data"] and result["data"]["feed_state"] == "UNAVAILABLE":
            result["state"] = "STALE" if result["data"]["items"] else "UNAVAILABLE"
            result["error"] = "Sources returned no new usable feed; retained headlines may be stale."
        elif result["data"] and result["data"]["feed_state"] == "PARTIAL":
            result["state"] = "PARTIAL" if not result["error"] else "STALE"
        return result

    def _news_report(self, result):
        report = result.to_dict()
        report["sources"] = dict(self._scanner.source_status)
        report["ai_available"] = self._scanner.use_llm
        report["ai_providers"] = self._scanner.providers.statuses()
        report["analysis_method"] = "AI + keyword fallback" if report["llm_used"] else "Keyword fallback (no successful AI analysis)"
        report["feed_state"] = ("PARTIAL" if any(v == "AVAILABLE" for v in report["sources"].values())
                                 and any(v not in {"AVAILABLE", "NOT_CONFIGURED"} for v in report["sources"].values())
                                 else "AVAILABLE" if any(v == "AVAILABLE" for v in report["sources"].values())
                                 else "UNAVAILABLE")
        return report


feeds = DashboardFeeds()
