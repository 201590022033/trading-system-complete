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


def prospective_outcomes(folder, horizons=(3, 4, 5)):
    """Label first-seen completed closes against later first-seen same-source closes.

    Horizons count observed sessions, not an inferred exchange calendar. A revised
    entry or exit remains visible but is excluded from the clean cohort.
    """
    root = folder / 'prospective-price-captures'
    result = {'schema': 'prospective-price-outcomes-v1', 'scope': 'PRICE_ONLY_SHADOW',
              'horizons_observed_sessions': list(horizons), 'assumed_round_trip_bps': 10,
              'sources': [], 'historical_admission': False, 'strategy_edge_claim': False}
    if not root.exists():
        return result
    for instrument in sorted(root.iterdir()):
        if not instrument.is_dir():
            continue
        for provider in sorted(instrument.iterdir()):
            if not provider.is_dir():
                continue
            first_seen = {}
            revised = set()
            files = sorted(provider.glob('*.json'))
            for path in files:
                capture = json.loads(path.read_text(encoding='utf-8'))
                if capture['instrument_id'] != instrument.name or capture['provider'] != provider.name:
                    raise ValueError('capture identity mismatch')
                acquired = timestamp(capture['acquired_at'])
                newest_session = max((bar['timestamp'][:10] for bar in capture['bars']), default=None)
                for bar in capture['bars']:
                    session = bar['timestamp'][:10]
                    if session in first_seen:
                        if first_seen[session]['bar'] != bar:
                            revised.add(session)
                        continue
                    # Only the newest completed session in a capture becomes a
                    # prospective anchor. Older rows are comparison context.
                    if session != newest_session:
                        continue
                    session_time = timestamp(session + 'T00:00:00+00:00')
                    if not acquired - timedelta(days=4) <= session_time <= acquired:
                        continue
                    if not bar.get('close') or not bar.get('high') or not bar.get('low'):
                        continue
                    if not bar['low'] <= bar['close'] <= bar['high']:
                        continue
                    first_seen[session] = {'bar': bar, 'acquired_at': acquired}
            sessions = sorted(first_seen)
            cohorts = {}
            for horizon in horizons:
                clean, revised_count, pending = [], 0, 0
                for index, entry_session in enumerate(sessions):
                    if index + horizon >= len(sessions):
                        pending += 1
                        continue
                    exit_session = sessions[index + horizon]
                    if first_seen[exit_session]['acquired_at'] <= first_seen[entry_session]['acquired_at']:
                        pending += 1
                        continue
                    if entry_session in revised or exit_session in revised:
                        revised_count += 1
                        continue
                    entry = first_seen[entry_session]['bar']['close']
                    exit_price = first_seen[exit_session]['bar']['close']
                    clean.append((exit_price / entry - 1) * 100 - 0.1)
                cohorts[str(horizon)] = {'clean_samples': len(clean),
                    'revision_excluded': revised_count, 'pending': pending,
                    'mean_net_return_pct': round(sum(clean) / len(clean), 4) if clean else None,
                    'positive_samples': sum(value > 0 for value in clean)}
            result['sources'].append({'instrument_id': instrument.name, 'provider': provider.name,
                'captures': len(files), 'first_seen_sessions': len(sessions),
                'revised_sessions': len(revised), 'cohorts': cohorts,
                'calendar_completeness': 'UNVERIFIED', 'corporate_action_basis': 'UNVERIFIED'})
    return result
