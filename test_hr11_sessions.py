import unittest
from dataclasses import replace
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from intraday_sessions import SessionWindow,aggregate
from test_hr11_data import bar,T

SESSION=SessionWindow('s1','2026-01-05',T,T+timedelta(hours=2),'fixture-calendar-v1')
class SessionTests(unittest.TestCase):
    def test_ohlcv_aggregation_and_lineage(self):
        result=aggregate([bar(i) for i in range(6)],[SESSION],'15m',bar(5).event_time)
        self.assertEqual(len(result.bars),2)
        b=result.bars[0]
        self.assertEqual((b.open,b.high,b.low,b.close,b.volume),(100,103,99,102,3000))
        self.assertEqual(len(b.input_record_ids),3)
    def test_future_mutation_in_every_timeframe(self):
        original=[bar(i) for i in range(24)]
        changed=[b if i<12 else replace(b,open=b.open+500,high=b.high+500,low=b.low+500,close=b.close+500) for i,b in enumerate(original)]
        for frame in ('5m','15m','30m','60m'):
            self.assertEqual(aggregate(original,[SESSION],frame,bar(11).event_time),aggregate(changed,[SESSION],frame,bar(11).event_time))
    def test_missing_delayed_and_partial_bars_do_not_fill(self):
        self.assertEqual(aggregate([bar(0),bar(2)],[SESSION],'15m',bar(2).event_time).bars,())
        late=replace(bar(2),available_time=bar(3).event_time,decision_time=bar(3).event_time)
        self.assertEqual(aggregate([bar(0),bar(1),late],[SESSION],'15m',bar(2).event_time).bars,())
        partial=replace(SESSION,close_time=T+timedelta(minutes=20))
        result=aggregate([bar(i) for i in range(4)],[partial],'15m',partial.close_time)
        self.assertEqual(len(result.bars),1);self.assertTrue(result.warnings)
    def test_no_aggregation_across_sessions(self):
        first=replace(SESSION,close_time=T+timedelta(minutes=10))
        second=SessionWindow('s2','2026-01-05',first.close_time,T+timedelta(minutes=20),'fixture')
        values=[bar(0),bar(1),bar(2,session_id='s2'),bar(3,session_id='s2')]
        self.assertEqual(aggregate(values,[first,second],'15m',second.close_time).bars,())
    def test_overnight_dst_explicit_intervals(self):
        zone=ZoneInfo('America/New_York')
        session=SessionWindow('overnight','2026-03-07',datetime(2026,3,7,22,tzinfo=zone),datetime(2026,3,8,4,tzinfo=zone),'fixture')
        self.assertEqual(session.trading_seconds(),5*3600)
    def test_daily_aggregation_does_not_invent_volume(self):
        partial=replace(SESSION,close_time=T+timedelta(minutes=15))
        result=aggregate([bar(0),bar(1,volume=None),bar(2)],[partial],'1d',partial.close_time)
        self.assertEqual(len(result.bars),1);self.assertIsNone(result.bars[0].volume)
