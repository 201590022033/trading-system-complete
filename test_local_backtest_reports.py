"""Read-only report integrity and disclosure boundary checks."""
import json
from pathlib import Path
import tempfile
import unittest
from flask import Flask
from application.opportunities.local_backtest_reports import (
    COUNTERS, create_local_backtest_blueprint, digest, read_summary,
)
from scripts.export_local_backtest_dashboard import export


class LocalReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload = dict(schema='local-backtest-dashboard-v1', b5_outcome='PARTIAL_CLOSED',
            evidence_date='2026-10-05', window=['2026-09-01','2026-10-02'],
            counters={k: 0 for k in COUNTERS},
            input_hashes={k: 'a'*64 for k in ('status','comparison','reference')})

    def save(self, payload=None):
        payload = self.payload if payload is None else payload
        (self.root/'dashboard-summary.json').write_text(json.dumps(dict(payload=payload,sha256=digest(payload))))

    def test_read_only_endpoint_never_certifies_data_or_allows_mutation(self):
        self.save()
        app = Flask(__name__)
        app.register_blueprint(create_local_backtest_blueprint(lambda: self.root))
        client = app.test_client()
        result = client.get('/api/v1/local-backtest/research-summary?file=.env')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.headers['Cache-Control'],'no-store')
        self.assertEqual(result.json['report']['b5_outcome'],'PARTIAL_CLOSED')
        self.assertEqual(result.json['admitted_real_trades'],0)
        for key in ('real_data_admitted','validated_strategy_results','execution_ready','live_execution'):
            self.assertIs(result.json[key],False)
        self.assertNotIn(str(self.root),result.get_data(as_text=True))
        self.assertEqual(client.post('/api/v1/local-backtest/research-summary',json={}).status_code,405)

    def test_changed_content_is_unavailable_and_does_not_leak(self):
        self.save()
        p = self.root/'dashboard-summary.json'
        report=json.loads(p.read_text());report['payload']['counters']['safe_tests']=999
        p.write_text(json.dumps(report))
        self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')
        p.write_text('SECRET-'+str(self.root))
        result=read_summary(self.root)
        self.assertEqual(set(result),{'state','real_data_admitted','live_execution'})
        self.assertNotIn('SECRET',json.dumps(result))

    def test_even_rehashed_unsupported_fields_or_claims_are_refused(self):
        for extra in ({'credentials':'secret'}, {'admitted_real_trades':2}):
            self.save({**self.payload,**extra})
            self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')
        self.save({**self.payload,'b5_outcome':'FULLY_ACCEPTED'})
        self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')
        for bad in (True,-1,1000001):
            self.save({**self.payload,'counters':{**self.payload['counters'],'safe_tests':bad}})
            self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')

    def test_missing_oversized_and_bad_denominators_fail_closed(self):
        self.assertEqual(read_summary(None)['state'],'NOT_CONFIGURED')
        self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')
        (self.root/'dashboard-summary.json').write_text('x'*65537)
        self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')
        self.save({**self.payload,'counters':{**self.payload['counters'],'price_match_days':1}})
        self.assertEqual(read_summary(self.root)['state'],'UNAVAILABLE')

    def test_export_requires_owner_close_and_matching_reference_source(self):
        paths=[self.root/x for x in ('status.json','comparison.json','reference.json')]
        values=[{'status':'B5_EXTERNAL_ACCEPTANCE_BLOCKED'}, {}, {}]
        for path,value in zip(paths,values):path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):export(*paths)
        paths[0].write_text(json.dumps({'status':'B5_PARTIAL_CLOSED','owner_approved_partial_close':True}))
        paths[2].write_text(json.dumps({'real_data_admitted':False,'replay_executed':False,'input_sha256':'a'*64}))
        with self.assertRaises(ValueError):export(*paths)


if __name__=='__main__':unittest.main()
