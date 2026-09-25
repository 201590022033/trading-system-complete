import tempfile
import unittest
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from application.opportunities.paper_config import PaperLoopConfig
from application.opportunities.paper_host import compose_paper_worker, DurablePaperOpportunities, PaperRefreshStatus
from application.opportunities.api import create_blueprint
from persistence.sqlite_repository import SQLiteRepository
from workers.shadow_learning import ShadowWorker
from test_paper_closed_loop import T, charts


class PaperHostTests(unittest.TestCase):
    def test_learning_status_exposes_daily_swing_learning(self):
        import app as deployed_app

        class Repository:
            def learning_status(self):
                return {"database_state": "AVAILABLE", "pending_outcomes": 0}

            def close(self):
                pass

        swing = {"state": "COLLECTING_OUTCOMES", "eligible_outcomes": 7,
                 "minimum_samples": 30, "horizon_sessions": 3}
        with patch.object(deployed_app, "paper_config", object()), \
                patch.object(deployed_app, "runtime_repository", return_value=Repository()), \
                patch.object(deployed_app, "paper_status", return_value={"learning": swing}):
            response = deployed_app.app.test_client().get("/api/learning/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["daily_swing"], swing)
        self.assertFalse(response.json["live_execution"])

    def test_worker_runtime_and_durable_web_after_restart_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"paper.db"
            config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))
            clock = [T]
            class Fetcher:
                def get_chart(self, symbol, period):
                    return charts(clock[0])["TFMJ"]
            for step in range(3):
                clock[0] = T+timedelta(days=step)
                repo = SQLiteRepository(path)
                try:
                    scheduler, handler = compose_paper_worker(repo, config, fetcher=Fetcher(),
                        clock=lambda: clock[0].isoformat())
                    scheduler.enqueue(clock[0].isoformat())
                    worker = ShadowWorker(repo, "test", {"paper-cycle": handler}, clock=lambda: clock[0].isoformat())
                    self.assertEqual(worker.run_once(), 1)
                    self.assertEqual(worker.run_once(), 0)
                finally:
                    repo.close()
            verify = SQLiteRepository(path)
            try:
                inputs = verify.paper_records(
                    config.account_id, "input", as_of=clock[0].isoformat(), limit=10)
                self.assertTrue(inputs)
                for frozen in inputs:
                    for chart in frozen["input"]["charts"].values():
                        self.assertLessEqual(len(chart["bars"]), 60)
                        self.assertTrue(all(set(bar) == {"timestamp", "close", "volume"}
                                            for bar in chart["bars"]))
            finally:
                verify.close()
            service = DurablePaperOpportunities(lambda: SQLiteRepository(path), config, clock=lambda: clock[0])
            app = Flask(__name__)
            app.register_blueprint(create_blueprint(service, PaperRefreshStatus(lambda: SQLiteRepository(path), config)))
            with app.test_client() as client:
                response = client.get("/api/v1/opportunities?limit=5")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["count"], 1)
                oid = response.json["opportunities"][0]["opportunity_id"]
                self.assertEqual(client.get("/api/v1/opportunities/"+oid).status_code, 200)
                with patch.object(service, "factory", side_effect=RuntimeError("private-credential")):
                    failure = client.get("/api/v1/opportunities")
                    self.assertEqual(failure.status_code, 503)
                    self.assertNotIn("private-credential", failure.get_data(as_text=True))
                clock[0] += timedelta(days=2)
                self.assertEqual(client.get("/api/v1/opportunities").json["count"], 0)

    def test_utc_future_nested_evidence_and_undated_news(self):
        from application.opportunities.evidence import causal_bundle, news_context
        nested = {"learned": {"cells": [{"updated_at": "2026-09-19T15:00:00+02:00"}]}}
        self.assertEqual(causal_bundle(nested, T), {})
        past = {"learned": {"updated_at": "2026-09-19T13:00:00+02:00"}}
        self.assertIn("learned", causal_bundle(past, T))
        self.assertEqual(news_context({"tickers": {"TFMJ": {"score": 1}}}, "TFMJ", T)["state"], "UNAVAILABLE")

    def test_discovery_feed_is_retired_and_does_not_schedule_network(self):
        from dashboard_feeds import DashboardFeeds
        feeds = DashboardFeeds()
        try:
            with self.assertRaises(RuntimeError):
                feeds.opportunities()
            self.assertEqual(feeds._entries, {})
        finally:
            feeds._pool.shutdown()
