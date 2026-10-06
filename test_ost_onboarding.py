import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from flask import Flask
from application.opportunities.ost_data import parse_export, normalize, install_exports, read_primary, coverage, LocalOSTFetcher, POLICY, SCHEMA
from application.opportunities.ost_data_api import create_ost_blueprint
from application.opportunities.swing_research import accept_dataset, UploadedFetcher, run_research
from application.opportunities.paper_host import completed_session_identity
from persistence.sqlite_repository import SQLiteRepository

RAW = b'Date,Closing (c),High (c),Low (c),Volume\n06 Oct 2026,999,1100,900,12\n05 Oct 2026,1000,1100,900,100\n02 Oct 2026,950,1050,900,200\n'
NOW = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)


class OSTOnboardingTests(unittest.TestCase):
    def entry(self, key='SASOL', raw=RAW, acquired=NOW):
        return {'instrument_id': key, 'raw': raw, 'acquired_at': acquired.isoformat()}

    def dataset(self):
        return {'schema': SCHEMA, 'source_policy': POLICY, 'observed_at': NOW.isoformat(),
                'charts': {'SASOL': parse_export(RAW, 'SASOL', NOW.isoformat(), NOW)}}

    def test_cents_completion_and_missing_open_for_any_registered_stock(self):
        for key in ('SASOL', 'NPN', 'ETF_STXFIN'):
            chart = parse_export(RAW, key, NOW.isoformat(), NOW)
            self.assertEqual(len(chart['bars']), 2)
            self.assertEqual(chart['bars'][-1]['close'], 10)
            self.assertIsNone(chart['bars'][-1]['open'])
            self.assertEqual(chart['provenance']['provider'], 'OST')

    def test_actual_open_only_from_explicit_source_column(self):
        raw = b'Date,Closing (c),High (c),Low (c),Volume,Opening (c)\n05 Oct 2026,1000,1100,900,100,950\n'
        chart = parse_export(raw, 'SASOL', NOW.isoformat(), NOW)
        data = {**self.dataset(), 'charts': {'SASOL': chart}}
        self.assertEqual(next(r for r in coverage(data, NOW)['instruments'] if r['instrument_id']=='SASOL')['state'], 'OHLCV_PRESENT')
        self.assertFalse(chart['historical_evaluation_allowed'])

    def test_native_excel_html_export_uses_bounded_recent_completed_sessions(self):
        rows = ''.join(f'<tr><td>{day:02d} Sep 2026</td><td>1000</td><td>1100</td><td>900</td><td>100</td></tr>'
                       for day in range(1, 31))
        raw = ('<div><table id="Main_gvHistory"><tr><th>Date</th><th>Closing (c)</th>'
               '<th>High (c)</th><th>Low (c)</th><th>Volume</th></tr>' + rows +
               '<tr><td>05 Oct 2026</td><td>1200</td><td>1300</td><td>1100</td><td>200</td></tr>' +
               '<tr><td>06 Oct 2026</td><td>999</td><td>1000</td><td>900</td><td>1</td></tr>' +
               '</table></div>').encode()
        chart = parse_export(raw, 'ETF_STXFIN', NOW.isoformat(), NOW)
        self.assertEqual(len(chart['bars']), 31)
        self.assertEqual(chart['bars'][-1]['timestamp'], '2026-10-05')
        self.assertEqual(chart['bars'][-1]['close'], 12)
        self.assertIsNone(chart['bars'][-1]['open'])
        with self.assertRaises(ValueError):
            parse_export(b'<div><table><tr><td>Account</td></tr></table></div>', 'ETF_STXFIN', NOW.isoformat(), NOW)

    def test_unknown_identity_bad_headers_nonfinite_and_duplicate_rejected(self):
        for key, raw in [('SSL', RAW), ('SASOL', b'Date,Close\n05 Oct 2026,10'),
                         ('SASOL', RAW.replace(b'1000,', b'nan,')),
                         ('SASOL', RAW.replace(b',Volume', b',Volume,Account')),
                         ('SASOL', RAW + b'05 Oct 2026,1000,1100,900,100\n')]:
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                parse_export(raw, key, NOW.isoformat(), NOW)

    def test_future_stale_and_before_close_receipts_rejected(self):
        for acquired in (NOW+timedelta(seconds=1), NOW-timedelta(days=5), datetime(2026,10,5,14,tzinfo=timezone.utc)):
            with self.assertRaises(ValueError): parse_export(RAW, 'SASOL', acquired.isoformat(), NOW)

    def test_quality_errors_retained_and_reported_without_repair(self):
        raw=RAW.replace(b'1000,1100',b'1200,1100')
        data={**self.dataset(),'charts':{'SASOL':parse_export(raw,'SASOL',NOW.isoformat(),NOW)}}
        row=next(r for r in coverage(data,NOW)['instruments'] if r['instrument_id']=='SASOL')
        self.assertEqual(row['invalid_hlc_bars'],1)
        self.assertEqual(row['state'],'PARTIAL_HLCV')

    def test_batch_failure_is_atomic_and_legacy_snapshot_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); (folder/'latest.json').write_bytes(b'{"legacy":true}')
            with self.assertRaises(ValueError):install_exports([self.entry(),self.entry('NPN',b'bad')],NOW,folder)
            self.assertIsNone(read_primary(folder))
            install_exports([self.entry(),self.entry('ETF_STX40')],NOW,folder)
            self.assertEqual((folder/'before-ost-primary.json').read_bytes(),b'{"legacy":true}')
            self.assertEqual(len(read_primary(folder)['charts']),2)

    def test_identical_reupload_does_not_rejuvenate_acquisition(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);install_exports([self.entry()],NOW,folder)
            later=NOW+timedelta(days=1)
            install_exports([self.entry(acquired=later)],later,folder)
            self.assertEqual(read_primary(folder)['charts']['SASOL']['provenance']['acquired_at'],NOW.isoformat())
            self.assertEqual(len(list((folder/'ost-exports').glob('*.csv'))),1)

    def test_durable_v3_fetch_has_no_yahoo_fallback_and_expires(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                accept_dataset(repo,self.dataset(),NOW)
                fetcher=UploadedFetcher(repo,clock=lambda:NOW)
                self.assertEqual(fetcher.get_chart('SOL.JO','1y')['provenance']['provider'],'OST')
                with self.assertRaises(ValueError):fetcher.get_chart('NPN.JO','1y')
                fetcher.clock=lambda:NOW+timedelta(days=5)
                with self.assertRaises(ValueError):fetcher.get_chart('SOL.JO','1y')
            finally:repo.close()

    def test_unverified_ost_never_invokes_historical_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                accept_dataset(repo,self.dataset(),NOW)
                result=run_research(repo,NOW,proposer=lambda _:self.fail('model invoked'))
                self.assertEqual(result['state'],'OST_SOURCE_SEMANTICS_UNVERIFIED')
            finally:repo.close()

    def test_provider_identity_changes_source_signature(self):
        chart=self.dataset()['charts']['SASOL']
        old={**chart};old.pop('provenance')
        self.assertNotEqual(completed_session_identity({'SASOL':old},NOW)[0],completed_session_identity({'SASOL':chart},NOW)[0])

    def test_worker_freezes_primary_ost_and_does_not_supply_missing_stock(self):
        from dataclasses import replace
        from application.opportunities.paper_config import PaperLoopConfig
        from application.opportunities.paper_host import compose_paper_worker
        from test_swing_research import chart, clock
        source=chart(160); source['symbol']='SOL.JO'; now=clock(source)
        source['provenance']={**self.dataset()['charts']['SASOL']['provenance'],'acquired_at':now.isoformat()}
        benchmark=json.loads(json.dumps(source));benchmark['symbol']='STX40.JO'
        benchmark['provenance']['origin_symbol']='STX40'
        for row in benchmark['bars']:row['open']=None
        payload={'schema':SCHEMA,'source_policy':POLICY,'observed_at':now.isoformat(),
                 'charts':{'SASOL':source,'ETF_STX40':benchmark}}
        with tempfile.TemporaryDirectory() as tmp:
            repo=SQLiteRepository(Path(tmp)/'db.sqlite')
            try:
                accept_dataset(repo,payload,now)
                config=replace(PaperLoopConfig.load('config/paper.example.json'),universe=('SASOL','NPN'))
                _,handler=compose_paper_worker(repo,config,fetcher=UploadedFetcher(repo,clock=lambda:now),clock=lambda:now.isoformat())
                frozen=handler.loader()
                self.assertNotIn('NPN',frozen['charts'])
                self.assertEqual(frozen['charts']['SASOL']['provenance']['provider'],'OST')
                self.assertEqual(frozen['swing_technical']['SASOL']['source_provenance']['provider'],'OST')
            finally:repo.close()

    def test_import_security_origin_cloud_bounds_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=Flask(__name__);app.register_blueprint(create_ost_blueprint(lambda:None,Path(tmp)))
            client=app.test_client();body={'exports':[{'instrument_id':'SASOL','csv':RAW.decode(),'acquired_at':datetime.now(timezone.utc).isoformat()}],'instrument_confirmed':True}
            headers={'Origin':'http://localhost'}
            with patch.dict('os.environ',{'OST_LOCAL_IMPORT_ENABLED':'1'},clear=True):
                self.assertEqual(client.post('/api/v1/ost/import',json=body).status_code,403)
                self.assertEqual(client.post('/api/v1/ost/import',json=body,headers={'Origin':'https://evil.example'}).status_code,403)
                self.assertEqual(client.post('/api/v1/ost/import',data='x'*2700001,headers=headers).status_code,413)
                bad={**body,'instrument_confirmed':False}
                self.assertEqual(client.post('/api/v1/ost/import',json=bad,headers=headers).status_code,422)
                # Clock independent valid payload: derive dates from actual test time.
                now=datetime.now(timezone.utc)
                date=(now-timedelta(days=2)).strftime('%d %b %Y')
                body['exports'][0]['csv']='Date,Closing (c),High (c),Low (c),Volume\n'+date+',1000,1100,900,100\n'
                self.assertEqual(client.post('/api/v1/ost/import',json=body,headers=headers).status_code,201)
                status = client.get('/api/v1/ost/onboarding').json
                self.assertTrue(status['primary_active'])
                self.assertEqual(status['source_resolution']['instruments']['SASOL']['next_action'],
                                 'OBTAIN_FULL_OHLCV_EXPORT')
                with patch.dict('os.environ',{'RAILWAY_ENVIRONMENT_ID':'production'}):
                    self.assertEqual(client.post('/api/v1/ost/import',json=body,headers=headers).status_code,403)


if __name__=='__main__':unittest.main()
