"""Explicit bounded research evaluation; same daily AI budget as scheduled runs."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_persistence import runtime_repository
from application.opportunities.swing_research import run_research

if __name__ == "__main__":
    repository = runtime_repository()
    try:
        result = run_research(repository, datetime.now(timezone.utc))
        print(json.dumps({"state": result["state"], "provider": (result.get("proposal") or {}).get("provider"),
                          "holdout_baseline": result.get("holdout_baseline"),
                          "holdout_variant": result.get("holdout_variant"), "live_execution": False}))
    finally:
        repository.close()
