"""Export a sanitized local report; offline, with no dataset admission."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from application.opportunities.local_backtest_reports import digest, validate


def export(status_path, comparison_path, reference_path):
    paths = dict(status=status_path, comparison=comparison_path, reference=reference_path)
    reports = {k: json.loads(p.read_text(encoding='utf-8')) for k, p in paths.items()}
    status, comparison, reference = (reports[k] for k in ('status', 'comparison', 'reference'))
    if status['status'] != 'B5_PARTIAL_CLOSED' or not status.get('owner_approved_partial_close'):
        raise ValueError('explicit owner-approved partial close required')
    if reference['real_data_admitted'] is not False or reference['replay_executed'] is not False:
        raise ValueError('only conditional accounting report is supported')
    actual_hash = hashlib.sha256(comparison_path.read_bytes()).hexdigest()
    if reference['input_sha256'] != actual_hash:
        raise ValueError('reference belongs to a different price comparison')
    payload = dict(schema='local-backtest-dashboard-v1', b5_outcome='PARTIAL_CLOSED',
        evidence_date='2026-10-05', window=comparison['window'],
        counters=dict(safe_tests=status['verification']['offline_tests'],
            protected_checks=status['verification']['protected_artifacts'],
            conditional_cases=reference['scenario_count'], fee_checks=reference['fee_component_checks'],
            stress_cases=status['stress_cases'], daily_sessions=comparison['days'],
            intraday_bars=comparison['iress_rows'],
            price_match_days=min(comparison['iress_aggregate_vs_iress_daily_match_days'][k]
                                 for k in ('Open', 'High', 'Low', 'Close')),
            volume_match_days=comparison['iress_aggregate_vs_iress_daily_match_days']['Volume']),
        input_hashes={k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()})
    validate(payload)
    return dict(payload=payload, sha256=digest(payload))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('status', 'comparison', 'reference', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args()
    result = export(args.status, args.comparison, args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'state': 'EXPORTED', 'sha256': result['sha256']}))
