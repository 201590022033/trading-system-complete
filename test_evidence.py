"""Offline tests for evidence normalization and deduplication."""

import unittest
from datetime import datetime, timezone

from data_pipeline import NewsItem, SentimentLabel
from evidence import (
    PROVENANCE_VERSION,
    deduplicate_evidence,
    evidence_id,
    normalize_news_item,
)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.item = NewsItem(
            ticker="NPN",
            headline="Naspers reports strong earnings",
            source="Moneyweb",
            timestamp=datetime(2026, 9, 3, 7, 0, tzinfo=timezone.utc),
            sentiment_label=SentimentLabel.BULLISH,
            sentiment_score=0.7,
            text="Naspers reported stronger earnings.",
        )

    def test_normalization_preserves_news_and_adds_provenance(self):
        record = normalize_news_item(
            self.item,
            source_id="moneyweb",
            url="https://example.test/story",
            assets=["zar"],
            sectors=["technology"],
        )
        self.assertEqual(record.source_id, "moneyweb")
        self.assertEqual(record.source_class, "financial_media")
        self.assertEqual(record.authority_tier, 3)
        self.assertEqual(record.tickers, ["NPN"])
        self.assertEqual(record.assets, ["ZAR"])
        self.assertEqual(record.sectors, ["technology"])
        self.assertEqual(record.score, 0.7)
        self.assertEqual(record.parser_version, PROVENANCE_VERSION)
        self.assertTrue(record.evidence_id)

    def test_evidence_id_is_stable(self):
        args = ("moneyweb", self.item.headline, self.item.timestamp, "story-1")
        self.assertEqual(evidence_id(*args), evidence_id(*args))

    def test_deduplicate_preserves_first_record(self):
        first = normalize_news_item(self.item, source_id="moneyweb")
        duplicate = normalize_news_item(self.item, source_id="moneyweb")
        unique = deduplicate_evidence([first, duplicate])
        self.assertEqual(unique, [first])


if __name__ == "__main__":
    unittest.main()
