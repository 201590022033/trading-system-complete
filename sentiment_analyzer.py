"""LLM-powered sentiment analyzer for South African market news.

Reads each headline (Moneyweb, SENS, NewsAPI, Reddit...) and produces
structured impact records:
  - which assets are affected (ZAR, GOLD, OIL, PLATINUM, EMERGING_MARKETS,
    or specific JSE tickers like NPN / SASOL / BTI)
  - direction (-1 negative, +1 positive) and strength (0.0-1.0)
  - a one-line summary

Company-name -> ticker alias detection is deterministic (no LLM needed).
Direction/strength comprehension uses the local Ollama LLM when available,
falling back to a keyword scorer when it isn't.
"""

from __future__ import annotations

import json
import os
import re
import socket
import importlib.util
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from data_pipeline import NewsItem, SentimentLabel
from jse_adapter import JSEDataAdapter, DataSourceType


# =========================
# Asset universe
# =========================

MACRO_ASSETS = ["ZAR", "GOLD", "OIL", "PLATINUM", "EMERGING_MARKETS"]

MACRO_KEYWORDS = {
    "ZAR": [
        "rand", "zar", "usd/zar", "usd zar", "exchange rate", "currency",
        "sarb", "reserve bank", "repo rate", "interest rate", "inflation",
        "south africa", "jse",
    ],
    "GOLD": ["gold", "bullion"],
    "OIL": ["oil", "brent", "crude", "opec", "petrol price", "fuel price"],
    "PLATINUM": ["platinum", "pgm", "palladium"],
    "EMERGING_MARKETS": [
        "emerging market", "brics", "developing econom", "africa",
        "load shedding", "eskom", "sovereign rating", "downgrade",
    ],
}

# Company-name / alias -> internal ticker key (as used in JSE_TICKERS where possible)
TICKER_ALIASES = {
    "NPN": ["naspers"],
    "PRX": ["prosus"],
    "SASOL": ["sasol"],
    "BHP": ["bhp"],
    "IMPJ": ["impala platinum", "implats"],
    "SHPJ": ["shoprite"],
    "ABSPJ": ["absa"],
    "TFMJ": ["foschini", "tfg"],
    "BTI": ["british american tobacco"],
    "AGL": ["anglo american"],
    "SBK": ["standard bank"],
    "FSR": ["firstrand", "first rand", "fnb"],
    "NED": ["nedbank"],
    "VOD": ["vodacom"],
    "MTN": ["mtn"],
    "GFI": ["gold fields"],
    "KIO": ["kumba iron"],
    "REM": ["remgro"],
    "CFR": ["richemont"],
}


# =========================
# Result structures
# =========================

@dataclass
class AssetImpact:
    name: str          # "ZAR", "GOLD", "NPN", ...
    direction: int     # -1, 0, +1
    strength: float    # 0.0 - 1.0


@dataclass
class AnalyzedItem:
    headline: str
    source: str
    timestamp: str
    summary: str
    sentiment: str
    score: float                       # -1.0 .. 1.0
    assets: List[AssetImpact] = field(default_factory=list)
    llm_used: bool = False
    url: str = ""
    timestamp_kind: str = "published"


@dataclass
class MacroReport:
    updated_at: str
    llm_used: bool
    macro: Dict[str, Dict]             # asset -> {score, mentions}
    tickers: Dict[str, Dict]           # ticker -> {score, mentions, headlines}
    items: List[AnalyzedItem]

    def to_dict(self) -> Dict:
        return {
            "updated_at": self.updated_at,
            "llm_used": self.llm_used,
            "macro": self.macro,
            "tickers": self.tickers,
            "items": [
                {
                    "headline": i.headline,
                    "source": i.source,
                    "timestamp": i.timestamp,
                    "summary": i.summary,
                    "sentiment": i.sentiment,
                    "score": round(i.score, 2),
                    "llm_used": i.llm_used,
                    "url": i.url,
                    "timestamp_kind": i.timestamp_kind,
                    "assets": [
                        {"name": a.name, "direction": a.direction, "strength": round(a.strength, 2)}
                        for a in i.assets
                    ],
                }
                for i in self.items
            ],
        }


# =========================
# LLM availability (cloud key first, then local service)
# =========================

_OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "").strip()
_CLOUD_MODEL = os.environ.get("OLLAMA_CLOUD_MODEL", "gpt-oss:20b-cloud")
_LOCAL_MODEL = os.environ.get("OLLAMA_LOCAL_MODEL", "llama3")


def _ollama_available() -> bool:
    if importlib.util.find_spec("ollama") is None:
        return False
    if _OLLAMA_API_KEY:
        return True
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            return True
    except OSError:
        return False


_ollama_client = None


def _get_ollama():
    global _ollama_client
    if _ollama_client is None:
        import ollama
        if _OLLAMA_API_KEY:
            _ollama_client = ollama.Client(
                host="https://ollama.com",
                headers={"Authorization": f"Bearer {_OLLAMA_API_KEY}"},
                timeout=60,
            )
        else:
            _ollama_client = ollama.Client(timeout=45)
    return _ollama_client


# =========================
# Deterministic mention detection (no LLM needed)
# =========================

def detect_mentions(text: str) -> List[AssetImpact]:
    """Find which macro assets and JSE tickers a text mentions."""
    low = f" {text.lower()} "
    impacts: List[AssetImpact] = []

    for asset, keywords in MACRO_KEYWORDS.items():
        if any(k in low for k in keywords):
            impacts.append(AssetImpact(name=asset, direction=0, strength=0.4))

    for ticker, aliases in TICKER_ALIASES.items():
        if any(a in low for a in aliases):
            impacts.append(AssetImpact(name=ticker, direction=0, strength=0.5))

    return impacts


# =========================
# Scoring
# =========================

_BULLISH = [
    "rise", "surge", "jump", "gain", "profit", "beat", "strong", "boost",
    "invest", "growth", "positive", "upgrade", "opportunity", "bullish",
    "outperform", "record", "rally", "recovery", "strengthen",
]
_BEARISH = [
    "fall", "drop", "decline", "loss", "miss", "weak", "downgrade", "risk",
    "concern", "bearish", "underperform", "struggle", "challenge", "slump",
    "crash", "plunge", "weaken", "pressure", "crisis",
]


def _keyword_score(text: str) -> float:
    low = text.lower()
    bull = sum(1 for w in _BULLISH if w in low)
    bear = sum(1 for w in _BEARISH if w in low)
    if bull == bear:
        return 0.0
    total = bull + bear
    return round((bull - bear) / total, 2)


_LLM_PROMPT = """You are a South African financial market analyst.

Read this news item and return ONLY valid JSON, nothing else.

HEADLINE: {headline}
SOURCE: {source}
TEXT: {text}

JSON schema:
{{
  "summary": "<one short sentence about the market impact>",
  "sentiment": "<bullish|bearish|neutral>",
  "score": <float -1.0 to 1.0, overall market impact>,
  "assets": [
    {{"name": "<ZAR|GOLD|OIL|PLATINUM|EMERGING_MARKETS or JSE ticker like NPN, SOL, BTI>",
      "direction": <-1, 0 or 1>,
      "strength": <float 0.0 to 1.0>}}
  ]
}}

Rules:
- Only include assets actually affected by the news.
- ZAR = South African rand, currency, SARB, interest rates, SA inflation.
- Use direction 0 only if the mention is neutral/factual.
- If nothing is affected, return an empty assets list.
"""


def _llm_analyze(headline: str, source: str, text: str) -> Optional[Dict]:
    """Ask the local LLM to read the item. Returns parsed dict or None."""
    try:
        client = _get_ollama()
        model = _CLOUD_MODEL if _OLLAMA_API_KEY else _LOCAL_MODEL
        response = client.generate(
            model=model,
            prompt=_LLM_PROMPT.format(headline=headline, source=source, text=text[:800]),
        )
        raw = response.get("response", "")
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return None
        data = json.loads(match.group(0))
        if not isinstance(data, dict):
            return None
        return data
    except Exception as exc:
        print(f"[SENTIMENT] LLM analysis failed ({type(exc).__name__}); using keywords")
        return None


# Alias that maps LLM-returned tickers (SOL, ABG, IMP...) to internal keys
_LLM_TICKER_MAP = {
    "SOL": "SASOL", "SSL": "SASOL",
    "ABG": "ABSPJ", "ABSP": "ABSPJ",
    "IMP": "IMPJ",
    "SHP": "SHPJ",
    "TFG": "TFMJ", "TFM": "TFMJ",
    "BHG": "BHP",
}


def analyze_item(item: NewsItem, use_llm: bool) -> AnalyzedItem:
    """Full analysis of one news item: mentions + direction/strength."""
    text = f"{item.headline} {getattr(item, 'text', '') or ''}"
    llm_used = False
    summary = item.headline
    sentiment = item.sentiment_label.value if item.sentiment_label else "neutral"
    score = item.sentiment_score or 0.0

    # Deterministic mentions always run
    impacts = detect_mentions(text)

    if use_llm:
        data = _llm_analyze(item.headline, item.source, getattr(item, "text", "") or "")
        if data:
            llm_used = True
            summary = str(data.get("summary") or item.headline)[:200]
            sentiment = str(data.get("sentiment") or sentiment).lower()
            try:
                score = max(-1.0, min(1.0, float(data.get("score", 0.0))))
            except (TypeError, ValueError):
                score = 0.0
            llm_impacts: List[AssetImpact] = []
            for a in data.get("assets", []) or []:
                try:
                    name = str(a.get("name", "")).upper().strip()
                    name = _LLM_TICKER_MAP.get(name, name)
                    direction = int(a.get("direction", 0))
                    direction = 1 if direction > 0 else (-1 if direction < 0 else 0)
                    strength = max(0.0, min(1.0, float(a.get("strength", 0.5))))
                    if name:
                        llm_impacts.append(AssetImpact(name, direction, strength))
                except (TypeError, ValueError):
                    continue
            if llm_impacts:
                impacts = llm_impacts

    if not llm_used:
        # Keyword fallback: apply one direction to every mention
        score = _keyword_score(text)
        direction = 1 if score > 0.1 else (-1 if score < -0.1 else 0)
        for imp in impacts:
            imp.direction = direction
            imp.strength = min(0.9, abs(score) + 0.2)
        sentiment = "bullish" if score > 0.1 else ("bearish" if score < -0.1 else "neutral")

    return AnalyzedItem(
        headline=item.headline,
        source=item.source,
        timestamp=item.timestamp.isoformat() if hasattr(item.timestamp, "isoformat") else str(item.timestamp),
        summary=summary,
        sentiment=sentiment,
        score=score,
        assets=impacts,
        llm_used=llm_used,
        url=getattr(item, "url", "") or next(iter(re.findall(r"https?://[^\s<>]+", getattr(item, "text", ""))), ""),
        timestamp_kind=getattr(item, "timestamp_kind", "published"),
    )


# =========================
# Scanner
# =========================

class MacroSentimentScanner:
    """Fetches SA + global headlines and builds a macro/ticker sentiment report."""

    def __init__(self, max_llm_items: int = 8, retain_items: bool = False):
        self.adapter = JSEDataAdapter(
            price_source=DataSourceType.MOCK,   # we only need its news fetchers
            news_source="mock",
        )
        self.use_llm = _ollama_available()
        self.max_llm_items = max_llm_items
        self._seen_headlines = set()
        self.retain_items = retain_items
        self._analyzed_cache = {}
        self.source_status = {}
        self.newsapi_key = os.environ.get("NEWSAPI_KEY", "").strip()

    # Global macro queries that move the Rand / commodities / SA sentiment
    GLOBAL_QUERIES = [
        "South Africa rand OR ZAR OR SARB",
        "gold price OR platinum price",
        "oil price OR Brent crude OR OPEC",
        "emerging markets OR BRICS",
    ]

    def _fetch_global_newsapi(self, limit: int = 8) -> List[NewsItem]:
        """Global headlines from NewsAPI (requires free NEWSAPI_KEY in .env)."""
        if not self.newsapi_key:
            self.source_status["NewsAPI"] = "NOT_CONFIGURED"
            return []
        import requests
        items: List[NewsItem] = []
        per_query = max(1, limit // len(self.GLOBAL_QUERIES))
        for q in self.GLOBAL_QUERIES:
            try:
                resp = requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": q,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": per_query,
                        "apiKey": self.newsapi_key,
                    },
                    timeout=12,
                )
                if resp.status_code >= 400:
                    print(f"[SENTIMENT] NewsAPI {resp.status_code} for '{q[:30]}'")
                    continue
                for art in resp.json().get("articles", []):
                    title = art.get("title") or ""
                    if not title or title == "[Removed]":
                        continue
                    items.append(NewsItem(
                        ticker="JSE",
                        headline=title,
                        source=f"NewsAPI/{(art.get('source') or {}).get('name', 'global')}",
                        timestamp=datetime.fromisoformat(
                            art.get("publishedAt", "").replace("Z", "+00:00")
                        ) if art.get("publishedAt") else datetime.now(),
                        sentiment_label=SentimentLabel.NEUTRAL,
                        sentiment_score=0.0,
                        text=(art.get("description") or "")[:300],
                        url=art.get("url") or "",
                        timestamp_kind="published" if art.get("publishedAt") else "observed; publication time unavailable",
                    ))
            except Exception as exc:
                print(f"[SENTIMENT] NewsAPI fetch failed ({type(exc).__name__})")
        self.source_status["NewsAPI"] = "AVAILABLE" if items else "EMPTY_OR_UNAVAILABLE"
        return items

    def _fetch(self, moneyweb_limit: int, sens_limit: int) -> List[NewsItem]:
        items: List[NewsItem] = []
        try:
            fetched = self.adapter.get_moneyweb_news(limit=moneyweb_limit)
            items.extend(fetched)
            self.source_status["Moneyweb"] = "AVAILABLE" if fetched else "EMPTY_OR_UNAVAILABLE"
        except Exception as exc:
            self.source_status["Moneyweb"] = "UNAVAILABLE"
        try:
            fetched = self.adapter.get_sens_news(limit=sens_limit)
            items.extend(fetched)
            self.source_status["SENS"] = "AVAILABLE" if fetched else "EMPTY_OR_UNAVAILABLE"
            if not fetched and self.adapter.sens_fetcher.last_status.startswith("HTTP_"):
                self.source_status["SENS"] = self.adapter.sens_fetcher.last_status
        except Exception as exc:
            self.source_status["SENS"] = "UNAVAILABLE"
        items.extend(self._fetch_global_newsapi(limit=8))

        fresh = []
        batch_seen = set()
        for it in items:
            key = it.headline.strip().lower()
            if key and key not in batch_seen and (self.retain_items or key not in self._seen_headlines):
                batch_seen.add(key)
                self._seen_headlines.add(key)
                fresh.append(it)
        if self.retain_items:
            self._seen_headlines = batch_seen
        return fresh

    def scan(self, moneyweb_limit: int = 12, sens_limit: int = 8, on_progress=None) -> MacroReport:
        raw_items = self._fetch(moneyweb_limit, sens_limit)

        if on_progress is not None:
            # Publish usable headlines before potentially slow model requests.
            preview = {it.headline.strip().lower():
                       self._analyzed_cache.get(it.headline.strip().lower()) or analyze_item(it, False)
                       for it in raw_items}
            preview.update({k: v for k, v in self._analyzed_cache.items() if k not in preview})
            on_progress(self._report(list(preview.values())[:100]))

        analyzed: List[AnalyzedItem] = []
        llm_budget = self.max_llm_items if self.use_llm else 0
        for item in raw_items:
            key = item.headline.strip().lower()
            cached = self._analyzed_cache.get(key) if self.retain_items else None
            if cached is not None:
                analyzed.append(cached)
                continue
            use_llm_now = llm_budget > 0
            result = analyze_item(item, use_llm=use_llm_now)
            if use_llm_now:
                llm_budget -= 1
            analyzed.append(result)

        if self.retain_items:
            # Keep up to 100 headlines across polls; duplicates never consume AI budget.
            current = {i.headline.strip().lower(): i for i in analyzed}
            current.update({k: v for k, v in self._analyzed_cache.items() if k not in current})
            self._analyzed_cache = dict(list(current.items())[:100])
            analyzed = list(self._analyzed_cache.values())

        return self._report(analyzed)

    @staticmethod
    def _report(analyzed: List[AnalyzedItem]) -> MacroReport:

        # Aggregate macro asset scores
        macro: Dict[str, Dict] = {}
        for asset in MACRO_ASSETS:
            vals = [i for a in analyzed for i in a.assets if i.name == asset]
            if vals:
                score = sum(v.direction * v.strength for v in vals) / len(vals)
                macro[asset] = {"score": round(max(-1.0, min(1.0, score)), 2), "mentions": len(vals)}
            else:
                macro[asset] = {"score": 0.0, "mentions": 0}

        # Aggregate per-ticker scores
        tickers: Dict[str, Dict] = {}
        for a in analyzed:
            for imp in a.assets:
                if imp.name in MACRO_ASSETS:
                    continue
                entry = tickers.setdefault(imp.name, {"score": 0.0, "mentions": 0, "headlines": []})
                entry["mentions"] += 1
                entry["headlines"].append(a.headline[:120])
        for name, entry in tickers.items():
            vals = [imp for a in analyzed for imp in a.assets if imp.name == name]
            if vals:
                entry["score"] = round(
                    max(-1.0, min(1.0, sum(v.direction * v.strength for v in vals) / len(vals))), 2
                )
            entry["headlines"] = entry["headlines"][:3]

        return MacroReport(
            updated_at=datetime.now().strftime("%H:%M:%S"),
            llm_used=any(a.llm_used for a in analyzed),
            macro=macro,
            tickers=dict(sorted(tickers.items(), key=lambda kv: -abs(kv[1]["score"]))),
            items=analyzed,
        )
