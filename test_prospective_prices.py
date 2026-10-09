from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from application.opportunities.prospective_prices import capture_summary, prospective_outcomes, record_capture


class ProspectivePriceTests(unittest.TestCase):
    def test_morning_receipts_count_completed_anchors_not_acquisition_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for index in range(3):
                session = f'2026-10-{6 + index:02d}'
                bars = [{'timestamp': session, 'high': 12, 'low': 9, 'close': 11}]
                record_capture(folder, 'SASOL', 'IRESS', {'bars': bars},
                               f'2026-10-{7 + index:02d}T07:00:00+00:00', f'{index:064x}')
                summary = capture_summary(folder)['sources'][0]
                self.assertEqual(summary['later_observed_sessions'], index)
                self.assertFalse(summary['prospective_outcome_ready'])
            outcomes = prospective_outcomes(folder)['sources'][0]
            self.assertEqual(outcomes['first_seen_sessions'], 3)
            self.assertTrue(all(c['clean_samples'] == 0 and c['pending'] == 3
                                for c in outcomes['cohorts'].values()))

    def test_readiness_counts_one_anchor_per_export_and_keeps_four_session_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            def capture(index, sessions, acquired):
                bars = [{'timestamp': session, 'high': 12, 'low': 9, 'close': 11}
                        for session in sessions]
                record_capture(folder, 'SASOL', 'IRESS', {'bars': bars}, acquired, f'{index:064x}')
            capture(0, ['2026-09-01', '2026-10-01'], '2026-10-02T07:00:00+00:00')
            capture(1, ['2026-10-02', '2026-10-05', '2026-10-06'], '2026-10-07T07:00:00+00:00')
            capture(2, ['2026-10-06'], '2026-10-07T08:00:00+00:00')
            summary = capture_summary(folder)['sources'][0]
            self.assertEqual(summary['later_observed_sessions'], 1)
            for index, day in enumerate((7, 8, 9), 3):
                capture(index, [f'2026-10-{day:02d}'], f'2026-10-{day + 1:02d}T07:00:00+00:00')
                summary = capture_summary(folder)['sources'][0]
                self.assertEqual(summary['later_observed_sessions'], index - 1)
                self.assertEqual(summary['prospective_outcome_ready'], index == 5)

    def test_readiness_rejects_live_stale_and_invalid_newest_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for index, (session, acquired, close) in enumerate((
                    ('2026-10-06', '2026-10-07T07:00:00+00:00', 11),
                    ('2026-10-08', '2026-10-08T07:00:00+00:00', 11),
                    ('2026-10-07', '2026-10-12T07:00:00+00:00', 11),
                    ('2026-10-09', '2026-10-10T07:00:00+00:00', 15))):
                record_capture(folder, 'SASOL', 'IRESS', {'bars': [
                    {'timestamp': session, 'high': 12, 'low': 9, 'close': close}]},
                    acquired, f'{index:064x}')
            self.assertEqual(capture_summary(folder)['sources'][0]['later_observed_sessions'], 0)

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
