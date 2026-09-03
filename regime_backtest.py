"""Descriptive walk-forward stability report for regime-v1.

This does not promote regimes or alter signal weights. Each label is calculated
from a trailing window ending at t, so no future prices enter the classification.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jse_adapter import DataSourceType, JSEDataAdapter, JSE_TICKERS
from regime_engine import classify_regime


def evaluate(ticker: str, prices, window: int = 60):
    labels = []
    for end in range(window, len(prices) + 1):
        regime = classify_regime(prices[end - window:end])
        labels.append({"trend": regime.trend, "volatility": regime.volatility, "risk": regime.risk})
    if not labels:
        return {"ticker": ticker, "observations": 0}
    transitions = sum(labels[i] != labels[i - 1] for i in range(1, len(labels)))
    return {
        "ticker": ticker,
        "observations": len(labels),
        "trend_distribution": dict(Counter(x["trend"] for x in labels)),
        "volatility_distribution": dict(Counter(x["volatility"] for x in labels)),
        "risk_distribution": dict(Counter(x["risk"] for x in labels)),
        "full_label_transitions": transitions,
        "transition_rate": round(transitions / max(1, len(labels) - 1), 6),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--tickers", nargs="+", default=["NPN", "SASOL", "BHP"])
    args = parser.parse_args()
    unknown = [ticker for ticker in args.tickers if ticker not in JSE_TICKERS]
    if unknown:
        parser.error(f"Unknown ticker(s): {', '.join(unknown)}")

    adapter = JSEDataAdapter(price_source=DataSourceType.YAHOO_FINANCE, news_source="mock")
    rows = []
    for ticker in args.tickers:
        prices = adapter.get_historical_prices(ticker, days=max(365, args.years * 365 + 30))
        prices = [float(p) for p in prices if p == p]
        rows.append(evaluate(ticker, prices, args.window))
        print(ticker, "regime observations:", rows[-1].get("observations", 0))

    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "window": args.window, "rows": rows}
    Path("regime_stability_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Wrote regime_stability_report.json")


if __name__ == "__main__":
    main()
