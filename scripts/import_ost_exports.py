"""Import a bounded, explicit JSON manifest of genuine OST exports locally."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from application.opportunities.ost_data import install_exports
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    rows = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    if not isinstance(rows, list) or not 1 <= len(rows) <= 34:
        raise ValueError('bounded manifest required')
    exports = []
    for row in rows:
        path = Path(row['path'])
        if not path.is_absolute(): path = args.manifest.parent / path
        if path.stat().st_size > 2_500_000: raise ValueError('bounded file required')
        exports.append({'instrument_id': row['instrument_id'], 'acquired_at': row['acquired_at'], 'raw': path.read_bytes()})
    result = install_exports(exports, datetime.now(timezone.utc))
    print(json.dumps({'state': 'OST_PRIMARY_INSTALLED_LOCALLY', 'imported': [r['instrument_id'] for r in exports],
                      'source_policy': result['source_policy'], 'live_execution': False}))


if __name__ == '__main__': main()
