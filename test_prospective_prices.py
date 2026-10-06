from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from application.opportunities.prospective_prices import capture_summary, prospective_outcomes, record_capture


class ProspectivePriceTests(unittest.TestCase):
    def test_forward_only_same_source_horizons_and_revision_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            start = datetime(2026, 10, 5, 16, tzinfo=timezone.utc)
            for index, close in enumerate((10, 11, 12, 13, 14, 15)):
                day = start + timedelta(days=index)
                bars = [{'timestamp': (start + timedelta(days=j)).date().isoformat(),
                         'open': None, 'high': value + 1, 'low': value - 1,
                         'close': value, 'volume': 100} for j, value in enumerate((10, 11, 12, 13, 14, 15)[:index + 1])]
                if index == 5:
                    bars[0] = dict(bars[0], close=10.1)
                record_capture(folder, 'SASOL', 'OST', {'bars': bars}, day.isoformat(), f'{index:064x}')
            record_capture(folder, 'SASOL', 'IRESS', {'bars': [bars[-1]]},
                           day.isoformat(), 'f' * 64)
            report = prospective_outcomes(folder)
            ost = next(source for source in report['sources'] if source['provider'] == 'OST')
            iress = next(source for source in report['sources'] if source['provider'] == 'IRESS')
            self.assertEqual(ost['first_seen_sessions'], 6)
            self.assertEqual(ost['revised_sessions'], 1)
            self.assertEqual(ost['cohorts']['3']['revision_excluded'], 1)
            self.assertEqual(ost['cohorts']['3']['clean_samples'], 2)
            self.assertEqual(ost['cohorts']['3']['positive_samples'], 2)
            self.assertEqual(iress['cohorts']['3']['clean_samples'], 0)

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
