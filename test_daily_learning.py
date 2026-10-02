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
    PANEL_DECISION_KIND,
    PANEL_OUTCOME_KIND,
    candidate_panel_summary,
    feature_outcomes,
    label_candidate_panel,
    label_matured,
    record_candidate_panel,
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
        eligibility_status="ELIGIBLE",
        ranking_score=60.0,
        input_evidence={"technical": {"momentum_20d_signal": 1,
                                      "rsi_14_signal": 0},
                        "news_macro": {"state": "UNAVAILABLE"}},
    )


def series(days):
    bars = [(T + timedelta(days=index), 100.0 + index, 1_000_000)
            for index in range(days)]
    return {"TFMJ": {"instrument_id": "EQ_ZAR_TFMJ", "bars": bars}}


class DailyLearningTests(unittest.TestCase):
    def test_delayed_signal_cannot_enter_before_the_actual_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            repository=SQLiteRepository(Path(directory)/"delayed.db")
            try:
                repository.create_paper_account("a",{"mode":"PAPER"})
                record_candidate_panel(repository,"a",(opportunity(),),series(1),
                                       evaluated_at=T+timedelta(days=2,hours=1))
                self.assertEqual(label_candidate_panel(repository,"a",series(6),
                    evaluated_at=T+timedelta(days=5)),0)
                self.assertEqual(label_candidate_panel(repository,"a",series(7),
                    evaluated_at=T+timedelta(days=6)),1)
                outcome=repository.paper_records("a",PANEL_OUTCOME_KIND,
                    as_of=(T+timedelta(days=6)).isoformat())[0]
                self.assertEqual(outcome["entry_bar_at"],(T+timedelta(days=3)).isoformat())
                self.assertEqual(outcome["exit_bar_at"],(T+timedelta(days=6)).isoformat())
            finally:repository.close()
    def test_candidate_panel_tracks_alternatives_and_next_session_proxy(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "panel.db")
            try:
                repository.create_paper_account("a", {"mode": "PAPER"})
                selected = opportunity()
                other = SimpleNamespace(**{**opportunity().__dict__,
                    "instrument_id": "EQ_ZAR_OTHER", "direction": "SHORT", "rank": 2})
                def panel_series(days):
                    return {
                        "TFMJ": {"instrument_id": "EQ_ZAR_TFMJ", "bars": [
                            (T + timedelta(days=i), float(100 + i), 1_000_000)
                            for i in range(days)]},
                        "OTHER": {"instrument_id": "EQ_ZAR_OTHER", "bars": [
                            (T + timedelta(days=i), float(100 - i), 1_000_000)
                            for i in range(days)]},
                    }
                self.assertEqual(record_candidate_panel(
                    repository, "a", (selected, other), panel_series(1), evaluated_at=T,
                    market_context={"state": "SUPPORTIVE"},
                    sectors={"TFMJ": "Retail", "OTHER": "Mining"}), 2)
                self.assertEqual(record_candidate_panel(
                    repository, "a", (selected, other), panel_series(1), evaluated_at=T), 0)
                decisions = repository.paper_records(
                    "a", PANEL_DECISION_KIND, as_of=T.isoformat(), limit=10)
                self.assertEqual(len(decisions), 2)
                self.assertTrue(any(row["selected"] for row in decisions))
                self.assertTrue(all(row["market_state"] == "SUPPORTIVE" for row in decisions))
                self.assertFalse(next(row for row in decisions
                                      if row["instrument_id"] == "EQ_ZAR_OTHER")["selected"])
                self.assertTrue(all("bars" not in row and len(json.dumps(row)) < 2000
                                    for row in decisions))
                self.assertEqual(label_candidate_panel(
                    repository, "a", panel_series(4), evaluated_at=T + timedelta(days=3)), 0)
                self.assertEqual(label_candidate_panel(
                    repository, "a", panel_series(5), evaluated_at=T + timedelta(days=4)), 2)
                outcomes = repository.paper_records(
                    "a", PANEL_OUTCOME_KIND, as_of=(T + timedelta(days=4)).isoformat(), limit=10)
                chosen = next(row for row in outcomes if row["selected"])
                self.assertEqual(chosen["entry_close"], 101.0)
                self.assertEqual(chosen["exit_close"], 104.0)
                self.assertAlmostEqual(chosen["net_return"], 104 / 101 - 1 - .001)
                summary = candidate_panel_summary(
                    repository, "a", evaluated_at=T + timedelta(days=4))
                self.assertEqual(summary["paired_sessions"], 1)
                self.assertEqual(summary["nonoverlapping_paired_sessions"], 1)
                self.assertGreater(summary["mean_selection_edge"], 0)
                self.assertEqual(summary["by_market_state"]["SUPPORTIVE"]["nonoverlapping_sessions"], 1)
                self.assertEqual(summary["state"], "COLLECTING_COMPARISONS")
            finally:
                repository.close()

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

    def test_selected_only_returns_do_not_change_ranking_without_comparison(self):
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
        self.assertEqual(positive.ranking_score, negative.ranking_score)
        self.assertNotIn(FEATURE_ID, negative.feature_evidence_summary.negative_feature_ids)


if __name__ == "__main__":
    unittest.main()
