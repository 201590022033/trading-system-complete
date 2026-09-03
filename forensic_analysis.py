"""Frozen-input post-fusion forensic analysis; never changes signal weights."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, pstdev
from types import SimpleNamespace

from data_pipeline import SignalGenerator
from jse_adapter import DataSourceType, JSEDataAdapter, JSE_TICKERS
from market_profiles import DEFAULT_PROFILE_REGISTRY
from regime_engine import classify_regime
from signal_pipeline import legacy_technical_score


TICKERS = ["NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ"]
HORIZONS = [1, 3, 5, 20]
COST_BPS = 10.0
ROOT = Path(__file__).parent
RESULTS = ROOT / "analysis" / "results"


def capture_prices() -> dict:
    adapter = JSEDataAdapter(price_source=DataSourceType.YAHOO_FINANCE, news_source="mock")
    prices = {}
    for ticker in TICKERS:
        values = adapter.get_historical_prices(ticker, days=760)
        prices[ticker] = [float(x) for x in values if math.isfinite(float(x)) and float(x) > 0]
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance daily close-like history via existing JSEDataAdapter",
        "limitations": "No dates or immutable provider revision identifier are exposed by the existing adapter.",
        "prices": prices,
    }


def _position(score):
    return 1 if score > 0.35 else -1 if score < -0.35 else 0


def _action(score):
    return "buy" if score > 0.35 else "sell" if score < -0.35 else "hold"


def matched_opportunity_analysis(snapshot):
    """Compare frozen price-only scores at fully warmed, common timestamps.

    This is deliberately labelled constrained: the repository has no aligned
    historical sentiment or macro series with which to replay production legacy.
    """
    opportunities = []
    for ticker, prices in snapshot["prices"].items():
        generator = SignalGenerator(buffer_size=max(100, len(prices)))
        for index, price in enumerate(prices):
            generator.add_vwap(ticker, price)
            if index < 19 or index + max(HORIZONS) >= len(prices):
                continue
            indicators = generator.generate_indicators(ticker)
            technical_score = legacy_technical_score(SimpleNamespace(indicators=indicators))
            legacy_score = 0.60 * technical_score
            adaptive_score = technical_score
            legacy_action = _action(legacy_score)
            adaptive_action = _action(adaptive_score)
            if legacy_action == adaptive_action:
                category = "both_agree_hold" if legacy_action == "hold" else "both_agree_trade"
            elif legacy_action == "hold":
                category = "adaptive_only_trade"
            elif adaptive_action == "hold":
                category = "legacy_only_trade"
            else:
                category = "directional_disagreement"
            opportunities.append({
                "ticker": ticker,
                "index": index,
                "technical_warmup_complete": True,
                "full_legacy_inputs_available": False,
                "legacy_score_price_only_reconstruction": legacy_score,
                "adaptive_score_price_only_reconstruction": adaptive_score,
                "simple_non_adaptive_technical_score": technical_score,
                "legacy_action_price_only_reconstruction": legacy_action,
                "adaptive_action_price_only_reconstruction": adaptive_action,
                "simple_non_adaptive_technical_action": _action(technical_score),
                "comparison_category": category,
                "subsequent_returns": {
                    str(horizon): prices[index + horizon] / price - 1.0
                    for horizon in HORIZONS
                },
            })

    def counts(rows):
        categories = Counter(row["comparison_category"] for row in rows)
        raw_scores = [row["adaptive_score_price_only_reconstruction"] for row in rows]
        return {
            "opportunities": len(rows),
            "both_agree_hold": categories["both_agree_hold"],
            "both_agree_trade": categories["both_agree_trade"],
            "adaptive_only_trades": categories["adaptive_only_trade"],
            "legacy_only_trades": categories["legacy_only_trade"],
            "directional_disagreements": categories["directional_disagreement"],
            "minimum_raw_technical_score": min(raw_scores) if raw_scores else 0.0,
            "maximum_raw_technical_score": max(raw_scores) if raw_scores else 0.0,
            "legacy_required_raw_score_magnitude": 0.35 / 0.60,
        }

    return {
        "status": "INSUFFICIENT HISTORICAL INPUTS",
        "status_explanation": (
            "A faithful full-production legacy replay is impossible because point-in-time "
            "sentiment/news aggregation and macro inputs were not persisted. The matched "
            "comparison below is valid only for the shared frozen close-derived technical input."
        ),
        "technical_warmup_sessions": 20,
        "cash_no_trade_benchmark": {
            "action": "hold", "gross_return": 0.0, "net_return": 0.0,
            "turnover": 0.0, "cost_bps": 0.0,
        },
        "simple_non_adaptive_technical_benchmark": (
            "Exactly identical to the reconstructed adaptive score/action because technical is "
            "the only available factor and adaptive normalization gives it 100% effective weight."
        ),
        "overall": counts(opportunities),
        "by_ticker": {
            ticker: counts([row for row in opportunities if row["ticker"] == ticker])
            for ticker in TICKERS
        },
        "opportunities": opportunities,
    }


def decision_records(ticker, prices, horizon):
    generator = SignalGenerator(buffer_size=max(100, len(prices)))
    profile = DEFAULT_PROFILE_REGISTRY.select(ticker)
    previous = {"legacy": 0, "adaptive": 0}
    records = []
    for index, price in enumerate(prices):
        generator.add_vwap(ticker, price)
        if index + horizon >= len(prices):
            break
        indicators = generator.generate_indicators(ticker)
        technical = legacy_technical_score(SimpleNamespace(indicators=indicators))
        legacy_score = 0.60 * technical
        adaptive_score = technical  # only available M7 factor; contextual multipliers normalize out
        regime = classify_regime(prices[:index + 1]) if index else None
        future = [(x / price) - 1.0 for x in prices[index + 1:index + horizon + 1]]
        for model, score in (("legacy", legacy_score), ("adaptive", adaptive_score)):
            position = _position(score)
            turnover = abs(position - previous[model])
            previous[model] = position
            aligned = position * future[-1]
            records.append({
                "ticker": ticker, "profile": profile.profile_id, "sector": profile.sector,
                "horizon": horizon, "index": index, "model": model, "score": score,
                "position": position, "trend": regime.trend if regime else "unavailable",
                "volatility": regime.volatility if regime else "unavailable",
                "risk": regime.risk if regime else "unavailable",
                "aligned_return": aligned,
                "forward_return": future[-1],
                "net_return": aligned - turnover * COST_BPS / 10000.0,
                "mfe": max([0.0] + [position * x for x in future]),
                "mae": min([0.0] + [position * x for x in future]),
                "turnover": turnover,
                "signals": {
                    "rsi": indicators.rsi_signal if indicators else 0,
                    "sma": indicators.sma_signal if indicators else 0,
                    "breakout": indicators.breakout_signal if indicators else 0,
                    "stochastic": indicators.stochastic_signal if indicators else 0,
                },
                "period": "first_half" if index < len(prices) / 2 else "second_half",
            })
    return records


def summarize(records):
    active = [r for r in records if r["position"]]
    aligned = [r["aligned_return"] for r in active]
    net = [r["net_return"] for r in records if r["position"] or r["turnover"]]
    wins = [x for x in aligned if x > 0]
    losses = [x for x in aligned if x < 0]
    n = len(active)
    p = len(wins) / n if n else 0.0
    if n:
        z = 1.96; den = 1 + z*z/n; centre = (p + z*z/(2*n))/den
        margin = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
        ci = [max(0, centre-margin), min(1, centre+margin)]
    else: ci = [0.0, 1.0]
    return {
        "sample_count": n, "wins": len(wins), "losses": len(losses), "win_rate": p,
        "win_rate_ci": ci, "mean_gross": mean(aligned) if aligned else 0.0,
        "mean_net": mean(net) if net else 0.0, "median": median(aligned) if aligned else 0.0,
        "dispersion": pstdev(aligned) if len(aligned) > 1 else 0.0,
        "average_winner": mean(wins) if wins else 0.0,
        "average_loser": mean(losses) if losses else 0.0,
        "win_loss_ratio": (mean(wins) / abs(mean(losses))) if wins and losses else 0.0,
        "mean_mfe": mean(r["mfe"] for r in active) if active else 0.0,
        "mean_mae": mean(r["mae"] for r in active) if active else 0.0,
        "turnover": sum(r["turnover"] for r in records),
        "signal_frequency": n / len(records) if records else 0.0,
        "cost_burden": sum(r["turnover"] for r in records) * COST_BPS / 10000.0,
    }


def analyse(snapshot):
    all_records = []
    for ticker, prices in snapshot["prices"].items():
        for horizon in HORIZONS:
            all_records.extend(decision_records(ticker, prices, horizon))
    ranking = []
    for ticker in TICKERS:
        for horizon in HORIZONS:
            subset = [r for r in all_records if r["ticker"] == ticker and r["horizon"] == horizon]
            legacy = summarize([r for r in subset if r["model"] == "legacy"])
            adaptive = summarize([r for r in subset if r["model"] == "adaptive"])
            adjacent = []
            for other in HORIZONS:
                s = summarize([r for r in all_records if r["ticker"] == ticker and r["horizon"] == other and r["model"] == "adaptive"])
                adjacent.append(s["mean_net"] > 0)
            halves = []
            for period in ("first_half", "second_half"):
                halves.append(summarize([r for r in subset if r["model"] == "adaptive" and r["period"] == period])["mean_net"])
            cash_benchmark = 0.0
            adaptive_net_vs_cash = adaptive["mean_net"] - cash_benchmark
            adaptive_increment_vs_technical = 0.0
            adaptive_records = [r for r in subset if r["model"] == "adaptive"]
            cost_stress = {}
            for bps in (0, 10, 20, 30):
                values = [r["aligned_return"] - r["turnover"] * bps / 10000.0
                          for r in adaptive_records if r["position"] or r["turnover"]]
                cost_stress[str(bps)] = mean(values) if values else 0.0
            robustness = sum(adjacent) / len(adjacent)
            downside = max(0.0, 1.0 + adaptive["mean_mae"] * 20.0)
            confidence = min(1.0, adaptive["sample_count"] / 100.0) * max(0.0, adaptive["win_rate_ci"][0] - 0.35) / 0.25
            temporal = sum(x > 0 for x in halves) / 2.0
            score = 100 / 0.75 * (0.20 * max(0, min(1, adaptive["mean_net"] / 0.02 + 0.5)) +
                           0.15 * confidence + 0.15 * robustness + 0.10 * temporal + 0.15 * downside)
            # No adaptive diamond can pass an incremental-value gate when the
            # adaptive result is exactly the simple non-adaptive technical benchmark.
            tier = "C"
            profile = DEFAULT_PROFILE_REGISTRY.select(ticker)
            ranking.append({
                "ticker": ticker, "company": JSE_TICKERS[ticker]["name"], "sector": profile.sector,
                "profile": profile.profile_id, "horizon": horizon, "adaptive": adaptive,
                "legacy_price_only_reconstruction": legacy,
                "adaptive_net_vs_cash_no_trade": adaptive_net_vs_cash,
                "adaptive_increment_vs_simple_technical": adaptive_increment_vs_technical,
                "adjacent_positive_fraction": robustness, "half_net_returns": halves,
                "cost_stress_bps": cost_stress,
                "technical_candidate_score": round(score, 2),
                "diamond_tier": tier,
                "diamond_gate": "failed: zero incremental value versus simple non-adaptive technical benchmark",
                "mechanism": "threshold de-dilution of the legacy technical score; no macro/source/profile contribution",
            })
    ranking.sort(key=lambda x: x["technical_candidate_score"], reverse=True)

    indicator = []
    for name in ("rsi", "sma", "breakout", "stochastic"):
        for trend in ("bull", "bear", "range"):
            for horizon in HORIZONS:
                selected = []
                for r in all_records:
                    if r["model"] != "adaptive" or r["trend"] != trend or r["horizon"] != horizon:
                        continue
                    signal = r["signals"][name]
                    if signal:
                        item = dict(r); item["position"] = signal
                        item["aligned_return"] = signal * r["forward_return"]
                        item["net_return"] = item["aligned_return"]
                        selected.append(item)
                stats = summarize(selected)
                indicator.append({"indicator": name, "trend": trend, "horizon": horizon, **stats})

    failures = Counter()
    for row in ranking:
        if row["adaptive"]["mean_net"] >= 0: continue
        if row["adaptive"]["mean_gross"] > 0: failures["transaction_cost_burden"] += 1
        elif row["adjacent_positive_fraction"] > 0: failures["horizon_mismatch_or_instability"] += 1
        elif row["adaptive"]["mean_mae"] < -0.03: failures["downside_or_volatility_exposure"] += 1
        else: failures["technical_signal_noise_or_lag"] += 1
    matched = matched_opportunity_analysis(snapshot)
    return {"metadata": {"version": "forensic-v2-methodology-audit", "cost_bps": COST_BPS,
            "critical_design_fact": "With only technical data available, adaptive contextual multipliers normalize out.",
            "legacy_comparison_status": "INSUFFICIENT HISTORICAL INPUTS",
            "delta_interpretation": "Adaptive net return versus cash/no-position; not adaptive outperformance versus full legacy."},
            "ranking": ranking, "indicator_by_regime": indicator,
            "failure_taxonomy": dict(failures), "matched_opportunity_analysis": matched,
            "records": all_records}


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    snapshot_path = RESULTS / "forensic_price_snapshot.json"
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    else:
        snapshot = capture_prices()
        snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    result = analyse(snapshot)
    (RESULTS / "forensic_analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    compact = {**result, "records": [], "matched_opportunity_analysis": {
        **result["matched_opportunity_analysis"], "opportunities": []}}
    (RESULTS / "forensic_summary.json").write_text(json.dumps(compact, indent=2), encoding="utf-8")
    print("captured", {k: len(v) for k, v in snapshot["prices"].items()})
    print("ranking", [(x["ticker"], x["horizon"], x["technical_candidate_score"], x["diamond_tier"]) for x in result["ranking"][:5]])


if __name__ == "__main__": main()
