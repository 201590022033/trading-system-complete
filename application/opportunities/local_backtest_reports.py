"""Bounded public report projection; no replay, provider or account access."""
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path
from flask import Blueprint, jsonify

COUNTERS = ('safe_tests', 'protected_checks', 'conditional_cases', 'fee_checks',
            'stress_cases', 'daily_sessions', 'intraday_bars', 'price_match_days',
            'volume_match_days')
KEYS = {'schema', 'b5_outcome', 'evidence_date', 'window', 'counters', 'input_hashes'}


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                      allow_nan=False).encode()).hexdigest()


def validate(payload):
    if not isinstance(payload, dict) or set(payload) != KEYS:
        raise ValueError('unsupported report schema')
    if payload['schema'] != 'local-backtest-dashboard-v1' or payload['b5_outcome'] != 'PARTIAL_CLOSED':
        raise ValueError('unsupported outcome')
    def iso(value):
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError('invalid date')
    iso(payload['evidence_date'])
    window = payload['window']
    if not isinstance(window, list) or len(window) != 2:
        raise ValueError('bounded window required')
    for value in window:
        iso(value)
    if window[0] > window[1]:
        raise ValueError('ordered window required')
    counters = payload['counters']
    if not isinstance(counters, dict) or set(counters) != set(COUNTERS):
        raise ValueError('unsupported counters')
    if any(type(v) is not int or not 0 <= v <= 1000000 for v in counters.values()):
        raise ValueError('bounded integer counters required')
    if max(counters['price_match_days'], counters['volume_match_days']) > counters['daily_sessions']:
        raise ValueError('invalid comparison denominator')
    hashes = payload['input_hashes']
    if not isinstance(hashes, dict) or set(hashes) != {'status', 'comparison', 'reference'}:
        raise ValueError('fixed provenance required')
    if any(not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for v in hashes.values()):
        raise ValueError('invalid content hash')
    return payload


def read_summary(directory):
    if not directory:
        return {'state': 'NOT_CONFIGURED', 'real_data_admitted': False, 'live_execution': False}
    try:
        with (Path(directory) / 'dashboard-summary.json').open('rb') as handle:
            raw = handle.read(65537)
        if len(raw) > 65536:
            raise ValueError('oversized summary')
        envelope = json.loads(raw)
        if set(envelope) != {'payload', 'sha256'}:
            raise ValueError('unsupported envelope')
        payload = validate(envelope['payload'])
        if envelope['sha256'] != digest(payload):
            raise ValueError('changed report')
        return dict(state='AVAILABLE', report=payload, real_data_admitted=False,
                    admitted_real_trades=0, validated_strategy_results=False,
                    execution_ready=False, live_execution=False,
                    ig_history_state='NOT_VERIFIED_BY_REPORT_INTEGRATION')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return {'state': 'UNAVAILABLE', 'real_data_admitted': False, 'live_execution': False}


def create_local_backtest_blueprint(directory=None):
    bp = Blueprint('local_backtest_reports', __name__)

    @bp.get('/api/v1/local-backtest/research-summary')
    def summary():
        report_dir = directory() if directory else os.environ.get('LOCAL_BACKTEST_REPORT_DIR', '')
        result = read_summary(report_dir)
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response, 503 if result['state'] == 'UNAVAILABLE' else 200

    return bp
