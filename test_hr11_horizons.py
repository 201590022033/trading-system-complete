import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_horizons import HORIZONS,get_horizon,primary_horizon
from test_hr11_sessions import SESSION
from test_hr11_data import T
class HorizonTests(unittest.TestCase):
    def test_ids_primary_and_duration(self):
        self.assertEqual(len({h.horizon_id for h in HORIZONS}),5)
        self.assertEqual(primary_horizon().minutes,30)
        self.assertEqual(get_horizon('intraday_15m').target(T,SESSION),T+timedelta(minutes=15))
        with self.assertRaises(KeyError):get_horizon('1')
    def test_session_end_half_day_and_break(self):
        half=replace(SESSION,close_time=T+timedelta(minutes=20))
        self.assertIsNone(primary_horizon().target(T,half))
        self.assertEqual(get_horizon('intraday_eod').target(T,half),half.close_time)
        self.assertIsNone(primary_horizon().target(SESSION.close_time,SESSION))
        broken=replace(SESSION,breaks=((T+timedelta(minutes=10),T+timedelta(minutes=20)),))
        self.assertIsNone(primary_horizon().target(T,broken))
