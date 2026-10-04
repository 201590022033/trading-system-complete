"""Daily LONG shadow policy and conservative OHLC replay; no order dependency."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
from math import isfinite

from domain.strategy.attribution import fields, reference
from domain.strategy.profile import StrategyProfileRef
from shadow_learning import timestamp

VERSION = "swing-daily-shadow-policy-v1"
PROFILE = StrategyProfileRef("jse_swing_3_5d", "1.2.0")
FEATURE_PROFILE = StrategyProfileRef("jse_swing_3_5d", "1.1.0")
HORIZONS = (3, 4, 5)


def rules():
    """A fresh declaration each time; changes require a new policy/profile version."""
    return {"entry": "FIRST_LATER_OBSERVABLE_CLOSE", "entry_expiry_calendar_days": 7,
            "stop": "LOWER_OF_PRIOR_LOW10_AND_SIGNAL_CLOSE_MINUS_ATR14",
            "target_r_multiple": 2, "trailing": False,
            "exit": "STOP_THEN_TARGET_THEN_HORIZON_CLOSE",
            "same_bar": "STOP_FIRST", "gap_stop": "OPEN_IF_BELOW_STOP",
            "gap_target": "TARGET_LIMIT_NO_PRICE_IMPROVEMENT",
            "entry_bar": "INVALIDATE_IF_LOW_TOUCHES_STOP_NO_PRE_ENTRY_EXIT",
            "holding": "3_4_5_OBSERVED_SESSIONS_AFTER_ENTRY",
            "round_trip_cost_bps_scenarios": [10, 25, 50],
            "cost_basis": "HYPOTHETICAL_ALL_IN_FEE_SPREAD_SLIPPAGE_NOT_OST",
            "setup": "EMA_UPTREND_AND_BREAKOUT20_OR_RECLAIM_AND_RSI50_70_AND_VOLUME_GT1_AND_RELATIVE_RETURN_GT0"}


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build_policy(features, *, decision_at):
    now = timestamp(decision_at)
    if reference(features) != FEATURE_PROFILE or features.get("version") != "swing-ohlcv-wilder-v1":
        raise ValueError("exact Swing 1.1.0 feature source required")
    if not timestamp(features["available_at"]) <= timestamp(features["evaluated_at"]) <= now:
        raise ValueError("future feature input")
    policy = {**fields(PROFILE), "policy_version": VERSION, "rules": rules(),
              "decision_at": now.isoformat(), "signal_session": features["session"],
              "source_feature_sha256": digest(features), "source_feature_profile": fields(FEATURE_PROFILE),
              "source_symbol": features["source_symbol"], "signal_close": features["last_close"], "direction": "LONG",
              "state": "BLOCKED", "reasons": [], "stop_price": None,
              "execution_enabled": False, "live_execution": False,
              "feasibility": "UNRESOLVED_LIQUIDITY_CALENDAR_ACTUAL_COSTS_ACCOUNT_M15_REQUIRED"}
    if features.get("state") != "AVAILABLE" or features.get("missing"):
        policy["reasons"] = ["COMPLETE_CAUSAL_FEATURES_REQUIRED"]
        return policy
    conditions = features.get("conditions", {})
    required = ("ema_uptrend", "rsi_50_70", "volume_above_prior20", "outperforming_benchmark20")
    if any(type(conditions.get(key)) is not bool for key in (*required, "breakout20", "ema20_reclaim", "core_setup")):
        policy["reasons"] = ["EXPLICIT_SETUP_CONDITIONS_REQUIRED"]
        return policy
    setup = all(conditions[key] for key in required) and (conditions["breakout20"] or conditions["ema20_reclaim"])
    if setup != conditions["core_setup"]:
        raise ValueError("inconsistent feature setup")
    if not setup:
        policy.update(state="NO_SETUP", reasons=["PREREGISTERED_SETUP_ABSENT"])
        return policy
    try:
        close = float(features["last_close"])
        atr = float(features["values"]["atr14_wilder"])
        low = float(features["values"]["prior_low10"])
        if not all(isfinite(x) and x > 0 for x in (close, atr, low)):
            raise ValueError()
        stop = min(low, close-atr)
        if not 0 < stop < close:
            raise ValueError()
    except (KeyError, TypeError, ValueError, OverflowError):
        policy["reasons"] = ["POSITIVE_STRUCTURAL_ATR_GEOMETRY_REQUIRED"]
        return policy
    policy.update(state="SHADOW_READY", stop_price=stop, reasons=["HYPOTHESIS_NOT_VALIDATED"])
    return policy


def simulate(policy, chart, *, evaluated_at, horizon_sessions):
    """Replay only completed daily bars. Returns pending/blocked/terminal, never an order."""
    from application.opportunities.public_research import _available_at
    from application.opportunities.swing_technical import usable_bars
    if reference(policy) != PROFILE or policy.get("policy_version") != VERSION or policy.get("rules") != rules():
        raise ValueError("exact immutable shadow policy required")
    if horizon_sessions not in HORIZONS:
        raise ValueError("explicit 3/4/5-session horizon required")
    now, decision = timestamp(evaluated_at), timestamp(policy["decision_at"])
    if now < decision:
        raise ValueError("evaluation precedes policy")
    result = {**fields(PROFILE), "policy_version": VERSION, "horizon_sessions": horizon_sessions,
              "state": "PENDING_ENTRY", "reason": None, "governance": "SHADOW_NOT_PROMOTED",
              "execution_enabled": False, "live_execution": False}
    if policy["state"] != "SHADOW_READY":
        return {**result, "state": policy["state"], "reason": policy["reasons"][0]}
    expiry = decision + timedelta(days=rules()["entry_expiry_calendar_days"])
    try:
        if chart.get("symbol") != policy["source_symbol"]:
            raise ValueError("source mismatch")
        bars = usable_bars(chart, now)
        # A retained history must include the original signal session. Never
        # replace a missing first entry with the first bar after truncation.
        signal = [row for row in bars if row["timestamp"][:10] == policy["signal_session"]]
        if len(signal) != 1 or float(signal[0]["close"]) != policy["signal_close"]:
            raise ValueError("signal session missing")
        later = [row for row in bars if _available_at(row["timestamp"]) > decision]
    except (KeyError, TypeError, ValueError, OverflowError):
        return {**result, "state": "DATA_UNAVAILABLE", "reason": "MATCHING_COMPLETE_HISTORY_REQUIRED"}
    if not later:
        return {**result, "state": "EXPIRED" if now > expiry else "PENDING_ENTRY", "reason": "NO_LATER_OBSERVABLE_CLOSE"}
    if _available_at(later[0]["timestamp"]) > expiry:
        return {**result, "state": "EXPIRED", "reason": "ENTRY_WINDOW_EXPIRED"}
    path = []
    for index, row in enumerate(later[:horizon_sessions+1]):
        try:
            from application.opportunities.swing_data_quality import real_ohlc
            if not real_ohlc(row):
                raise ValueError("real OHLC required")
            o, h, l, c = (float(row[key]) for key in ("open", "high", "low", "close"))
            if not all(isfinite(x) and x > 0 for x in (o, h, l, c)) or l > min(o, c) or h < max(o, c):
                raise ValueError("invalid OHLC")
        except (KeyError, TypeError, ValueError, OverflowError):
            return {**result, "state": "DATA_UNAVAILABLE", "reason": "REAL_VALID_OHLC_REQUIRED",
                    "path": deepcopy(path), "path_sha256": digest(path)}
        path.append({key: row[key] for key in ("timestamp", "open", "high", "low", "close")})
        if index == 0:
            stop, entry = policy["stop_price"], c
            if l <= stop or entry <= stop:
                return {**result, "state": "INVALIDATED", "reason": "STOP_TOUCHED_BEFORE_ENTRY_CLOSE"}
            target = entry + rules()["target_r_multiple"]*(entry-stop)
            result.update(state="OPEN", entry_price=entry, stop_price=stop, target_price=target,
                          entry_session=row["timestamp"][:10], entry_observed_at=_available_at(row["timestamp"]).isoformat())
            continue
        exit_price, reason, ambiguous = None, None, l <= stop and h >= target
        if o <= stop:
            exit_price, reason = o, "GAP_STOP"
        elif o >= target:
            # The opening quote establishes target before the later daily range.
            exit_price, reason, ambiguous = target, "GAP_TARGET_LIMIT", False
        elif l <= stop:
            exit_price, reason = stop, "AMBIGUOUS_STOP_FIRST" if ambiguous else "STOP"
        elif h >= target:
            exit_price, reason = target, "TARGET"
        elif index == horizon_sessions:
            exit_price, reason = c, "HORIZON_CLOSE"
        if exit_price is not None:
            gross = exit_price/entry-1
            return {**result, "state": "CLOSED", "reason": reason, "ambiguous_bar": ambiguous,
                    "exit_price": exit_price, "exit_session": row["timestamp"][:10],
                    "exit_observed_at": _available_at(row["timestamp"]).isoformat(),
                    "held_observed_sessions": index, "gross_return": gross,
                    "gross_r_multiple": (exit_price-entry)/(entry-stop),
                    "net_return_scenarios": {str(bps): gross-bps/10000 for bps in rules()["round_trip_cost_bps_scenarios"]},
                    "cost_basis": rules()["cost_basis"], "path": deepcopy(path), "path_sha256": digest(path),
                    "calendar_basis": "OBSERVED_PROVIDER_SESSIONS_NOT_VERIFIED_EXCHANGE_CALENDAR"}
    return {**result, "path": deepcopy(path), "path_sha256": digest(path)}
