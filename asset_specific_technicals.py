"""Build HR7 point-in-time technical contexts by asset and profile."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


VERSION = "asset-specific-technicals-v1"
ROOT = Path(__file__).parent
RAW = ROOT / "analysis" / "data" / "hr2"
CROSS = ROOT / "analysis" / "data" / "hr3" / "cross_asset_features.csv"
OUTPUT = ROOT / "analysis" / "data" / "hr7" / "asset_technical_features.csv"
MANIFEST = ROOT / "analysis" / "results" / "asset_technical_availability.json"
ASSETS = {
    "NPN": ("npn", "equity", "offshore_earner"),
    "SASOL": ("sasol", "equity", "energy_sasol"),
    "BHP": ("bhp", "equity", "diversified_mining"),
    "IMPJ": ("impj", "equity", "pgm_mining"),
    "SHPJ": ("shpj", "equity", "retail_consumer"),
    "ABSPJ": ("abspj", "equity", "banks_financials"),
    "USDZAR": ("usdzar", "fx", "usdzar"),
    "GOLD": ("gold", "commodity_future_proxy", "gold"),
    "BRENT": ("brent", "commodity_future_proxy", "energy"),
    "JSE_ALL_SHARE_PROXY": ("jse_all_share_proxy", "equity_index", "jse_index"),
}


def _classify(series: pd.Series, upper: float, lower: float, positive: str, negative: str, neutral: str) -> pd.Series:
    result = pd.Series(index=series.index, dtype="object")
    result.loc[series.notna()] = neutral
    result.loc[series >= upper] = positive
    result.loc[series <= lower] = negative
    return result


def build_asset_features(frame: pd.DataFrame, instrument: str, asset_class: str, profile: str, benchmark: pd.DataFrame | None = None) -> pd.DataFrame:
    data = frame.copy()
    data["event_time"] = pd.to_datetime(data["event_time"], utc=True)
    data = data.sort_values("event_time").set_index("event_time")
    for column in ("open", "high", "low", "close", "volume"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    close, high, low, open_, volume = (data[name] for name in ("close", "high", "low", "open", "volume"))
    delta = close.diff()
    gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
    avg_gain, avg_loss = gain.rolling(14).mean(), loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.where(avg_loss != 0, np.where(avg_gain > 0, 100.0, 50.0)).where(avg_gain.notna())
    sma_fast, sma_slow = close.rolling(5).mean(), close.rolling(20).mean()
    sma_diff = sma_fast / sma_slow - 1
    prior_high, prior_low = close.rolling(19).max().shift(1), close.rolling(19).min().shift(1)
    range14_high, range14_low = close.rolling(14).max(), close.rolling(14).min()
    stochastic = 100 * (close - range14_low) / (range14_high - range14_low).replace(0, np.nan)
    rsi_signal = np.select([rsi < 30, rsi > 70], [1, -1], default=0)
    sma_signal = np.select([sma_diff > .001, sma_diff < -.001], [1, -1], default=0)
    breakout_signal = np.select([close > prior_high, close < prior_low], [1, -1], default=0)
    stochastic_signal = np.select([stochastic < 20, stochastic > 80], [1, -1], default=0)
    ema12, ema26 = close.ewm(span=12, adjust=False).mean(), close.ewm(span=26, adjust=False).mean()
    middle, std20 = close.rolling(20).mean(), close.rolling(20).std(ddof=0)
    previous = close.shift(1)
    true_range = pd.concat((high-low, (high-previous).abs(), (low-previous).abs()), axis=1).max(axis=1)
    atr = true_range.rolling(14).mean()
    up_move, down_move = high.diff(), -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    tr_sum = true_range.rolling(14).sum()
    plus_di, minus_di = 100*plus_dm.rolling(14).sum()/tr_sum, 100*minus_dm.rolling(14).sum()/tr_sum
    dx = 100*(plus_di-minus_di).abs()/(plus_di+minus_di).replace(0, np.nan)
    tenkan = (high.rolling(9).max()+low.rolling(9).min())/2
    kijun = (high.rolling(26).max()+low.rolling(26).min())/2
    visible_a = ((tenkan+kijun)/2).shift(26)
    visible_b = ((high.rolling(52).max()+low.rolling(52).min())/2).shift(26)
    cloud_top, cloud_bottom = pd.concat((visible_a, visible_b), axis=1).max(axis=1), pd.concat((visible_a, visible_b), axis=1).min(axis=1)
    ichimoku_direction = pd.Series(np.nan, index=data.index)
    cloud_available = visible_a.notna() & visible_b.notna()
    ichimoku_direction.loc[cloud_available] = 0
    ichimoku_direction.loc[cloud_available & (close > cloud_top)] = 1
    ichimoku_direction.loc[cloud_available & (close < cloud_bottom)] = -1
    trend_return = close.pct_change(20, fill_method=None)
    realized_vol = close.pct_change(fill_method=None).rolling(20).std(ddof=0)
    result = pd.DataFrame({
        "instrument": instrument, "asset_class": asset_class, "profile": profile,
        "available_time": data["available_time"], "decision_time": data["available_time"],
        "feature_version": VERSION, "close": close,
        "technical_warmup_complete": np.arange(len(data)) >= 19,
        "rsi": rsi, "rsi_signal": rsi_signal, "sma_fast": sma_fast, "sma_slow": sma_slow,
        "sma_signal": sma_signal, "breakout_signal": breakout_signal,
        "stochastic": stochastic, "stochastic_signal": stochastic_signal,
        "raw_technical_score": .35*rsi_signal+.30*sma_signal+.20*breakout_signal+.15*stochastic_signal,
        "macd": ema12-ema26, "bollinger_zscore": (close-middle)/std20.replace(0, np.nan),
        "atr_ratio": atr/close, "adx": dx.rolling(14).mean(), "dmi_direction": np.sign(plus_di-minus_di),
        "ichimoku_direction": ichimoku_direction,
        "ichimoku_cloud_thickness": (visible_a-visible_b).abs()/close,
        "ichimoku_tk_direction": np.sign(tenkan-kijun),
        "ichimoku_distance_kijun": close/kijun-1,
        "trend_return_20": trend_return, "realized_volatility_20": realized_vol,
        "trend_regime": _classify(trend_return, .02, -.02, "bull", "bear", "range"),
        "volatility_regime": _classify(realized_vol, .025, .008, "high", "low", "normal"),
        "relative_volume": volume/volume.rolling(20).mean().shift(1).replace(0, np.nan),
        "gap_return": open_/previous-1,
    }, index=data.index)
    if benchmark is not None:
        bench = benchmark.copy()
        bench["event_time"] = pd.to_datetime(bench["event_time"], utc=True)
        bench = bench.set_index("event_time")["close"].astype(float)
        result["relative_strength_20"] = close.pct_change(20, fill_method=None) - bench.pct_change(20, fill_method=None).reindex(result.index)
    else:
        result["relative_strength_20"] = np.nan
    return result.reset_index()


def generate() -> dict:
    benchmark = pd.read_csv(RAW / "jse_all_share_proxy.csv")
    cross = pd.read_csv(CROSS)
    cross["event_time"] = pd.to_datetime(cross["event_time"], utc=True)
    context_columns = ["event_time", "usdzar_return_20", "rand_regime_20", "vix_zscore_20",
                       "dxy_zscore_20", "us10y_return_20", "gold_zar_return_20",
                       "brent_zar_return_20", "platinum_zar_return_20",
                       "palladium_zar_return_20", "global_risk_composite"]
    outputs = []
    availability = []
    for instrument, (filename, asset_class, profile) in ASSETS.items():
        raw = pd.read_csv(RAW / f"{filename}.csv")
        features = build_asset_features(raw, instrument, asset_class, profile, benchmark if asset_class == "equity" else None)
        features = features.merge(cross[context_columns], on="event_time", how="left", validate="one_to_one")
        outputs.append(features)
        availability.append({
            "instrument": instrument, "asset_class": asset_class, "profile": profile,
            "rows": len(features), "ohlcv": True, "daily_technicals": True,
            "cross_asset_context": True, "intraday": False,
            "basis": False, "open_interest": False, "term_structure": False,
            "market_breadth": False,
        })
    combined = pd.concat(outputs, ignore_index=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT, index=False, lineterminator="\n")
    manifest = {
        "version": VERSION, "path": OUTPUT.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "rows": len(combined), "instruments": availability,
        "capability_unavailable": ["intraday VWAP", "anchored VWAP", "opening range", "session momentum", "basis", "open interest", "term structure", "calendar spreads", "roll yield", "JSE breadth"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = generate()
    print(result["rows"], len(result["instruments"]))
