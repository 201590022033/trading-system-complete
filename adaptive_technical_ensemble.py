"""Explainable walk-forward adaptive technical ensemble (shadow only)."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from indicator_effectiveness import COST_BPS, HORIZONS, ReliabilityAccumulator


VERSION = "adaptive-technical-ensemble-v1"
ROOT = Path(__file__).parent
FEATURES = ROOT / "analysis" / "data" / "hr7" / "asset_technical_features.csv"
OUTPUT = ROOT / "analysis" / "data" / "hr9" / "adaptive_technical_decisions.csv"
SUMMARY = ROOT / "analysis" / "results" / "adaptive_technical_ensemble_summary.json"
INDICATORS = ("rsi", "sma", "breakout", "stochastic", "macd", "bollinger", "adx_dmi", "ichimoku")


def _signal_frame(asset: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=asset.index, columns=INDICATORS, dtype=float)
    result["rsi"] = asset["rsi_signal"].where(asset["rsi"].notna())
    result["sma"] = asset["sma_signal"].where(asset["sma_slow"].notna())
    result["breakout"] = asset["breakout_signal"].where(asset["technical_warmup_complete"])
    result["stochastic"] = asset["stochastic_signal"].where(asset["stochastic"].notna())
    result["macd"] = np.sign(asset["macd"]).where(asset.index >= 25)
    result["bollinger"] = pd.Series(np.select(
        [asset["bollinger_zscore"] <= -1.5, asset["bollinger_zscore"] >= 1.5],
        [1, -1], default=0), index=asset.index).where(asset["bollinger_zscore"].notna())
    result["adx_dmi"] = pd.Series(np.where(asset["adx"] >= 25, asset["dmi_direction"], 0), index=asset.index).where(asset["adx"].notna())
    result["ichimoku"] = asset["ichimoku_direction"]
    return result


def _action(score: float) -> str:
    return "buy" if score > .35 else "sell" if score < -.35 else "hold"


def build_ensemble(frame: pd.DataFrame) -> pd.DataFrame:
    outputs = []
    for instrument, asset in frame.groupby("instrument", sort=True):
        asset = asset.sort_values("event_time").reset_index(drop=True)
        signals = _signal_frame(asset)
        for horizon in HORIZONS:
            histories = defaultdict(ReliabilityAccumulator)
            for index, row in asset.iterrows():
                known = index-horizon
                if known >= 0:
                    realized = row["close"]/asset.loc[known, "close"]-1
                    prior_context = (asset.loc[known, "trend_regime"], asset.loc[known, "volatility_regime"])
                    for indicator in INDICATORS:
                        signal = signals.loc[known, indicator]
                        if pd.notna(signal) and signal != 0 and math.isfinite(realized):
                            aligned = float(signal)*realized
                            histories[(indicator, *prior_context)].update(
                                aligned-COST_BPS/10000.0, aligned
                            )
                weights, contributions, unavailable = {}, {}, []
                available = [name for name in INDICATORS if pd.notna(signals.loc[index, name])]
                for indicator in INDICATORS:
                    signal = signals.loc[index, indicator]
                    if pd.isna(signal):
                        unavailable.append(indicator)
                        continue
                    weights[indicator] = histories[(indicator, row["trend_regime"], row["volatility_regime"])].weight()
                denominator = sum(weights.values()) or 1.0
                for indicator, weight in weights.items():
                    contributions[indicator] = float(signals.loc[index, indicator])*weight/denominator
                score = sum(contributions.values())
                output = {
                    "event_time": row["event_time"], "available_time": row["available_time"],
                    "decision_time": row["decision_time"], "instrument": instrument,
                    "asset_class": row["asset_class"], "profile": row["profile"],
                    "trend_regime": row["trend_regime"], "volatility_regime": row["volatility_regime"],
                    "horizon": horizon, "close": row["close"],
                    "raw_technical_score": row["raw_technical_score"],
                    "static_expanded_score": sum(float(signals.loc[index, name]) for name in available)/len(available) if available else 0.0,
                    "adaptive_score": score, "adaptive_action": _action(score),
                    "indicators_considered": ";".join(available),
                    "indicators_unavailable": ";".join(unavailable),
                    "ensemble_version": VERSION, "shadow_only": True,
                }
                for indicator in INDICATORS:
                    output[f"{indicator}_signal"] = signals.loc[index, indicator]
                    output[f"{indicator}_weight"] = weights.get(indicator, np.nan)
                    output[f"{indicator}_contribution"] = contributions.get(indicator, np.nan)
                outputs.append(output)
    return pd.DataFrame(outputs)


def generate() -> dict:
    output = build_ensemble(pd.read_csv(FEATURES))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False, lineterminator="\n")
    weight_columns = [f"{name}_weight" for name in INDICATORS]
    summary = {
        "version": VERSION, "path": OUTPUT.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "rows": len(output), "actions": output["adaptive_action"].value_counts().to_dict(),
        "non_neutral_weight_cells": int(sum((output[column]-1).abs().gt(1e-12).sum() for column in weight_columns)),
        "threshold": .35, "shadow_only": True,
        "explainability_columns": [column for column in output.columns if column.endswith(("_signal", "_weight", "_contribution"))],
    }
    SUMMARY.write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(generate())
