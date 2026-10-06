import unittest
from datetime import datetime, timezone
from scripts.check_swing_data_readiness import coverage, recover_sasol, recover_benchmark


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

    def test_benchmark_close_recovery_keeps_open_missing_and_excludes_today(self):
        raw=b'Date,Closing (c),High (c),Low (c),Volume\n06 Oct 2026,10311,10549,10227,801\n05 Oct 2026,10227,10470,10165,504250\n'
        b=recover_benchmark(raw,self.now)
        self.assertEqual(len(b['bars']),1)
        self.assertEqual(b['bars'][0]['close'],102.27)
        self.assertIsNone(b['bars'][0]['open'])
        self.assertFalse(b['real_data_admitted'])

    def test_benchmark_duplicate_nonpositive_close_and_nonfinite_volume_rejected(self):
        header=b'Date,Closing (c),High (c),Low (c),Volume\n'
        row=b'05 Oct 2026,10227,10470,10165,504250\n'
        for raw in (header+row+row, header+row.replace(b'10227',b'0'),header+row.replace(b'504250',b'nan')):
            with self.assertRaises(ValueError):recover_benchmark(raw,self.now)

    def test_benchmark_bad_hlc_is_reported_never_repaired(self):
        raw=b'Date,Closing (c),High (c),Low (c),Volume\n05 Oct 2026,10227,10470,10300,504250\n'
        b=recover_benchmark(raw,self.now)
        self.assertEqual(b['invalid_hlc_sessions'],['2026-10-05'])
        self.assertEqual(b['bars'][0]['low'],103)
        self.assertIsNone(b['bars'][0]['open'])
        self.assertFalse(b['upload_eligible'])


if __name__ == '__main__':
    unittest.main()
