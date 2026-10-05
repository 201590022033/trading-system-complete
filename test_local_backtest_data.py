"""Data/time admission independent fixtures, no external services."""
from dataclasses import replace
from datetime import timedelta
import unittest
from decimal import Decimal as D
from domain.backtest.data import number
from research.fixtures.daily_oracle import fixture, ORACLE

class LocalDataTests(unittest.TestCase):
    def test_calendar_holiday_and_hand_arithmetic(self):
        m = fixture()
        self.assertEqual(len(m.admit('0', '4', m.sessions[4].close_at)), 5)
        self.assertEqual(m.sessions[3].close_at.day, 8)
        self.assertEqual(2000-102*10-2+106*10-2, ORACLE['final_cash'])
        self.assertEqual(m.sha256, replace(m).sha256)
        self.assertNotEqual(m.sha256, replace(m, revision='2').sha256)

    def test_future_data_invariance_and_delayed_availability(self):
        m = fixture(); now = m.sessions[1].close_at
        before = m.admit('0', '4', now)
        changed = replace(m, bars=m.bars[:2]+tuple(replace(b, close=D(-1)) for b in m.bars[2:]))
        self.assertEqual(before, changed.admit('0', '4', now))
        delayed = replace(m, bars=(m.bars[0], replace(m.bars[1], available_at=now+timedelta(hours=1)))+m.bars[2:])
        with self.assertRaises(ValueError): delayed.admit('0', '1', now)

    def test_missing_duplicate_bad_ohlc_estimates_activity_and_calendar(self):
        m = fixture(); now = m.sessions[4].close_at
        bads = [replace(m, bars=m.bars[:2]+m.bars[3:]),
                replace(m, bars=m.bars+(m.bars[2],)), replace(m, calendar_verified=False)]
        for attrs in ({'estimated':True}, {'low':D(200)}, {'close':D('NaN')}, {'activity':None},
                      {'available_at':m.sessions[2].open_at}):
            bads.append(replace(m, bars=m.bars[:2]+(replace(m.bars[2], **attrs),)+m.bars[3:]))
        for bad in bads:
            with self.assertRaises(ValueError): bad.admit('0','4',now,activity_required=True)
        zero = replace(m, bars=tuple(replace(b, activity=D(0)) for b in m.bars))
        self.assertEqual(len(zero.admit('0','4',now,activity_required=True)),5)
        with self.assertRaises(ValueError): number('Infinity')
        with self.assertRaises(ValueError): replace(m, sessions=tuple(reversed(m.sessions)))
        with self.assertRaises(ValueError): replace(m, price_basis='ADJUSTED')

if __name__ == '__main__': unittest.main()
