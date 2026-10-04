"""Bounded free-key JSE coverage probe; never prints key or raw provider errors."""
import argparse
import json
from datetime import datetime, timezone
from ai_config import project_environment
from application.opportunities.alpha_vantage_data import AlphaVantageClient
from application.opportunities.public_research import public_share_catalog, public_etf_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instrument", nargs="?", default="SASOL")
    parser.add_argument("--cache-db", default="runtime/alpha-vantage-probe.db")
    args = parser.parse_args()
    from pathlib import Path
    from persistence.sqlite_repository import SQLiteRepository
    # Explicit isolated local cache avoids accidental connection to Railway DB.
    path = Path(args.cache_db)
    path.parent.mkdir(parents=True, exist_ok=True)
    repo = SQLiteRepository(path)
    try:
        catalog = {**public_share_catalog(), **public_etf_catalog()}
        symbol = catalog[args.instrument]["yahoo_symbol"]
        client = AlphaVantageClient(repo, project_environment().get("ALPHA_VANTAGE_API_KEY", ""), daily_limit=5)
        now = datetime.now(timezone.utc)
        result = client.discover(symbol, now)
        if result["state"] == "VERIFIED_SEARCH_IDENTITY":
            history = client.request({"function": "TIME_SERIES_DAILY", "symbol": result["symbol"],
                                     "outputsize": "compact", "datatype": "json"}, now)
            result = {"mapping": result, "state": history["state"],
                      "bars": len(history.get("bars", {})), "price_basis": history.get("price_basis")}
        print(json.dumps(result, sort_keys=True))
        return 0 if result["state"] == "AVAILABLE" else 2
    except Exception:
        print(json.dumps({"state": "CONFIGURATION_OR_PROVIDER_UNAVAILABLE"}))
        return 2
    finally:
        repo.close()


if __name__ == "__main__":
    raise SystemExit(main())
