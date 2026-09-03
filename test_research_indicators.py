"""Deterministic tests for expanded research indicators and capability gates."""

import unittest

from research_indicators import DataCapabilities, MarketBar, calculate_expanded_indicators


def make_bars(count=60):
    return [
        MarketBar(
            open=100.0 + index,
            high=101.5 + index,
            low=99.0 + index,
            close=101.0 + index,
            volume=1000.0 + 10.0 * index,
        )
        for index in range(count)
    ]


class ResearchIndicatorTests(unittest.TestCase):
    def test_close_only_features_do_not_fabricate_ohlcv_or_intraday_values(self):
        bars = [MarketBar(close=100.0 + index) for index in range(40)]
        snapshot = calculate_expanded_indicators(bars, DataCapabilities())
        self.assertTrue(snapshot.features["macd"].available)
        self.assertTrue(snapshot.features["close_zscore"].available)
        for name in ("atr", "adx", "relative_volume", "session_vwap", "opening_range_high"):
            self.assertFalse(snapshot.features[name].available)

    def test_ohlcv_and_benchmark_features_are_finite(self):
        bars = make_bars()
        benchmark = [100.0 + 0.5 * index for index in range(len(bars))]
        capabilities = DataCapabilities(True, True, True, False, "daily")
        snapshot = calculate_expanded_indicators(bars, capabilities, benchmark)
        for name in ("atr", "adx", "plus_di", "minus_di", "macd", "close_zscore",
                     "relative_strength", "relative_volume", "median_dollar_volume"):
            self.assertTrue(snapshot.features[name].available, name)
            self.assertIsInstance(snapshot.features[name].value, float)
        self.assertFalse(snapshot.features["session_vwap"].available)

    def test_intraday_features_require_explicit_intraday_capability(self):
        snapshot = calculate_expanded_indicators(
            make_bars(10), DataCapabilities(True, True, False, True, "5m")
        )
        self.assertTrue(snapshot.features["session_vwap"].available)
        self.assertEqual(snapshot.features["opening_range_high"].value, 105.5)
        self.assertEqual(snapshot.features["opening_range_low"].value, 99.0)

    def test_as_of_index_prevents_future_leakage(self):
        original = make_bars(60)
        changed_future = original[:40] + [
            MarketBar(close=10000.0, high=10001.0, low=9999.0, open=10000.0, volume=999999.0)
            for _ in range(20)
        ]
        capabilities = DataCapabilities(True, True)
        first = calculate_expanded_indicators(original, capabilities, as_of_index=39)
        second = calculate_expanded_indicators(changed_future, capabilities, as_of_index=39)
        self.assertEqual(first.features, second.features)

    def test_invalid_declared_capabilities_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_expanded_indicators(
                [MarketBar(close=100.0)] * 30,
                DataCapabilities(has_ohlc=True),
            )


if __name__ == "__main__":
    unittest.main()
