import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

from application.opportunities.ost_data import SCHEMA, POLICY, parse_export
from application.opportunities.ost_data_api import create_ost_blueprint
from application.opportunities.source_resolution import (
    audit, install_iress_candidate, local_audit, parse_iress_export,
)

NOW = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
DATES = [f'{day:02d} Sep 2026' for day in range(1, 12)]
OST = ('Date,Closing (c),High (c),Low (c),Volume\n' +
       ''.join(f'{day},1000,1100,900,100\n' for day in DATES)).encode()
IRESS = ('Date,Open,High,Low,Close,% Change,% Change vs Average,Volume\n' +
         ''.join(f'{day:02d}/09/2026,950,1100,900,1000,0,0,100\n' for day in range(1, 12))).encode()


class SourceResolutionTests(unittest.TestCase):
    def dataset(self):
        return {'schema': SCHEMA, 'source_policy': POLICY, 'observed_at': NOW.isoformat(),
                'charts': {'SASOL': parse_export(OST, 'SASOL', NOW.isoformat(), NOW)}}

    def test_whole_source_candidate_and_existing_yahoo_quality(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            chart = install_iress_candidate(IRESS, 'SASOL', 'SOL.JSE', NOW.isoformat(), NOW, folder)
            self.assertEqual(chart['bars'][-1]['open'], 9.5)
            archived = {'charts': {'SASOL': {'bars': [
                {'timestamp': '2026-09-01', 'open': None, 'high': 11, 'low': 9, 'close': 10}]}}}
            (folder / 'before-ost-primary.json').write_text(json.dumps(archived))
            complete_report = local_audit(self.dataset(), NOW, folder)
            self.assertEqual(complete_report['candidate_scope'], 'LOCAL_SOURCE_ARCHIVE')
            report = complete_report['instruments']['SASOL']
            self.assertEqual(report['alternatives']['IRESS']['state'], 'WHOLE_SOURCE_OHLCV_CANDIDATE')
            self.assertEqual(report['alternatives']['IRESS']['overlap_sessions'], 11)
            self.assertEqual(report['alternatives']['IRESS']['close_mismatches'], 0)
            self.assertEqual(report['alternatives']['YAHOO']['invalid_ohlc_bars'], 1)
            self.assertEqual(report['next_action'], 'VERIFY_IRESS_SOURCE_SEMANTICS')
            self.assertTrue(report['whole_source_only'])
            self.assertFalse(report['real_data_admitted'])
            self.assertIsNone(self.dataset()['charts']['SASOL']['bars'][0]['open'])

    def test_wrong_identity_bad_headers_duplicate_and_invalid_prices_rejected(self):
        for raw, origin in ((IRESS, 'SSL.JSE'), (b'Date,Open\n01/09/2026,1', 'SOL.JSE'),
                            (IRESS + IRESS.splitlines()[1] + b'\n', 'SOL.JSE'),
                            (IRESS.replace(b',950,1100,900,1000', b',1200,1100,900,1000'), 'SOL.JSE')):
            with self.subTest(origin=origin), self.assertRaises((ValueError, KeyError)):
                parse_iress_export(raw, 'SASOL', origin, NOW.isoformat(), NOW)

    def test_source_disagreement_stale_and_raw_receipt_loss_are_explicit(self):
        changed = IRESS.replace(b',1000,0,0,100\n', b',1002,0,0,100\n', 1)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            install_iress_candidate(changed, 'SASOL', 'SOL.JSE', NOW.isoformat(), NOW, folder)
            self.assertEqual(local_audit(self.dataset(), NOW, folder)['instruments']['SASOL']['next_action'],
                             'REVIEW_SOURCE_DISAGREEMENT')
            path = next((folder / 'alternative-exports').glob('*.csv'))
            path.write_bytes(b'tampered')
            report = local_audit(self.dataset(), NOW, folder)['instruments']['SASOL']
            self.assertEqual(report['next_action'], 'REIMPORT_IRESS_EXPORT')
            self.assertEqual(report['alternatives']['IRESS']['state'], 'RAW_RECEIPT_UNAVAILABLE')
            self.assertEqual(audit(self.dataset(), NOW + timedelta(days=5),
                                   {'charts': {'SASOL': {'IRESS': parse_iress_export(
                                       IRESS, 'SASOL', 'SOL.JSE', NOW.isoformat(), NOW)}}})
                             ['instruments']['SASOL']['alternatives']['IRESS']['state'], 'EXPIRED')

    def test_local_alternative_import_is_same_origin_and_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Flask(__name__)
            app.register_blueprint(create_ost_blueprint(lambda: None, Path(tmp)))
            client = app.test_client()
            now = datetime.now(timezone.utc)
            day = (now-timedelta(days=2)).strftime('%d/%m/%Y')
            payload = {'provider': 'IRESS', 'instrument_id': 'SASOL', 'origin_symbol': 'SOL.JSE',
                'acquired_at': now.isoformat(), 'csv': 'Date,Open,High,Low,Close,Volume\n'
                + day + ',950,1100,900,1000,100\n', 'instrument_confirmed': True}
            with patch.dict('os.environ', {'OST_LOCAL_IMPORT_ENABLED': '1'}, clear=True):
                self.assertEqual(client.post('/api/v1/ost/alternative-import', json=payload).status_code, 403)
                headers = {'Origin': 'http://localhost'}
                response = client.post('/api/v1/ost/alternative-import', json=payload, headers=headers)
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.json['resolution']['alternatives']['IRESS']['state'],
                                 'WHOLE_SOURCE_OHLCV_CANDIDATE')
                self.assertFalse(response.json['real_data_admitted'])
                self.assertEqual(client.post('/api/v1/ost/alternative-import', json={**payload,
                    'origin_symbol': 'SSL.JSE'}, headers=headers).status_code, 422)
                with patch.dict('os.environ', {'RAILWAY_ENVIRONMENT_ID': 'production'}):
                    self.assertEqual(client.post('/api/v1/ost/alternative-import', json=payload,
                                                 headers=headers).status_code, 403)
