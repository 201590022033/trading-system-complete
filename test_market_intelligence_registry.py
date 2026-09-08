"""Offline tests for market_intelligence persisted source registry."""

import tempfile
import unittest
from pathlib import Path

from source_catalog import SourcePolicy
from market_intelligence.source_registry import SourceRegistry
from market_intelligence.store import MarketIntelligenceStore


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mi_registry_test.db"
        self.store = MarketIntelligenceStore(self.db_path)
        self.registry = SourceRegistry(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_seed_defaults_inserts_builtin_policies(self):
        inserted = self.registry.seed_defaults()
        self.assertGreater(inserted, 0)
        policies = self.registry.list_policies()
        ids = {p.source_id for p in policies}
        self.assertIn("moneyweb_rss", ids)
        self.assertIn("efficient_group_commentary", ids)
        # Second seed is idempotent.
        self.assertEqual(self.registry.seed_defaults(), 0)

    def test_enable_disable(self):
        self.registry.seed_defaults()
        self.registry.enable("moneyweb_rss", False)
        policy = self.registry.get_policy("moneyweb_rss")
        self.assertFalse(policy.enabled)

        self.registry.enable("moneyweb_rss", True)
        policy = self.registry.get_policy("moneyweb_rss")
        self.assertTrue(policy.enabled)

    def test_enable_unknown_raises(self):
        with self.assertRaises(KeyError):
            self.registry.enable("unknown", True)

    def test_update_policy(self):
        self.registry.seed_defaults()
        updated = self.registry.update_policy(
            "moneyweb_rss",
            source_name="Moneyweb ZA",
            notes="updated note",
            minimum_poll_seconds=120,
        )
        self.assertEqual(updated.source_name, "Moneyweb ZA")
        self.assertEqual(updated.minimum_poll_seconds, 120)
        row = self.store.get_source_policy("moneyweb_rss")
        self.assertEqual(row["notes"], "updated note")

    def test_update_policy_preserves_store_only_fields(self):
        self.registry.seed_defaults()
        # Inject store-only fields directly.
        row = self.store.get_source_policy("moneyweb_rss")
        row["weight"] = 2.5
        row["region"] = "ZA"
        row["market_relevance"] = "financial_press"
        self.store.upsert_source_policy(row)

        self.registry.update_policy("moneyweb_rss", notes="preserve me")
        refreshed = self.store.get_source_policy("moneyweb_rss")
        self.assertEqual(refreshed["weight"], 2.5)
        self.assertEqual(refreshed["region"], "ZA")
        self.assertEqual(refreshed["market_relevance"], "financial_press")
        self.assertEqual(refreshed["notes"], "preserve me")

    def test_add_and_remove_user_policy(self):
        self.registry.seed_defaults()
        user_policy = SourcePolicy(
            source_id="user_blog",
            source_name="User Blog",
            source_class="financial_media",
            authority_tier=4,
            access_mode="public_rss",
            status="live_existing",
            url="https://example.test/feed",
            enabled=True,
            notes="user-added",
        )
        added = self.registry.add_policy(user_policy)
        self.assertEqual(added.source_id, "user_blog")
        self.assertTrue(self.registry.remove_policy("user_blog"))
        self.assertIsNone(self.registry.get_policy("user_blog"))

    def test_cannot_remove_builtin_policy(self):
        self.registry.seed_defaults()
        with self.assertRaises(ValueError):
            self.registry.remove_policy("moneyweb_rss")

    def test_cannot_add_duplicate_source_id(self):
        self.registry.seed_defaults()
        existing = self.registry.get_policy("moneyweb_rss")
        with self.assertRaises(ValueError):
            self.registry.add_policy(existing)


if __name__ == "__main__":
    unittest.main()
