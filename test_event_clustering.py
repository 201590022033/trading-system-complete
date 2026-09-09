import unittest
from datetime import datetime, timedelta, timezone

from domain.intelligence.clustering import (EventClusterPolicy, EventClusterer,
                                             token_jaccard)
from evidence import EvidenceRecord, deduplicate_evidence


UTC = timezone.utc


def record(eid, headline, *, source="wire", ticker="NPN", hours=0, sentiment="neutral", score=0.0, assets=()):
    stamp = (datetime(2026, 1, 1, 10, tzinfo=UTC) + timedelta(hours=hours)).isoformat()
    return EvidenceRecord(eid, source, source.title(), "financial_media", 3, headline, "body", None,
                          stamp, stamp, stamp, [ticker] if ticker else [], list(assets), [], sentiment, score, abs(score), None, metadata={})


class EventClusteringTests(unittest.TestCase):
    def setUp(self):
        self.policy = EventClusterPolicy("test-policy", "v1", 21600, "token_jaccard", .55, True)
        self.clusterer = EventClusterer(self.policy)

    def test_identical_and_syndicated_reports_cluster_preserving_members(self):
        records = [record("a", "Naspers reports strong annual profit", source="reuters", sentiment="bullish", score=.8),
                   record("b", "Naspers reports strong annual profit", source="moneyweb", sentiment="bullish", score=.6),
                   record("c", "Naspers reports strong annual profit", source="newsapi", sentiment="neutral")]
        events = self.clusterer.cluster(records)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].underlying_evidence_ids, ("a", "b", "c"))
        self.assertEqual(events[0].source_ids, ("moneyweb", "newsapi", "reuters"))
        self.assertEqual(events[0].duplicate_evidence_count, 2)

    def test_small_rewrite_and_entity_overlap(self):
        records = [record("a", "Naspers announces strong annual profit"),
                   record("b", "Naspers announces strong annual profits", hours=1),
                   record("c", "Sasol announces strong annual profit", ticker="SOL", hours=1)]
        self.assertEqual(len(self.clusterer.cluster(records)), 2)

    def test_window_and_policy_version_change_identity(self):
        records = [record("a", "Naspers reports annual profit"), record("b", "Naspers reports annual profit", hours=7)]
        self.assertEqual(len(self.clusterer.cluster(records)), 2)
        other = EventClusterer(EventClusterPolicy("test-policy", "v2", 21600, "token_jaccard", .55, True))
        self.assertNotEqual(self.clusterer.cluster(records)[0].event_id, other.cluster(records)[0].event_id)

    def test_false_duplicate_safety(self):
        records = [record("a", "Naspers announces results and dividend declaration"),
                   record("b", "Naspers announces director dealing notification", hours=1),
                   record("c", "Naspers announces results and dividend declaration", hours=1)]
        events = self.clusterer.cluster(records)
        self.assertEqual(len(events), 2)
        self.assertEqual(sum(len(event.underlying_evidence_ids) for event in events), 3)

    def test_missing_metadata_and_empty_headline_do_not_crash_or_merge(self):
        records = [record("a", "", ticker=None), record("b", "", ticker=None, hours=1), record("c", "Brent supply shock", ticker=None)]
        self.assertEqual(len(self.clusterer.cluster(records)), 3)

    def test_exact_dedup_tier_remains_unchanged(self):
        first = record("a", "Naspers event")
        duplicate = record("a", "Naspers event", source="copy")
        self.assertEqual(len(deduplicate_evidence([first, duplicate])), 1)
        self.assertEqual(len(self.clusterer.cluster([first, duplicate])), 1)

    def test_as_of_snapshot_excludes_future_evidence(self):
        early = record("a", "Naspers reports annual profit")
        late = record("b", "Naspers reports annual profit", hours=1)
        cutoff = datetime(2026, 1, 1, 10, 30, tzinfo=UTC)
        snapshot = self.clusterer.cluster([early, late], as_of=cutoff)
        full = self.clusterer.cluster([early, late])
        self.assertEqual(snapshot[0].underlying_evidence_ids, ("a",))
        self.assertEqual(full[0].underlying_evidence_ids, ("a", "b"))

    def test_stable_identity_and_provenance(self):
        records = [record("a", "Naspers event", source="reuters", assets=("gold",)), record("b", "Naspers event", source="moneyweb", assets=("gold",))]
        left = self.clusterer.cluster(records)[0]
        right = self.clusterer.cluster(records)[0]
        self.assertEqual(left.event_id, right.event_id)
        self.assertEqual(left.entity_references, ("NPN",))
        self.assertEqual(left.macro_references, ("gold",))

    def test_policy_validation_and_similarity(self):
        self.assertGreaterEqual(token_jaccard("Naspers profit rises", "Naspers profit rises sharply"), .6)
        with self.assertRaises(ValueError): EventClusterPolicy("x", "v1", 0, "token_jaccard", .5, True)
        with self.assertRaises(ValueError): EventClusterPolicy("x", "v1", 1, "embedding", .5, True)


if __name__ == "__main__":
    unittest.main()
