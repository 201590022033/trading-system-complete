"""Independent numeric/malformed-source checks for the offline B5 diagnostics."""
from copy import deepcopy
import unittest

from domain.backtest.acceptance import compare_sources, published_share_fee


def source():
    return dict(provider='YAHOO', symbol='SOL.JO', provider_currency='ZAc',
                timezone='Africa/Johannesburg', bars=[dict(timestamp='2026-09-01T09:00:00+02:00',
                Open=100, High=120, Low=90, Close=110, Volume=1000)])


class RealSourceAuditTests(unittest.TestCase):
    def test_exact_aggregate_never_self_certifies_calendar_or_fills(self):
        daily = source()
        result = compare_sources(daily, deepcopy(daily))
        self.assertEqual(result['matched_sessions'], 1)
        self.assertFalse(result['real_data_accepted'])
        self.assertIsNone(result['real_trade_audit'])
        self.assertIn('NOT_VERIFIED', result['calendar_basis'])

    def test_close_and_volume_mismatch_are_not_repaired(self):
        daily, intraday = source(), source()
        intraday['bars'][0].update(Close=109, Volume=600)
        before = deepcopy(intraday)
        result = compare_sources(daily, intraday)
        self.assertEqual(result['matched_sessions'], 0)
        self.assertEqual(result['sessions'][0]['differences_in_provider_units']['Close'], '-1')
        self.assertEqual(result['sessions'][0]['differences_in_provider_units']['Volume'], '-400')
        self.assertEqual(intraday, before)

    def test_duplicate_invalid_and_reordered_sources_block_comparison(self):
        for kind in ('duplicate', 'invalid', 'reordered', 'naive', 'missing'):
            with self.subTest(kind=kind):
                daily = source()
                if kind == 'duplicate': daily['bars'] *= 2
                elif kind == 'invalid': daily['bars'][0]['High'] = 99
                elif kind == 'naive': daily['bars'][0]['timestamp'] = '2026-09-01T09:00:00'
                elif kind == 'missing': del daily['bars'][0]['Volume']
                else:
                    other = deepcopy(daily['bars'][0]); other['timestamp'] = '2026-08-31T09:00:00+02:00'
                    daily['bars'].append(other)
                result = compare_sources(daily, source())
                self.assertTrue(result['daily_defects'])
                self.assertEqual(result['sessions'], [])

    def test_identity_missing_metadata_and_extra_dates_remain_explicit(self):
        daily, intraday = source(), source()
        intraday['symbol'] = 'SSL'
        self.assertFalse(compare_sources(daily, intraday)['identity_match'])
        intraday = source(); del intraday['provider_currency']
        self.assertFalse(compare_sources(daily, intraday)['metadata_match'])
        self.assertFalse(compare_sources(daily, intraday)['real_data_accepted'])
        intraday = source(); other = deepcopy(intraday['bars'][0]); other['timestamp'] = '2026-09-02T09:00:00+02:00'
        intraday['bars'].append(other)
        self.assertEqual(compare_sources(daily, intraday)['extra_intraday_dates'], ['2026-09-02'])

    def test_independent_cash_share_fee_numbers_and_purchase_only_tax(self):
        # 10k: 110 brokerage + 6.29 Strate + .03 levy; VAT 16.50+.94+.00.
        buy = published_share_fee(10000, 1)
        sell = published_share_fee(10000, -1)
        self.assertEqual(buy['total'], '158.76')
        self.assertEqual(sell['total'], '133.76')
        self.assertEqual(buy['components']['purchase_tax'], '25.00')
        self.assertEqual(sell['components']['purchase_tax'], '0.00')
        # 100k: 500 + 6.29 + .33 + 75 + .94 + .05 + 250.
        self.assertEqual(published_share_fee(100000, 1)['total'], '832.61')
        self.assertEqual(published_share_fee(3000000, -1)['components']['strate'], '142.20')
        self.assertFalse(buy['historical_invoice_verified'])

    def test_invalid_fee_inputs_fail(self):
        for amount, side in ((0, 1), (-1, 1), ('NaN', 1), (100, 0), (100, True)):
            with self.assertRaises(ValueError): published_share_fee(amount, side)
        with self.assertRaises(ValueError): published_share_fee(100, 1, strate_minimum=20, strate_maximum=10)


if __name__ == '__main__': unittest.main()
