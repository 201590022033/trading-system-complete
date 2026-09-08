"""Offline tests for market_intelligence SQLite store and schemas."""

import json
import tempfile
import unittest
from pathlib import Path

from evidence import EvidenceRecord
from market_intelligence import (
    InstrumentCandidate,
    MarketNarrative,
    MarketTheme,
    SourceEvidence,
    TickerSelection,
)
from market_intelligence.store import MarketIntelligenceStore


class MarketIntelligenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mi_test.db"
        self.store = MarketIntelligenceStore(self.db_path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_migrations_create_expected_tables(self):
        tables = {
            row["name"]
            for row in self.store._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected = {
            "schema_version",
            "source_policies",
            "evidence_records",
            "documents",
            "market_narratives",
            "ticker_selections",
            "audit_log",
            "watchlists",
        }
        self.assertTrue(expected.issubset(tables))

    def test_source_policy_crud(self):
        policy = {
            "source_id": "test_source",
            "source_name": "Test Source",
            "source_class": "financial_media",
            "authority_tier": 3,
            "access_mode": "public_rss",
            "status": "live_existing",
            "enabled": 1,
            "weight": 1.5,
            "region": "ZA",
            "market_relevance": "jse_company_news",
            "minimum_poll_seconds": 60,
            "notes": "unit test",
            "created_at": "2026-09-08T00:00:00+00:00",
            "updated_at": "2026-09-08T00:00:00+00:00",
        }
        self.store.upsert_source_policy(policy)
        row = self.store.get_source_policy("test_source")
        self.assertIsNotNone(row)
        self.assertEqual(row["source_name"], "Test Source")
        self.assertEqual(row["weight"], 1.5)
        self.assertEqual(row["market_relevance"], "jse_company_news")

        # Update preserves identity and mutates mutable fields.
        policy["weight"] = 2.0
        policy["updated_at"] = "2026-09-08T01:00:00+00:00"
        self.store.upsert_source_policy(policy)
        row = self.store.get_source_policy("test_source")
        self.assertEqual(row["weight"], 2.0)

        self.assertTrue(self.store.delete_source_policy("test_source"))
        self.assertIsNone(self.store.get_source_policy("test_source"))

    def test_upsert_source_policy_requires_required_fields(self):
        with self.assertRaises(ValueError):
            self.store.upsert_source_policy({"source_id": "x"})

    def test_evidence_round_trip(self):
        record = EvidenceRecord(
            evidence_id="ev1",
            source_id="moneyweb_rss",
            source_name="Moneyweb",
            source_class="financial_media",
            authority_tier=3,
            headline="Naspers rises",
            text="Naspers shares advanced.",
            url="https://example.test/naspers",
            observed_at="2026-09-08T10:00:00+00:00",
            published_at="2026-09-08T09:00:00+00:00",
            ingested_at="2026-09-08T10:05:00+00:00",
            tickers=["NPN"],
            assets=["ZAR"],
            sectors=["technology"],
            sentiment="bullish",
            score=0.6,
            confidence=0.6,
            horizon="short",
            metadata={"content_hash": "abc123"},
        )
        self.store.save_evidence(record)
        loaded = self.store.get_evidence("ev1")
        self.assertEqual(loaded.evidence_id, "ev1")
        self.assertEqual(loaded.tickers, ["NPN"])
        self.assertEqual(loaded.metadata["content_hash"], "abc123")

    def test_narrative_round_trip(self):
        evidence = SourceEvidence(
            evidence_id="ev1",
            source_id="moneyweb_rss",
            source_name="Moneyweb",
            headline="Naspers rises",
            url="https://example.test",
            published_at="2026-09-08T09:00:00+00:00",
            direction=1,
            strength=0.6,
        )
        theme = MarketTheme(
            theme="tech momentum",
            direction=1,
            confidence=0.6,
            expected_horizon="short",
            supporting_evidence=[evidence],
        )
        candidate = InstrumentCandidate(
            instrument_id="NPN",
            display_symbol="NPN",
            reason="tech momentum",
            theme="tech momentum",
            confidence=0.6,
        )
        narrative = MarketNarrative(
            narrative_id="nar1",
            generated_at="2026-09-08T10:00:00+00:00",
            model="test-model",
            provider="test",
            schema_version="market-intelligence-v1",
            summary="Tech is moving.",
            themes=[theme],
            candidates=[candidate],
            enabled_sources=["moneyweb_rss"],
        )
        self.store.save_narrative(narrative)
        loaded = self.store.latest_narrative()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.narrative_id, "nar1")
        self.assertEqual(len(loaded.themes), 1)
        self.assertEqual(loaded.themes[0].theme, "tech momentum")
        self.assertEqual(len(loaded.candidates), 1)
        self.assertEqual(loaded.candidates[0].instrument_id, "NPN")

    def test_ticker_selection_round_trip(self):
        selection = TickerSelection(
            instrument_id="USDZAR",
            display_symbol="USD/ZAR",
            pinned=False,
            reason="ZAR fiscal risk",
            theme="ZAR weakness",
            confidence=0.72,
            source_evidence_ids=["ev1"],
            selected_at="2026-09-08T10:00:00+00:00",
            review_at="2026-09-08T12:00:00+00:00",
        )
        self.store.save_ticker_selection(selection)
        active = self.store.active_ticker_selections()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].instrument_id, "USDZAR")
        self.assertFalse(active[0].pinned)

    def test_audit_log(self):
        self.store.audit(
            action="test_action",
            entity_type="source_policy",
            entity_id="x",
            before={"enabled": False},
            after={"enabled": True},
            actor="test",
        )
        rows = self.store._connection.execute(
            "SELECT * FROM audit_log WHERE entity_id = ?", ("x",)
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]["before_json"]), {"enabled": False})
        self.assertEqual(json.loads(rows[0]["after_json"]), {"enabled": True})


if __name__ == "__main__":
    unittest.main()
