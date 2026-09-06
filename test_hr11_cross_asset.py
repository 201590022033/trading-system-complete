import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_cross_asset import FactorObservation,join_factors,factor_return
from test_hr11_data import bar,T
class CrossAssetTests(unittest.TestCase):
    def setUp(self):self.observation=FactorObservation('USDZAR',.01,T,T+timedelta(minutes=1),'fixture',('record',),300)
    def test_availability_out_of_order_and_lineage(self):
        future=replace(self.observation,value=9,available_time=T+timedelta(hours=1))
        a=join_factors([future,self.observation],T+timedelta(minutes=2),('USDZAR','GOLD'))
        self.assertEqual(a.values,{'USDZAR':.01});self.assertEqual(a.unavailable,{'GOLD':'MISSING_ASOF'})
        self.assertEqual(a.lineage['USDZAR']['record_ids'],('record',))
        self.assertEqual(a,join_factors([self.observation,future],T+timedelta(minutes=2),('USDZAR','GOLD')))
    def test_age_uses_event_not_late_publication(self):
        late=replace(self.observation,available_time=T+timedelta(hours=1))
        self.assertEqual(join_factors([late],late.available_time,('USDZAR',)).unavailable,{'USDZAR':'STALE'})
        self.assertFalse(join_factors([self.observation],T,('USDZAR',)).values)
    def test_returns_never_fill_gaps(self):
        self.assertIsNone(factor_return([bar(0),bar(2)],'USDZAR',bar(2).event_time))
        self.assertAlmostEqual(factor_return([bar(0),bar(1)],'USDZAR',bar(1).event_time).value,.01)
        self.assertIsNone(factor_return([bar(0,close=None),bar(1)],'USDZAR',bar(1).event_time))
