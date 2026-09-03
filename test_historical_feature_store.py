import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from historical_feature_store import (
    FeatureProvenance, HistoricalFeature, PointInTimeFeatureStore, write_schema,
)


UTC = timezone.utc


class HistoricalFeatureStoreTests(unittest.TestCase):
    def feature(self, **changes):
        event = datetime(2024, 1, 31, tzinfo=UTC)
        values = dict(
            instrument="USDZAR", asset_class="fx", sector="fx", profile="usdzar",
            feature_group="macro", feature_name="cpi_yoy", value=5.1,
            event_time=event, available_time=event + timedelta(days=14),
            decision_time=event + timedelta(days=15),
            provenance=FeatureProvenance("stats_sa", "Statistics South Africa"),
            is_raw=True, revision_status="initial",
        )
        values.update(changes)
        return HistoricalFeature(**values)

    def test_rejects_future_availability_and_untraceable_derived_feature(self):
        with self.assertRaisesRegex(ValueError, "available_time"):
            self.feature(available_time=datetime(2024, 3, 1, tzinfo=UTC))
        with self.assertRaisesRegex(ValueError, "input_record_ids"):
            self.feature(is_raw=False)

    def test_as_of_excludes_later_revision_then_selects_it(self):
        with tempfile.TemporaryDirectory() as folder:
            store = PointInTimeFeatureStore(Path(folder) / "features.jsonl")
            initial = self.feature()
            revised = self.feature(
                value=5.3, available_time=initial.available_time + timedelta(days=30),
                decision_time=initial.decision_time + timedelta(days=60),
                revision_status="revised", supersedes_id=initial.record_id,
            )
            store.append((initial, revised))
            not_materialized = store.as_of(initial.available_time, instrument="USDZAR")
            before = store.as_of(initial.decision_time, instrument="USDZAR")
            after = store.as_of(revised.decision_time, instrument="USDZAR")
            self.assertEqual(not_materialized, [])
            self.assertEqual([item.value for item in before], [5.1])
            self.assertEqual([item.value for item in after], [5.3])

    def test_round_trip_identity_duplicate_guard_and_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "features.jsonl"
            store = PointInTimeFeatureStore(path)
            record = self.feature()
            self.assertEqual(store.append([record]), 1)
            self.assertEqual(store.read_all()[0].record_id, record.record_id)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                store.append([record])
            schema_path = Path(folder) / "schema.json"
            write_schema(schema_path)
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["eligibility_rule"], "available_time <= decision_time")


if __name__ == "__main__":
    unittest.main()
