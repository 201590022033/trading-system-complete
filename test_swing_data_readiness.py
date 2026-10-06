import unittest
from datetime import datetime, timezone
from scripts.check_swing_data_readiness import coverage, recover_sasol


class ReadinessTests(unittest.TestCase):
    now = datetime(2026, 10, 6, 7, tzinfo=timezone.utc)
    raw = b'Date,Open,High,Low,Close,Volume\n06/10/2026,10000,10400,9900,10200,50\n05/10/2026,10000,10400,9900,10200,500\n'

    def reference(self):
        return {'symbol':'SOL.JO','currency':'ZAR','interval':'1d','bars':[
            {'timestamp':'2026-10-05','open':100,'high':104,'low':101,'close':102,'volume':450}]}

    def test_separate_recovery_retains_real_values_and_excludes_unfinished(self):
        ref = self.reference()
        recovered = recover_sasol(self.raw, ref, self.now)
        self.assertEqual(len(recovered['bars']), 1)
        self.assertEqual(recovered['bars'][0]['low'], 99)
        self.assertEqual(recovered['bars'][0]['volume'], 500)
        self.assertEqual(ref['bars'][0]['low'], 101)
        self.assertEqual(recovered['volume_mismatches'], 1)
        self.assertEqual(recovered['invalid_reference_sessions_with_valid_alternative'], 1)
        self.assertFalse(recovered['upload_eligible'])
        self.assertIsNone(recovered['capture_time'])

    def test_different_close_cannot_be_repaired(self):
        with self.assertRaises(ValueError):
            recover_sasol(self.raw.replace(b'10200',b'10300'), self.reference(), self.now)

    def test_duplicate_dates_and_invalid_source_rejected(self):
        for raw in (self.raw.replace(b'06/10/2026',b'05/10/2026'), self.raw.replace(b'9900',b'10100')):
            with self.assertRaises(ValueError):
                recover_sasol(raw, self.reference(), self.now)

    def test_wrong_product_units_rejected(self):
        ref = self.reference(); ref['symbol'] = 'SSL'
        with self.assertRaises(ValueError):
            recover_sasol(self.raw, ref, self.now)

    def test_fresh_upload_does_not_imply_valid_prices(self):
        ref = self.reference()
        ref['bars'].append({**ref['bars'][0], 'timestamp':'2026-10-06'})
        r = coverage({'observed_at':self.now.isoformat(),'charts':{'SASOL':ref}},self.now)
        self.assertEqual(r['invalid_ohlc_total'],1)
        self.assertEqual(r['charts']['SASOL']['unfinished_bars_excluded'],1)
        self.assertEqual(r['charts']['SASOL']['last_completed_session'],'2026-10-05')


if __name__ == '__main__':
    unittest.main()
