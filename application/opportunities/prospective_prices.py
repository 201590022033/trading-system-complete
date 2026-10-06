"""Immutable local capture record for forward-only price-source research."""
from datetime import datetime, timedelta
from hashlib import sha256
import json

from shadow_learning import timestamp


def record_capture(folder, instrument_id, provider, chart, acquired_at, source_sha256):
    """Keep the actual receipt and complete source snapshot; never backdate availability."""
    acquired = timestamp(acquired_at)
    folder = folder / 'prospective-price-captures' / instrument_id / provider
    folder.mkdir(parents=True, exist_ok=True)
    payload = {'schema': 'prospective-price-capture-v1', 'instrument_id': instrument_id,
               'provider': provider, 'acquired_at': acquired.isoformat(),
               'source_sha256': source_sha256, 'bars': chart['bars'],
               'research_only': True, 'historical_admission': False}
    name = acquired.strftime('%Y%m%dT%H%M%S%fZ') + '-' + source_sha256 + '.json'
    path = folder / name
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != payload:
            raise ValueError('existing capture receipt differs')
        return path
    # Exclusive creation preserves earlier captures and rejects a same-name collision.
    with path.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, allow_nan=False, separators=(',', ':'))
    return path


def capture_summary(folder):
    """Read source-local receipts, count later observed revisions and forward sessions."""
    root = folder / 'prospective-price-captures'
    result = {'schema': 'prospective-price-summary-v1', 'scope': 'LOCAL_RESEARCH_ONLY',
              'sources': [], 'historical_admission': False, 'live_execution': False}
    if not root.exists():
        return result
    for instrument in sorted(root.iterdir()):
        if not instrument.is_dir():
            continue
        for provider in sorted(instrument.iterdir()):
            if not provider.is_dir():
                continue
            files = sorted(provider.glob('*.json'))
            first = None
            seen = {}
            revisions = 0
            recent_sessions = set()
            later_sessions = set()
            latest = None
            for path in files:
                capture = json.loads(path.read_text(encoding='utf-8'))
                if capture['instrument_id'] != instrument.name or capture['provider'] != provider.name:
                    raise ValueError('capture identity mismatch')
                acquired = timestamp(capture['acquired_at'])
                if first is None or acquired < first:
                    first = acquired
                latest = max(latest, acquired) if latest else acquired
                for bar in capture['bars']:
                    session = bar['timestamp'][:10]
                    digest = sha256(json.dumps(bar, sort_keys=True).encode()).hexdigest()
                    if session in seen and seen[session] != digest:
                        revisions += 1
                    seen[session] = digest
                    # The initial capture can establish only a recent baseline.
                    # Older rows become useful for revision checks, never as past as-of evidence.
                    session_time = timestamp(session + 'T00:00:00+00:00')
                    if acquired - timedelta(days=4) <= session_time <= acquired:
                        recent_sessions.add(session)
                    if first and session_time.date() > first.date() and session_time <= acquired:
                        later_sessions.add(session)
            result['sources'].append({'instrument_id': instrument.name, 'provider': provider.name,
                'captures': len(files), 'first_captured_at': first.isoformat(),
                'latest_captured_at': latest.isoformat(), 'recent_observed_sessions': len(recent_sessions),
                'later_observed_sessions': len(later_sessions),
                'observed_revisions': revisions,
                'prospective_outcome_ready': len(files) >= 2 and len(later_sessions) >= 4})
    return result
