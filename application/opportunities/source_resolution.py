"""Read-only multi-source OHLCV candidates; never splice provider fields."""
import csv
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import io
import json
import math
from pathlib import Path

from shadow_learning import timestamp
from .ost_data import ROOT, atomic_json, catalog
from .public_research import _available_at
from .swing_data_quality import real_ohlc

SCHEMA = 'price-source-candidates-v1'
PROVIDER_LINKS = {
    'IRESS': 'https://www.iress.com/software/trading-and-market-data/viewpoint/',
    'SHAREDATA': 'https://www.sharedata.co.za/v2/Scripts/Directory/FAQ/faq_General.aspx',
    'JSE': 'https://www.jse.co.za/data/historical-data',
}


def parse_iress_export(raw, instrument_id, origin_symbol, acquired_at, now):
    """Validate a complete daily IRESS table as its own source candidate."""
    registry = catalog()
    if (instrument_id not in registry or origin_symbol != registry[instrument_id]['ost_code'] + '.JSE'
            or not isinstance(raw, bytes) or not 0 < len(raw) <= 2_500_000):
        raise ValueError('explicit registered IRESS JSE identity required')
    acquired = timestamp(acquired_at)
    if acquired > now or now - acquired > timedelta(days=4):
        raise ValueError('fresh actual IRESS acquisition required')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    required = {'Date', 'Open', 'High', 'Low', 'Close', 'Volume'}
    allowed = required | {'% Change', '% Change vs Average'}
    columns = set(reader.fieldnames or ())
    if not required <= columns or columns - allowed:
        raise ValueError('IRESS daily OHLCV headers required')
    source_rows, seen = [], set()
    for index, row in enumerate(reader):
        if index >= 10000:
            raise ValueError('maximum 10000 IRESS rows')
        session = datetime.strptime(row['Date'].strip(), '%d/%m/%Y').date().isoformat()
        if session in seen:
            raise ValueError('duplicate IRESS session')
        seen.add(session)
        if _available_at(session) <= now:
            source_rows.append((session, row))
    source_rows.sort(key=lambda item: item[0])
    bars = []
    for session, row in source_rows[-600:]:
        bar = {'timestamp': session}
        for field in ('open', 'high', 'low', 'close', 'volume'):
            value = float(row[field.title()].replace(',', '').replace(' ', '').replace('\xa0', ''))
            if not math.isfinite(value) or value < 0:
                raise ValueError('invalid IRESS numeric value')
            bar[field] = value if field == 'volume' else value / 100
        if not real_ohlc(bar):
            raise ValueError('invalid IRESS OHLC relation')
        bars.append(bar)
    if not bars:
        raise ValueError('no completed IRESS sessions')
    close_at = datetime.fromisoformat(bars[-1]['timestamp']).replace(tzinfo=timezone.utc) + timedelta(hours=15)
    if acquired < close_at:
        raise ValueError('IRESS acquisition predates session close')
    return {'instrument_id': instrument_id, 'symbol': registry[instrument_id]['symbol'],
        'provider': 'IRESS', 'origin_symbol': origin_symbol, 'acquired_at': acquired.isoformat(),
        'source_sha256': sha256(raw).hexdigest(), 'currency': 'ZAR', 'interval': '1d',
        'price_basis': 'UNVERIFIED', 'volume_basis': 'UNVERIFIED',
        'historical_availability': 'UNVERIFIED', 'bars': bars}


def read_candidates(folder=ROOT):
    path = folder / 'alternative-sources.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'schema': SCHEMA, 'charts': {}}


def install_iress_candidate(raw, instrument_id, origin_symbol, acquired_at, now, folder=ROOT):
    chart = parse_iress_export(raw, instrument_id, origin_symbol, acquired_at, now)
    existing = read_candidates(folder)
    previous = existing.get('charts', {}).get(instrument_id, {}).get('IRESS')
    if previous:
        if timestamp(chart['acquired_at']) < timestamp(previous['acquired_at']):
            raise ValueError('older source receipt cannot replace newer IRESS evidence')
        if chart['source_sha256'] == previous['source_sha256']:
            chart = previous
    result = {'schema': SCHEMA, 'charts': {**existing.get('charts', {})}}
    result['charts'][instrument_id] = {**result['charts'].get(instrument_id, {}), 'IRESS': chart}
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'alternative-exports'
    archive.mkdir(exist_ok=True)
    raw_path = archive / (instrument_id + '-IRESS-' + chart['source_sha256'] + '.csv')
    if not raw_path.exists():
        raw_path.write_bytes(raw)
    atomic_json(folder / 'alternative-sources.json', result)
    return chart


def _comparison(primary, alternative):
    base = {b['timestamp'][:10]: b for b in primary['bars']}
    joined = [(base[b['timestamp']], b) for b in alternative['bars'] if b['timestamp'] in base]
    return {'overlap_sessions': len(joined),
        'close_mismatches': sum(abs(a['close']-b['close']) > 0.01 for a,b in joined),
        'high_low_mismatches': sum(abs(a['high']-b['high']) > 0.01 or abs(a['low']-b['low']) > 0.01 for a,b in joined),
        'volume_mismatches': sum(abs(a['volume']-b['volume']) > 0 for a,b in joined)}


def audit(dataset, now, alternatives=None, yahoo_archive=None):
    """Resolve the next evidence action per stock without changing any input chart."""
    primary = (dataset or {}).get('charts', {})
    candidates = (alternatives or {}).get('charts', {})
    legacy = (yahoo_archive or {}).get('charts', {})
    result = {}
    for key, item in catalog().items():
        ost = primary.get(key)
        chart = candidates.get(key, {}).get('IRESS')
        iress = {'state': 'EXPORT_REQUIRED', 'url': PROVIDER_LINKS['IRESS']}
        if chart:
            valid = (chart.get('instrument_id') == key and chart.get('provider') == 'IRESS'
                     and chart.get('origin_symbol') == item['ost_code'] + '.JSE'
                     and chart.get('symbol') == item['symbol']
                     and all(real_ohlc(b) for b in chart.get('bars', [])))
            fresh = valid and timedelta(0) <= now - timestamp(chart['acquired_at']) <= timedelta(days=4)
            comparison = _comparison(ost, chart) if ost and valid else {'overlap_sessions': 0, 'close_mismatches': 0,
                'high_low_mismatches': 0, 'volume_mismatches': 0}
            state = ('INVALID_RECEIPT' if not valid else 'EXPIRED' if not fresh else
                     'SOURCE_DISAGREEMENT' if ost and (comparison['overlap_sessions'] < 10 or comparison['close_mismatches']) else
                     'WHOLE_SOURCE_OHLCV_CANDIDATE')
            iress = {'state': state, 'bars': len(chart.get('bars', [])),
                'last_session': chart['bars'][-1]['timestamp'] if chart.get('bars') else None,
                'acquired_at': chart.get('acquired_at'), 'source_sha256': chart.get('source_sha256'),
                **comparison, 'url': PROVIDER_LINKS['IRESS']}
        saved = legacy.get(key)
        yahoo = {'state': 'ARCHIVE_UNAVAILABLE'}
        if saved:
            bars = saved.get('bars', [])
            invalid = sum(not real_ohlc(b) for b in bars)
            yahoo = {'state': 'ARCHIVED_QUALITY_FAILED' if invalid else 'ARCHIVED_COMPARISON_ONLY',
                'bars': len(bars), 'invalid_ohlc_bars': invalid,
                'last_session': bars[-1]['timestamp'][:10] if bars else None}
        needs_open = bool(ost and any(b.get('open') is None for b in ost.get('bars', [])))
        next_action = ('IMPORT_OST_HISTORY' if not ost else 'VERIFY_IRESS_SOURCE_SEMANTICS'
            if iress['state'] == 'WHOLE_SOURCE_OHLCV_CANDIDATE' else 'REVIEW_SOURCE_DISAGREEMENT'
            if iress['state'] == 'SOURCE_DISAGREEMENT' else 'REFRESH_IRESS_EXPORT'
            if iress['state'] == 'EXPIRED' else 'OBTAIN_FULL_OHLCV_EXPORT'
            if needs_open else 'VERIFY_SOURCE_SEMANTICS')
        result[key] = {'instrument_id': key, 'ost_code': item['ost_code'],
            'next_action': next_action, 'opening_price_needed': needs_open,
            'alternatives': {'IRESS': iress, 'YAHOO': yahoo,
                'SHAREDATA': {'state': 'EXPORT_ENTITLEMENT_UNVERIFIED', 'url': PROVIDER_LINKS['SHAREDATA']},
                'JSE': {'state': 'HISTORICAL_DATA_ACCESS_REQUIRED', 'url': PROVIDER_LINKS['JSE']}},
            'whole_source_only': True, 'real_data_admitted': False}
    return {'schema': 'price-source-resolution-v1', 'checked_at': now.isoformat(),
        'instruments': result, 'primary_policy_unchanged': True,
        'candidate_scope': 'PROVIDER_ROUTE_ONLY',
        'source_semantics_verified': False, 'real_data_admitted': False,
        'sharepoint_role': 'OPTIONAL_FILE_STORAGE_NOT_MARKET_DATA_PROVIDER'}


def local_audit(dataset, now, folder=ROOT):
    archive = folder / 'before-ost-primary.json'
    try:
        yahoo = json.loads(archive.read_text(encoding='utf-8')) if archive.exists() else None
        candidates = read_candidates(folder)
        result = audit(dataset, now, candidates, yahoo)
    except (ValueError, KeyError, TypeError, OSError):
        result = audit(dataset, now)
        result['candidate_archive_state'] = 'UNAVAILABLE_INVALID_LOCAL_ARCHIVE'
        return result
    result['candidate_scope'] = 'LOCAL_SOURCE_ARCHIVE'
    for key, providers in candidates.get('charts', {}).items():
        chart = providers.get('IRESS')
        if chart and key in result['instruments']:
            raw_path = folder / 'alternative-exports' / (key + '-IRESS-' + chart['source_sha256'] + '.csv')
            if not raw_path.exists() or sha256(raw_path.read_bytes()).hexdigest() != chart['source_sha256']:
                result['instruments'][key]['alternatives']['IRESS']['state'] = 'RAW_RECEIPT_UNAVAILABLE'
                result['instruments'][key]['next_action'] = 'REIMPORT_IRESS_EXPORT'
    return result
