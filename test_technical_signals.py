import unittest

import numpy as np
import pandas as pd

from technical_signals import INDICATORS, technical_signal_frame


class TechnicalSignalDefinitionTests(unittest.TestCase):
    def test_authoritative_definitions_and_unavailable_values(self):
        frame = pd.DataFrame({
            "rsi": [20.0, np.nan], "rsi_signal": [1, 1],
            "sma_slow": [100.0, np.nan], "sma_signal": [-1, -1],
            "technical_warmup_complete": [True, False], "breakout_signal": [1, 1],
            "stochastic": [80.0, np.nan], "stochastic_signal": [-1, -1],
            "macd": [2.0, np.nan], "bollinger_zscore": [-2.0, np.nan],
            "adx": [30.0, np.nan], "dmi_direction": [1, np.nan],
            "ichimoku_direction": [-1, np.nan],
        })
        result = technical_signal_frame(frame)
        self.assertEqual(tuple(result.columns), INDICATORS)
        self.assertEqual(result.iloc[0].tolist(), [1, -1, 1, -1, 1, 1, 1, -1])
        self.assertTrue(result.iloc[1].isna().all())


if __name__ == "__main__":
    unittest.main()
