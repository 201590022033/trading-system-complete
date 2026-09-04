"""HR10 robustness evaluation for the HR9 shadow ensemble.

This module is offline research code. It has no Flask, data-provider, or broker
imports and cannot submit orders.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from adaptive_technical_ensemble import OUTPUT, PRE_HR9_BASELINE

ROOT = Path(__file__).parent
RESULT = ROOT / "analysis" / "results" / "hr10_robustness.json"
VERSION = "hr10-robustness-v1"
HORIZONS = (1, 3, 5, 20)
COSTS_BPS = (0.0, 10.0, 25.0)
# Declared before final evaluation: activation threshold is the only parameter
# that can be replayed from the frozen HR9 decision artifact without retraining.
THRESHOLDS = (0.30, 0.35, 0.40)
PRIMARY_THRESHOLD = 0.35
PRIMARY_COST_BPS = 10.0
SEED = 20260904


@dataclass(frozen=True)
class AdmissionRules:
    minimum_trades: int = 30
    minimum_positive_fold_fraction: float = 2 / 3
    maximum_drawdown: float = 0.25
    minimum_cost_stress_mean: float = 0.0
    minimum_sensitivity_positive_fraction: float = 2 / 3
    fdr_alpha: float = 0.05
    require_positive_ci_low: bool = True
    require_legacy_outperformance: bool = True


RULES = AdmissionRules()


def purged_embargoed_folds(count: int, horizon: int, folds: int = 3) -> list[dict]:
    """Expanding temporal folds with H-row purge and H-row embargo gaps."""
    if count < 1 or horizon < 1 or folds < 1:
        raise ValueError("count, horizon and folds must be positive")
    block = count // (folds + 1)
    result = []
    for fold in range(folds):
        nominal = block * (fold + 1)
        train_end = nominal - horizon - 1
        test_start = nominal + horizon
        test_end = min(count, test_start + block)
        if train_end >= 0 and test_start < test_end:
            result.append({
                "fold": fold + 1,
                "train_indices": list(range(0, train_end + 1)),
                "test_indices": list(range(test_start, test_end)),
                "purge_sessions": horizon,
                "embargo_sessions": horizon,
            })
    return result


def positions(scores: pd.Series, threshold: float = PRIMARY_THRESHOLD) -> pd.Series:
    values = pd.to_numeric(scores, errors="coerce")
    return pd.Series(np.select([values > threshold, values < -threshold], [1, -1], default=0), index=scores.index, dtype=int)


def signal_state_returns(close: pd.Series, position: pd.Series, cost_bps: float) -> pd.DataFrame:
    """One-session marked returns; unchanged positions incur no repeated cost."""
    p = position.fillna(0).astype(int)
    turnover = p.diff().abs().fillna(p.abs()).astype(float)
    gross = p * pd.to_numeric(close).pct_change().shift(-1)
    return pd.DataFrame({"position": p, "turnover": turnover, "gross_return": gross,
                         "net_return": gross - turnover * cost_bps / 10000.0})


def non_overlapping_trades(close: pd.Series, position: pd.Series, horizon: int, cost_bps: float) -> pd.DataFrame:
    """Enter after the signal cutoff at close[t], exit at close[t+H].

    Signals received during a holding interval are ignored. Flat signals do not
    consume an interval. Every completed trade pays one entry and one exit unit.
    """
    prices = pd.to_numeric(close).reset_index(drop=True)
    actions = position.reset_index(drop=True).fillna(0).astype(int)
    trades, next_eligible = [], 0
    for entry in range(len(prices)):
        if entry < next_eligible or actions.iloc[entry] == 0:
            continue
        exit_index = entry + horizon
        if exit_index >= len(prices):
            break
        side = int(actions.iloc[entry])
        gross = side * (prices.iloc[exit_index] / prices.iloc[entry] - 1.0)
        trades.append({"entry_index": entry, "exit_index": exit_index, "side": side,
                       "gross_return": float(gross), "turnover": 2.0,
                       "net_return": float(gross - 2 * cost_bps / 10000.0)})
        next_eligible = exit_index
    return pd.DataFrame(trades)


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Return monotone Benjamini-Hochberg adjusted p-values."""
    if not p_values:
        return []
    p = np.asarray(p_values, dtype=float)
    if np.any((p < 0) | (p > 1) | ~np.isfinite(p)):
        raise ValueError("p-values must be finite and between zero and one")
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p)+1))[::-1])[::-1]
    output = np.empty(len(p))
    output[order] = np.minimum(adjusted, 1.0)
    return output.tolist()


def _p_positive(values: np.ndarray) -> float:
    if len(values) < 2 or np.std(values, ddof=1) == 0:
        return 1.0
    z = float(np.mean(values) / (np.std(values, ddof=1) / math.sqrt(len(values))))
    return float(0.5 * math.erfc(z / math.sqrt(2)))


def block_bootstrap_ci(values: np.ndarray, seed: int = SEED, samples: int = 1000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return (0.0, 0.0)
    block = max(1, int(round(math.sqrt(len(values)))))
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(samples):
        chunks = []
        while sum(len(x) for x in chunks) < len(values):
            start = int(rng.integers(0, max(1, len(values)-block+1)))
            chunks.append(values[start:start+block])
        means.append(float(np.mean(np.concatenate(chunks)[:len(values)])))
    return tuple(float(x) for x in np.quantile(means, [0.025, 0.975]))


def _metrics(trades: pd.DataFrame, uncertainty: bool = False) -> dict:
    if trades.empty:
        return {"trades": 0, "mean_net_return": 0.0, "cumulative_net_return": 0.0,
                "median_net_return": 0.0, "win_rate": 0.0, "turnover": 0.0,
                "exposure_sessions": 0, "maximum_drawdown": 0.0, "sharpe": None,
                "sortino": None, "ci_low": 0.0, "ci_high": 0.0, "raw_p_value": 1.0}
    values = trades.net_return.to_numpy(float)
    equity = np.cumprod(1 + values)
    peaks = np.maximum.accumulate(np.r_[1.0, equity])[1:]
    downside = values[values < 0]
    std = np.std(values, ddof=1) if len(values) > 1 else 0.0
    down_std = np.std(downside, ddof=1) if len(downside) > 1 else 0.0
    ci = block_bootstrap_ci(values) if uncertainty else (None, None)
    return {"trades": len(values), "mean_net_return": float(np.mean(values)),
            "cumulative_net_return": float(np.prod(1 + values)-1), "median_net_return": float(np.median(values)),
            "win_rate": float(np.mean(values > 0)), "turnover": float(trades.turnover.sum()),
            "exposure_sessions": int((trades.exit_index-trades.entry_index).sum()),
            "maximum_drawdown": float(np.min(equity/peaks-1)),
            "sharpe": float(np.mean(values)/std*math.sqrt(len(values))) if std else None,
            "sortino": float(np.mean(values)/down_std*math.sqrt(len(values))) if down_std else None,
            "ci_low": ci[0], "ci_high": ci[1], "raw_p_value": _p_positive(values)}


def admission_state(primary: dict, fold_means: list[float], cost25_mean: float,
                    sensitivity_means: list[float], adjusted_p: float, legacy_mean: float,
                    rules: AdmissionRules = RULES) -> tuple[str, list[str]]:
    if primary["trades"] < rules.minimum_trades:
        return "INSUFFICIENT_EVIDENCE", ["minimum_trades"]
    failures = []
    checks = {
        "positive_realistic_cost": primary["mean_net_return"] > 0,
        "positive_uncertainty_bound": (not rules.require_positive_ci_low) or primary["ci_low"] > 0,
        "fold_stability": np.mean(np.asarray(fold_means) > 0) >= rules.minimum_positive_fold_fraction if fold_means else False,
        "drawdown": abs(primary["maximum_drawdown"]) <= rules.maximum_drawdown,
        "cost_stress": cost25_mean > rules.minimum_cost_stress_mean,
        "parameter_stability": np.mean(np.asarray(sensitivity_means) > 0) >= rules.minimum_sensitivity_positive_fraction,
        "multiple_testing": adjusted_p <= rules.fdr_alpha,
        "legacy_comparison": (not rules.require_legacy_outperformance) or primary["mean_net_return"] > legacy_mean,
    }
    failures.extend(name for name, passed in checks.items() if not passed)
    return ("ADMIT_FOR_CONTINUED_SHADOW" if not failures else "REJECT", failures)


def evaluate() -> dict:
    old, new = pd.read_csv(PRE_HR9_BASELINE), pd.read_csv(OUTPUT)
    keys = ["instrument", "event_time", "horizon"]
    joined = old.merge(new, on=keys, suffixes=("_pre", "_hr9"), validate="one_to_one")
    score_columns = {"legacy_raw": "raw_technical_score_hr9", "static_expanded": "static_expanded_score_hr9",
                     "pre_hr9_adaptive": "adaptive_score_pre", "hr9_adaptive": "adaptive_score_hr9"}
    cell_work = []
    for (instrument, horizon), cell in joined.groupby(["instrument", "horizon"], sort=True):
        cell = cell.sort_values("event_time").reset_index(drop=True)
        evaluations = {}
        for model, column in score_columns.items():
            evaluations[model] = {}
            for threshold in THRESHOLDS:
                evaluations[model][str(threshold)] = {}
                for cost in COSTS_BPS:
                    trades = non_overlapping_trades(cell.close_hr9, positions(cell[column], threshold), int(horizon), cost)
                    use_uncertainty = (model == "hr9_adaptive" and threshold == PRIMARY_THRESHOLD
                                       and cost == PRIMARY_COST_BPS)
                    evaluations[model][str(threshold)][str(cost)] = _metrics(trades, use_uncertainty)
        primary = evaluations["hr9_adaptive"][str(PRIMARY_THRESHOLD)][str(PRIMARY_COST_BPS)]
        folds = purged_embargoed_folds(len(cell), int(horizon))
        fold_means = []
        fold_metadata = []
        for fold in folds:
            selected = cell.iloc[fold["test_indices"]]
            trades = non_overlapping_trades(selected.close_hr9, positions(selected.adaptive_score_hr9), int(horizon), PRIMARY_COST_BPS)
            fold_means.append(_metrics(trades)["mean_net_return"])
            fold_metadata.append({"fold": fold["fold"], "train_start": min(fold["train_indices"]),
                                  "train_end": max(fold["train_indices"]), "train_count": len(fold["train_indices"]),
                                  "test_start": min(fold["test_indices"]), "test_end": max(fold["test_indices"]),
                                  "test_count": len(fold["test_indices"]), "purge_sessions": fold["purge_sessions"],
                                  "embargo_sessions": fold["embargo_sessions"]})
        cell_work.append({"instrument": instrument, "horizon": int(horizon), "folds": fold_metadata,
                          "fold_mean_net_returns": fold_means, "evaluations": evaluations,
                          "raw_p_value": primary["raw_p_value"]})
    adjusted = benjamini_hochberg([x["raw_p_value"] for x in cell_work])
    counts = {"ADMIT_FOR_CONTINUED_SHADOW": 0, "REJECT": 0, "INSUFFICIENT_EVIDENCE": 0}
    for cell, adjusted_p in zip(cell_work, adjusted):
        ev = cell["evaluations"]
        primary = ev["hr9_adaptive"][str(PRIMARY_THRESHOLD)][str(PRIMARY_COST_BPS)]
        state, failures = admission_state(primary, cell["fold_mean_net_returns"],
            ev["hr9_adaptive"][str(PRIMARY_THRESHOLD)]["25.0"]["mean_net_return"],
            [ev["hr9_adaptive"][str(x)][str(PRIMARY_COST_BPS)]["mean_net_return"] for x in THRESHOLDS],
            adjusted_p, ev["legacy_raw"][str(PRIMARY_THRESHOLD)][str(PRIMARY_COST_BPS)]["mean_net_return"])
        cell.update({"adjusted_p_value": adjusted_p, "admission_state": state, "failed_gates": failures})
        counts[state] += 1
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = "UNKNOWN"
    result = {"version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(), "code_commit": commit,
              "command": "python hr10_robustness.py", "seed": SEED,
              "design": {"horizons": HORIZONS, "costs_bps": COSTS_BPS, "thresholds_predeclared": THRESHOLDS,
                         "primary_threshold": PRIMARY_THRESHOLD, "primary_cost_bps": PRIMARY_COST_BPS,
                         "purge_sessions": "target horizon", "embargo_sessions": "target horizon",
                         "multiple_testing": "Benjamini-Hochberg FDR across 40 primary instrument×horizon hypotheses",
                         "uncertainty": "moving-block bootstrap; block length round(sqrt(number of trades))",
                         "admission_rules": asdict(RULES)},
              "artifact_hashes": {"pre_hr9": hashlib.sha256(PRE_HR9_BASELINE.read_bytes()).hexdigest(),
                                  "hr9": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()},
              "admission_counts": counts, "cells": cell_work}
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["output_sha256"] = hashlib.sha256(RESULT.read_bytes()).hexdigest()
    return result


if __name__ == "__main__":
    summary = evaluate()
    print(json.dumps({"version": summary["version"], "admission_counts": summary["admission_counts"],
                      "output_sha256": summary["output_sha256"]}, indent=2))
