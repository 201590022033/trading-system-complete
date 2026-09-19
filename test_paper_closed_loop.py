import math
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_loop import PaperLoop, paper_feature_outcomes, VERSION
from application.opportunities.public_research import public_share_catalog, refresh_public_research
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres

T = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)


def charts(at, *, price_override=None):
    start = T.date()-timedelta(days=210)
    count = (at.date()-start).days
    bars = [{"timestamp": (start+timedelta(days=i)).isoformat(),
             "close": 100+i*.4+math.sin(i)*3, "volume": 1e6} for i in range(count)]
    if price_override is not None:
        bars[-1]["close"] = price_override
    return {"TFMJ": {"symbol": public_share_catalog()["TFMJ"]["yahoo_symbol"],
                      "interval": "1d", "currency": "ZAR", "bars": bars}}


def frozen(i, **kwargs):
    at = T+timedelta(days=i)
    return {"job_key": "j"+str(i), "evaluated_at": at.isoformat(), "input": {"charts": charts(at, **kwargs)}}


class ClosedLoopTests(unittest.TestCase):
    def config(self):
        return replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))

    def test_real_chain_restart_idempotence_outcomes_and_rollback_both_backends(self):
        for backend in ("sqlite", "postgresql"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/"state.db"
                def open_repo():
                    if backend == "sqlite":
                        return SQLiteRepository(path)
                    repo = PostgresRepository("postgresql://fixture", connection=SQLiteDBAPIForPostgres(path))
                    repo.initialize()
                    return repo
                repo = open_repo()
                try:
                    loop = PaperLoop(repo, self.config())
                    loop.initialize()
                    first = loop.cycle("j0", frozen(0))
                    self.assertFalse(first["opened"])
                    repo.close()
                    repo = open_repo()
                    loop = PaperLoop(repo, self.config())
                    loop.initialize()
                    second = loop.cycle("j1", frozen(1))
                    self.assertEqual(second["opened"], ["EQ_ZAR_TFMJ"], second)
                    saved = repo.paper_account(self.config().account_id)
                    self.assertEqual(second, loop.cycle("j1", frozen(1)))
                    self.assertEqual(saved, repo.paper_account(self.config().account_id))
                    # Failure after fills/outcomes but before final commit must undo everything.
                    original = repo.save_paper_record
                    def fail(rid, account, kind, at, payload):
                        if kind == "ranking":
                            raise RuntimeError("injected commit boundary")
                        return original(rid, account, kind, at, payload)
                    with patch.object(repo, "save_paper_record", side_effect=fail), self.assertRaises(RuntimeError):
                        loop.cycle("j2", frozen(2))
                    self.assertEqual(saved, repo.paper_account(self.config().account_id))
                    self.assertEqual(repo.paper_records(self.config().account_id, "outcome", as_of=(T+timedelta(days=3)).isoformat()), [])
                    third = loop.cycle("j2", frozen(2))
                    self.assertEqual(third["closed"], ["EQ_ZAR_TFMJ"])
                    self.assertEqual(third["outcome_count"], 1)
                    self.assertEqual(third["account"]["position_count"], 0)
                    outcomes = paper_feature_outcomes(repo, self.config().account_id, T+timedelta(days=3))
                    self.assertEqual(len(outcomes), 1)
                    self.assertEqual(paper_feature_outcomes(repo, self.config().account_id, T), ())
                    state = repo.paper_account(self.config().account_id)
                    self.assertEqual(len(state["broker"]["fills"]), 2)
                    self.assertAlmostEqual(third["account"]["equity"]-self.config().starting_cash,
                        repo.paper_records(self.config().account_id, "outcome", as_of=(T+timedelta(days=3)).isoformat())[0]["net_pnl"])
                finally:
                    repo.close()

    def test_missing_prices_do_not_invent_exit_and_pause_blocks_open(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"state.db")
            try:
                loop = PaperLoop(repo, self.config())
                loop.initialize()
                loop.cycle("j0", frozen(0))
                self.assertFalse(loop.cycle("j1", frozen(1), paused=True)["opened"])
                opened = loop.cycle("j2", frozen(2))
                self.assertTrue(opened["opened"], opened)
                empty = frozen(3)
                empty["input"]["charts"] = {}
                missing = loop.cycle("j3", empty)
                self.assertFalse(missing["closed"])
                self.assertEqual(missing["account"]["position_count"], 1)
                self.assertEqual(missing["outcome_count"], 0)
                gap = loop.cycle("j4", frozen(4, price_override=20))
                self.assertEqual(len(gap["closed"]), 1)
                fills = repo.paper_account(self.config().account_id)["broker"]["fills"]
                self.assertEqual(fills[-1]["observed_price"], 20)
                self.assertLess(fills[-1]["fill_price"], 20)
            finally:
                repo.close()

    def test_causal_strategy_learning_changes_existing_m13_score(self):
        from domain.evaluation.effectiveness import FeatureOutcome
        from application.opportunities.paper_loop import FrozenCharts
        kwargs = dict(fetcher=FrozenCharts(charts(T)), evaluated_at=T, universe=("TFMJ",), max_workers=1)
        def observations(net):
            return tuple(FeatureOutcome("paper_strategy", VERSION, "strategy", "EQ_ZAR_TFMJ", "1d",
                None, None, 1, T-timedelta(days=i+2), T-timedelta(days=i+2),
                T-timedelta(days=i+1), .01, net, str(i)) for i in range(30))
        positive = refresh_public_research(**kwargs, paper_outcomes=observations(.01)).opportunities[0]
        negative = refresh_public_research(**kwargs, paper_outcomes=observations(-.01)).opportunities[0]
        self.assertGreater(positive.ranking_score, negative.ranking_score)
        self.assertIn("paper_strategy", negative.feature_evidence_summary.negative_feature_ids)
        future = tuple(replace(x, outcome_maturity=T+timedelta(days=1)) for x in observations(-1))
        base = refresh_public_research(**kwargs).opportunities[0]
        changed = refresh_public_research(**kwargs, paper_outcomes=future).opportunities[0]
        self.assertEqual(base.ranking_score, changed.ranking_score)

    def test_accounts_cannot_collide_and_future_bars_cannot_displace_history(self):
        from application.opportunities.paper_loop import causal_series, FrozenCharts
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"state.db")
            try:
                for account in ("paper-a", "paper-b"):
                    loop = PaperLoop(repo, replace(self.config(), account_id=account))
                    loop.initialize()
                    loop.cycle("j0", frozen(0))
                    self.assertEqual(loop.cycle("j1", frozen(1))["opened"], ["EQ_ZAR_TFMJ"])
                    self.assertEqual(loop.cycle("j2", frozen(2))["closed"], ["EQ_ZAR_TFMJ"])
                    self.assertEqual(len(repo.paper_records(account, "fill", as_of=(T+timedelta(days=3)).isoformat())), 2)
                self.assertNotEqual(repo.paper_records("paper-a", "policy", as_of=(T+timedelta(days=2)).isoformat())[0]["policy_id"],
                                    repo.paper_records("paper-b", "policy", as_of=(T+timedelta(days=2)).isoformat())[0]["policy_id"])
            finally:
                repo.close()
        initial = charts(T)
        extended = charts(T)
        extended["TFMJ"]["bars"].extend({"timestamp": (T+timedelta(days=i)).date().isoformat(),
                                         "close": -1, "volume": 0} for i in range(450))
        self.assertEqual(causal_series("TFMJ", initial["TFMJ"], T), causal_series("TFMJ", extended["TFMJ"], T))
        kwargs = dict(evaluated_at=T, universe=("TFMJ",), max_workers=1)
        base = refresh_public_research(fetcher=FrozenCharts(initial), **kwargs).opportunities[0]
        changed = refresh_public_research(fetcher=FrozenCharts(extended), **kwargs).opportunities[0]
        self.assertEqual(base.to_dict(), changed.to_dict())

    def test_stale_prices_cannot_reach_authoritative_ranking(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"state.db")
            try:
                loop = PaperLoop(repo, self.config())
                loop.initialize()
                data = frozen(3)
                data["input"]["charts"] = charts(T)
                result = loop.cycle("j3", data)
                self.assertFalse(repo.paper_record(result["ranking_record_id"])["opportunities"])
                self.assertEqual(result["unavailable"], ["TFMJ"])
            finally:
                repo.close()
