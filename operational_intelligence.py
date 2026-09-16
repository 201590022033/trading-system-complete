"""OI2 orchestration layer. Every component carries independent provenance/state."""

from __future__ import annotations

import csv
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from confidence_gates import evaluate_gates
from data_pipeline import MarketData, UnifiedDataPipeline
from instrument_registry import INSTRUMENTS, instrument_list, resolve_instrument
from signal_pipeline import legacy_technical_score

UTC = timezone.utc
DATASET = Path(__file__).parent / "analysis/data/hr7/asset_technical_features.csv"


def utcnow(): return datetime.now(UTC)


@dataclass
class ComponentResult:
    component: str
    success: bool
    state: str
    source: str
    source_timestamp: str | None
    retrieved_at: str
    data: dict = field(default_factory=dict)
    reason: str | None = None
    version: str = "oi2-v1"

    def to_dict(self): return asdict(self)


@dataclass
class AnalysisRun:
    run_id: str
    instrument: dict
    horizon: str
    started_at: str
    completed_at: str
    components: dict
    decision: dict
    gates: dict
    overall_state: str

    def to_dict(self): return asdict(self)


class OperationalIntelligence:
    def __init__(self):
        self._lock = threading.Lock()
        self._rows = None
        self.runs = {}

    def _load_rows(self):
        with self._lock:
            if self._rows is None:
                with DATASET.open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self._rows = {key: [r for r in rows if r["instrument"] == item.research_symbol]
                              for key, item in INSTRUMENTS.items()}
        return self._rows

    def _causal_rows(self, symbol, as_of=None, observation_context=None):
        """Select inputs, not scores. Missing availability never implies availability."""
        item = resolve_instrument(symbol)
        rows = (observation_context["history"] if observation_context is not None
                else self._load_rows()[item.instrument_id])
        if as_of is None:
            return rows
        from shadow_learning import timestamp
        cutoff = timestamp(as_of)
        selected = []
        for row in rows:
            if row.get("instrument") not in {item.instrument_id, item.research_symbol}:
                raise ValueError("cross-instrument observation history")
            if not row.get("available_time") or not row.get("event_time"):
                continue
            if timestamp(row["event_time"]) <= cutoff and timestamp(row["available_time"]) <= cutoff:
                selected.append(row)
        return sorted(selected, key=lambda row: timestamp(row["event_time"]))

    def market(self, symbol, provider="historical", *, as_of=None, observation_context=None):
        item = resolve_instrument(symbol)
        now = utcnow().isoformat()
        if provider == "yahoo":
            from dashboard_feeds import feeds
            snapshot = feeds.chart(symbol, "1d")
            data = snapshot.get("data") or {}
            usable = snapshot["state"] == "AVAILABLE"
            return ComponentResult("market", usable,
                                   snapshot["data_state"] if usable else snapshot["state"],
                                   snapshot["source"], data.get("source_timestamp"), now,
                                   {"price": data.get("price"), "currency": data.get("currency"),
                                    "symbol": item.yahoo_symbol, "last_success": snapshot["last_success"]},
                                   snapshot.get("error") or snapshot["note"]).to_dict()
        if provider != "historical":
            return ComponentResult("market", False, "UNAVAILABLE", provider, None, now,
                                   reason="Unsupported provider").to_dict()
        rows = self._causal_rows(symbol, as_of, observation_context)
        if not rows:
            return ComponentResult("market", False, "UNAVAILABLE", str(DATASET), None, now,
                                   reason="No point-in-time history").to_dict()
        last = rows[-1]
        return ComponentResult("market", True, "HISTORICAL", "HR7 frozen point-in-time dataset",
                               last["event_time"], now,
                               {"price": float(last["close"]), "currency": "ZAR",
                                "history_count": len(rows), "available_time": last["available_time"],
                                "feature_version": last["feature_version"]}).to_dict()

    def technical(self, symbol, *, as_of=None, observation_context=None):
        item = resolve_instrument(symbol); now = utcnow().isoformat()
        rows = self._causal_rows(symbol, as_of, observation_context)
        if len(rows) < 20:
            return ComponentResult("technical", False, "INSUFFICIENT_DATA", "HR7 frozen point-in-time dataset",
                                   None, now, reason="At least 20 observations required").to_dict()
        pipe = UnifiedDataPipeline(jse_tickers=[item.research_symbol], buffer_size=max(100, len(rows)))
        for row in rows:
            price = float(row["close"])
            pipe.add_market_data(MarketData(item.research_symbol, price, datetime.fromisoformat(row["event_time"]), vwap=price))
        observation = pipe.get_observation(item.research_symbol)
        indicators = observation.indicators
        score = legacy_technical_score(observation)
        last = rows[-1]
        metric_names = ("rsi", "macd", "stochastic", "atr_ratio", "adx", "relative_volume",
                        "trend_return_20", "realized_volatility_20")
        metrics = {name: _number(last.get(name)) for name in metric_names}
        metrics.update({"rsi_signal": indicators.rsi_signal, "sma_fast": indicators.sma_fast,
                        "sma_slow": indicators.sma_slow, "sma_signal": indicators.sma_signal,
                        "breakout_signal": indicators.breakout_signal,
                        "stochastic_signal": indicators.stochastic_signal})
        data = {"metrics": metrics, "legacy_technical_score": score, "history_count": len(rows),
                "recent_prices": [float(r["close"]) for r in rows[-40:]]}
        return ComponentResult("technical", True, "HISTORICAL", "HR7 data + legacy_technical_score",
                               last["event_time"], now, data).to_dict()

    def news(self, symbol, allow_network=False):
        item = resolve_instrument(symbol); now = utcnow().isoformat()
        if not allow_network:
            return ComponentResult("news", False, "UNAVAILABLE", "SENS and Moneyweb public feeds",
                                   None, now, reason="Network scan not requested; no fabricated fallback").to_dict()
        from dashboard_feeds import feeds
        snapshot = feeds.news()
        report = snapshot.get("data") or {}
        matched = [n for n in report.get("items", [])
                   if any(a["name"] == item.research_symbol for a in n.get("assets", []))]
        score = report.get("tickers", {}).get(item.research_symbol, {}).get("score", 0.0)
        success = snapshot["state"] in {"AVAILABLE", "PARTIAL"} and report.get("feed_state") != "UNAVAILABLE"
        return ComponentResult("news", success, "CURRENT_PUBLIC" if success else snapshot["state"],
                               snapshot["source"], None, now,
                               {"items": matched, "sentiment_score": score,
                                "macro": report.get("macro", {}), "llm_used": report.get("llm_used", False),
                                "analysis_method": report.get("analysis_method", "Loading"),
                                "sens_signal": None, "agreement_signal": None, "macro_signal": None,
                                "conflict_signal": None},
                               snapshot.get("error") or ("News scan in progress" if snapshot["refreshing"] else
                               "See market-wide news stream for macro headlines and publication timestamps")).to_dict()

    def analyze(self, symbol, horizon="swing", provider="historical", allow_network=False,
                *, as_of=None, observation_context=None):
        started = utcnow(); item = resolve_instrument(symbol)
        if as_of is not None:
            from shadow_learning import timestamp
            timestamp(as_of)
            if provider != "historical" or allow_network:
                raise ValueError("as-of analysis requires causal historical inputs")
            market = self.market(symbol, provider, as_of=as_of, observation_context=observation_context)
            technical = self.technical(symbol, as_of=as_of, observation_context=observation_context)
        else:
            market = self.market(symbol, provider); technical = self.technical(symbol)
        news = self.news(symbol, allow_network)
        tech_score = technical.get("data", {}).get("legacy_technical_score", 0.0)
        sentiment = news.get("data", {}).get("sentiment_score", 0.0) if news["success"] else 0.0
        score = .60 * tech_score + .30 * sentiment
        action = "buy" if score > .35 else "sell" if score < -.35 else "hold"
        decision = {"action": action, "score": round(score, 4), "technical_score": tech_score,
                    "sentiment_score": sentiment, "macro_adjustment": 0.0,
                    "strategy": "characterized-legacy-v1", "state": "RESEARCH",
                    "actionable": False, "reason": "Legacy benchmark; not admitted for execution"}
        flat_technical = {**technical.get("data", {}), "success": technical["success"]}
        flat_news = {**news.get("data", {}), "success": news["success"]}
        gates = evaluate_gates(market, flat_technical, flat_news, decision)
        states = {market["state"], technical["state"], news["state"]}
        overall = "PARTIAL" if not all(x["success"] for x in (market, technical, news)) else (
            "HISTORICAL" if states == {"HISTORICAL"} else "MIXED")
        run = AnalysisRun(uuid.uuid4().hex, item.to_dict(), horizon, started.isoformat(), utcnow().isoformat(),
                          {"market": market, "technical": technical, "news": news}, decision, gates, overall)
        self.runs[run.run_id] = run
        return run.to_dict()

    def scan(self, horizon="swing"):
        runs = [self.analyze(key, horizon) for key in INSTRUMENTS]
        return sorted(runs, key=lambda x: abs(x["decision"]["score"]), reverse=True)

    def status(self):
        rows = self._load_rows()
        return {"service": "operational", "live_execution": False, "default_data_state": "HISTORICAL",
                "dataset": {"available": DATASET.exists(), "rows": sum(map(len, rows.values())),
                            "instruments": len(rows)}, "providers": {"historical": "AVAILABLE",
                            "yahoo": "CACHED_PUBLIC_FEED", "sens_moneyweb": "CACHED_SENTIMENT_FEED", "broker": "DISABLED"},
                "timestamp": utcnow().isoformat()}


def _number(value):
    try: return float(value) if value not in (None, "") else None
    except (TypeError, ValueError): return None


service = OperationalIntelligence()
