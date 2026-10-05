"""Explicit local SENS acquisition or offline price-context audit. No default network."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from application.opportunities.sens_history import HistoricalSENSFetcher, Issuer, parse_announcement, parse_search, SOURCES
from domain.backtest.events import align_observed_price_context, events_available_as_of
from evidence import EvidenceRecord


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch = commands.add_parser('fetch-sharedata', help='explicit bounded public network acquisition')
    fetch.add_argument('--start', type=date.fromisoformat, required=True)
    fetch.add_argument('--end', type=date.fromisoformat, required=True)
    fetch.add_argument('--instrument', required=True)
    fetch.add_argument('--issuer', required=True)
    fetch.add_argument('--code', required=True)
    fetch.add_argument('--isin', required=True)
    fetch.add_argument('--output', type=Path, required=True)
    snapshot = commands.add_parser('import-search', help='offline owner-permitted public/browser search snapshot')
    snapshot.add_argument('--source', choices=sorted(SOURCES), required=True)
    snapshot.add_argument('--snapshot', type=Path, required=True)
    snapshot.add_argument('--url', required=True)
    snapshot.add_argument('--retrieved-at', type=datetime.fromisoformat, required=True)
    for name in ('instrument', 'issuer', 'code', 'isin'):
        snapshot.add_argument('--'+name, required=True)
    snapshot.add_argument('--output', type=Path, required=True)
    audit = commands.add_parser('audit', help='offline sidecar; never admits prices or changes trades')
    for name in ('evidence', 'daily', 'intraday', 'output'):
        audit.add_argument('--'+name, type=Path, required=True)
    audit.add_argument('--as-of', type=datetime.fromisoformat, required=True)
    args = parser.parse_args()
    if args.command == 'import-search':
        issuer = Issuer(args.instrument, args.issuer, args.code, args.isin)
        raw = args.snapshot.read_bytes()
        leads = parse_search(args.source, raw, args.url, issuer)
        records = [parse_announcement(args.source, raw, lead['url'], issuer, args.retrieved_at,
                   lead=lead, snapshot_url=args.url).to_dict() for lead in leads]
        # Search metadata alone does not qualify full-text issuer/security identity.
        write_json(args.output, {'records': records, 'coverage': 'SEARCH_METADATA_ONLY_UNVERIFIED'})
        print(json.dumps({'search_records': len(records)}))
        return 0
    if args.command == 'fetch-sharedata':
        issuer = Issuer(args.instrument, args.issuer, args.code, args.isin)
        client = HistoricalSENSFetcher(max_requests=12)
        leads = client.search_sharedata(issuer, args.start, args.end)
        records, failures = [], []
        for lead in leads:
            raw = client.read('sharedata_sens', lead['url'])
            if raw is None:
                failures.append({'url': lead['url'], 'state': client.last_status})
                continue
            try:
                records.append(parse_announcement('sharedata_sens', raw, lead['url'], issuer,
                    datetime.fromisoformat(client.receipts[-1]['retrieved_at']), lead=lead).to_dict())
            except ValueError as exc:
                failures.append({'url': lead['url'], 'state': str(exc)})
        write_json(args.output, {'records': records, 'receipts': client.receipts, 'failures': failures,
            'search_lead_count': len(leads), 'search_state': 'OBSERVED_RESULTS' if leads else 'EMPTY_OR_ACCESS_UNVERIFIED',
            'coverage': 'BOUNDED_PROVIDER_SEARCH_NOT_CERTIFIED_COMPLETE_JSE_HISTORY'})
        print(json.dumps({'records': len(records), 'requests': client.requests, 'failures': len(failures)}))
        return 0 if records and not failures else 1
    payload = json.loads(args.evidence.read_bytes())
    records = [EvidenceRecord(**r) for r in payload['records']]
    daily = json.loads(args.daily.read_bytes())
    intraday = json.loads(args.intraday.read_bytes())
    report = {'source_record_count': len(records),
              'eligible_as_of_count': len(events_available_as_of(records, args.as_of)),
              'as_of': args.as_of.isoformat(),
              'events': align_observed_price_context(records, daily, intraday),
              'price_admission': 'UNCHANGED_BLOCKED', 'corporate_action_completeness': 'UNVERIFIED'}
    write_json(args.output, report)
    print(json.dumps({'source_records': len(records), 'event_groups': len(report['events']),
                      'eligible_as_of': report['eligible_as_of_count']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
