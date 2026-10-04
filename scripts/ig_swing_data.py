"""Explicit read-only Demo Swing volume/entitlement probe, with safe output."""
import json
import os
from datetime import datetime, timezone
from application.opportunities.ig_swing_data import investigate
from application.opportunities.paper_config import PaperLoopConfig
from domain.broker.ig import IGConfig, IGReadOnlyAdapter


def main():
    try:
        config = IGConfig.from_env(os.environ)
        if config.environment != "DEMO":
            raise ValueError("Demo required")
        result = investigate(IGReadOnlyAdapter(config),
            PaperLoopConfig.load("config/paper.railway.json").universe,
            datetime.now(timezone.utc))
    except Exception:
        result = {"state": "CONFIGURATION_OR_PROVIDER_UNAVAILABLE", "live_execution": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state") == "DATA_OBSERVED_NOT_ADMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
