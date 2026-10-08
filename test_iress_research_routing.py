"""Whole-source v3 numerical routing, with canonical and historical gates intact."""
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from application.opportunities.ost_data import POLICY, SCHEMA
from application.opportunities.source_resolution import attach_iress_research, install_iress_candidate, audit
from application.opportunities.supplemental_data import input_status
from application.opportunities.swing_research import accept_dataset, UploadedFetcher, validate_dataset, run_research
from application.opportunities.swing_technical import snapshot, record_and_label, OUTCOME_KIND, DECISION_KIND
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_host import compose_paper_worker, completed_session_identity
from persistence.sqlite_repository import SQLiteRepository
from test_swing_technical import chart, clock


class IRESSRoutingTests(unittest.TestCase):
    def setUp(self):
        self.sasol = chart(160)
        self.sasol['symbol'] = 'SOL.JO'
        self.now = clock(self.sasol)
        self.sasol['provenance'] = self.receipt('IRESS', 'SOL.JSE', 'OHLCV')
        canonical = deepcopy(self.sasol)
        canonical['provenance'] = self.receipt('OST', 'SOL', 'JSE_DAILY_RESEARCH')
        benchmark = deepcopy(canonical)
        benchmark.update(symbol='STX40.JO', provenance=self.receipt('OST', 'STX40', 'JSE_DAILY_RESEARCH'))
        for c in (canonical, benchmark):
            for b in c['bars']: b['open'] = None
        canonical['bars'][-1]['volume'] = 1234
        self.payload = {'schema': SCHEMA, 'source_policy': POLICY, 'observed_at': self.now.isoformat(),
            'charts': {'SASOL': canonical, 'ETF_STX40': benchmark}, 'research_charts': {'SASOL': self.sasol}}

    def receipt(self, provider, origin, purpose):
        return {'provider': provider, 'origin_symbol': origin, 'purpose': purpose,
            'source_sha256': 'a'*64, 'acquired_at': self.now.isoformat(),
            'price_basis': 'UNVERIFIED', 'volume_basis': 'UNVERIFIED', 'historical_availability': 'UNVERIFIED'}

    def raw_iress(self):
        from datetime import datetime
        rows = ['Date,Open,High,Low,Close,Volume']
        for b in self.sasol['bars']:
            day = datetime.fromisoformat(b['timestamp']).strftime('%d/%m/%Y')
            rows.append(day+','+','.join(str(b[f]*100 if f!='volume' else b[f])
                                       for f in ('open','high','low','close','volume')))
        rows.append(self.now.strftime('%d/%m/%Y')+',25900,26000,25800,25900,0')
        return ('\n'.join(rows)+'\n').encode()

    def test_upload_roundtrip_delivers_open_to_actual_numerical_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                accept_dataset(repo, self.payload, self.now)
                fetcher = UploadedFetcher(repo, clock=lambda: self.now)
                canonical = fetcher.get_chart('SOL.JO', '1y')
                research = fetcher.get_research_chart('SOL.JO', self.now)
                self.assertIsNone(canonical['bars'][-1]['open'])
                self.assertEqual(canonical['bars'][-1]['volume'], 1234)
                self.assertEqual(research['bars'][-1]['open'], 259)
                self.assertEqual(research['bars'][-1]['volume'], 1000)
                benchmark = fetcher.get_research_chart('STX40.JO', self.now)
                result = snapshot(research, evaluated_at=self.now, benchmark_chart=benchmark)
                self.assertEqual(result['state'], 'AVAILABLE')
                self.assertEqual(result['values']['atr14_wilder'], 2)
                # This is the existing OHLC feature gate, not merely a displayed Open.
                research['bars'][-1]['open'] = None
                missing = snapshot(research, evaluated_at=self.now, benchmark_chart=benchmark)
                self.assertIn('REAL_OHLC_UNAVAILABLE', missing['missing'])
                self.assertIsNone(missing['values']['atr14_wilder'])
                self.assertIsNone(fetcher.get_research_chart('SOL.JO', self.now+timedelta(days=5)))
                self.assertEqual(run_research(repo, self.now, proposer=lambda _: self.fail('model called'))['state'],
                                 'OST_SOURCE_SEMANTICS_UNVERIFIED')
            finally: repo.close()

    def test_worker_uses_iress_for_shadow_and_ost_for_canonical_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                accept_dataset(repo, self.payload, self.now)
                config = replace(PaperLoopConfig.load('config/paper.example.json'), universe=('SASOL',))
                _, handler = compose_paper_worker(repo, config, fetcher=UploadedFetcher(repo, clock=lambda: self.now),
                                                  clock=lambda: self.now.isoformat())
                frozen = handler.loader()
                self.assertEqual(frozen['charts']['SASOL']['provenance']['provider'], 'OST')
                self.assertIsNone(frozen['charts']['SASOL']['bars'][-1].get('open'))
                self.assertEqual(frozen['swing_charts']['SASOL']['provenance']['provider'], 'IRESS')
                self.assertEqual(frozen['swing_charts']['SASOL']['bars'][-1]['open'], 259)
                self.assertEqual(frozen['swing_technical']['SASOL']['state'], 'AVAILABLE')
                self.assertEqual(frozen['swing_technical']['SASOL']['source_provenance'], self.sasol['provenance'])
                without = deepcopy(self.payload); without.pop('research_charts')
                self.assertEqual(completed_session_identity(self.payload['charts'], self.now.isoformat()),
                                 completed_session_identity(without['charts'], self.now.isoformat()))
            finally: repo.close()

    def test_v3_rejects_invalid_extra_stale_future_and_missing_open_receipts(self):
        for field, value in [('provider', 'OST'), ('origin_symbol', 'SSL.JSE'), ('source_sha256', 'bad'),
                             ('price_basis', 'VERIFIED'), ('acquired_at', (self.now-timedelta(days=5)).isoformat()),
                             ('acquired_at', (self.now+timedelta(seconds=1)).isoformat())]:
            p = deepcopy(self.payload); p['research_charts']['SASOL']['provenance'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): validate_dataset(p, self.now)
        p = deepcopy(self.payload); p['research_charts']['SASOL']['bars'][-1]['open'] = None
        with self.assertRaises(ValueError): validate_dataset(p, self.now)
        p = deepcopy(self.payload); p['research_charts']['ETF_STX40'] = p['charts']['ETF_STX40']
        with self.assertRaises(ValueError): validate_dataset(p, self.now)
        p = deepcopy(self.payload); p['research_charts']['SASOL']['bars'].append(
            {**p['research_charts']['SASOL']['bars'][-1], 'timestamp': self.now.date().isoformat()})
        with self.assertRaises(ValueError): validate_dataset(p, self.now)

    def test_attach_is_raw_bound_does_not_rejuvenate_or_later_admit_live_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            candidate = install_iress_candidate(self.raw_iress(), 'SASOL', 'SOL.JSE', self.now.isoformat(), self.now, folder)
            p = deepcopy(self.payload); p.pop('research_charts')
            later = self.now+timedelta(days=1)
            p['observed_at'] = later.isoformat()
            result = attach_iress_research(p, later, folder)
            self.assertEqual(result['charts'], validate_dataset(p, later)['charts'])
            self.assertEqual(result['research_charts']['SASOL']['bars'], candidate['bars'])
            self.assertEqual(result['research_charts']['SASOL']['provenance']['acquired_at'], self.now.isoformat())
            self.assertNotEqual(result['research_charts']['SASOL']['bars'][-1]['timestamp'], self.now.date().isoformat())
            p['observed_at'] = (self.now+timedelta(days=5)).isoformat()
            self.assertNotIn('research_charts', attach_iress_research(p, self.now+timedelta(days=5), folder))
            path = folder/'alternative-sources.json'
            saved = json.loads(path.read_text()); saved['charts']['SASOL']['IRESS']['bars'][-1]['open'] = 258.5
            path.write_text(json.dumps(saved))
            self.assertNotIn('research_charts', attach_iress_research(self.payload, self.now, folder))
            path.write_text(json.dumps({'charts': {'SASOL': {'IRESS': candidate}}}))
            archive = next((folder/'alternative-exports').glob('*.csv')); archive.write_bytes(b'tampered')
            self.assertNotIn('research_charts', attach_iress_research(self.payload, self.now, folder))

    def test_newer_ireSS_observation_does_not_rejuvenate_ost_or_modify_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            candidate = install_iress_candidate(self.raw_iress(), 'SASOL', 'SOL.JSE', self.now.isoformat(), self.now, folder)
            p = deepcopy(self.payload); p.pop('research_charts')
            old = self.now-timedelta(hours=2)
            p['observed_at'] = old.isoformat()
            for c in p['charts'].values(): c['provenance']['acquired_at'] = old.isoformat()
            original = deepcopy(p)
            result = attach_iress_research(p, self.now, folder)
            self.assertEqual(result['observed_at'], self.now.isoformat())
            self.assertEqual(result['charts'], validate_dataset(original,self.now)['charts'])
            self.assertEqual(result['research_charts']['SASOL']['provenance']['acquired_at'], candidate['acquired_at'])
            self.assertEqual(result['research_charts']['SASOL']['provenance']['source_sha256'], candidate['source_sha256'])
            self.assertEqual(p, original)

    def test_failed_normalization_or_expired_ost_never_returns_unvalidated_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            install_iress_candidate(self.raw_iress(), 'SASOL', 'SOL.JSE', self.now.isoformat(), self.now, folder)
            p = deepcopy(self.payload); p.pop('research_charts'); original = deepcopy(p)
            with patch('application.opportunities.ost_data.normalize',side_effect=ValueError('invalid')):
                self.assertEqual(attach_iress_research(p,self.now,folder), original)
            self.assertEqual(p, original)
            for c in p['charts'].values(): c['provenance']['acquired_at'] = (self.now-timedelta(days=5)).isoformat()
            original = deepcopy(p)
            self.assertEqual(attach_iress_research(p,self.now,folder), original)

    def test_preview_names_provider_and_remains_partial_when_benchmark_unaligned(self):
        p = validate_dataset(self.payload, self.now)
        status = input_status(p, self.now)
        self.assertEqual(status['sasol']['state'], 'AVAILABLE')
        self.assertEqual(status['charts']['SASOL']['missing_open_bars'], 0)
        self.assertEqual(status['charts']['SASOL']['latest_open'], 259)
        self.assertEqual(status['sasol']['provider'], 'IRESS')
        p['charts']['ETF_STX40']['bars'].pop()
        self.assertIn('ALIGNED_BENCHMARK_UNAVAILABLE', input_status(p, self.now)['sasol']['missing'])

    def test_hosted_audit_derives_exact_differences_from_separate_uploaded_charts(self):
        report = audit(validate_dataset(self.payload, self.now), self.now)
        self.assertEqual(report['candidate_scope'], 'UPLOADED_RESEARCH_RECEIPT')
        comparison = report['instruments']['SASOL']['alternatives']['IRESS']
        self.assertEqual(comparison['overlap_sessions'], 160)
        self.assertEqual(comparison['open_missing_primary'], 160)
        self.assertEqual(comparison['volume_mismatches'], 1)
        self.assertFalse(report['real_data_admitted'])

    def test_new_iress_decisions_do_not_replace_or_label_frozen_ost_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                repo.create_paper_account('test', {'mode':'PAPER'})
                initial = chart(80); initial['symbol'] = 'SOL.JO'; now = clock(initial)
                initial['provenance'] = {**self.receipt('OST','SOL','JSE_DAILY_RESEARCH'), 'acquired_at': now.isoformat()}
                for b in initial['bars']: b['open'] = None
                feature = snapshot(initial, evaluated_at=now, benchmark_chart=initial)
                feature['source_provenance'] = initial['provenance']
                record_and_label(repo,'test',{'SASOL':feature},{'SASOL':initial},evaluated_at=now)
                old = repo.paper_records('test',DECISION_KIND,as_of=now.isoformat())[0]
                new = chart(81); new['symbol'] = 'SOL.JO'; now = clock(new)
                new['provenance'] = {**self.receipt('IRESS','SOL.JSE','OHLCV'),'acquired_at':now.isoformat()}
                feature = snapshot(new,evaluated_at=now,benchmark_chart=new)
                feature['source_provenance'] = new['provenance']
                record_and_label(repo,'test',{'SASOL':feature},{'SASOL':new},evaluated_at=now)
                later = chart(89); later['symbol'] = 'SOL.JO'
                later['provenance'] = {**new['provenance'],'source_sha256':'b'*64,'acquired_at':clock(later).isoformat()}
                record_and_label(repo,'test',{}, {'SASOL':later},evaluated_at=clock(later))
                outcomes = repo.paper_records('test',OUTCOME_KIND,as_of=clock(later).isoformat())
                self.assertEqual(len(outcomes),3)
                self.assertNotIn(old['decision_id'], {r['decision_id'] for r in outcomes})
                self.assertEqual(repo.paper_record(old['decision_id']), old)
                self.assertEqual({r['source_provenance']['provider'] for r in outcomes},{'IRESS'})
            finally: repo.close()


if __name__ == '__main__': unittest.main()
