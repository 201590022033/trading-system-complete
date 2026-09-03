"""Offline tests for source registry and reliability outcomes."""

import unittest
from datetime import datetime, timedelta, timezone

from reliability_store import ReliabilityStore, SourceDefinition, SourceRegistry


class ReliabilityStoreTests(unittest.TestCase):
    def test_registry_validates_and_filters_sources(self):
        registry = SourceRegistry()
        registry.register(SourceDefinition("moneyweb", "Moneyweb", "media", 3))
        registry.register(SourceDefinition("reddit", "Reddit", "community", 4, enabled=False))
        self.assertEqual([s.source_id for s in registry.enabled()], ["moneyweb"])
        with self.assertRaises(ValueError):
            registry.register(SourceDefinition("bad", "Bad", "other", 5))

    def test_summary_uses_conservative_prior(self):
        store = ReliabilityStore()
        observed = datetime(2026, 9, 3, tzinfo=timezone.utc)
        for index in range(4):
            store.record_outcome(
                evidence_id=f"e{index}", source_id="moneyweb", scope_key="gold_mining",
                horizon="5d", observed_at=observed,
                evaluated_at=observed + timedelta(days=5), direction=1,
                forward_return=0.02,
            )
        summary = store.summarize("moneyweb", "gold_mining", "5d")
        self.assertEqual(summary.samples, 4)
        self.assertEqual(summary.wins, 4)
        self.assertEqual(summary.hit_rate, 1.0)
        self.assertLess(summary.reliability, 1.0)
        self.assertGreater(summary.reliability, 0.5)

    def test_evaluation_before_observation_is_rejected(self):
        store = ReliabilityStore()
        observed = datetime(2026, 9, 3, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            store.record_outcome(
                evidence_id="e1", source_id="source", scope_key="global", horizon="1d",
                observed_at=observed, evaluated_at=observed - timedelta(days=1),
                direction=1, forward_return=0.01,
            )

    def test_duplicate_outcome_is_ignored(self):
        store = ReliabilityStore()
        observed = datetime(2026, 9, 3, tzinfo=timezone.utc)
        args = dict(
            evidence_id="same", source_id="source", scope_key="global", horizon="1d",
            observed_at=observed, evaluated_at=observed + timedelta(days=1),
            direction=1, forward_return=0.01,
        )
        store.record_outcome(**args)
        store.record_outcome(**args)
        self.assertEqual(store.summarize("source", "global", "1d").samples, 1)


if __name__ == "__main__":
    unittest.main()
