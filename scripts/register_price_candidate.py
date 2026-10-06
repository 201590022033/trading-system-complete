"""Register an independently captured IRESS daily OHLCV export for source audit."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from application.opportunities.source_resolution import install_iress_candidate
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instrument', required=True)
    parser.add_argument('--origin-symbol', required=True)
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--acquired-at', required=True, help='Actual source capture time with timezone offset')
    args = parser.parse_args()
    if args.file.stat().st_size > 2_500_000:
        raise ValueError('bounded export required')
    chart = install_iress_candidate(args.file.read_bytes(), args.instrument,
        args.origin_symbol, args.acquired_at, datetime.now(timezone.utc))
    print(json.dumps({'state': 'WHOLE_SOURCE_CANDIDATE_REGISTERED_LOCAL_ONLY',
        'instrument_id': chart['instrument_id'], 'provider': chart['provider'],
        'bars': len(chart['bars']), 'last_session': chart['bars'][-1]['timestamp'],
        'real_data_admitted': False, 'primary_policy_unchanged': True}))


if __name__ == '__main__':
    main()
