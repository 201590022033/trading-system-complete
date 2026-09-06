import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from intraday_data import IntradayBar,SourcePolicy,as_of,canonical_bars,fetch_canonical
from intraday_instruments import DataGrade

T=datetime(2026,1,5,9,tzinfo=timezone.utc)
SOURCE=SourcePolicy('fixture-only',3,'manual_research',DataGrade.RESEARCH,600)
def bar(index=0,**changes):
    end=T+timedelta(minutes=5*(index+1))
    values=dict(instrument_id='SOL_CASH',interval_start=end-timedelta(minutes=5),event_time=end,
        available_time=end,decision_time=end,ingestion_timestamp=end,session_id='s1',session_date='2026-01-05',
        timeframe='5m',source=SOURCE,close=100+index,open=100+index,high=101+index,low=99+index,
        volume=1000,currency='ZAR')
    values.update(changes);return IntradayBar(**values)

class DataTests(unittest.TestCase):
    def test_clock_order_and_naive_rejected(self):
        b=bar()
        for values in ({'available_time':T},{'decision_time':T},{'event_time':T.replace(tzinfo=None)},
                       {'ingestion_timestamp':b.event_time+timedelta(seconds=1)}):
            with self.assertRaises(ValueError):replace(b,**values)
    def test_timezone_roundtrip(self):
        b=bar();other=replace(b,decision_time=b.decision_time.astimezone(timezone(timedelta(hours=2))))
        self.assertEqual(b,other);self.assertEqual(IntradayBar.from_dict(b.to_dict()),b)
        self.assertEqual(other.record_id,b.record_id)
    def test_missing_is_not_fabricated(self):
        b=bar(close=None,open=None,high=None,low=None,volume=None)
        self.assertIsNone(b.mid);self.assertIsNone(b.spread);self.assertIsNone(b.close)
        with self.assertRaises(ValueError):bar(bid=10)
        with self.assertRaises(ValueError):bar(bid=11,ask=10)
        with self.assertRaises(ValueError):bar(high=90)
    def test_duplicates_out_of_order_and_missing_sessions(self):
        self.assertEqual(canonical_bars([bar(2),bar(0)]),(bar(0),bar(2)))
        with self.assertRaises(ValueError):canonical_bars([bar(),bar()])
        self.assertEqual(len(as_of([bar(2),bar(0)],bar(0).decision_time)),1)
        self.assertEqual(as_of([bar(2)],bar(0).decision_time),())
    def test_delayed_stale_and_future_rejection(self):
        b=bar(delayed=True,stale=True,available_time=T+timedelta(minutes=10),decision_time=T+timedelta(minutes=10))
        self.assertEqual(as_of([b],T+timedelta(minutes=5)),())
        self.assertTrue(as_of([b],b.decision_time)[0].stale)
        with self.assertRaises(ValueError):replace(SOURCE,data_grade=DataGrade.EXECUTION)
    def test_provider_failure_is_sanitized(self):
        def fail():raise RuntimeError('SECRET-TOKEN')
        result=fetch_canonical(fail)
        self.assertEqual(result['state'],'UNAVAILABLE');self.assertNotIn('SECRET',result['reason'])
        self.assertEqual(fetch_canonical(lambda:[])['records'],())
