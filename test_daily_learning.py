import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from application.opportunities.daily_learning import (
    DECISION_KIND,
    FEATURE_ID,
    OUTCOME_KIND,
    feature_outcomes,
    label_matured,
    record_decisions,
)
from application.opportunities.paper_loop import FrozenCharts
from application.opportunities.public_research import refresh_public_research
from domain.evaluation.effectiveness import FeatureOutcome
from persistence.sqlite_repository import SQLiteRepository
from test_paper_closed_loop import charts


T = datetime(2026, 9, 21, tzinfo=timezone.utc)


def opportunity():
    return SimpleNamespace(
        rank=1,
        direction="LONG",
        instrument_id="EQ_ZAR_TFMJ",
        opportunity_id="opp:test",
        regime_version="regime-v1",
        regime_context={"trend": "BULL"},
        ranking_version="ranking-v1",
    )


def series(days):
    bars = [(T + timedelta(days=index), 100.0 + index, 1_000_000)
            for index in range(days)]
    return {"TFMJ": {"instrument_id": "EQ_ZAR_TFMJ", "bars": bars}}


class DailyLearningTests(unittest.TestCase):
    def test_compact_decision_is_deduplicated_and_labels_only_after_three_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "learning.db")
            try:
                repository.create_paper_account("a", {"mode": "PAPER"})
                initial = series(1)
                self.assertEqual(record_decisions(
                    repository, "a", (opportunity(),), initial, evaluated_at=T), 1)
                self.assertEqual(record_decisions(
                    repository, "a", (opportunity(),), initial, evaluated_at=T), 0)
                stored = repository.paper_records(
                    "a", DECISION_KIND, as_of=T.isoformat(), limit=10)
                self.assertEqual(len(stored), 1)
                self.assertNotIn("bars", stored[0])
                self.assertLess(len(json.dumps(stored[0])), 2000)

                self.assertEqual(label_matured(
                    repository, "a", series(3), evaluated_at=T + timedelta(days=2)), 0)
                self.assertEqual(label_matured(
                    repository, "a", series(4), evaluated_at=T + timedelta(days=3)), 1)
                self.assertEqual(label_matured(
                    repository, "a", series(5), evaluated_at=T + timedelta(days=4)), 0)

                outcomes = repository.paper_records(
                    "a", OUTCOME_KIND, as_of=(T + timedelta(days=4)).isoformat(), limit=10)
                self.assertEqual(len(outcomes), 1)
                self.assertAlmostEqual(outcomes[0]["gross_return"], .03)
                self.assertAlmostEqual(outcomes[0]["net_return"], .029)
                adapted = feature_outcomes(
                    repository, "a", evaluated_at=T + timedelta(days=4))
                self.assertEqual(len(adapted), 1)
                self.assertEqual(adapted[0].feature_id, FEATURE_ID)
                self.assertEqual(adapted[0].horizon_id, "1d")
                self.assertEqual(adapted[0].outcome_maturity, T + timedelta(days=3))
            finally:
                repository.close()

    def test_non_long_or_unranked_candidates_are_not_collected(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "learning.db")
            try:
                repository.create_paper_account("a", {"mode": "PAPER"})
                short = SimpleNamespace(**{**opportunity().__dict__, "direction": "SHORT"})
                unranked = SimpleNamespace(**{**opportunity().__dict__, "rank": None})
                self.assertEqual(record_decisions(
                    repository, "a", (short, unranked), series(1), evaluated_at=T), 0)
                self.assertEqual(repository.paper_records(
                    "a", DECISION_KIND, as_of=T.isoformat(), limit=10), [])
            finally:
                repository.close()

    def test_thirty_matured_swing_outcomes_feed_existing_ranking_support(self):
        kwargs = dict(fetcher=FrozenCharts(charts(T)), evaluated_at=T,
                      universe=("TFMJ",), max_workers=1)

        def evidence(net_return):
            return tuple(FeatureOutcome(
                FEATURE_ID, "ranked-long-swing-v1", "strategy", "EQ_ZAR_TFMJ", "1d",
                None, None, 1, T - timedelta(days=index + 5),
                T - timedelta(days=index + 5), T - timedelta(days=index + 2),
                net_return + .001, net_return, f"swing:{index}",
            ) for index in range(30))

        positive = refresh_public_research(
            **kwargs, paper_outcomes=evidence(.02)).opportunities[0]
        negative = refresh_public_research(
            **kwargs, paper_outcomes=evidence(-.02)).opportunities[0]
        self.assertGreater(positive.ranking_score, negative.ranking_score)
        self.assertIn(FEATURE_ID, negative.feature_evidence_summary.negative_feature_ids)


if __name__ == "__main__":
    unittest.main()
