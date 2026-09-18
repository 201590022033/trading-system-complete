"""Safe read-only broker account/position view for the dashboard."""
from __future__ import annotations
import os
from datetime import datetime
from enum import Enum
from ai_config import project_environment
from domain.broker.ig import IGConfig, IGReadOnlyAdapter, IGRequestError

def _json(value):
    if isinstance(value, Enum): return value.value
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, dict): return {key: _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [_json(item) for item in value]
    return value

def unavailable(reason="IG read-only account status is disabled"):
    return {"state":"UNAVAILABLE","broker":"IG","environment":"DEMO","reason":reason,"accounts":(),"positions":(),"live_execution":False}

def read_only_ig_status(environ=None):
    env=os.environ if environ is None else environ
    if env.get("IG_ACCOUNT_STATUS_ENABLED","").strip().upper() not in {"1","TRUE","YES"}: return unavailable()
    if env.get("IG_ENVIRONMENT", "DEMO").strip().upper() != "DEMO": return unavailable("IG account dashboard is restricted to DEMO")
    config=IGConfig.from_env(project_environment(env))
    if config.environment != "DEMO": return unavailable("IG account dashboard is restricted to DEMO")
    adapter=IGReadOnlyAdapter(config); adapter.authenticate(); accounts=adapter.get_accounts()
    account_id=config.account_id or (adapter._session.account_id if adapter._session else None)
    if not account_id and accounts: account_id=next((item.account_id for item in accounts if item.preferred), accounts[0].account_id)
    if not account_id: return unavailable("No IG DEMO account was returned")
    snapshot=adapter.create_state_service(stale_after_seconds=300).get_broker_snapshot(account_id)
    return _json({"state":"AVAILABLE","broker":"IG","environment":"DEMO","account":snapshot.account,"positions":snapshot.positions,"position_count":snapshot.position_count,"freshness":snapshot.freshness,"retrieved_at":snapshot.retrieved_at,"live_execution":False})

def safe_status(environ=None):
    try: return read_only_ig_status(environ)
    except IGRequestError as exc: return {"state":"ERROR","broker":"IG","environment":"DEMO","error":exc.diagnostic("DEMO"),"live_execution":False}
    except (ValueError, LookupError, RuntimeError) as exc: return unavailable(str(exc))
