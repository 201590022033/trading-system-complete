import unittest
from dataclasses import replace
from datetime import timedelta

from domain.market_data import aggregate, join_factors
from domain.market_data.costs import transition_cost
from domain.market_data.cross_asset import FactorObservation
from domain.market_data.horizons import DailySessionHorizon, IntradayDurationHorizon
from domain.market_data.sessions import SessionWindow
from intraday_costs import CostSchedule
from intraday_instruments import DEFAULT_REGISTRY
from test_hr11_data import T, bar
from test_hr11_costs import INSTRUMENT, SCHEDULE


class CanonicalMarketDataTests(unittest.TestCase):
    def test_completed_bars_and_future_mutation_are_causal(self):
        session = SessionWindow("s1", "2026-01-05", T, T + timedelta(hours=2), "fixture")
        original = [bar(i) for i in range(6)]
        changed = [replace(value, open=value.open + 500, high=value.high + 500,
                           low=value.low + 500, close=value.close + 500) if i >= 3 else value
                   for i, value in enumerate(original)]
        self.assertEqual(aggregate(original, [session], "15m", bar(2).event_time),
                         aggregate(changed, [session], "15m", bar(2).event_time))
        self.assertEqual(len(aggregate(original, [session], "15m", bar(5).event_time).bars), 2)

    def test_session_break_and_timezone_boundary(self):
        session = SessionWindow("s1", "2026-01-05", T, T + timedelta(hours=2), "fixture",
                                ((T + timedelta(minutes=10), T + timedelta(minutes=20)),))
        with self.assertRaises(ValueError):
            aggregate([bar(0), bar(1), bar(2)], [session], "15m", bar(2).event_time)

    def test_horizon_identity_separates_daily_and_intraday(self):
        session = SessionWindow("s1", "2026-01-05", T, T + timedelta(hours=2), "fixture")
        intraday = IntradayDurationHorizon("intraday_30m", 30)
        daily = DailySessionHorizon()
        self.assertNotEqual(intraday.horizon_id, daily.horizon_id)
        self.assertEqual(intraday.target(T, session), T + timedelta(minutes=30))
        self.assertEqual(daily.target(T, session), session.close_time)

    def test_cross_asset_asof_and_missing_state(self):
        observation = FactorObservation("BRENT", 1.0, T, T + timedelta(minutes=1), "fixture", ("r",), 300)
        future = replace(observation, value=9.0, available_time=T + timedelta(hours=1))
        result = join_factors([future, observation], T + timedelta(minutes=2), ("BRENT", "GOLD"))
        self.assertEqual(result.values, {"BRENT": 1.0})
        self.assertEqual(result.unavailable, {"GOLD": "MISSING_ASOF"})

    def test_turnover_and_reversal_costs_remain_position_based(self):
        entry = transition_cost(INSTRUMENT, SCHEDULE, 0, 10, 100)
        self.assertEqual(transition_cost(INSTRUMENT, SCHEDULE, 10, 10, 100).total, 0)
        self.assertEqual(transition_cost(INSTRUMENT, SCHEDULE, 10, 0, 100).turnover_units, entry.turnover_units)
        self.assertEqual(transition_cost(INSTRUMENT, SCHEDULE, 10, -10, 100).turnover_units, 20)


if __name__ == "__main__":
    unittest.main()
