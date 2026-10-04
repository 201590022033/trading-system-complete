"""Causal display diagnostics; estimates never enter a trading chart or policy."""
from math import isfinite

VERSION = "swing-display-quality-v1"
FIELDS = ("open", "high", "low", "close")


def real_ohlc(row):
    if row.get("estimated") or row.get("price_quality") == "ESTIMATED":
        return False
    try:
        o, h, l, c = (float(row[key]) for key in FIELDS)
        return all(isfinite(v) and v > 0 for v in (o, h, l, c)) and l <= min(o, c) and h >= max(o, c)
    except (KeyError, ValueError, TypeError, OverflowError):
        return False


def diagnostics(bars):
    """Keep observed dates; never invent exchange sessions or average volume."""
    good, issues, run = [], [], 0
    for row in bars:
        if real_ohlc(row):
            good.append(row)
            run += 1
            continue
        # Only an isolated damaged observation after real observations receives
        # a display estimate. No recursive estimates or future neighbours.
        prior = good[-5:] if run else []
        estimate = ({key: sum(float(r[key]) for r in prior)/len(prior) for key in FIELDS}
                    if prior else None)
        issues.append({"session": row["timestamp"][:10], "reason": "INVALID_OR_MISSING_OHLC",
                       "price_quality": "ESTIMATED" if estimate else "UNAVAILABLE",
                       "display_ohlc": estimate, "volume": None,
                       "basis_sessions": [r["timestamp"][:10] for r in prior]})
        run = 0
    windows = {}
    for window in (10, 20):
        prior = bars[-window-1:-1]
        valid = len(prior) == window and all(real_ohlc(r) for r in prior)
        windows[str(window)] = {"state": "REAL_DATA_AVAILABLE" if valid else "REAL_DATA_REQUIRED",
                               "high": max(float(r["high"]) for r in prior) if valid else None,
                               "low": min(float(r["low"]) for r in prior) if valid else None}
    return {"version": VERSION, "purpose": "DISPLAY_ONLY_NOT_POLICY_INPUT",
            "invalid_ohlc_count": len(issues), "issues": issues[-10:],
            "issues_truncated": len(issues) > 10,
            "estimate_method": "MEAN_OF_UP_TO_5_PRECEDING_REAL_OHLC_BARS",
            "calendar": "OBSERVED_DATES_ONLY_MISSING_SESSIONS_NOT_VERIFIED",
            "indicator_checks": {"close_indicators": "INDEPENDENT_VALID_CLOSES",
                                 "atr": "REAL_FULL_HISTORY_REQUIRED" if issues else "REAL_DATA_AVAILABLE",
                                 "prior_structure": windows},
            "policy_admissible": False}
