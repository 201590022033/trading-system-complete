"""Generate the M7 historical legacy/adaptive evaluation report."""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

from evaluation import CostAssumptions, evaluate_walk_forward
from jse_adapter import DataSourceType, JSEDataAdapter, JSE_TICKERS


DEFAULT_TICKERS = ["NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=2)
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS)
    parser.add_argument("--spread-bps", type=float, default=5.0)
    parser.add_argument("--fees-bps", type=float, default=2.0)
    parser.add_argument("--slippage-bps", type=float, default=3.0)
    args = parser.parse_args()
    unknown = [ticker for ticker in args.tickers if ticker not in JSE_TICKERS]
    if unknown:
        parser.error(f"Unknown ticker(s): {', '.join(unknown)}")

    yf.set_tz_cache_location(str(Path(tempfile.gettempdir()) / "jse-yfinance-cache"))
    adapter = JSEDataAdapter(price_source=DataSourceType.YAHOO_FINANCE, news_source="mock")
    costs = CostAssumptions(args.spread_bps, args.fees_bps, args.slippage_bps)
    reports = []
    observations = {}
    for ticker in args.tickers:
        prices = adapter.get_historical_prices(ticker, days=max(365, args.years * 365 + 30))
        prices = [float(price) for price in prices if math.isfinite(float(price)) and float(price) > 0]
        observations[ticker] = len(prices)
        if len(prices) >= 30:
            reports.append(evaluate_walk_forward(ticker, prices, costs=costs))
        print(ticker, "daily closes:", len(prices))

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "Yahoo Finance daily close-like history",
        "observations": observations,
        "context_limitations": (
            "No point-in-time macro/source histories were available; macro-only and source-only "
            "ablations therefore have zero active samples and adaptive uses neutral context inputs."
        ),
        "reports": reports,
    }
    root = Path(__file__).parent
    (root / "adaptive_evaluation_report.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )

    lines = [
        "# Adaptive Evaluation Report", "",
        f"Generated: `{output['generated_at']}`", "",
        "> Research/shadow evidence only. This report does not promote adaptive weights or place orders.", "",
        f"Data: {output['data_source']}",
        "Costs: 5 bps spread + 2 bps fees + 3 bps slippage per unit of turnover.",
        f"Limitation: {output['context_limitations']}", "",
        "| Ticker | Model | Horizon | Samples | Win rate (95% CI) | Mean aligned | Median aligned | Mean net | Max drawdown | Turnover |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for report in reports:
        for row in report["rows"]:
            if row["segment_type"] != "overall":
                continue
            lines.append(
                f"| {row['ticker']} | {row['model']} | {row['horizon']} | {row['sample_count']} | "
                f"{row['win_rate']:.1%} ({row['win_rate_ci_low']:.1%}-{row['win_rate_ci_high']:.1%}) | "
                f"{row['mean_aligned_return']:.2%} | {row['median_aligned_return']:.2%} | "
                f"{row['mean_net_return']:.2%} | {row['max_drawdown']:.2%} | {row['turnover']:.1f} |"
            )
    lines.extend([
        "", "## Interpretation", "",
        "- Rows below 30 active signals are flagged as insufficient in the JSON report.",
        "- Regime, volatility and profile segments are included in the JSON report.",
        "- MFE/MAE are measured from daily closes, not intraday extremes.",
        "- Overlapping horizon observations are research signals, not a capital-allocation simulation.",
        "- Missing point-in-time context prevents a fair historical test of macro/source contributions.",
    ])
    (root / "adaptive_evaluation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote adaptive_evaluation_report.json and adaptive_evaluation_report.md")


if __name__ == "__main__":
    main()
