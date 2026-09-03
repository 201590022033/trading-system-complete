import unittest

import pandas as pd

from adaptive_technical_ensemble import INDICATORS, build_ensemble


class AdaptiveTechnicalEnsembleTests(unittest.TestCase):
    def frame(self, count=90):
        dates = pd.date_range("2024-01-01", periods=count, tz="UTC")
        data = {
            "event_time": dates, "available_time": dates+pd.Timedelta(days=1),
            "decision_time": dates+pd.Timedelta(days=1), "instrument": "TEST",
            "asset_class": "equity", "profile": "test", "close": [100+i for i in range(count)],
            "trend_regime": "bull", "volatility_regime": "normal", "technical_warmup_complete": True,
            "rsi": 50.0, "rsi_signal": 1, "sma_slow": 100.0, "sma_signal": 1,
            "breakout_signal": 1, "stochastic": 50.0, "stochastic_signal": 1,
            "macd": 1.0, "bollinger_zscore": -2.0, "adx": 30.0,
            "dmi_direction": 1, "ichimoku_direction": 1, "raw_technical_score": 1.0,
        }
        return pd.DataFrame(data)

    def test_logs_every_signal_weight_and_contribution(self):
        result = build_ensemble(self.frame(35))
        row = result.iloc[-1]
        for indicator in INDICATORS:
            self.assertIn(f"{indicator}_signal", result)
            self.assertIn(f"{indicator}_weight", result)
            self.assertIn(f"{indicator}_contribution", result)
        self.assertTrue(row["shadow_only"])

    def test_future_mutation_does_not_change_earlier_decisions(self):
        frame = self.frame()
        first = build_ensemble(frame)
        frame.loc[frame.index >= 70, "close"] *= 100
        second = build_ensemble(frame)
        columns = ["adaptive_score", "adaptive_action"]+[f"{name}_weight" for name in INDICATORS]
        pd.testing.assert_frame_equal(first[first.event_time < frame.loc[70, "event_time"]][columns].reset_index(drop=True), second[second.event_time < frame.loc[70, "event_time"]][columns].reset_index(drop=True))

    def test_small_samples_keep_neutral_weights(self):
        result = build_ensemble(self.frame(20))
        self.assertTrue((result[[f"{name}_weight" for name in INDICATORS]].fillna(1.0) == 1.0).all().all())


if __name__ == "__main__":
    unittest.main()
