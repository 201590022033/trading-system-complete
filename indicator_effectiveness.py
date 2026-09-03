"""Interpretable conditional indicator-effectiveness learning for HR8."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import numpy as np
import pandas as pd


VERSION = "indicator-effectiveness-v1"
ROOT = Path(__file__).parent
FEATURES = ROOT / "analysis" / "data" / "hr7" / "asset_technical_features.csv"
OUTPUT = ROOT / "analysis" / "results" / "indicator_effectiveness.json"
HORIZONS = (1, 3, 5, 20)
MINIMUM_SAMPLE = 30
PRIOR_STRENGTH = 20
COST_BPS = 10.0


@dataclass(frozen=True)
class ReliabilityEstimate:
    observations: int
    hit_rate: float
    shrunk_hit_rate: float
    mean_net_return: float
    median_net_return: float
    false_positive_rate: float
    ci_low: float
    ci_high: float
    stability: float
    recency_weighted_net_return: float
    current_reliability_weight: float
    sample_gate_passed: bool


def _wilson(wins: int, count: int) -> tuple[float, float]:
    if not count:
        return 0.0, 1.0
    z = 1.96
    p = wins / count
    denominator = 1 + z*z/count
    centre = (p + z*z/(2*count))/denominator
    margin = z*math.sqrt(p*(1-p)/count + z*z/(4*count*count))/denominator
    return max(0.0, centre-margin), min(1.0, centre+margin)


def estimate_reliability(net_returns: list[float], gross_returns: list[float], recency_half_life: float = 252.0) -> ReliabilityEstimate:
    count = len(net_returns)
    wins = sum(value > 0 for value in gross_returns)
    hit = wins/count if count else .5
    shrunk = (wins + PRIOR_STRENGTH*.5)/(count+PRIOR_STRENGTH)
    ci_low, ci_high = _wilson(wins, count)
    first = mean(net_returns[:count//2]) if count >= 2 else 0.0
    second = mean(net_returns[count//2:]) if count else 0.0
    stability = 1.0 if count >= MINIMUM_SAMPLE and first*second > 0 else 0.5 if count >= MINIMUM_SAMPLE and (first == 0 or second == 0) else 0.0
    if count:
        ages = np.arange(count-1, -1, -1)
        weights = np.power(.5, ages/recency_half_life)
        recency = float(np.average(net_returns, weights=weights))
    else:
        recency = 0.0
    gate = count >= MINIMUM_SAMPLE
    if gate:
        evidence = 2*(shrunk-.5) + max(-.5, min(.5, recency/.02))
        weight = max(.5, min(1.5, 1 + stability*evidence))
    else:
        weight = 1.0
    return ReliabilityEstimate(
        count, hit, shrunk, mean(net_returns) if count else 0.0,
        median(net_returns) if count else 0.0, 1-hit, ci_low, ci_high,
        stability, recency, weight, gate,
    )


def walk_forward_weights(signals: list[int], forward_returns: list[float], horizon: int) -> list[float]:
    """At index i use only outcomes j for which j+horizon <= i."""
    weights = []
    realized_net: list[float] = []
    prefix_sum = [0.0]
    wins = 0
    recency_numerator = 0.0
    recency_denominator = 0.0
    decay = .5 ** (1/252.0)
    for index in range(len(signals)):
        newly_known = index - horizon
        if newly_known >= 0 and signals[newly_known] and math.isfinite(forward_returns[newly_known]):
            gross = signals[newly_known]*forward_returns[newly_known]
            net = gross-COST_BPS/10000.0
            realized_net.append(net)
            prefix_sum.append(prefix_sum[-1] + net)
            wins += gross > 0
            recency_numerator = recency_numerator*decay + net
            recency_denominator = recency_denominator*decay + 1.0
        count = len(realized_net)
        if count < MINIMUM_SAMPLE:
            weights.append(1.0)
            continue
        split = count//2
        first = prefix_sum[split]/split
        second = (prefix_sum[count]-prefix_sum[split])/(count-split)
        stability = 1.0 if first*second > 0 else 0.5 if first == 0 or second == 0 else 0.0
        shrunk = (wins+PRIOR_STRENGTH*.5)/(count+PRIOR_STRENGTH)
        recency = recency_numerator/recency_denominator
        evidence = 2*(shrunk-.5) + max(-.5, min(.5, recency/.02))
        weights.append(max(.5, min(1.5, 1+stability*evidence)))
    return weights


def _signals(frame: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "rsi": frame["rsi_signal"].fillna(0).astype(int),
        "sma": frame["sma_signal"].fillna(0).astype(int),
        "breakout": frame["breakout_signal"].fillna(0).astype(int),
        "stochastic": frame["stochastic_signal"].fillna(0).astype(int),
        "macd": np.sign(frame["macd"]).fillna(0).astype(int),
        "bollinger_mean_reversion": pd.Series(np.select([frame["bollinger_zscore"] <= -1.5, frame["bollinger_zscore"] >= 1.5], [1, -1], default=0), index=frame.index),
        "adx_dmi": pd.Series(np.where(frame["adx"] >= 25, frame["dmi_direction"], 0), index=frame.index).fillna(0).astype(int),
        "ichimoku": frame["ichimoku_direction"].fillna(0).astype(int),
    }


def evaluate(frame: pd.DataFrame) -> dict:
    data = frame.copy()
    data["event_time"] = pd.to_datetime(data["event_time"], utc=True)
    rows = []
    walk_forward_summary = []
    for instrument, asset in data.groupby("instrument", sort=True):
        asset = asset.sort_values("event_time").reset_index(drop=True)
        signals = _signals(asset)
        for horizon in HORIZONS:
            forward = asset["close"].shift(-horizon)/asset["close"]-1
            for indicator, signal in signals.items():
                weights = walk_forward_weights(signal.tolist(), forward.fillna(float("nan")).tolist(), horizon)
                walk_forward_summary.append({
                    "instrument": instrument, "indicator": indicator, "horizon": horizon,
                    "eligible_decisions": len(weights),
                    "non_neutral_learned_weights": sum(abs(value-1.0) > 1e-12 for value in weights),
                    "final_prior_only_weight": weights[-1] if weights else 1.0,
                })
                previous = signal.shift(1).fillna(0)
                turnover = (signal-previous).abs()
                base = pd.DataFrame({
                    "signal": signal, "gross": signal*forward,
                    "net": signal*forward-turnover*COST_BPS/10000.0,
                    "trend_regime": asset["trend_regime"],
                    "volatility_regime": asset["volatility_regime"],
                })
                for trend in sorted(base["trend_regime"].dropna().unique()):
                    for volatility in sorted(base["volatility_regime"].dropna().unique()):
                        selected = base[(base.signal != 0) & (base.trend_regime == trend) & (base.volatility_regime == volatility) & base.gross.notna()]
                        if selected.empty:
                            continue
                        estimate = estimate_reliability(selected.net.tolist(), selected.gross.tolist())
                        rows.append({
                            "indicator": indicator, "instrument": instrument,
                            "asset_class": asset["asset_class"].iloc[0], "profile": asset["profile"].iloc[0],
                            "market_regime": trend, "volatility_regime": volatility,
                            "horizon": horizon, **estimate.__dict__,
                        })
    return {
        "version": VERSION, "cost_bps": COST_BPS,
        "minimum_sample": MINIMUM_SAMPLE, "prior_strength": PRIOR_STRENGTH,
        "method": "conditional outcomes; Wilson interval; 20-observation neutral prior; walk-forward weights only after horizon elapses",
        "rows": rows, "walk_forward_summary": walk_forward_summary,
    }


def generate() -> dict:
    result = evaluate(pd.read_csv(FEATURES))
    OUTPUT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = generate()
    print(len(result["rows"]), len(result["walk_forward_summary"]))
