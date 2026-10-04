"""Bounded IG data readiness beside cash Swing; no substitution or orders."""
from datetime import timedelta
from domain.broker.ig import IGConfig, IGReadOnlyAdapter, IGRequestError

VERSION = "ig-swing-data-readiness-v1"
# Found by authenticated Demo search on 2026-10-04. Candidates, not cash mappings.
CANDIDATES = {"SASOL": "AR.D.SOLSJ.CASH.IP", "NPN": "AR.D.NPNSJ.CASH.IP",
              "SHPJ": "AR.D.SHPSJ.CASH.IP"}


def investigate(adapter, universe, evaluated_at):
    """At most three 70-point/one-page DAY requests; stop on quota/auth errors."""
    keys = [key for key in universe if key in CANDIDATES]
    result = {"version": VERSION, "evaluated_at": evaluated_at.isoformat(),
              "environment": adapter.config.environment, "state": "BLOCKED",
              "live_execution": False, "cash_swing_admitted": False,
              "price_basis": "IG_DERIVED_MID_NOT_CASH_EXCHANGE_OHLC",
              "unmapped": [key for key in universe if key not in CANDIDATES],
              "instruments": {}, "required_action":
              "VERIFY_IG_EQUITY_ENTITLEMENT_THEN_JSE_VOLUME_AND_CASH_PRICE_BASIS"}
    if not keys:
        result["state"] = "NO_VERIFIED_CANDIDATE"
        return result
    try:
        adapter.authenticate()
    except IGRequestError as error:
        result["error"] = error.history_diagnostic()
        return result
    for key in keys:
        epic = CANDIDATES[key]
        try:
            series = adapter.get_historical_prices(epic, "DAY", evaluated_at-timedelta(days=90),
                evaluated_at, max_points=70, page_size=70, max_pages=1,
                retrieved_at=evaluated_at)
            result["instruments"][key] = {"epic": epic, "mapping_status": "CANDIDATE_ONLY",
                "state": "SEMANTICS_VALIDATION_REQUIRED", "history": series.summary()}
        except IGRequestError as error:
            result["instruments"][key] = {"epic": epic, "mapping_status": "CANDIDATE_ONLY",
                "state": error.error_category, "error": error.history_diagnostic()}
            if error.error_category in {"RATE_LIMITED", "AUTHENTICATION_FAILED", "INVALID_API_KEY"}:
                break  # Do not multiply failing requests or spend remaining allowance.
    if result["instruments"] and all(row["state"] == "SEMANTICS_VALIDATION_REQUIRED"
                                    for row in result["instruments"].values()):
        result["state"] = "DATA_OBSERVED_NOT_ADMITTED"
    return result


def configured_investigation(universe, evaluated_at):
    import os
    if os.environ.get("PAPER_IG_SWING_DIAGNOSTICS") != "1":
        return {"version": VERSION, "state": "NOT_ENABLED", "cash_swing_admitted": False,
                "live_execution": False}
    try:
        adapter = IGReadOnlyAdapter(IGConfig.from_env(os.environ))
        if adapter.config.environment != "DEMO":
            return {"version": VERSION, "state": "DEMO_REQUIRED", "cash_swing_admitted": False,
                    "live_execution": False}
        return investigate(adapter, universe, evaluated_at)
    except Exception:
        # No raw configuration/transport exception can reach the ledger or API.
        return {"version": VERSION, "state": "CONFIGURATION_OR_PROVIDER_UNAVAILABLE",
                "cash_swing_admitted": False, "live_execution": False}
