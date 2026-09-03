import unittest

import pandas as pd

from cross_asset_features import build_features


class CrossAssetFeatureTests(unittest.TestCase):
    def frames(self, length=50):
        dates = pd.date_range("2024-01-01", periods=length, tz="UTC")
        return {
            name: pd.DataFrame({
                "event_time": dates,
                "available_time": dates + pd.Timedelta(days=1),
                "close": [base + index for index in range(length)],
            })
            for name, base in {
                "usdzar": 18, "vix": 15, "sp500": 4000, "dxy": 100,
                "us10y": 4, "brent": 70, "gold": 1900, "platinum": 900,
                "palladium": 1000, "jse_all_share_proxy": 70000,
            }.items()
        }

    def test_interactions_and_availability(self):
        result = build_features(self.frames())
        last = result.iloc[-1]
        self.assertAlmostEqual(last["gold_zar"], last["gold_close"] * last["usdzar_close"])
        self.assertEqual(last["available_time"], "2024-02-20T00:00:00+00:00")
        self.assertIn(last["rand_regime_20"], {"rand_weakening", "rand_strengthening", "neutral"})

    def test_future_mutation_does_not_change_prior_features(self):
        frames = self.frames()
        original = build_features(frames).iloc[39].copy()
        for frame in frames.values():
            frame.loc[frame.index >= 40, "close"] *= 100
        mutated = build_features(frames).iloc[39]
        pd.testing.assert_series_equal(original, mutated)

    def test_exact_date_join_does_not_forward_fill(self):
        frames = self.frames()
        frames["gold"] = frames["gold"].drop(index=30)
        result = build_features(frames)
        row = result[result["event_time"] == pd.Timestamp("2024-01-31", tz="UTC")].iloc[0]
        self.assertTrue(pd.isna(row["gold_zar"]))


if __name__ == "__main__":
    unittest.main()
