"""Quota-governed Alpha Vantage cash-bar repair; no simulated data or orders."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
from math import isfinite
from urllib.parse import urlencode
from urllib.request import urlopen
from shadow_learning import timestamp

VERSION = "alpha-vantage-cash-repair-v1"
ACCOUNT = "market-data-alpha-vantage-v1"
DAILY_LIMIT = 20  # Reserve five free-key calls for the explicit local probe.
MINUTE_LIMIT = 5


def number(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError("invalid numeric value")
    result = float(value)
    if not isfinite(result) or result < 0 or (positive and result == 0):
        raise ValueError("invalid numeric value")
    return result


def valid_bar(row):
    try:
        o, h, l, c = (number(row[k], positive=True) for k in ("open", "high", "low", "close"))
        number(row["volume"])
        return l <= min(o, c) <= max(o, c) <= h
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


class AlphaVantageClient:
    """Shared durable budget/cache uses the existing locked repository boundary."""
    def __init__(self, repository, api_key, *, transport=None, daily_limit=DAILY_LIMIT):
        if not api_key or not api_key.strip() or api_key.strip() == "demo":
            raise ValueError("private Alpha Vantage API key required")
        self.repository, self.key = repository, api_key.strip()
        if isinstance(daily_limit, bool) or not isinstance(daily_limit, int) or not 1 <= daily_limit <= DAILY_LIMIT:
            raise ValueError("bounded daily budget required")
        self.daily_limit = daily_limit
        self.transport = transport or self._transport
        repository.create_paper_account(ACCOUNT, {"mode": "PAPER", "purpose": "DATA_CACHE_ONLY",
            "requests": [], "cache": {}, "blocked_until": None})

    def _transport(self, params):
        # Never persist/print this URL or raw transport errors: query contains key.
        with urlopen("https://www.alphavantage.co/query?" + urlencode({**params, "apikey": self.key}),
                     timeout=20) as response:
            return json.loads(response.read(2_000_000).decode())

    def request(self, params, now):
        now = timestamp(now.isoformat())
        if params.get("function") not in {"SYMBOL_SEARCH", "TIME_SERIES_DAILY"}:
            raise ValueError("unsupported function")
        if params.get("function") == "TIME_SERIES_DAILY" and params.get("outputsize") != "compact":
            raise ValueError("free compact history only")
        cache_key = sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
        with self.repository.paper_account_transaction(ACCOUNT) as state:
            cached = state["cache"].get(cache_key)
            if cached and timestamp(cached.get("created_at", cached["result"].get("retrieved_at", now.isoformat()))) > now:
                return {"state": "FUTURE_CACHE_UNAVAILABLE"}
            if cached and now < timestamp(cached["expires_at"]):
                return deepcopy(cached["result"])
            state["requests"] = [at for at in state["requests"] if now-timestamp(at) < timedelta(days=1)]
            if state.get("blocked_until") and now < timestamp(state["blocked_until"]):
                return {"state": "PROVIDER_LIMITED"}
            if len(state["requests"]) >= self.daily_limit:
                return {"state": "DAILY_BUDGET_EXHAUSTED"}
            if sum(now-timestamp(at) < timedelta(minutes=1) for at in state["requests"]) >= MINUTE_LIMIT:
                return {"state": "MINUTE_BUDGET_EXHAUSTED"}
            # Commit reservation BEFORE network; failures/restarts still consume budget.
            state["requests"].append(now.isoformat())
            state["cache"][cache_key] = {"created_at": now.isoformat(), "expires_at": (now+timedelta(minutes=2)).isoformat(),
                                         "result": {"state": "REQUEST_IN_PROGRESS"}}
        ttl = timedelta(hours=24)
        try:
            payload = self.transport(params)
            if not isinstance(payload, dict):
                raise ValueError("unexpected payload")
            if "Note" in payload or "Information" in payload:
                result = {"state": "PROVIDER_LIMITED_OR_PREMIUM_REQUIRED"}
            elif "Error Message" in payload:
                result, ttl = {"state": "SYMBOL_OR_REQUEST_UNSUPPORTED"}, timedelta(days=30)
            elif params["function"] == "SYMBOL_SEARCH":
                matches = payload.get("bestMatches")
                if not isinstance(matches, list):
                    raise ValueError("missing search results")
                # Only retain whitelisted mapping metadata, never raw provider errors.
                result = {"state": "AVAILABLE", "matches": [
                    {k: item.get(k) for k in ("1. symbol", "2. name", "3. type", "4. region", "8. currency")}
                    for item in matches[:20] if isinstance(item, dict)]}
                ttl = timedelta(days=30)
            else:
                meta, rows = payload.get("Meta Data", {}), payload.get("Time Series (Daily)")
                if not isinstance(rows, dict) or not isinstance(meta, dict):
                    raise ValueError("missing daily data")
                if meta.get("2. Symbol") != params["symbol"] or meta.get("5. Time Zone") != "Africa/Johannesburg":
                    result, ttl = {"state": "IDENTITY_OR_SESSION_UNVERIFIED"}, timedelta(days=30)
                else:
                    bars = {}
                    for date, row in sorted(rows.items())[-100:]:
                        try:
                            timestamp(date+"T00:00:00+00:00")
                            bar = {k: number(row[field], positive=k != "volume") for k, field in (
                                ("open", "1. open"), ("high", "2. high"), ("low", "3. low"),
                                ("close", "4. close"), ("volume", "5. volume"))}
                            if valid_bar(bar) and timestamp(date+"T00:00:00+00:00")+timedelta(days=1) <= now:
                                bars[date] = bar
                        except (KeyError, TypeError, ValueError, OverflowError):
                            continue
                    result = {"state": "AVAILABLE", "symbol": params["symbol"], "bars": bars,
                        "retrieved_at": now.isoformat(), "price_basis": "RAW_AS_TRADED",
                        "source_sha256": sha256(json.dumps(bars, sort_keys=True).encode()).hexdigest()}
        except Exception:
            result, ttl = {"state": "PROVIDER_UNAVAILABLE"}, timedelta(hours=1)
        with self.repository.paper_account_transaction(ACCOUNT) as state:
            state["cache"][cache_key] = {"created_at": now.isoformat(), "expires_at": (now+ttl).isoformat(), "result": result}
            if result["state"] == "PROVIDER_LIMITED_OR_PREMIUM_REQUIRED":
                state["blocked_until"] = (now+timedelta(hours=24)).isoformat()
            # Keep the cache bounded; mappings/series are cheap compared with ticks.
            if len(state["cache"]) > 100:
                oldest = sorted(state["cache"], key=lambda k: state["cache"][k]["expires_at"])
                for key in oldest[:-100]:
                    del state["cache"][key]
        return deepcopy(result)

    def discover(self, yahoo_symbol, now):
        stem = yahoo_symbol.removesuffix(".JO")
        result = self.request({"function": "SYMBOL_SEARCH", "keywords": stem}, now)
        if result["state"] != "AVAILABLE":
            return result
        matches = [item for item in result["matches"] if item.get("4. region") == "South Africa"
                   and item.get("8. currency") == "ZAR" and item.get("3. type") in {"Equity", "ETF"}
                   and str(item.get("1. symbol", "")).rsplit(".", 1)[0] == stem]
        return {"state": "VERIFIED_SEARCH_IDENTITY", "symbol": matches[0]["1. symbol"]} if len(matches) == 1 \
            else {"state": "JSE_SYMBOL_UNVERIFIED"}

    def ordered_keys(self, charts):
        """Daily batches rotate so the minute cap cannot starve later instruments."""
        keys = list(charts)
        if not keys:
            return keys
        with self.repository.paper_account_transaction(ACCOUNT) as state:
            start = state.get("rotation", 0) % len(keys)
            state["rotation"] = (start+MINUTE_LIMIT) % len(keys)
        return keys[start:]+keys[:start]


def repair_chart(client, chart, now):
    """Repair only bad same-session bars; preserve cash benchmark and valid rows."""
    repaired = deepcopy(chart)
    report = {"version": VERSION, "state": "YAHOO_VALID", "repaired_sessions": [],
              "unresolved_sessions": [], "live_execution": False}
    if chart.get("interval") != "1d" or chart.get("currency") != "ZAR" or not str(chart.get("symbol", "")).endswith(".JO"):
        report["state"] = "YAHOO_IDENTITY_UNVERIFIED"
        return repaired, report
    completed = [bar for bar in chart.get("bars", [])
                 if timestamp(bar["timestamp"][:10]+"T00:00:00+00:00")+timedelta(days=1) <= now]
    bad = [bar for bar in completed if not valid_bar(bar)]
    if not bad:
        return repaired, report
    report["unresolved_sessions"] = [bar["timestamp"][:10] for bar in bad]
    recent = {bar["timestamp"][:10] for bar in completed[-100:]}
    if not any(bar["timestamp"][:10] in recent for bar in bad):
        report["state"] = "OUTSIDE_FREE_COMPACT_WINDOW"
        return repaired, report
    mapping = client.discover(chart["symbol"], now)
    if mapping["state"] != "VERIFIED_SEARCH_IDENTITY":
        report["state"] = mapping["state"]
        return repaired, report
    data = client.request({"function": "TIME_SERIES_DAILY", "symbol": mapping["symbol"],
                           "outputsize": "compact", "datatype": "json"}, now)
    report["state"] = data["state"]
    if data["state"] != "AVAILABLE":
        return repaired, report
    for row in repaired.get("bars", []):
        date = row["timestamp"][:10]
        other = data["bars"].get(date)
        # Never guess cent/rand scales or substitute ADR/CFD prices; closes must match.
        if date in report["unresolved_sessions"] and other and abs(number(row["close"], positive=True)-other["close"]) < 1e-8:
            row.update(other)
            row["repair_source"] = {"provider": "ALPHA_VANTAGE", "symbol": mapping["symbol"],
                "source_sha256": data["source_sha256"], "retrieved_at": data["retrieved_at"],
                "price_basis": "RAW_AS_TRADED", "version": VERSION}
            report["repaired_sessions"].append(date)
    report["unresolved_sessions"] = [date for date in report["unresolved_sessions"]
                                     if date not in report["repaired_sessions"]]
    report["state"] = "REPAIRED" if report["repaired_sessions"] and not report["unresolved_sessions"] \
        else "PARTIAL_REPAIR" if report["repaired_sessions"] else "NO_MATCHING_VALID_BARS"
    return repaired, report


def configured_client(repository):
    from ai_config import project_environment
    env = project_environment()
    if env.get("ALPHA_VANTAGE_ENABLED") != "1" or not env.get("ALPHA_VANTAGE_API_KEY"):
        return None
    return AlphaVantageClient(repository, env["ALPHA_VANTAGE_API_KEY"])
