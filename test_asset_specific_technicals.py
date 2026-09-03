import unittest

import pandas as pd

from asset_specific_technicals import build_asset_features


class AssetSpecificTechnicalTests(unittest.TestCase):
    def frame(self, count=100):
        dates = pd.date_range("2024-01-01", periods=count, tz="UTC")
        return pd.DataFrame({
            "event_time": dates, "available_time": dates + pd.Timedelta(days=1),
            "open": [100+i for i in range(count)], "high": [102+i for i in range(count)],
            "low": [99+i for i in range(count)], "close": [101+i for i in range(count)],
            "volume": [1000+i for i in range(count)],
        })

    def test_asset_profile_and_expected_families(self):
        result = build_asset_features(self.frame(), "ABSPJ", "equity", "banks_financials", self.frame())
        row = result.iloc[-1]
        self.assertEqual(row["profile"], "banks_financials")
        self.assertIn(row["trend_regime"], {"bull", "bear", "range"})
        self.assertTrue(pd.notna(row["ichimoku_direction"]))
        self.assertTrue(pd.notna(row["relative_strength_20"]))

    def test_future_mutation_cannot_change_prior_row(self):
        frame = self.frame()
        before = build_asset_features(frame, "GOLD", "commodity_future_proxy", "gold").iloc[79]
        frame.loc[frame.index >= 80, ["open", "high", "low", "close"]] *= 100
        after = build_asset_features(frame, "GOLD", "commodity_future_proxy", "gold").iloc[79]
        pd.testing.assert_series_equal(before, after)

    def test_missing_benchmark_is_explicit(self):
        result = build_asset_features(self.frame(), "USDZAR", "fx", "usdzar")
        self.assertTrue(result["relative_strength_20"].isna().all())


if __name__ == "__main__":
    unittest.main()
