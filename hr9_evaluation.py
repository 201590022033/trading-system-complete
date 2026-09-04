"""Causal research evaluation for the HR9 shadow technical ensemble."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from adaptive_technical_ensemble import OUTPUT, PRE_HR9_BASELINE, VERSION
from indicator_effectiveness import MINIMUM_SAMPLE
from technical_signals import INDICATORS


ROOT = Path(__file__).parent
REPORT = ROOT / "analysis" / "results" / "hr9_adaptive_ensemble_evaluation.json"
EVALUATION_VERSION = "hr9-causal-evaluation-v1"
COST_SCENARIOS_BPS = (0.0, 10.0, 25.0)
MODELS = ("legacy_raw", "static_expanded", "pre_hr9_adaptive", "hr9_adaptive")


def _position(score: pd.Series) -> pd.Series:
    return pd.Series(np.select([score > .35, score < -.35], [1, -1], default=0), index=score.index)


def _wilson(wins: int, count: int) -> tuple[float, float]:
    if not count:
        return 0.0, 1.0
    z = 1.96
    p = wins / count
    denominator = 1 + z*z/count
    centre = (p + z*z/(2*count))/denominator
    margin = z*math.sqrt(p*(1-p)/count + z*z/(4*count*count))/denominator
    return max(0.0, centre-margin), min(1.0, centre+margin)


def _metrics(frame: pd.DataFrame, position: pd.Series, cost_bps: float) -> dict:
    valid = frame["forward_return"].notna()
    position = position.astype(int)
    turnover = position.diff().abs().fillna(position.abs())
    aligned = position * frame["forward_return"]
    net = aligned - turnover * cost_bps / 10000.0
    active = valid & position.ne(0)
    wins = int((aligned[active] > 0).sum())
    count = int(active.sum())
    ci_low, ci_high = _wilson(wins, count)
    sequence = net[valid].fillna(0.0).cumsum()
    drawdown = sequence - sequence.cummax()
    return {
        "eligible_decisions": int(valid.sum()),
        "active_decisions": count,
        "wins": wins,
        "win_rate": wins/count if count else 0.0,
        "win_rate_ci_low": ci_low,
        "win_rate_ci_high": ci_high,
        "mean_aligned_return": float(aligned[active].mean()) if count else 0.0,
        "mean_net_return_all_decisions": float(net[valid].mean()) if valid.any() else 0.0,
        "turnover_units": float(turnover[valid].sum()),
        "decision_sequence_max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
        "insufficient_sample": count < MINIMUM_SAMPLE,
    }


def evaluate() -> dict:
    old = pd.read_csv(PRE_HR9_BASELINE)
    new = pd.read_csv(OUTPUT)
    keys = ["instrument", "event_time", "horizon"]
    if old.duplicated(keys).any() or new.duplicated(keys).any():
        raise ValueError("decision keys must be unique")
    joined = old.merge(
        new,
        on=keys,
        suffixes=("_pre", "_hr9"),
        validate="one_to_one",
    )
    if len(joined) != len(old) or len(joined) != len(new):
        raise ValueError("pre-HR9 and HR9 decision universes do not align")

    score_columns = {
        "legacy_raw": "raw_technical_score_hr9",
        "static_expanded": "static_expanded_score_hr9",
        "pre_hr9_adaptive": "adaptive_score_pre",
        "hr9_adaptive": "adaptive_score_hr9",
    }
    rows = []
    for (instrument, horizon), asset in joined.groupby(["instrument", "horizon"], sort=True):
        asset = asset.sort_values("event_time").reset_index(drop=True)
        asset["forward_return"] = asset["close_hr9"].shift(-int(horizon))/asset["close_hr9"]-1
        midpoint = len(asset)//2
        segments = (("overall", asset), ("early_half", asset.iloc[:midpoint].copy()), ("late_half", asset.iloc[midpoint:].copy()))
        for segment, selected in segments:
            for model, score_column in score_columns.items():
                positions = _position(selected[score_column])
                for cost_bps in COST_SCENARIOS_BPS:
                    rows.append({
                        "instrument": instrument,
                        "profile": selected["profile_hr9"].iloc[0],
                        "horizon": int(horizon),
                        "horizon_role": selected["horizon_role"].iloc[0],
                        "segment": segment,
                        "model": model,
                        "cost_bps_per_turnover_unit": cost_bps,
                        **_metrics(selected, positions, cost_bps),
                    })

    evidence_columns = [f"{name}_evidence_observations" for name in INDICATORS]
    weight_columns = [f"{name}_weight" for name in INDICATORS]
    sample_gate_violations = 0
    for evidence_column, weight_column in zip(evidence_columns, weight_columns):
        changed = new[weight_column].notna() & new[weight_column].sub(1.0).abs().gt(1e-12)
        sample_gate_violations += int((changed & new[evidence_column].lt(MINIMUM_SAMPLE)).sum())

    result = {
        "version": EVALUATION_VERSION,
        "ensemble_version": VERSION,
        "method": "causal/prequential decisions; outcome t to t+h; action-state turnover; overlapping horizon outcomes are decision diagnostics, not a portfolio equity curve",
        "baseline_definitions": {
            "legacy_raw": "unchanged raw_technical_score from the frozen HR7 feature dataset",
            "static_expanded": "equal-weight mean of available authoritative technical signals",
            "pre_hr9_adaptive": "immutable adaptive-technical-ensemble-v1 audit baseline",
            "hr9_adaptive": "v2 shared-signal, turnover-corrected, HR8-contract ensemble",
        },
        "artifact_hashes": {
            "pre_hr9": hashlib.sha256(PRE_HR9_BASELINE.read_bytes()).hexdigest(),
            "hr9": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        },
        "causality_checks": {
            "aligned_decision_rows": len(joined),
            "duplicate_pre_hr9_keys": int(old.duplicated(keys).sum()),
            "duplicate_hr9_keys": int(new.duplicated(keys).sum()),
            "event_after_available_violations": int((pd.to_datetime(new.event_time, utc=True) > pd.to_datetime(new.available_time, utc=True)).sum()),
            "available_after_decision_violations": int((pd.to_datetime(new.available_time, utc=True) > pd.to_datetime(new.decision_time, utc=True)).sum()),
            "sample_gate_violations": sample_gate_violations,
            "shadow_only_false_rows": int((~new.shadow_only.astype(bool)).sum()),
        },
        "cost_scenarios_bps": COST_SCENARIOS_BPS,
        "rows": rows,
    }
    REPORT.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps({"rows": len(result["rows"]), "causality_checks": result["causality_checks"], "artifact_hashes": result["artifact_hashes"]}, indent=2))
