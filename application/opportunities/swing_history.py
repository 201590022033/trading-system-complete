"""Compact offline Yahoo research, attached as evidence rather than ranking skill."""
import json
from datetime import datetime, timedelta, timezone
from math import isfinite, sqrt
from pathlib import Path
from statistics import mean, stdev
from domain.evaluation.effectiveness import ContextualEffectivenessLearner, FeatureOutcome

VERSION = "yahoo-swing-context-v1"
REPORT = Path(__file__).resolve().parents[2] / "analysis/results/swing_history_v1.json"
HORIZONS = (3, 4)
BENCHMARK = "ETF_STX40"


def usable_bars(chart, cutoff):
    if cutoff.tzinfo is None:
        raise ValueError("aware evaluation clock required")
    rows = []
    for item in chart.get("bars", ()):
        day = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")).date()
        available = datetime.combine(day + timedelta(days=1), datetime.min.time(), timezone.utc)
        if available > cutoff:
            continue
        close = float(item["close"])
        if not isfinite(close) or close <= 0:
            raise ValueError("invalid daily close")
        if available <= cutoff:
            rows.append((day.isoformat(), close))
    if any(a[0] >= b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("daily dates must increase uniquely")
    return rows


def setup(closes):
    """Predeclared close-only states; never tuned against the evaluation window."""
    if len(closes) < 21:
        return "UNAVAILABLE"
    if not continuous(closes[-21:]):
        return "UNAVAILABLE"
    if closes[-1] <= closes[-21]:
        return "NO_LONG_SETUP"
    if closes[-1] > max(closes[-21:-1]):
        return "BREAKOUT"
    if closes[-1] < closes[-6]:
        return "TREND_PULLBACK"
    return "TREND"


def continuous(prices):
    """Quarantine possible unit/split discontinuities, never infer a repair."""
    return all(.5 <= right/left <= 2 for left, right in zip(prices, prices[1:]))


def market_state(rows, day):
    prices = [price for date, price in rows if date <= day]
    if len(prices) < 21 or not rows or not any(date == day for date, _ in rows) or not continuous(prices[-21:]):
        return "UNKNOWN"
    return "SUPPORTIVE" if prices[-1] > prices[-21] else "DEFENSIVE"


def metrics(trades):
    values = [item["net"] for item in trades]
    n = len(values)
    if not n:
        return {"sample_count": 0, "state": "INSUFFICIENT_EVIDENCE"}
    # Normal interval is descriptive, not an admission/promotion test.
    error = stdev(values) / sqrt(n) if n > 1 else None
    result = {"sample_count": n, "state": "DESCRIPTIVE" if n >= 30 else "INSUFFICIENT_EVIDENCE",
            "mean_net_return": mean(values), "mean_gross_return": mean(x["gross"] for x in trades),
            "mean_net_50bps_stress": mean(values) - .003,
            "win_rate": sum(v > 0 for v in values) / n,
            "mean_close_mae": mean(x["mae"] for x in trades),
            "mean_close_mfe": mean(x["mfe"] for x in trades),
            "mean_etf_excess": mean(x["excess"] for x in trades if x["excess"] is not None)
                if any(x["excess"] is not None for x in trades) else None,
            "etf_comparison_count": sum(x["excess"] is not None for x in trades),
            "mean_net_interval_95": [mean(values)-1.96*error, mean(values)+1.96*error] if error is not None else None}
    outcomes = [x["outcome"] for x in trades if "outcome" in x]
    if outcomes:
        first = outcomes[0]
        estimate = ContextualEffectivenessLearner().estimate(
            outcomes, feature_id=first.feature_id, evaluated_at=max(x.outcome_maturity for x in outcomes),
            instrument_id=first.instrument_id, horizon_id=first.horizon_id)
        result["contextual_learner"] = {"status": estimate.status,
            "configuration_version": estimate.configuration_version,
            "sample_count": estimate.sample_count, "shrunk_mean_net_return": estimate.expected_return_net,
            "governance": "HISTORICAL_FEATURE_ESTIMATE_NOT_PROMOTION"}
    return result


def summarize_history(chart, benchmark, *, cutoff):
    """Forward replay with later-close entry, exact horizons, non-overlap per cell.

    Today's close labels a setup. Entry is the NEXT session close, then H full
    subsequent sessions to exit. This deliberately matches the existing delayed
    close paper proxy, not a claim to executable next-open prices or intrabar stops.
    """
    rows, market = usable_bars(chart, cutoff), usable_bars(benchmark or {}, cutoff)
    prices = [price for _, price in rows]
    benchmark_prices = dict(market)
    cells, next_entry = {}, {}
    excluded = 0
    holdout_start = len(rows) * 2 // 3
    for i in range(20, len(rows)):
        state = setup(prices[:i+1])
        if state in {"UNAVAILABLE", "NO_LONG_SETUP"}:
            continue
        regime = market_state(market, rows[i][0])
        for horizon in HORIZONS:
            entry, exit_index = i+1, i+1+horizon
            if exit_index >= len(rows):
                continue
            if not continuous(prices[i:exit_index+1]):
                excluded += 1
                continue
            for context in (regime, "ALL"):
                identity = f"{state}|{context}|{horizon}"
                if entry <= next_entry.get(identity, -1):
                    continue
                next_entry[identity] = exit_index
                gross = prices[exit_index]/prices[entry]-1
                path = [p/prices[entry]-1 for p in prices[entry:exit_index+1]]
                bentry, bexit = benchmark_prices.get(rows[entry][0]), benchmark_prices.get(rows[exit_index][0])
                benchmark_path = [p for day, p in market if rows[entry][0] <= day <= rows[exit_index][0]]
                benchmark_usable = bentry and bexit and continuous(benchmark_path)
                trade = {"gross": gross, "net": gross-.002, "mae": min(path), "mfe": max(path),
                         "excess": gross-(bexit/bentry-1) if benchmark_usable else None,
                         "held_out": i >= holdout_start}
                clock = lambda day: datetime.fromisoformat(day).replace(tzinfo=timezone.utc)+timedelta(days=1)
                trade["outcome"] = FeatureOutcome(
                    state, VERSION, "technical_setup", chart.get("symbol", "TEST"),
                    f"{horizon}_sessions", VERSION, regime, 1,
                    clock(rows[i][0]), clock(rows[i][0]), clock(rows[exit_index][0]),
                    gross, gross-.002, f"{chart.get('symbol', 'TEST')}:{state}:{horizon}:{rows[i][0]}")
                cells.setdefault(identity, []).append(trade)
    return {"source_sessions": len(rows), "first_session": rows[0][0] if rows else None,
            "last_session": rows[-1][0] if rows else None,
            "held_out_start": rows[holdout_start][0] if rows else None,
            "data_quality": {"policy": "QUARANTINE_DAILY_RATIOS_OUTSIDE_0.5_TO_2_NOT_REPAIR",
                "discontinuity_sessions": [rows[i][0] for i in range(1, len(rows))
                                           if not continuous(prices[i-1:i+1])],
                "excluded_forward_windows": excluded,
                "benchmark_discontinuity_sessions": [market[i][0] for i in range(1, len(market))
                    if not continuous([market[i-1][1], market[i][1]])]},
            "cells": {key: {"all_history": metrics(values),
                            "held_out": metrics([x for x in values if x["held_out"]])}
                      for key, values in cells.items()}}


def load_report(path=REPORT):
    try:
        if path.stat().st_size > 1_000_000:
            raise ValueError("compact report size exceeded")
        result = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(result, dict) or result.get("version") != VERSION:
            raise ValueError("unsupported report")
        return result
    except (OSError, ValueError, TypeError):
        return {}


def current_evidence(key, chart, benchmark, *, evaluated_at, report=None):
    report = load_report() if report is None else report
    try:
        rows = usable_bars(chart, evaluated_at)
    except (ValueError, KeyError, TypeError, OverflowError):
        return {"state": "UNAVAILABLE", "reason": "INVALID_SWING_INPUT", "setup": "UNAVAILABLE",
                "market_state": "UNKNOWN", "governance": "SHADOW_ONLY_NO_RANKING_EFFECT"}
    state = setup([price for _, price in rows])
    try:
        valid_benchmark = (benchmark and benchmark.get("symbol") == "STX40.JO"
                           and benchmark.get("interval") == "1d" and benchmark.get("currency") == "ZAR")
        market = market_state(usable_bars(benchmark, evaluated_at), rows[-1][0]) if valid_benchmark and rows else "UNKNOWN"
    except (ValueError, KeyError, TypeError, OverflowError):
        market = "UNKNOWN"
    unavailable = {"state": "UNAVAILABLE", "reason": "NO_CAUSAL_MATCHING_HISTORY", "setup": state,
                   "market_state": market, "governance": "SHADOW_ONLY_NO_RANKING_EFFECT"}
    try:
        generated = datetime.fromisoformat(report["available_at"])
        if generated.tzinfo is None or generated > evaluated_at or report["version"] != VERSION:
            return unavailable
        history = report["instruments"][key]
        if history["symbol"] != chart.get("symbol"):
            return unavailable
        history_available = datetime.fromisoformat(history["last_session"]).replace(tzinfo=timezone.utc)+timedelta(days=1)
        if history_available > generated or evaluated_at-generated > timedelta(days=90):
            return unavailable
        result = {**unavailable, "state": "HISTORICAL_RESEARCH_CONTEXT", "reason": "DESCRIPTIVE_NOT_VALIDATED_TRADE_SKILL", "version": VERSION,
                  "available_at": generated.isoformat(), "source_sessions": history["source_sessions"],
                  "history_through": history["last_session"], "held_out_start": history["held_out_start"],
                  "source_sha256": history["source_sha256"], "cost_round_trip_bps": 20,
                  "data_quality": history.get("data_quality", {}),
                  "execution_model": "NEXT_SESSION_CLOSE_PLUS_H_SESSIONS",
                  "limitations": report["limitations"], "horizons": {}}
        for horizon in HORIZONS:
            exact = f"{state}|{market}|{horizon}"
            fallback = f"{state}|ALL|{horizon}"
            cell = history["cells"].get(exact)
            context = market
            if not cell or cell["all_history"]["sample_count"] < 30:
                cell, context = history["cells"].get(fallback), "ALL_MARKET_STATES_FALLBACK"
            result["horizons"][f"{horizon}_sessions"] = {"context": context,
                **(cell or {"all_history": {"state": "INSUFFICIENT_EVIDENCE", "sample_count": 0},
                            "held_out": {"state": "INSUFFICIENT_EVIDENCE", "sample_count": 0}})}
        return result
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
        return unavailable
