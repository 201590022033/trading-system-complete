"""Read-only learning projection with explicit runtime ownership."""
from datetime import datetime, timezone
import json
import os
import time
from threading import Lock
from flask import Blueprint, jsonify
from ai_config import project_environment
from .paper_host import configured_paper, paper_status
from .swing_research import research_status

REMOTE = 'https://trading-system-complete-production.up.railway.app'


def public_status(path):
    import requests
    with requests.get(REMOTE + path, timeout=5, allow_redirects=False, stream=True) as response:
        response.raise_for_status()
        raw = bytearray()
        for chunk in response.iter_content(16384):
            raw.extend(chunk)
            if len(raw) > 2_000_000:
                raise ValueError('bounded status required')
        return json.loads(raw)


def count(value):
    if type(value) is not int or not 0 <= value <= 1_000_000:
        raise ValueError('invalid counter')
    return value


def project(paper, research, learning, *, source, now):
    """Allowlist aggregate evidence only; never return account fields."""
    technical = paper.get('swing_technical_learning') or {}
    decisions = count(technical['decision_count_in_read_window']) if technical else None
    horizons = {}
    for h in ('3', '4', '5'):
        row = (technical.get('horizons') or {}).get(h)
        if row is None:
            horizons[h] = {'matured': None, 'pending': None, 'negative': None}
            continue
        matured, negative = count(row['sample_count']), count(row['negative_count'])
        if decisions is None or matured > decisions or negative > matured:
            raise ValueError('inconsistent progress')
        horizons[h] = {'matured': matured, 'pending': decisions-matured, 'negative': negative}
    cohorts = {}
    for h in ('3', '4', '5'):
        cohorts[h] = []
        for name, row in (technical.get('condition_cohorts', {}).get(h) or {}).items():
            if not isinstance(name, str) or len(name) > 100 or not name.endswith(('_present', '_absent')):
                raise ValueError('unsupported cohort')
            samples, negatives = count(row['sample_count']), count(row['negative_outcomes'])
            if negatives > samples or len(cohorts[h]) >= 30:
                raise ValueError('bounded cohorts required')
            cohorts[h].append({'condition': name, 'samples': samples, 'negative': negatives})
    features = paper.get('swing_technical') or {}
    quality = {'available': 0, 'partial': 0, 'unavailable': 0}
    for row in features.values():
        state = row.get('state')
        quality['available' if state == 'AVAILABLE' else 'partial' if state == 'PARTIAL' else 'unavailable'] += 1
    sasol = features.get('SASOL') or {}
    run = research.get('last_run') or {}
    candidate = paper.get('candidate_learning') or {}
    worker = learning.get('worker_status') or {}
    return {'schema': 'daily-learning-overview-v1', 'state': 'AVAILABLE',
        'runtime': source, 'database': 'POSTGRESQL' if source == 'RAILWAY' else learning.get('database_backend', 'LOCAL'),
        'retrieved_at': now.isoformat(), 'live_execution': False, 'automatic_promotion': False,
        'real_data_backtest_admitted': False,
        'worker': {k: worker.get(k) for k in ('status', 'last_heartbeat_at', 'next_scheduled_at')},
        'paper_state': paper.get('state'), 'data_state': research.get('data_state'),
        'source_observed_at': research.get('source_observed_at'),
        'decision_at': paper.get('last_evaluated_at'),
        'feature_strategy': {'id': technical.get('strategy_profile_id'), 'version': technical.get('strategy_profile_version')},
        'decisions_in_read_window': decisions, 'read_limit': technical.get('read_limit'),
        'horizons': horizons, 'condition_cohorts': cohorts, 'latest_feature_quality': quality,
        'sasol': {'state': sasol.get('state'), 'session': sasol.get('session'),
                  'missing': sasol.get('missing', []),
                  'invalid_ohlc_days': (sasol.get('data_quality') or {}).get('invalid_ohlc_count')},
        'selected_vs_other': {'decisions': candidate.get('decision_count'),
                              'outcomes': candidate.get('outcome_count'),
                              'independent_sessions': candidate.get('nonoverlapping_paired_sessions')},
        'ai_comparison': {'state': run.get('state'), 'validation': run.get('validation_state'),
            'evaluated_at': run.get('evaluated_at'), 'provider': (run.get('proposal') or {}).get('provider'),
            'baseline_holdout_samples': (run.get('holdout_baseline') or {}).get('sample_count'),
            'candidate_holdout_samples': (run.get('holdout_variant') or {}).get('sample_count'),
            'baseline_blocked': (run.get('holdout_baseline') or {}).get('blocked_or_unresolved'),
            'candidate_blocked': (run.get('holdout_variant') or {}).get('blocked_or_unresolved')},
        'basis': 'NEXT_OBSERVABLE_CLOSE_FORWARD_RETURN; 10_BPS_ASSUMED_NOT_OST',
        'limitations': 'Pending counts cover the bounded decision read window. Observed sessions are not a verified exchange calendar. Overlapping outcomes and present/absent cohorts are descriptive, not causal or independent samples. AI proposals do not train model weights.'}


def overview(factory, env, reader=public_status):
    source = 'RAILWAY' if env.get('SWING_LEARNING_SOURCE') == 'RAILWAY' and not env.get('RAILWAY_ENVIRONMENT_ID') else 'LOCAL'
    now = datetime.now(timezone.utc)
    try:
        if source == 'RAILWAY':
            if env.get('SWING_RESEARCH_URL', '').rstrip('/') != REMOTE:
                raise ValueError('pinned deployment required')
            learning = reader('/api/learning/status')
            paper = reader('/api/paper/status')
            research = reader('/api/v1/swing-research/status')
            if learning.get('database_backend') != 'postgresql' or learning.get('database_state') != 'AVAILABLE':
                raise ValueError('shared database required')
        else:
            repo = factory()
            try:
                learning = repo.learning_status()
                config = configured_paper()
                paper = paper_status(repo, config) if config else {'state': 'NOT_CONFIGURED'}
                research = research_status(repo, now)
            finally:
                repo.close()
        return project(paper, research, learning, source=source, now=now)
    except Exception:
        return {'schema': 'daily-learning-overview-v1', 'state': 'UNAVAILABLE',
                'runtime': source, 'live_execution': False, 'automatic_promotion': False}


def create_learning_overview_blueprint(factory):
    bp = Blueprint('learning_overview', __name__)
    lock, cache = Lock(), {}
    @bp.get('/api/v1/learning/overview')
    def status():
        env = project_environment()
        key = (env.get('SWING_LEARNING_SOURCE'), env.get('SWING_RESEARCH_URL'), bool(env.get('RAILWAY_ENVIRONMENT_ID')))
        with lock:
            if cache.get('key') != key or time.monotonic() - cache.get('at', 0) >= 60:
                cache.update(key=key, at=time.monotonic(), result=overview(factory, env))
            result = cache['result']
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response, 503 if result['state'] == 'UNAVAILABLE' else 200
    return bp
