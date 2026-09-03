import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from historical_reconstruction import normalize_history


class HistoricalReconstructionTests(unittest.TestCase):
    def test_normalization_preserves_ohlcv_and_uses_next_day_availability(self):
        index = pd.DatetimeIndex(["2024-01-02", "2024-01-03"])
        frame = pd.DataFrame({
            "Open": [10, 11], "High": [12, 13], "Low": [9, 10],
            "Close": [11, 12], "Adj Close": [10.5, 11.5], "Volume": [100, 200],
        }, index=index)
        result = normalize_history(frame, datetime(2024, 2, 1, tzinfo=timezone.utc))
        self.assertEqual(result.loc[0, "available_time"], "2024-01-03T00:00:00+00:00")
        self.assertEqual(result.loc[1, "adj_close"], 11.5)
        self.assertEqual(result.loc[1, "volume"], 200)

    def test_normalization_drops_missing_close_but_does_not_forward_fill(self):
        frame = pd.DataFrame({
            "Open": [10, 11], "High": [12, 13], "Low": [9, 10],
            "Close": [10, None], "Adj Close": [10, None], "Volume": [100, 200],
        }, index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]))
        result = normalize_history(frame, datetime.now(timezone.utc))
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
