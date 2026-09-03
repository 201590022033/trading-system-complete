"""Deterministic tests for regime-v1."""

import unittest

from regime_engine import REGIME_VERSION, classify_regime


class RegimeEngineTests(unittest.TestCase):
    def test_bull_low_volatility(self):
        prices = [100 + index * 0.2 for index in range(40)]
        regime = classify_regime(prices)
        self.assertEqual(regime.trend, "bull")
        self.assertEqual(regime.volatility, "low")
        self.assertEqual(regime.risk, "risk_on")
        self.assertEqual(regime.version, REGIME_VERSION)

    def test_bear_high_volatility(self):
        prices = [100, 104, 96, 105, 93, 102, 90, 98, 86, 94, 82, 90, 78, 86, 74, 82, 70, 78, 66, 74, 62, 70]
        regime = classify_regime(prices)
        self.assertEqual(regime.trend, "bear")
        self.assertEqual(regime.volatility, "high")
        self.assertEqual(regime.risk, "risk_off")

    def test_flat_series_is_range_and_low_volatility(self):
        regime = classify_regime([100.0] * 30)
        self.assertEqual(regime.trend, "range")
        self.assertEqual(regime.volatility, "low")
        self.assertEqual(regime.risk, "neutral")

    def test_invalid_prices_are_rejected(self):
        with self.assertRaises(ValueError):
            classify_regime([100.0, 0.0, 101.0])
        with self.assertRaises(ValueError):
            classify_regime([100.0])


if __name__ == "__main__":
    unittest.main()
