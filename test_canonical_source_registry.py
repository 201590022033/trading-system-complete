import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from domain.registry.source import (CanonicalSourcePolicy,
                                    CanonicalSourceRegistry, GovernanceState,
                                    default_canonical_policies)
from market_intelligence.source_registry import SourceRegistry as LegacySourceRegistry
from market_intelligence.store import MarketIntelligenceStore
from source_catalog import DEFAULT_SOURCE_POLICIES


class CanonicalSourceRegistryTests(unittest.TestCase):
    def registry(self, path):
        return CanonicalSourceRegistry(LegacySourceRegistry(MarketIntelligenceStore(path)))

    def test_builtin_mapping_and_unique_ids(self):
        policies = default_canonical_policies()
        self.assertEqual(len(policies), len(DEFAULT_SOURCE_POLICIES))
        self.assertEqual(len({item.source_id for item in policies}), len(policies))
        moneyweb = next(item for item in policies if item.source_id == "moneyweb_rss")
        self.assertEqual(moneyweb.governance_state, GovernanceState.PRODUCTION)
        self.assertTrue(moneyweb.provenance_capable)

    def test_custom_registration_duplicate_and_malformed_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = self.registry(Path(directory) / "sources.db")
            registry.seed_defaults()
            custom = replace(default_canonical_policies()[0], source_id="custom-test",
                             display_name="Custom test", endpoint=None,
                             governance_state=GovernanceState.RESEARCH, enabled=False)
            self.assertEqual(registry.register(custom).source_id, "custom-test")
            with self.assertRaises(ValueError): registry.register(custom)
            with self.assertRaises(ValueError): replace(custom, authority_tier=9)
            with self.assertRaises(FrozenInstanceError): custom.enabled = True
            registry.legacy.store.close()

    def test_enable_disable_and_manual_weight_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.db"
            first = self.registry(path)
            first.seed_defaults()
            first.update("moneyweb_rss", notes="preserved test note")
            disabled = first.enable("moneyweb_rss", False)
            self.assertFalse(disabled.enabled)
            self.assertEqual(first.legacy.store.get_source_policy("moneyweb_rss")["weight"], 1.0)
            first.legacy.store.close()
            second = self.registry(path)
            restored = second.get("moneyweb_rss")
            self.assertFalse(restored.enabled)
            self.assertEqual(restored.notes, "preserved test note")
            second.legacy.store.close()

    def test_legacy_registry_is_the_persistence_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = LegacySourceRegistry(MarketIntelligenceStore(Path(directory) / "sources.db"))
            canonical = CanonicalSourceRegistry(legacy)
            canonical.seed_defaults()
            self.assertEqual(len(canonical.list_policies()), len(legacy.list_policies()))
            self.assertIs(canonical.legacy, legacy)
            legacy.store.close()

    def test_unknown_optional_metadata_and_provenance_mapping(self):
        policy = next(item for item in default_canonical_policies() if item.source_id == "jse_market_data")
        self.assertIsNone(policy.maximum_age_seconds)
        self.assertIsNone(policy.learned_weight)
        self.assertEqual(policy.provenance()["source_id"], policy.source_id)


if __name__ == "__main__":
    unittest.main()
