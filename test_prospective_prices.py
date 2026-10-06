from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from application.opportunities.prospective_prices import capture_summary, record_capture


class ProspectivePriceTests(unittest.TestCase):
    def test_capture_is_immutable_source_specific_and_outcomes_need_later_sessions(self):
        start = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
        base = {'bars': [{'timestamp': '2026-10-05', 'open': None, 'high': 11,
                          'low': 9, 'close': 10, 'volume': 100},
                         {'timestamp': '2024-03-12', 'open': None, 'high': 12,
                          'low': 8, 'close': 9, 'volume': 200}]}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = record_capture(folder, 'SASOL', 'OST', base, start.isoformat(), 'a' * 64)
            self.assertEqual(record_capture(folder, 'SASOL', 'OST', base, start.isoformat(), 'a' * 64), path)
            self.assertEqual(capture_summary(folder)['sources'][0]['captures'], 1)
            self.assertFalse(capture_summary(folder)['sources'][0]['prospective_outcome_ready'])
            changed = {'bars': [dict(base['bars'][0], close=10.1), base['bars'][1],
                                {'timestamp': '2026-10-07', 'open': None, 'high': 12,
                                 'low': 9, 'close': 11, 'volume': 120}]}
            record_capture(folder, 'SASOL', 'OST', changed,
                           (start + timedelta(days=2)).isoformat(), 'b' * 64)
            summary = capture_summary(folder)['sources'][0]
            self.assertEqual(summary['observed_revisions'], 1)
            self.assertEqual(summary['later_observed_sessions'], 1)
            self.assertFalse(summary['prospective_outcome_ready'])
            self.assertEqual(len(list(path.parent.glob('*.json'))), 2)


if __name__ == '__main__':
    unittest.main()
