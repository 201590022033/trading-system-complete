"""Redacted read-only IG discovery CLI."""

import argparse
from datetime import datetime
import json

from domain.broker.ig import IGConfig, IGReadOnlyAdapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "accounts", "search", "market", "history"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("resolution", nargs="?")
    parser.add_argument("start", nargs="?")
    parser.add_argument("end", nargs="?")
    parser.add_argument("--max-points", type=int, default=10_000)
    parser.add_argument("--page-size", type=int, default=500)
    args = parser.parse_args()
    adapter = IGReadOnlyAdapter(IGConfig.from_env())
    if args.command == "status":
        result = adapter.authentication_status()
    else:
        adapter.authenticate()
        if args.command == "accounts": result = [item.__dict__ for item in adapter.get_accounts()]
        elif args.command == "search": result = [item.__dict__ for item in adapter.search_markets(args.value or "")]
        elif args.command == "market": result = adapter.get_market(args.value or "").__dict__
        else:
            if not all((args.value, args.resolution, args.start, args.end)):
                parser.error("history requires EPIC RESOLUTION START END")
            try:
                start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
                end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
            except ValueError:
                parser.error("history START and END must be ISO-8601 timestamps")
            result = adapter.get_historical_prices(
                args.value, args.resolution, start, end,
                max_points=args.max_points, page_size=args.page_size,
            ).summary()
    print(json.dumps(result, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
