import os
import unittest
import tempfile
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from application.opportunities.ig_swing_data import investigate, configured_investigation, CANDIDATES
from domain.broker.ig import IGRequestError
import test_ig_history as history_fixture

T = datetime(2026, 10, 4, tzinfo=timezone.utc)


class VolumeTests(unittest.TestCase):
    def series(self, volumes):
        # Reuse authenticated mocked normalization; these tests never open a socket.
        fixture = history_fixture.IGHistoryTests()
        fixture.setUp()
        fixture.payloads[1] = history_fixture.response([
            {**history_fixture.price(f"2026-01-{i+1:02d}T00:00:00"), "lastTradedVolume": value}
            for i, value in enumerate(volumes)])
        return fixture.adapter.get_historical_prices("EPIC", "DAY", fixture.start,
            datetime(2026, 2, 1, tzinfo=timezone.utc),
            retrieved_at=datetime(2026, 2, 2, tzinfo=timezone.utc))

    def test_null_volume_is_missing_not_zero(self):
        q = self.series([None]*21).summary()["volume_quality"]
        self.assertEqual((q["state"], q["missing"], q["zero"]), ("MISSING", 21, 0))
        self.assertIsNone(q["relative_volume20"])

    def test_zero_volume_cannot_supply_relative_volume_denominator(self):
        q = self.series([0]*21).volume_quality()
        self.assertEqual(q["state"], "ALL_ZERO")
        self.assertFalse(q["relative_volume20_numerically_available"])

    def test_positive_field_coverage_does_not_admit_cash_strategy(self):
        q = self.series([10]*20+[20]).volume_quality()
        self.assertEqual(q["relative_volume20"], 2)
        self.assertEqual(q["positive"], 21)
        self.assertFalse(q["cash_swing_admitted"])

    def test_partial_and_short_volume_stay_unavailable(self):
        for values in ([10]*20+[None], [10]*20):
            self.assertIsNone(self.series(values).volume_quality()["relative_volume20"])

    def test_latest_zero_is_observed_zero_when_prior_volume_exists(self):
        self.assertEqual(self.series([10]*20+[0]).volume_quality()["relative_volume20"], 0)

    def test_empty_series_is_explicit(self):
        self.assertEqual(self.series([]).volume_quality()["state"], "EMPTY")


class ReadinessTests(unittest.TestCase):
    def adapter(self):
        a = Mock()
        a.config = SimpleNamespace(environment="DEMO")
        return a

    def test_permission_denial_is_retained_without_fake_volume(self):
        a = self.adapter()
        a.get_historical_prices.side_effect = IGRequestError(403,
            "unauthorised.access.to.equity.exception", "PERMISSION_DENIED", "IG denied equity access")
        r = investigate(a, ("NPN", "SASOL", "SHPJ", "TFMJ"), T)
        self.assertEqual(a.get_historical_prices.call_count, 3)
        self.assertEqual(r["unmapped"], ["TFMJ"])
        self.assertEqual(r["instruments"]["NPN"]["error"]["http_status"], 403)
        self.assertNotIn("history", r["instruments"]["NPN"])
        self.assertFalse(r["cash_swing_admitted"])

    def test_quota_failure_stops_other_history_requests(self):
        a = self.adapter()
        a.get_historical_prices.side_effect = IGRequestError(429, None, "RATE_LIMITED", "Quota")
        investigate(a, tuple(CANDIDATES), T)
        self.assertEqual(a.get_historical_prices.call_count, 1)

    def test_success_is_bounded_diagnostic_not_feed_substitution(self):
        a = self.adapter()
        a.get_historical_prices.return_value.summary.return_value = {"volume_quality": {"state": "PRESENT"}}
        r = investigate(a, ("NPN",), T)
        args, kwargs = a.get_historical_prices.call_args
        self.assertEqual(args[1], "DAY")
        self.assertEqual(kwargs["max_points"], 70)
        self.assertEqual(kwargs["max_pages"], 1)
        self.assertEqual(r["instruments"]["NPN"]["state"], "SEMANTICS_VALIDATION_REQUIRED")
        self.assertNotIn("charts", r)

    def test_disabled_diagnostics_never_construct_broker(self):
        with patch.dict(os.environ, {}, clear=True), patch(
                "application.opportunities.ig_swing_data.IGReadOnlyAdapter") as factory:
            self.assertEqual(configured_investigation(("NPN",), T)["state"], "NOT_ENABLED")
            factory.assert_not_called()

    def test_unmapped_universe_makes_no_requests(self):
        a = self.adapter()
        self.assertEqual(investigate(a, ("TFMJ",), T)["state"], "NO_VERIFIED_CANDIDATE")
        a.authenticate.assert_not_called()

    def test_authentication_failure_is_safe_and_stops(self):
        a = self.adapter()
        a.authenticate.side_effect = IGRequestError(401, None, "AUTHENTICATION_FAILED", "Denied")
        self.assertEqual(investigate(a, ("NPN",), T)["error"]["http_status"], 401)
        a.get_historical_prices.assert_not_called()

    def test_worker_freezes_report_retry_and_status_without_changing_cash_feed(self):
        from application.opportunities.paper_host import compose_paper_worker, paper_status
        from application.opportunities.paper_config import PaperLoopConfig
        from persistence.sqlite_repository import SQLiteRepository
        from test_paper_closed_loop import T as decision_time, charts
        data = charts(decision_time)["TFMJ"]
        fetcher = Mock()
        fetcher.get_chart.return_value = data
        report = {"state": "BLOCKED", "cash_swing_admitted": False, "live_execution": False}
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory)/"data.db")
            try:
                config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))
                scheduler, handler = compose_paper_worker(repo, config, fetcher=fetcher,
                    clock=lambda: decision_time.isoformat())
                with patch("application.opportunities.ig_swing_data.configured_investigation", return_value=report) as probe:
                    job = scheduler.enqueue(decision_time.isoformat())
                    result = handler(job)
                    self.assertEqual(handler(job), result)
                    probe.assert_called_once()
                frozen = repo.paper_records(config.account_id, "input", as_of=decision_time.isoformat())[0]
                self.assertEqual(frozen["input"]["charts"]["TFMJ"]["bars"], data["bars"][-60:])
                self.assertEqual(paper_status(repo, config)["ig_swing_data"], report)
            finally:
                repo.close()
