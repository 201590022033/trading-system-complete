"""Offline compact research build: existing Yahoo normalizer, no Railway downloads.

Run explicitly; protected HR2/HR9/HR10 artifacts are never regenerated.
Raw download snapshots stay in ignored analysis/cache; compact evidence ships
with code. A failed ticker stays explicitly unavailable, never zero-filled.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from historical_reconstruction import normalize_history
from application.opportunities.public_research import public_share_catalog, public_etf_catalog
from application.opportunities.swing_history import BENCHMARK, REPORT, VERSION, summarize_history


def main():
    import yfinance as yf
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--cached", action="store_true", help="re-evaluate existing hashed local snapshots without downloads")
    args = parser.parse_args()
    cutoff = datetime.now(timezone.utc)
    cache = Path("analysis/cache/swing_history_v1")
    cache.mkdir(parents=True, exist_ok=True)
    catalog = {**public_share_catalog(), **public_etf_catalog()}
    charts, sources, unavailable = {}, {}, {}
    for key, info in catalog.items():
        try:
            if args.cached:
                import pandas as pd
                paths = sorted(cache.glob(f"{key}-*.csv"), key=lambda p:p.stat().st_mtime)
                if not paths:
                    raise ValueError("missing cached snapshot")
                raw = paths[-1].read_bytes()
                normalized = pd.read_csv(paths[-1])
            else:
                frame = yf.download(info["yahoo_symbol"], start=args.start, auto_adjust=False,
                                    actions=False, progress=False, threads=False, timeout=15)
                normalized = normalize_history(frame, cutoff)
                raw = normalized.to_csv(index=False, lineterminator="\n").encode("utf-8")
            if len(normalized) < 30:
                raise ValueError("insufficient history")
            digest = hashlib.sha256(raw).hexdigest()
            path = cache / f"{key}-{digest[:16]}.csv"
            if not path.exists():
                path.write_bytes(raw)
            charts[key] = {"symbol": info["yahoo_symbol"], "bars": [
                {"timestamp": str(row.event_time), "close": float(row.close)}
                for row in normalized.itertuples()]}
            sources[key] = digest
            print(f"{key}: {len(normalized)} sessions", flush=True)
        except Exception as exc:
            unavailable[key] = {"state": "UNAVAILABLE", "reason": type(exc).__name__}
            print(f"{key}: unavailable ({type(exc).__name__})", flush=True)
    if not charts:
        raise SystemExit("No history retrieved; existing report retained")
    report = {"version": VERSION, "available_at": datetime.now(timezone.utc).isoformat(),
              "requested_start": args.start, "build_mode": "CACHED" if args.cached else "YAHOO_DOWNLOAD",
              "benchmark": BENCHMARK, "instruments": {},
              "unavailable": unavailable, "limitations": [
                  "REVISED_YAHOO_HISTORY_NOT_POINT_IN_TIME_VINTAGES",
                  "CLOSE_ONLY_NO_INTRABAR_STOP_OR_TARGET_EVIDENCE",
                  "20BPS_ROUND_TRIP_ASSUMED_NOT_ACTUAL_OST_FEES",
                  "FINAL_THIRD_TEMPORAL_HOLDOUT_FIXED_RULES_NOT_TRAINED_MODEL",
                  "DESCRIPTIVE_INTERVAL_NOT_MULTIPLE_TESTING_ADMISSION",
                  "CURRENT_NEWS_NOT_BACKFILLED_AS_HISTORICAL_SENTIMENT",
                  "NO_PROFITABILITY_OR_PRODUCTION_PROMOTION"]}
    report["limitations"].extend(["UNADJUSTED_PRICE_RETURN_NOT_DIVIDEND_TOTAL_RETURN",
                                "DISCONTINUOUS_WINDOWS_QUARANTINED_EXCLUSIONS_CAN_BIAS_RESULTS"])
    for key, chart in charts.items():
        report["instruments"][key] = {"symbol": chart["symbol"], "source_sha256": sources[key],
            **summarize_history(chart, charts.get(BENCHMARK), cutoff=cutoff)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    print(f"Compact report: {REPORT.stat().st_size} bytes; {len(charts)} instruments")


if __name__ == "__main__":
    main()
