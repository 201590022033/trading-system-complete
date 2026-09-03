"""Walk-forward validation for the JSE technical signals.

This is research code, not an order generator. For each historical close it:
1. feeds only prices up to that date into SignalGenerator;
2. records the indicator signal available at that close;
3. evaluates the next five trading sessions as the outcome.

Usage:
    python backtest.py
    python backtest.py --years 2 --horizon 5

The report is written to backtest_report.json and backtest_report.md.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from data_pipeline import SignalGenerator
from jse_adapter import JSEDataAdapter, DataSourceType, JSE_TICKERS


DEFAULT_TICKERS = ["NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ"]
SIGNAL_NAMES = ("rsi", "sma", "breakout", "stochastic")


@dataclass
class SignalStats:
    ticker: str
    indicator: str
    observations: int = 0
    wins: int = 0
    losses: int = 0
    flat_outcomes: int = 0
    win_rate: float = 0.0
    average_aligned_return: float = 0.0
    average_forward_return: float = 0.0

    def finish(self) -> None:
        if self.observations:
            self.win_rate = round(self.wins / self.observations, 4)
            self.average_aligned_return = round(
                self.average_aligned_return / self.observations, 6
            )
            self.average_forward_return = round(
                self.average_forward_return / self.observations, 6
            )


def evaluate_series(ticker: str, prices: List[float], horizon: int) -> List[SignalStats]:
    """Evaluate signals without allowing future prices into the indicator state."""
    stats = {name: SignalStats(ticker=ticker, indicator=name) for name in SIGNAL_NAMES}

    # 100 is enough for the current indicators and preserves the warm-up period.
    generator = SignalGenerator(buffer_size=100)
    for index, price in enumerate(prices):
        generator.add_vwap(ticker, price)
        if index + horizon >= len(prices):
            break

        indicators = generator.generate_indicators(ticker)
        if indicators is None:
            continue
        forward_return = (prices[index + horizon] - price) / price
        signal_values = {
            "rsi": indicators.rsi_signal,
            "sma": indicators.sma_signal,
            "breakout": indicators.breakout_signal,
            "stochastic": indicators.stochastic_signal,
        }

        for name, signal in signal_values.items():
            if signal == 0:
                continue
            item = stats[name]
            item.observations += 1
            item.average_forward_return += forward_return
            aligned_return = signal * forward_return
            item.average_aligned_return += aligned_return
            if aligned_return > 0:
                item.wins += 1
            elif aligned_return < 0:
                item.losses += 1
            else:
                item.flat_outcomes += 1

    for item in stats.values():
        item.finish()
    return list(stats.values())


def fetch_prices(tickers: List[str], years: int) -> Dict[str, List[float]]:
    adapter = JSEDataAdapter(price_source=DataSourceType.YAHOO_FINANCE, news_source="mock")
    days = max(365, years * 365 + 30)
    result = {}
    for ticker in tickers:
        prices = adapter.get_historical_prices(ticker, days=days)
        prices = [price for price in prices if math.isfinite(price)]
        if prices:
            result[ticker] = prices
            print(f"{ticker}: {len(prices)} daily closes")
        else:
            print(f"{ticker}: no data")
    return result


def make_report(price_data: Dict[str, List[float]], horizon: int) -> Dict:
    rows = []
    for ticker, prices in price_data.items():
        rows.extend(asdict(row) for row in evaluate_series(ticker, prices, horizon))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "horizon_sessions": horizon,
        "method": "walk-forward close-only; signal at t evaluated at t+horizon",
        "rows": rows,
    }


def write_outputs(report: Dict) -> None:
    root = Path(__file__).parent
    (root / "backtest_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    lines = [
        "# JSE Indicator Backtest Report",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Forward horizon: **{report['horizon_sessions']} trading sessions**",
        "",
        "> This report is research evidence only. It does not change production weights or place orders.",
        "",
        "| Ticker | Indicator | Observations | Win rate | Avg aligned return | Avg forward return |",
        "| ------ | --------- | ------------ | -------- | ------------------ | ------------------ |",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['ticker']} | {row['indicator']} | {row['observations']} | "
            f"{row['win_rate']:.1%} | {row['average_aligned_return']:.2%} | "
            f"{row['average_forward_return']:.2%} |"
        )
    lines.extend([
        "",
        "## Interpretation rules",
        "",
        "- A signal with zero observations is not evidence that it is accurate or inaccurate.",
        "- Win rate alone is insufficient; compare aligned return, costs, liquidity and drawdown.",
        "- This first pass uses Yahoo adjusted close-like daily data and ignores spread, fees, taxes and slippage.",
        "- Do not promote an indicator or alter weights until the result is reviewed and recorded in `INDICATOR_BIBLE.md`.",
    ])
    (root / "backtest_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    args = parser.parse_args()

    unknown = [ticker for ticker in args.tickers if ticker not in JSE_TICKERS]
    if unknown:
        parser.error(f"Unknown JSE ticker(s): {', '.join(unknown)}")
    if args.years < 1 or args.horizon < 1:
        parser.error("years and horizon must be positive")

    price_data = fetch_prices(args.tickers, args.years)
    if not price_data:
        raise SystemExit("No historical data was available.")
    report = make_report(price_data, args.horizon)
    write_outputs(report)
    print("Wrote backtest_report.json and backtest_report.md")


if __name__ == "__main__":
    main()
