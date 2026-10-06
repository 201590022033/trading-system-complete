from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from test_swing_technical import chart, clock
from persistence.sqlite_repository import SQLiteRepository
from application.opportunities.swing_research import validate_dataset, accept_dataset, UploadedFetcher, research_status, evaluate, BASELINE
from scripts.collect_swing_data import attach_supplements
from application.opportunities.supplemental_data import current_research_charts
from dataclasses import replace
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_host import compose_paper_worker
from application.opportunities.swing_technical import snapshot, record_and_label, OUTCOME_KIND


class SupplementalTests(unittest.TestCase):
    def setUp(self):
        self.data = chart(160)
        self.now = clock(self.data)
        self.data['symbol'] = 'SOL.JO'
        self.benchmark = deepcopy(self.data); self.benchmark['symbol'] = 'STX40.JO'
        for row in self.benchmark['bars']: row['open'] = None
        self.sasol = deepcopy(self.data)
        self.sasol['provenance'] = self.receipt('IRESS','SOL.JSE','OHLCV')
        self.benchmark['provenance'] = self.receipt('OST','STX40','HLCV_CLOSE_BENCHMARK')
        self.payload = {'schema':'local-swing-dataset-v2','observed_at':self.now.isoformat(),
            'charts':{'SASOL':self.data}, 'research_charts':{'SASOL':self.sasol,'ETF_STX40':self.benchmark}}

    def receipt(self, provider, origin, purpose):
        return {'provider':provider,'origin_symbol':origin,'purpose':purpose,
            'source_sha256':'a'*64,'acquired_at':self.now.isoformat(),
            'price_basis':'UNVERIFIED','volume_basis':'UNVERIFIED','historical_availability':'UNVERIFIED'}

    def test_v2_roundtrip_source_provenance_and_canonical_separation(self):
        self.payload['charts']['SASOL']['bars'][-1]['volume'] = 1234
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRepository(Path(directory)/'db.sqlite')
            try:
                accepted=accept_dataset(repo,self.payload,self.now)
                self.assertEqual(accepted,accept_dataset(repo,self.payload,self.now))
                fetcher=UploadedFetcher(repo)
                self.assertEqual(fetcher.get_chart('SOL.JO','1y')['bars'][-1]['volume'],1234)
                research=fetcher.get_research_chart('SOL.JO',self.now)
                self.assertEqual(research['provenance']['provider'],'IRESS')
                self.assertNotEqual(research['bars'][-1]['volume'],1234)
                self.assertEqual(research_status(repo,self.now)['research_inputs']['sasol']['state'],'AVAILABLE')
                self.assertIsNone(fetcher.get_research_chart('SOL.JO',self.now+timedelta(days=5)))
            finally:repo.close()

    def test_missing_wrong_future_stale_and_unadmitted_receipts_rejected(self):
        for field,value in [('provider','YAHOO'),('origin_symbol','SSL'),('source_sha256','bad'),
                            ('price_basis','VERIFIED'),('acquired_at',(self.now+timedelta(seconds=1)).isoformat()),
                            ('acquired_at',(self.now-timedelta(days=5)).isoformat())]:
            p=deepcopy(self.payload);p['research_charts']['SASOL']['provenance'][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):validate_dataset(p,self.now)
        p=deepcopy(self.payload);del p['research_charts']['SASOL']['provenance']
        with self.assertRaises(KeyError):validate_dataset(p,self.now)

    def test_invalid_ohlc_estimates_and_fake_benchmark_open_rejected(self):
        for key,field,value in [('SASOL','low',99999),('SASOL','estimated',True),('ETF_STX40','open',100)]:
            p=deepcopy(self.payload);p['research_charts'][key]['bars'][-1][field]=value
            with self.assertRaises(ValueError):validate_dataset(p,self.now)

    def test_refresh_does_not_rejuvenate_old_capture_or_mutate_canonical(self):
        p=deepcopy(self.payload)
        attached=attach_supplements(p,p,self.now)
        self.assertEqual(attached['charts'],p['charts'])
        expired=attach_supplements(p,p,self.now+timedelta(days=5))
        self.assertEqual(expired['schema'],'local-swing-dataset-v1')
        self.assertNotIn('research_charts',expired)
        self.assertEqual(p,self.payload)

    def test_legacy_upload_still_valid_and_v1_cannot_smuggle_supplements(self):
        legacy={'schema':'local-swing-dataset-v1','observed_at':self.now.isoformat(),'charts':{'SASOL':self.data}}
        self.assertNotIn('research_charts',validate_dataset(legacy,self.now))
        legacy['research_charts']=self.payload['research_charts']
        with self.assertRaises(ValueError):validate_dataset(legacy,self.now)

    def test_historical_evaluation_uses_original_charts_not_supplements(self):
        normalized=validate_dataset(self.payload,self.now)
        self.assertEqual(evaluate(normalized['charts'],BASELINE,'2000-01-01','2099-01-01'),
                         evaluate(self.payload['charts'],BASELINE,'2000-01-01','2099-01-01'))
        self.assertFalse(normalized['research_charts']['SASOL']['historical_evaluation_allowed'])

    def test_worker_freezes_research_inputs_without_replacing_canonical_prices(self):
        self.payload['charts']['SASOL']['bars'][-1]['volume']=1234
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRepository(Path(directory)/'db.sqlite')
            try:
                accept_dataset(repo,self.payload,self.now)
                config=replace(PaperLoopConfig.load('config/paper.example.json'),universe=('SASOL',))
                scheduler,handler=compose_paper_worker(repo,config,fetcher=UploadedFetcher(repo),clock=lambda:self.now.isoformat())
                frozen=handler.loader()
                self.assertEqual(frozen['charts']['SASOL']['bars'][-1]['volume'],1234)
                self.assertNotEqual(frozen['swing_charts']['SASOL']['bars'][-1]['volume'],1234)
                self.assertEqual(frozen['swing_technical']['SASOL']['state'],'AVAILABLE')
                self.assertEqual(frozen['swing_technical']['SASOL']['source_provenance']['provider'],'IRESS')
                result=handler(scheduler.enqueue(self.now.isoformat()))
                saved=repo.paper_record(result['ranking_record_id'])
                self.assertEqual(saved['swing_technical']['SASOL']['source_provenance']['provider'],'IRESS')
                self.assertEqual(handler.loader()['state'],'NO_NEW_COMPLETED_SESSION')
            finally:repo.close()

    def test_provider_change_cannot_label_legacy_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRepository(Path(directory)/'db.sqlite')
            try:
                repo.create_paper_account('test',{'mode':'PAPER'})
                initial=chart(80);initial['symbol']='SOL.JO';now=clock(initial)
                feature=snapshot(initial,evaluated_at=now,benchmark_chart=initial)
                record_and_label(repo,'test',{'SASOL':feature},{'SASOL':initial},evaluated_at=now)
                later=chart(86);later['symbol']='SOL.JO';later['provenance']=self.receipt('IRESS','SOL.JSE','OHLCV')
                record_and_label(repo,'test',{}, {'SASOL':later},evaluated_at=clock(later))
                self.assertEqual(repo.paper_records('test',OUTCOME_KIND,as_of=clock(later).isoformat()),[])
                later.pop('provenance')
                record_and_label(repo,'test',{}, {'SASOL':later},evaluated_at=clock(later))
                self.assertEqual(len(repo.paper_records('test',OUTCOME_KIND,as_of=clock(later).isoformat())),3)
            finally:repo.close()

    def test_actual_post_close_capture_precedes_conservative_usability(self):
        p=deepcopy(self.payload)
        session=p['research_charts']['SASOL']['bars'][-1]['timestamp'][:10]
        p['research_charts']['SASOL']['provenance']['acquired_at']=session+'T16:00:00+00:00'
        validate_dataset(p,self.now)
        p['research_charts']['SASOL']['provenance']['acquired_at']=session+'T14:00:00+00:00'
        with self.assertRaises(ValueError):validate_dataset(p,self.now)

    def test_new_same_provider_exports_mature_labels_with_source_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            repo=SQLiteRepository(Path(directory)/'db.sqlite')
            try:
                repo.create_paper_account('test',{'mode':'PAPER'})
                initial=chart(80);initial['symbol']='SOL.JO';now=clock(initial)
                initial['provenance']={**self.receipt('IRESS','SOL.JSE','OHLCV'),'acquired_at':now.isoformat()}
                feature=snapshot(initial,evaluated_at=now,benchmark_chart=initial)
                feature['source_provenance']=initial['provenance']
                record_and_label(repo,'test',{'SASOL':feature},{'SASOL':initial},evaluated_at=now)
                later=chart(86);later['symbol']='SOL.JO'
                later['provenance']={**initial['provenance'],'source_sha256':'b'*64,'acquired_at':clock(later).isoformat()}
                record_and_label(repo,'test',{}, {'SASOL':later},evaluated_at=clock(later))
                outcomes=repo.paper_records('test',OUTCOME_KIND,as_of=clock(later).isoformat())
                self.assertEqual(len(outcomes),3)
                self.assertEqual({r['source_provenance']['source_sha256'] for r in outcomes},{'b'*64})
            finally:repo.close()


if __name__=='__main__':unittest.main()
