"""Offline coverage audit and separate IRESS recovery; never uploads or admits data."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from application.opportunities.swing_data_quality import real_ohlc
from application.opportunities.public_research import _available_at
from application.opportunities.swing_technical import snapshot


def coverage(dataset, now):
    charts = {}
    for key, chart in dataset['charts'].items():
        bars = chart['bars']
        completed = [b for b in bars if _available_at(b['timestamp']) <= now]
        invalid = [b['timestamp'][:10] for b in completed if not real_ohlc(b)]
        charts[key] = {'symbol': chart['symbol'], 'completed_bars': len(completed),
            'unfinished_bars_excluded': len(bars)-len(completed),
            'last_completed_session': completed[-1]['timestamp'][:10] if completed else None,
            'invalid_ohlc_count': len(invalid), 'invalid_sessions': invalid}
    return {'schema': 'swing-data-readiness-v1', 'checked_at': now.isoformat(),
        'uploaded_observed_at': dataset['observed_at'], 'charts': charts,
        'invalid_ohlc_total': sum(c['invalid_ohlc_count'] for c in charts.values()),
        'real_data_admitted': False,
        'calendar_basis': 'OBSERVED_PROVIDER_SESSIONS_NOT_VERIFIED'}


def recover_sasol(raw, reference, now):
    """Explicit SOL.JSE, cents and export-column contract; retain a single source."""
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not 1 <= len(rows) <= 600:
        raise ValueError('bounded IRESS daily export required')
    bars = []
    for row in rows:
        stamp = datetime.strptime(row['Date'], '%d/%m/%Y').date().isoformat()
        bar = {'timestamp': stamp}
        for field in ('open', 'high', 'low', 'close', 'volume'):
            value = float(row[field.title()].replace(',', ''))
            bar[field] = value if field == 'volume' else value / 100
        if not real_ohlc(bar) or not 0 <= bar['volume'] < float('inf'):
            raise ValueError('invalid IRESS OHLCV')
        if _available_at(stamp) <= now:
            bars.append(bar)
    bars.sort(key=lambda b: b['timestamp'])
    if len({b['timestamp'] for b in bars}) != len(bars):
        raise ValueError('duplicate IRESS sessions')
    source = {b['timestamp']: b for b in bars}
    overlap = [(b, source[b['timestamp'][:10]]) for b in reference['bars']
               if b['timestamp'][:10] in source and _available_at(b['timestamp']) <= now]
    if reference['symbol'] != 'SOL.JO' or reference['currency'] != 'ZAR' or reference['interval'] != '1d':
        raise ValueError('Sasol daily ZAR identity required')
    close_matches = sum(abs(a['close']-b['close']) <= 1e-8 for a,b in overlap)
    if not overlap or close_matches != len(overlap):
        raise ValueError('overlapping close identity mismatch')
    return {'schema': 'sasol-source-recovery-v1', 'source': 'IRESS_SOL_JSE_DAILY_TABLE',
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'checked_at': now.isoformat(),
        'capture_time': None, 'capture_time_basis': 'CHECK_TIME_IS_NOT_HISTORICAL_AVAILABILITY',
        'symbol': 'SOL.JO', 'interval': '1d', 'currency': 'ZAR', 'provider_currency': 'ZAc',
        'bars': bars, 'overlapping_close_matches': close_matches,
        'invalid_reference_sessions_with_valid_alternative': sum(not real_ohlc(a) for a,b in overlap),
        'volume_mismatches': sum(a['volume'] != b['volume'] for a,b in overlap),
        'real_data_admitted': False, 'upload_eligible': False,
        'remaining_gates': ['RAW_ACTION_SEMANTICS', 'VOLUME_SEMANTICS', 'HISTORICAL_AVAILABILITY',
                            'ALIGNED_BENCHMARK_SESSIONS']}


def recover_benchmark(raw, now):
    """OST STX40 history is HLCV: missing opens remain missing."""
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not 1 <= len(rows) <= 10000:
        raise ValueError('bounded OST history required')
    bars = []
    seen = set()
    import math
    for row in rows:
        stamp = datetime.strptime(row['Date'], '%d %b %Y').date().isoformat()
        if stamp in seen:
            raise ValueError('duplicate OST sessions')
        seen.add(stamp)
        bar = {'timestamp': stamp, 'open': None}
        for field, column in (('close','Closing (c)'),('high','High (c)'),('low','Low (c)'),('volume','Volume')):
            value = float(row[column].replace(',', '').replace(' ', ''))
            bar[field] = value if field == 'volume' else value/100
        if not all(math.isfinite(bar[k]) and bar[k] > 0 for k in ('close','high','low')) or not math.isfinite(bar['volume']) or bar['volume'] < 0:
            raise ValueError('invalid OST HLCV')
        if _available_at(stamp) <= now:
            bars.append(bar)
    bars.sort(key=lambda b: b['timestamp'])
    return {'schema':'stx40-source-recovery-v1', 'source':'OST_STX40_DAILY_HISTORY',
        'source_sha256':hashlib.sha256(raw).hexdigest(), 'checked_at':now.isoformat(),
        'symbol':'STX40.JO', 'currency':'ZAR', 'provider_currency':'ZAc', 'interval':'1d',
        'bars':bars[-600:], 'missing_fields':['open'], 'purpose':'BENCHMARK_CLOSE_RETURN_ONLY',
        'invalid_hlc_sessions':[b['timestamp'] for b in bars[-600:] if not b['low'] <= b['close'] <= b['high']],
        'real_data_admitted':False, 'upload_eligible':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT/'runtime/local-swing-data/latest.json')
    parser.add_argument('--iress-sasol', type=Path)
    parser.add_argument('--ost-stx40', type=Path, help='Explicitly identified STX40 cash ETF HLCV export')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    dataset = json.loads(args.dataset.read_text(encoding='utf-8'))
    report = coverage(dataset, now)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.iress_sasol:
        recovered = recover_sasol(args.iress_sasol.read_bytes(), dataset['charts']['SASOL'], now)
        (args.output/'Sasol-source-recovery.json').write_text(json.dumps(recovered, indent=2, allow_nan=False))
        report['sasol_recovery'] = {k:v for k,v in recovered.items() if k != 'bars'}
        benchmark = dataset['charts'].get('ETF_STX40', {}).get('bars', [])
        sessions = {b['timestamp'][:10] for b in benchmark if _available_at(b['timestamp']) <= now}
        report['sasol_recovery']['sessions_missing_from_benchmark'] = [b['timestamp'] for b in recovered['bars'] if b['timestamp'] not in sessions]
        if args.ost_stx40:
            benchmark = recover_benchmark(args.ost_stx40.read_bytes(), now)
            (args.output/'STX40-source-recovery.json').write_text(json.dumps(benchmark, indent=2, allow_nan=False))
            feature = snapshot(recovered, evaluated_at=now, benchmark_chart=benchmark)
            report['paired_source_diagnostic'] = {'scope':'OFFLINE_NUMERICAL_DIAGNOSTIC_ONLY',
                'real_data_admitted':False, 'upload_eligible':False, 'feature':feature,
                'benchmark_source_sha256':benchmark['source_sha256'],
                'benchmark_last_completed_session':benchmark['bars'][-1]['timestamp'] if benchmark['bars'] else None,
                'benchmark_missing_fields':benchmark['missing_fields'],
                'benchmark_invalid_hlc_sessions':benchmark['invalid_hlc_sessions']}
    (args.output/'Coverage-audit.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps({'state': 'AUDIT_SAVED_NO_UPLOAD', 'charts': len(report['charts']),
                      'invalid_ohlc_total': report['invalid_ohlc_total']}))


if __name__ == '__main__':
    main()
