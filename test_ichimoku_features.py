import unittest

from ichimoku_features import calculate_ichimoku
from research_indicators import DataCapabilities, MarketBar


class IchimokuFeatureTests(unittest.TestCase):
    def bars(self, count=100):
        return [MarketBar(open=99 + i, high=102 + i, low=98 + i, close=100 + i) for i in range(count)]

    def test_requires_ohlc_and_full_displaced_warmup(self):
        self.assertFalse(calculate_ichimoku(self.bars(), DataCapabilities(), 99).available)
        short = calculate_ichimoku(self.bars(77), DataCapabilities(has_ohlc=True), 76)
        self.assertFalse(short.available)
        self.assertIn("78", short.reason)

    def test_full_model_exposes_known_projection_and_chikou_without_future(self):
        result = calculate_ichimoku(self.bars(), DataCapabilities(has_ohlc=True), 90)
        self.assertTrue(result.available)
        self.assertEqual(result.values["price_cloud_state"], "above")
        self.assertGreater(result.values["chikou_vs_historical_price_26"], 0)
        self.assertIn("future_senkou_a_known_at_t", result.values)

    def test_future_mutation_does_not_change_prior_snapshot(self):
        bars = self.bars()
        before = calculate_ichimoku(bars, DataCapabilities(has_ohlc=True), 80)
        for index in range(81, len(bars)):
            bars[index] = MarketBar(open=1, high=2, low=0.5, close=1)
        after = calculate_ichimoku(bars, DataCapabilities(has_ohlc=True), 80)
        self.assertEqual(before, after)

    def test_visible_cloud_uses_displaced_source_not_current_window(self):
        result = calculate_ichimoku(self.bars(), DataCapabilities(has_ohlc=True), 90)
        self.assertLess(result.values["current_senkou_a"], result.values["future_senkou_a_known_at_t"])


if __name__ == "__main__":
    unittest.main()
