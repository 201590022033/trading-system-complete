"""Point-in-time South African cross-asset features for HR3 research."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_VERSION = "sa-cross-asset-v1"
ROOT = Path(__file__).parent
RAW_DIR = ROOT / "analysis" / "data" / "hr2"
OUTPUT = ROOT / "analysis" / "data" / "hr3" / "cross_asset_features.csv"
MANIFEST = ROOT / "analysis" / "results" / "cross_asset_feature_manifest.json"
CROSS_ASSETS = (
    "usdzar", "vix", "sp500", "dxy", "us10y", "brent", "gold",
    "platinum", "palladium", "jse_all_share_proxy",
)


def _single_series(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    data = frame[["event_time", "available_time", "close"]].copy()
    data["event_time"] = pd.to_datetime(data["event_time"], utc=True)
    data = data.sort_values("event_time").set_index("event_time")
    close = pd.to_numeric(data["close"], errors="coerce")
    result = pd.DataFrame(index=data.index)
    result[f"{name}_close"] = close
    for horizon in (1, 5, 20):
        result[f"{name}_return_{horizon}"] = close.pct_change(horizon, fill_method=None)
    returns = close.pct_change(fill_method=None)
    result[f"{name}_realized_volatility_20"] = returns.rolling(20, min_periods=20).std(ddof=0)
    mean20 = close.rolling(20, min_periods=20).mean()
    std20 = close.rolling(20, min_periods=20).std(ddof=0)
    result[f"{name}_trend_deviation_20"] = close / mean20 - 1.0
    result[f"{name}_zscore_20"] = (close - mean20) / std20.replace(0.0, np.nan)
    return result


def build_features(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build exact-date features; never forward-fill a missing market session."""
    individual = {name: _single_series(frame, name) for name, frame in frames.items()}
    result = pd.concat(individual.values(), axis=1, join="outer", sort=False).sort_index()

    def interaction(left: str, right: str, output: str) -> None:
        level = result[f"{left}_close"] * result[f"{right}_close"]
        result[output] = level
        result[f"{output}_return_5"] = level.pct_change(5, fill_method=None)
        result[f"{output}_return_20"] = level.pct_change(20, fill_method=None)

    interaction("gold", "usdzar", "gold_zar")
    interaction("brent", "usdzar", "brent_zar")
    interaction("platinum", "usdzar", "platinum_zar")
    interaction("palladium", "usdzar", "palladium_zar")

    rand_return = result["usdzar_return_20"]
    rand_regime = pd.Series(index=result.index, dtype="object")
    rand_regime.loc[rand_return.notna()] = "neutral"
    rand_regime.loc[rand_return > 0.03] = "rand_weakening"
    rand_regime.loc[rand_return < -0.03] = "rand_strengthening"
    result["rand_regime_20"] = rand_regime
    # Continuous context; no claim that either sign is universally risk-on/off.
    result["global_risk_composite"] = (
        result["vix_zscore_20"]
        - result["sp500_zscore_20"]
        + result["dxy_zscore_20"]
    ) / 3.0
    result.insert(0, "available_time", [
        (timestamp + pd.Timedelta(days=1)).isoformat() for timestamp in result.index
    ])
    result.insert(1, "decision_time", result["available_time"])
    result.insert(2, "feature_version", FEATURE_VERSION)
    return result.reset_index()


def generate() -> dict:
    frames = {
        name: pd.read_csv(RAW_DIR / f"{name}.csv")
        for name in CROSS_ASSETS
    }
    output = build_features(frames)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False, lineterminator="\n")
    manifest = {
        "version": FEATURE_VERSION,
        "path": OUTPUT.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "rows": len(output), "feature_columns": len(output.columns) - 4,
        "first_event_time": output["event_time"].iloc[0].isoformat(),
        "last_event_time": output["event_time"].iloc[-1].isoformat(),
        "no_lookahead": "rolling and return features use current/prior observations only; exact-date joins; no forward fill",
        "interactions": ["gold_zar", "brent_zar", "platinum_zar", "palladium_zar"],
        "unavailable": ["SARB rate", "SA yield curve", "CPI vintages", "economic surprises", "US real yield"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(generate())
