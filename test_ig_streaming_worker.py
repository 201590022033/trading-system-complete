"""Tests for durable IG Demo streaming ingestion worker."""
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from domain.broker.ig import IGConfig, IGMarket, IGSession
from domain.market_data.streaming import OrderingState
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import timestamp
from workers.ig_streaming import (
    IGStreamIngestion, IGStreamIngestionConfig, IGStreamScheduler, compose_ig_stream_worker,
    IG_STREAM_JOB_INTERVAL_SECONDS,
)


UTC = timezone.utc
NOW = datetime(2026, 9, 20, 10, 0, 0, tzinfo=UTC)


class FakeIGTransport:
    """Never makes a network call; captures request metadata."""

    def __init__(self):
        self.calls = []
        self.responses = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        return self.responses.pop(0)


class FakeIGAdapter:
    """Minimal read-only adapter stub for streaming tests."""

    broker = "IG"

    def __init__(self, config):
        self.config = config
        self._session = None
        self._markets = {
            "CC.D.LCO.BMU.IP": IGMarket("CC.D.LCO.BMU.IP", "Brent", "COMMODITY", "USD",
                                        "TRADEABLE", None, 1.0, 1.0, 1.0, 0.001, None,
                                        (), 75.0, 76.0, "AVAILABLE", "DEMO", "fake"),
            "CS.D.GOLD.CFD.IP": IGMarket("CS.D.GOLD.CFD.IP", "Gold", "COMMODITY", "USD",
                                         "TRADEABLE", None, 1.0, 1.0, 1.0, 0.001, None,
                                         (), 2000.0, 2001.0, "AVAILABLE", "DEMO", "fake"),
        }

    def authenticate(self):
        self._session = IGSession("CST", "XST", "ACC", "https://demo-apd.marketdatasystems.com")
        return {"authenticated": True, "environment": "DEMO"}

    def get_market(self, epic):
        return self._markets[epic]


class FakeLightstreamerTransport:
    """Synchronously delivers programmed observations to the ingestion callback."""

    def __init__(self, on_observation=None, observations=(), clock=None):
        self.on_observation = on_observation or (lambda x: None)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.connected = False
        self.subscribed = set()
        self.observations = observations
        self.rejected_updates = 0
        self._callbacks = {}

    def connect(self, endpoint, account, password):
        self.connected = True

    def subscribe(self, item, fields, callback):
        self.subscribed.add(item)
        self._callbacks[item] = callback
        received_at = self.clock()
        for values in self.observations:
            obs = callback(values, received_at)
            self.on_observation(obs)

    def unsubscribe(self, item):
        self.subscribed.discard(item)
        self._callbacks.pop(item, None)

    def disconnect(self):
        self.connected = False
        self.subscribed.clear()
        self._callbacks.clear()


def sample_values(bid="75", offer="76", timestamp_ms=None, market_state="TRADEABLE", delay="0"):
    if timestamp_ms is None:
        # Source timestamp must be in the past relative to real receipt time.
        timestamp_ms = str(int((datetime.now(timezone.utc) - timedelta(seconds=2)).timestamp() * 1000))
    return {
        "BIDPRICE1": bid,
        "ASKPRICE1": offer,
        "TIMESTAMP": timestamp_ms,
        "DLG_FLAG": market_state,
        "DELAY": delay,
    }


class IGStreamingWorkerTests(unittest.TestCase):
    def setUp(self):
        self._repos = []
        self._tmps = []
        self._env_patch = patch.dict(os.environ, {
            "IG_API_KEY": "TEST_KEY",
            "IG_USERNAME": "testuser",
            "IG_PASSWORD": "testpass",
            "IG_IDENTIFIER": "testuser",
        }, clear=False)
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        for repo in self._repos:
            try:
                repo.store.close()
            except Exception:
                pass
        for tmp in self._tmps:
            try:
                tmp.cleanup()
            except Exception:
                pass

    def repo(self):
        tmp = tempfile.TemporaryDirectory()
        self._tmps.append(tmp)
        repo = SQLiteRepository(Path(tmp.name) / "state.db")
        self._repos.append(repo)
        return repo

    def test_config_disabled_by_default(self):
        config = IGStreamIngestionConfig.from_env({})
        self.assertFalse(config.enabled)
        self.assertEqual(config.instruments, ())

    def test_config_parses_instruments(self):
        env = {"IG_STREAM_ENABLED": "1", "IG_STREAM_INSTRUMENTS": "BRENT:CC.D.LCO.BMU.IP,GOLD:CS.D.GOLD.CFD.IP"}
        config = IGStreamIngestionConfig.from_env(env)
        self.assertTrue(config.enabled)
        self.assertEqual(config.instruments, ("BRENT:CC.D.LCO.BMU.IP", "GOLD:CS.D.GOLD.CFD.IP"))

    def test_run_once_disabled_returns_disabled(self):
        repo = self.repo()
        config = IGStreamIngestionConfig.from_env({})
        ingestion = IGStreamIngestion(repo, config)
        self.assertEqual(ingestion.run_once()["status"], "DISABLED")

    def test_run_once_saves_observations_and_reports_health(self):
        repo = self.repo()
        env = {"IG_STREAM_ENABLED": "1", "IG_STREAM_INSTRUMENTS": "BRENT:CC.D.LCO.BMU.IP",
               "IG_STREAM_RUN_SECONDS": "1"}
        config = IGStreamIngestionConfig.from_env(env)
        base_ms = int((NOW - timedelta(seconds=2)).timestamp() * 1000)
        observations = [
            sample_values(timestamp_ms=str(base_ms)),
            sample_values(bid="76", offer="77", timestamp_ms=str(base_ms + 1)),
        ]
        stop_event = threading.Event()

        def transport_factory(on_observation):
            return FakeLightstreamerTransport(on_observation=on_observation, observations=observations, clock=lambda: NOW)

        ingestion = IGStreamIngestion(repo, config, clock=lambda: NOW,
                                      adapter_factory=FakeIGAdapter,
                                      transport_factory=transport_factory)
        health = ingestion.run_once(stop_event=stop_event)
        self.assertEqual(health["status"], "LIVE")
        self.assertEqual(health["observations"], 2)
        self.assertFalse(health["live_execution"])

        rows = repo.store._connection.execute("SELECT payload FROM observations ORDER BY observed_at").fetchall()
        self.assertEqual(len(rows), 2)
        import json
        data = json.loads(rows[-1]["payload"])
        self.assertEqual(data["instrument"], "BRENT")
        self.assertEqual(data["horizon"], "streaming")
        self.assertEqual(data["market_data"]["mid"], 76.5)
        self.assertEqual(data["research_context"]["broker"], "IG")

    def test_run_once_fail_closed_on_auth_error(self):
        repo = self.repo()
        env = {"IG_STREAM_ENABLED": "1", "IG_STREAM_INSTRUMENTS": "BRENT:CC.D.LCO.BMU.IP",
               "IG_STREAM_RUN_SECONDS": "1"}
        config = IGStreamIngestionConfig.from_env(env)

        class FailingAdapter(FakeIGAdapter):
            def authenticate(self):
                from domain.broker.ig import IGRequestError
                raise IGRequestError(401, "error.security.invalid-details", "AUTHENTICATION_FAILED",
                                     "bad credentials")

        ingestion = IGStreamIngestion(repo, config, clock=lambda: NOW,
                                      adapter_factory=FailingAdapter,
                                      transport_factory=lambda on_observation: FakeLightstreamerTransport())
        health = ingestion.run_once()
        self.assertEqual(health["status"], "AUTH_FAILED")
        self.assertIn("bad credentials", health["error"])

    def test_scheduler_enqueues_one_job_per_bucket(self):
        repo = self.repo()
        scheduler = IGStreamScheduler(repo)
        now = datetime(2026, 9, 20, 10, 0, 0, tzinfo=UTC).isoformat()
        job1 = scheduler.enqueue(now)
        job2 = scheduler.enqueue(now)
        self.assertEqual(job1.job_key, job2.job_key)
        self.assertEqual(job1.job_type, "ig-stream-ingestion")
        due = repo.due_jobs(datetime(2026, 9, 20, 10, 1, 0, tzinfo=UTC).isoformat())
        self.assertEqual(len(due), 1)

    def test_compose_ig_stream_worker_disabled_without_env(self):
        repo = self.repo()
        scheduler, handler = compose_ig_stream_worker(repo)
        self.assertIsNone(scheduler)
        self.assertIsNone(handler)

    def test_compose_ig_stream_worker_enabled(self):
        repo = self.repo()
        with patch.dict(os.environ, {"IG_STREAM_ENABLED": "1",
                                      "IG_STREAM_INSTRUMENTS": "BRENT:CC.D.LCO.BMU.IP",
                                      "IG_API_KEY": "KEY", "IG_USERNAME": "user", "IG_PASSWORD": "pass"}):
            scheduler, handler = compose_ig_stream_worker(repo)
        self.assertIsNotNone(scheduler)
        self.assertIsNotNone(handler)

    def test_no_order_submission_interface(self):
        repo = self.repo()
        env = {"IG_STREAM_ENABLED": "1", "IG_STREAM_INSTRUMENTS": "BRENT:CC.D.LCO.BMU.IP",
               "IG_API_KEY": "KEY", "IG_USERNAME": "user", "IG_PASSWORD": "pass"}
        config = IGStreamIngestionConfig.from_env(env)
        ingestion = IGStreamIngestion(repo, config)
        self.assertFalse(hasattr(ingestion, "place_order"))
        self.assertFalse(hasattr(ingestion, "submit_order"))


if __name__ == "__main__":
    unittest.main()
