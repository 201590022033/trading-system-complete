"""Freeze permitted public daily historical series for HR2 research."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf


RECONSTRUCTION_VERSION = "hr2-yahoo-daily-v1"
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "analysis" / "data" / "hr2"
RESULTS_DIR = ROOT / "analysis" / "results"


@dataclass(frozen=True)
class SeriesSpec:
    instrument: str
    symbol: str
    asset_class: str
    sector: str
    profile: str
    role: str


SERIES = (
    SeriesSpec("NPN", "NPN.JO", "equity", "offshore_earner", "offshore_earner", "jse_ohlcv"),
    SeriesSpec("SASOL", "SOL.JO", "equity", "energy", "energy_sasol", "jse_ohlcv"),
    SeriesSpec("BHP", "BHG.JO", "equity", "diversified_mining", "diversified_mining", "jse_ohlcv"),
    SeriesSpec("IMPJ", "IMP.JO", "equity", "pgm_mining", "pgm_mining", "jse_ohlcv"),
    SeriesSpec("SHPJ", "SHP.JO", "equity", "retail_consumer", "retail_consumer", "jse_ohlcv"),
    SeriesSpec("ABSPJ", "ABG.JO", "equity", "banks_financials", "banks_financials", "jse_ohlcv"),
    SeriesSpec("JSE_ALL_SHARE_PROXY", "^J203.JO", "equity_index", "broad_market", "jse_index", "jse_broad_market"),
    SeriesSpec("USDZAR", "ZAR=X", "fx", "fx", "usdzar", "rand"),
    SeriesSpec("VIX", "^VIX", "volatility_index", "global_risk", "global_risk", "global_risk"),
    SeriesSpec("SP500", "^GSPC", "equity_index", "global_equity", "global_risk", "global_risk"),
    SeriesSpec("DXY", "DX-Y.NYB", "currency_index", "global_fx", "global_risk", "usd"),
    SeriesSpec("US10Y", "^TNX", "yield_proxy", "rates", "global_rates", "nominal_yield"),
    SeriesSpec("BRENT", "BZ=F", "commodity_future", "energy", "commodity", "brent"),
    SeriesSpec("GOLD", "GC=F", "commodity_future", "precious_metals", "commodity", "gold"),
    SeriesSpec("PLATINUM", "PL=F", "commodity_future", "pgm", "commodity", "platinum"),
    SeriesSpec("PALLADIUM", "PA=F", "commodity_future", "pgm", "commodity", "palladium"),
)


def normalize_history(frame: pd.DataFrame, retrieval_time: datetime) -> pd.DataFrame:
    """Normalize one-symbol daily history without filling missing observations."""
    if retrieval_time.tzinfo is None:
        raise ValueError("retrieval_time must be timezone-aware")
    if isinstance(frame.columns, pd.MultiIndex):
        frame = frame.droplevel(-1, axis=1)
    required = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(f"missing OHLCV columns: {missing}")
    result = frame[required].copy().dropna(subset=["Close"])
    result.index = pd.to_datetime(result.index, utc=True)
    result.index.name = "event_time"
    # Conservative daily boundary: usable from 00:00 UTC after the labelled day.
    result.insert(0, "available_time", [
        datetime.combine(index.date() + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat()
        for index in result.index
    ])
    result.insert(1, "retrieval_time", retrieval_time.astimezone(timezone.utc).isoformat())
    result = result.rename(columns={name: name.lower().replace(" ", "_") for name in required})
    return result.reset_index()


def reconstruct(
    start: str = "2016-01-01",
    end: str | None = None,
    downloader: Callable = yf.download,
) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(ROOT / "analysis" / "cache" / "yfinance"))
    retrieval_time = datetime.now(timezone.utc)
    manifest = {
        "version": RECONSTRUCTION_VERSION,
        "retrieved_at": retrieval_time.isoformat(),
        "provider": "Yahoo Finance through the repository's existing yfinance dependency",
        "availability_policy": "daily labelled bar conservatively available 00:00 UTC next calendar day",
        "adjustment_warning": "Yahoo history can be revised; raw files are frozen with hashes and retrieval time.",
        "series": [],
        "unavailable": [
            {"instrument": "SARB_POLICY_RATE", "status": "CAPABILITY_UNAVAILABLE", "reason": "No release-vintage loader with verified historical availability timestamps in HR2."},
            {"instrument": "SA_GOVERNMENT_YIELDS", "status": "CAPABILITY_UNAVAILABLE", "reason": "No permitted stable historical endpoint integrated; licensed curves not assumed."},
            {"instrument": "SA_CPI_VINTAGES", "status": "CAPABILITY_UNAVAILABLE", "reason": "Release calendar and unrevised vintage values not yet reconstructed."},
            {"instrument": "ECONOMIC_SURPRISES", "status": "CAPABILITY_UNAVAILABLE", "reason": "No licensed point-in-time surprise dataset."},
            {"instrument": "US_REAL_YIELD", "status": "CAPABILITY_UNAVAILABLE", "reason": "No separately verified real-yield series integrated in HR2."},
            {"instrument": "JSE_DERIVATIVES", "status": "CAPABILITY_UNAVAILABLE", "reason": "Licensed futures/SSF volume, basis, term structure and open interest unavailable."},
        ],
    }
    for spec in SERIES:
        frame = downloader(
            spec.symbol, start=start, end=end, auto_adjust=False,
            actions=False, progress=False, threads=False,
        )
        if frame.empty:
            manifest["series"].append({**asdict(spec), "status": "UNAVAILABLE", "rows": 0})
            continue
        normalized = normalize_history(frame, retrieval_time)
        path = DATA_DIR / f"{spec.instrument.lower()}.csv"
        normalized.to_csv(path, index=False, lineterminator="\n")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["series"].append({
            **asdict(spec), "status": "AVAILABLE", "rows": len(normalized),
            "first_event_time": normalized["event_time"].iloc[0].isoformat(),
            "last_event_time": normalized["event_time"].iloc[-1].isoformat(),
            "path": path.relative_to(ROOT).as_posix(), "sha256": digest,
            "fields": list(normalized.columns),
        })
    target = RESULTS_DIR / "historical_feature_availability.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = reconstruct()
    print({item["instrument"]: item["rows"] for item in result["series"]})
