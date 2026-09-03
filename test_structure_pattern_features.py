import unittest

from research_indicators import DataCapabilities, MarketBar
from structure_pattern_features import calculate_candlestick_context, calculate_fibonacci_context


CAPS = DataCapabilities(has_ohlc=True, has_volume=True)


class StructurePatternTests(unittest.TestCase):
    def trend_bars(self, count=70):
        return [MarketBar(open=100+i, high=102+i, low=99+i, close=101+i, volume=100+i) for i in range(count)]

    def test_fibonacci_uses_preceding_swing_and_never_emits_action(self):
        result = calculate_fibonacci_context(self.trend_bars(), CAPS, 69)
        self.assertTrue(result.available)
        self.assertEqual(result.values["swing_direction"], "upswing")
        self.assertEqual(set(result.values["levels"]), {"0.236", "0.382", "0.5", "0.618", "0.786"})
        self.assertIsNone(result.values["automatic_action"])
        self.assertLess(result.values["swing_high_index"], 69)

    def test_hanging_man_requires_uptrend_and_geometry(self):
        bars = self.trend_bars(25)
        bars[-1] = MarketBar(open=125, high=125.4, low=120, close=124.5, volume=500)
        result = calculate_candlestick_context(bars, CAPS, 24)
        self.assertTrue(result.values["patterns"]["hanging_man"])
        self.assertIsNone(result.values["next_bar_confirmation"])
        self.assertFalse(result.values["confirmation_available"])

    def test_confirmation_is_only_available_after_next_bar(self):
        bars = self.trend_bars(26)
        bars[24] = MarketBar(open=125, high=125.4, low=120, close=124.5, volume=500)
        bars[25] = MarketBar(open=124, high=125, low=122, close=123, volume=300)
        result = calculate_candlestick_context(bars, CAPS, 25, pattern_index=24)
        self.assertTrue(result.values["confirmation_available"])
        self.assertTrue(result.values["next_bar_confirmation"])

    def test_future_mutation_does_not_change_current_patterns(self):
        bars = self.trend_bars(30)
        before = calculate_candlestick_context(bars, CAPS, 24)
        bars[25:] = [MarketBar(open=1, high=2, low=.5, close=1, volume=1) for _ in bars[25:]]
        after = calculate_candlestick_context(bars, CAPS, 24)
        self.assertEqual(before, after)

    def test_all_required_patterns_are_exposed(self):
        names = calculate_candlestick_context(self.trend_bars(), CAPS, 69).values["patterns"]
        required = {"hanging_man", "hammer", "inverted_hammer", "shooting_star", "doji",
                    "dragonfly_doji", "gravestone_doji", "bullish_engulfing", "bearish_engulfing",
                    "morning_star", "evening_star", "harami", "piercing_line", "dark_cloud_cover",
                    "three_white_soldiers", "three_black_crows"}
        self.assertEqual(set(names), required)


if __name__ == "__main__":
    unittest.main()
