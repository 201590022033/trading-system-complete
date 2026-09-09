"""Redacted read-only IG discovery CLI."""

import argparse
import json

from domain.broker.ig import IGConfig, IGReadOnlyAdapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "accounts", "search", "market"))
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    adapter = IGReadOnlyAdapter(IGConfig.from_env())
    if args.command == "status":
        result = adapter.session_status()
    else:
        adapter.authenticate()
        if args.command == "accounts": result = [item.__dict__ for item in adapter.get_accounts()]
        elif args.command == "search": result = [item.__dict__ for item in adapter.search_markets(args.value or "")]
        else: result = adapter.get_market(args.value or "").__dict__
    print(json.dumps(result, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
