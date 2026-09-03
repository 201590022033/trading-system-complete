"""Offline tests for M8 specialist source policy and provenance."""

from datetime import datetime, timedelta, timezone
import unittest

from data_pipeline import NewsItem, SentimentLabel
from source_catalog import DEFAULT_SPECIALIST_SOURCES


class SourceCatalogTests(unittest.TestCase):
    def test_only_existing_permitted_collectors_are_enabled(self):
        enabled = {item.source_id for item in DEFAULT_SPECIALIST_SOURCES.configured() if item.enabled}
        self.assertEqual(enabled, {"moneyweb_sens", "moneyweb_rss"})
        self.assertEqual(
            DEFAULT_SPECIALIST_SOURCES.get("tradingview_ideas").status,
            "excluded_non_display_terms",
        )

    def test_sources_can_be_disabled_independently(self):
        changed = DEFAULT_SPECIALIST_SOURCES.with_enabled("moneyweb_rss", False)
        self.assertFalse(changed.get("moneyweb_rss").enabled)
        self.assertTrue(changed.get("moneyweb_sens").enabled)

    def test_poll_interval_is_enforced(self):
        catalog = DEFAULT_SPECIALIST_SOURCES.with_enabled("moneyweb_rss", True)
        now = datetime(2026, 9, 3, tzinfo=timezone.utc)
        self.assertTrue(catalog.poll_allowed("moneyweb_rss", now))
        catalog.mark_polled("moneyweb_rss", now)
        self.assertFalse(catalog.poll_allowed("moneyweb_rss", now + timedelta(seconds=299)))
        self.assertTrue(catalog.poll_allowed("moneyweb_rss", now + timedelta(seconds=300)))

    def test_normalization_preserves_policy_provenance(self):
        item = NewsItem(
            ticker="JSE", headline="Issuer publishes results", source="Moneyweb",
            timestamp=datetime(2026, 9, 3, tzinfo=timezone.utc),
            sentiment_label=SentimentLabel.NEUTRAL, sentiment_score=0.0,
        )
        record = DEFAULT_SPECIALIST_SOURCES.normalize("moneyweb_sens", item, tickers=["NPN"])
        self.assertEqual(record.source_id, "moneyweb_sens")
        self.assertEqual(record.authority_tier, 1)
        self.assertEqual(record.tickers, ["NPN"])
        self.assertEqual(record.metadata["catalog_version"], "specialist-sources-v1")

    def test_reliability_registry_uses_independent_enabled_flags(self):
        registry = DEFAULT_SPECIALIST_SOURCES.reliability_registry()
        self.assertTrue(registry.get("moneyweb_rss").enabled)
        self.assertFalse(registry.get("reddit_personalfinanceza").enabled)


if __name__ == "__main__":
    unittest.main()
