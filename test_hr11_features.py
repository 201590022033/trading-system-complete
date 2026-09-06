import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_features import compute_features
from technical_feature_registry import build_intraday_registry,DEFAULT_TECHNICAL_REGISTRY
from test_hr11_data import bar,T
from intraday_sessions import SessionWindow

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.bars=[bar(i) for i in range(90)]
        self.session=SessionWindow('s1','2026-01-05',T,T+timedelta(hours=8),'fixture')
    def test_extended_registry_preserves_daily(self):
        self.assertEqual(DEFAULT_TECHNICAL_REGISTRY.definition('rsi').implementation_status,'planned')
        self.assertEqual(build_intraday_registry().definition('intraday_continuous').parameters['rsi'],14)
    def test_features_and_units(self):
        result=compute_features(self.bars,self.bars[-1].event_time,[self.session])
        for key in ('rsi','ema_fast','macd','adx','tenkan','stochastic_k','atr','bollinger_upper','realized_volatility_20','session_vwap','opening_range_high','donchian_high','support'):
            self.assertIn(key,result.values,key)
        self.assertEqual(result.values['rsi'],100)
        self.assertEqual(result.values['opening_range_high'],103)
    def test_warmup_missing_and_zero_volume(self):
        result=compute_features([bar(0)],bar(0).event_time,[self.session])
        self.assertNotIn('rsi',result.values)
        result=compute_features([replace(b,volume=0) for b in self.bars],self.bars[-1].event_time,[self.session])
        self.assertNotIn('session_vwap',result.values);self.assertNotIn('relative_volume',result.values)
        result=compute_features([replace(b,high=None,low=None,open=None) for b in self.bars],self.bars[-1].event_time,[self.session])
        self.assertNotIn('atr',result.values);self.assertIn('rsi',result.values)
    def test_future_mutation_and_missing_slots(self):
        cutoff=self.bars[40].event_time
        mutated=[b if i<=40 else replace(b,open=b.open+500,high=b.high+500,low=b.low+500,close=b.close+500) for i,b in enumerate(self.bars)]
        self.assertEqual(compute_features(self.bars,cutoff,[self.session]),compute_features(mutated,cutoff,[self.session]))
        self.assertEqual(compute_features(self.bars[1:10]+self.bars[11:],self.bars[-1].event_time,[self.session]).values,{})
    def test_missing_session_start_blocks_session_features(self):
        result=compute_features(self.bars[1:],self.bars[-1].event_time,[self.session])
        self.assertNotIn('session_vwap',result.values)
