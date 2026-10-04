import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import replace

from application.opportunities.alpha_vantage_data import AlphaVantageClient, repair_chart, ACCOUNT
from persistence.sqlite_repository import SQLiteRepository

T = datetime(2026, 10, 4, tzinfo=timezone.utc)


def search(symbol="SOL.JSE", region="South Africa", currency="ZAR"):
    return {"bestMatches": [{"1. symbol": symbol, "2. name": "Sasol", "3. type": "Equity",
                             "4. region": region, "8. currency": currency}]}


def history(symbol="SOL.JSE", close=101, timezone_name="Africa/Johannesburg"):
    return {"Meta Data": {"2. Symbol": symbol, "5. Time Zone": timezone_name},
            "Time Series (Daily)": {"2026-10-02": {"1. open": "100", "2. high": "105",
                "3. low": "99", "4. close": str(close), "5. volume": "250"}}}


def chart():
    return {"symbol": "SOL.JO", "currency": "ZAR", "interval": "1d", "bars": [
        {"timestamp": "2026-10-02T00:00:00+02:00", "open": 98, "high": 105,
         "low": 99, "close": 101, "volume": 250}]}


class AlphaDataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)/"cache.db"
        self.repo = SQLiteRepository(self.path)
        self.transport = Mock(side_effect=lambda p: search() if p["function"] == "SYMBOL_SEARCH" else history())
        self.client = AlphaVantageClient(self.repo, "PRIVATE-TEST-KEY", transport=self.transport)

    def tearDown(self):
        self.repo.close()
        self.directory.cleanup()

    def test_valid_yahoo_never_calls_fallback(self):
        data = chart()
        data["bars"][0]["open"] = 100
        result, report = repair_chart(self.client, data, T)
        self.assertEqual(result, data)
        self.assertEqual(report["state"], "YAHOO_VALID")
        self.transport.assert_not_called()

    def test_repair_is_same_session_traceable_and_does_not_modify_input(self):
        data = chart()
        original = copy.deepcopy(data)
        result, report = repair_chart(self.client, data, T)
        self.assertEqual(data, original)
        self.assertEqual(report["state"], "REPAIRED")
        row = result["bars"][0]
        self.assertEqual(row["open"], 100)
        self.assertEqual(row["timestamp"], data["bars"][0]["timestamp"])
        self.assertEqual(row["repair_source"]["symbol"], "SOL.JSE")
        self.assertEqual(row["repair_source"]["price_basis"], "RAW_AS_TRADED")
        self.assertEqual(self.transport.call_args.args[0]["outputsize"], "compact")
        self.assertEqual(self.transport.call_count, 2)
        self.assertNotIn("PRIVATE-TEST-KEY", json.dumps(self.repo.paper_account(ACCOUNT)))

    def test_quote_scale_or_close_mismatch_is_not_guessed(self):
        self.transport.side_effect = lambda p: search() if p["function"] == "SYMBOL_SEARCH" else history(close=10100)
        result, report = repair_chart(self.client, chart(), T)
        self.assertEqual(result, chart())
        self.assertEqual(report["state"], "NO_MATCHING_VALID_BARS")

    def test_foreign_listing_is_not_jse(self):
        self.transport.side_effect = lambda p: search("SOL", "United States", "USD")
        result, report = repair_chart(self.client, chart(), T)
        self.assertEqual(report["state"], "JSE_SYMBOL_UNVERIFIED")
        self.assertEqual(result, chart())
        self.assertEqual(self.transport.call_count, 1)

    def test_ambiguous_search_does_not_select_first(self):
        payload = search()
        payload["bestMatches"] *= 2
        self.transport.return_value, self.transport.side_effect = payload, None
        self.assertEqual(self.client.discover("SOL.JO", T)["state"], "JSE_SYMBOL_UNVERIFIED")

    def test_provider_metadata_symbol_and_timezone_gate(self):
        for data in (history(symbol="SSL"), history(timezone_name="US/Eastern")):
            with self.subTest(data=data):
                self.transport.side_effect = None
                self.transport.return_value = data
                r = self.client.request({"function": "TIME_SERIES_DAILY", "symbol": "SOL.JSE",
                    "outputsize": "compact"}, T+timedelta(days=35 if data["Meta Data"]["2. Symbol"] == "SOL.JSE" else 0))
                self.assertEqual(r["state"], "IDENTITY_OR_SESSION_UNVERIFIED")

    def test_compact_cache_survives_repository_restart(self):
        repair_chart(self.client, chart(), T)
        self.repo.close()
        self.repo = SQLiteRepository(self.path)
        second = AlphaVantageClient(self.repo, "PRIVATE-TEST-KEY", transport=Mock(side_effect=AssertionError("refetch")))
        self.assertEqual(repair_chart(second, chart(), T+timedelta(hours=1))[1]["state"], "REPAIRED")

    def test_cached_data_cannot_be_used_before_its_retrieval(self):
        self.client.discover("SOL.JO", T)
        self.assertEqual(self.client.discover("SOL.JO", T-timedelta(minutes=1))["state"], "FUTURE_CACHE_UNAVAILABLE")
        self.assertEqual(self.transport.call_count, 1)

    def test_unsupported_search_is_negative_cached(self):
        self.transport.side_effect = None
        self.transport.return_value = {"Error Message": "PRIVATE-TEST-KEY raw secret"}
        self.assertEqual(self.client.discover("SOL.JO", T)["state"], "SYMBOL_OR_REQUEST_UNSUPPORTED")
        self.client.discover("SOL.JO", T+timedelta(days=1))
        self.assertEqual(self.transport.call_count, 1)
        self.assertNotIn("PRIVATE-TEST-KEY", json.dumps(self.repo.paper_account(ACCOUNT)))

    def test_provider_note_cools_down_other_symbols(self):
        self.transport.side_effect = None
        self.transport.return_value = {"Information": "Premium endpoint PRIVATE-TEST-KEY"}
        self.assertEqual(self.client.discover("SOL.JO", T)["state"], "PROVIDER_LIMITED_OR_PREMIUM_REQUIRED")
        self.assertEqual(self.client.discover("NPN.JO", T)["state"], "PROVIDER_LIMITED")
        self.assertEqual(self.transport.call_count, 1)

    def test_network_error_does_not_leak_key_and_is_counted(self):
        self.transport.side_effect = RuntimeError("url?apikey=PRIVATE-TEST-KEY")
        self.assertEqual(self.client.discover("SOL.JO", T)["state"], "PROVIDER_UNAVAILABLE")
        state = self.repo.paper_account(ACCOUNT)
        self.assertEqual(len(state["requests"]), 1)
        self.assertNotIn("PRIVATE-TEST-KEY", json.dumps(state))

    def test_five_per_minute_budget_defers_without_sleep(self):
        self.transport.side_effect = None
        self.transport.return_value = {"bestMatches": []}
        for i in range(5):
            self.client.discover(f"X{i}.JO", T)
        self.assertEqual(self.client.discover("NEXT.JO", T)["state"], "MINUTE_BUDGET_EXHAUSTED")
        self.client.discover("NEXT.JO", T+timedelta(seconds=61))
        self.assertEqual(self.transport.call_count, 6)

    def test_rolling_daily_budget_does_not_reset_at_midnight(self):
        self.transport.side_effect = None
        self.transport.return_value = {"bestMatches": []}
        for i in range(20):
            self.client.discover(f"X{i}.JO", T+timedelta(minutes=i))
        self.assertEqual(self.client.discover("NEXT.JO", T+timedelta(hours=23))["state"], "DAILY_BUDGET_EXHAUSTED")
        self.client.discover("NEXT.JO", T+timedelta(hours=24, minutes=21))
        self.assertEqual(self.transport.call_count, 21)

    def test_same_request_in_flight_does_not_duplicate_network(self):
        observed = []
        def transport(params):
            second = SQLiteRepository(self.path)
            try:
                client = AlphaVantageClient(second, "PRIVATE-TEST-KEY", transport=Mock(side_effect=AssertionError()))
                observed.append(client.discover("SOL.JO", T)["state"])
            finally:
                second.close()
            return search()
        self.client.transport = transport
        self.client.discover("SOL.JO", T)
        self.assertEqual(observed, ["REQUEST_IN_PROGRESS"])

    def test_old_invalid_bars_do_not_spend_free_calls(self):
        data = chart()
        data["bars"][0]["timestamp"] = "2025-01-01T00:00:00+00:00"
        for i in range(100):
            date = (T-timedelta(days=101-i)).isoformat()
            data["bars"].append({"timestamp": date, "open": 100, "high": 105,
                                "low": 99, "close": 101, "volume": 250})
        self.assertEqual(repair_chart(self.client, data, T)[1]["state"], "OUTSIDE_FREE_COMPACT_WINDOW")
        self.transport.assert_not_called()

    def test_missing_volume_requires_actual_provider_volume(self):
        data = chart()
        data["bars"][0]["open"] = 100
        data["bars"][0]["volume"] = None
        result, report = repair_chart(self.client, data, T)
        self.assertEqual(report["state"], "REPAIRED")
        self.assertEqual(result["bars"][0]["volume"], 250)

    def test_future_bar_and_invalid_provider_ohlc_not_admitted(self):
        payload = history()
        payload["Time Series (Daily)"]["2026-10-02"]["1. open"] = "98"
        payload["Time Series (Daily)"]["2026-10-04"] = history()["Time Series (Daily)"]["2026-10-02"]
        self.transport.side_effect = lambda p: search() if p["function"] == "SYMBOL_SEARCH" else payload
        result, report = repair_chart(self.client, chart(), T)
        self.assertEqual(result, chart())
        self.assertEqual(report["state"], "NO_MATCHING_VALID_BARS")

    def test_full_premium_history_cannot_be_requested(self):
        with self.assertRaises(ValueError):
            self.client.request({"function": "TIME_SERIES_DAILY", "symbol": "SOL.JSE", "outputsize": "full"}, T)
        self.transport.assert_not_called()

    def test_daily_scan_rotates_across_restart_without_provider_calls(self):
        keys = {str(i): {} for i in range(12)}
        self.assertEqual(self.client.ordered_keys(keys)[0], "0")
        other = AlphaVantageClient(self.repo, "PRIVATE-TEST-KEY", transport=self.transport)
        self.assertEqual(other.ordered_keys(keys)[0], "5")
        self.transport.assert_not_called()

    def test_empty_demo_keys_are_not_accepted(self):
        for value in ("", "demo", " "):
            with self.assertRaises(ValueError):
                AlphaVantageClient(self.repo, value, transport=self.transport)

    def test_worker_repair_is_frozen_separate_from_paper_prices(self):
        from application.opportunities.paper_host import compose_paper_worker, paper_status
        from application.opportunities.paper_config import PaperLoopConfig
        from test_paper_closed_loop import T as decision_time, charts
        data = charts(decision_time)["TFMJ"]
        data["bars"][-1].update(open=1, high=5, low=2)
        fixed = copy.deepcopy(data)
        fixed["bars"][-1].update(open=fixed["bars"][-1]["close"], high=fixed["bars"][-1]["close"]+2, low=2,
                                 repair_source={"provider": "ALPHA_VANTAGE", "source_sha256": "a"*64})
        fetcher = Mock()
        fetcher.get_chart.return_value = data
        config = replace(PaperLoopConfig.load("config/paper.example.json"), universe=("TFMJ",))
        client = Mock()
        client.ordered_keys.side_effect = lambda charts: list(charts)
        with patch("application.opportunities.alpha_vantage_data.configured_client", return_value=client), \
                patch("application.opportunities.alpha_vantage_data.repair_chart", return_value=(fixed,
                    {"state": "REPAIRED", "repaired_sessions": [fixed["bars"][-1]["timestamp"][:10]]})) as repair:
            scheduler, handler = compose_paper_worker(self.repo, config, fetcher=fetcher,
                clock=lambda: decision_time.isoformat())
            job = scheduler.enqueue(decision_time.isoformat())
            result = handler(job)
            self.assertEqual(handler(job), result)
            self.assertEqual(repair.call_count, 1)
        frozen = self.repo.paper_records(config.account_id, "input", as_of=decision_time.isoformat())[0]["input"]
        self.assertEqual(frozen["charts"]["TFMJ"]["bars"][-1]["open"], 1)
        self.assertIn("repair_source", frozen["swing_charts"]["TFMJ"]["bars"][-1])
        self.assertEqual(paper_status(self.repo, config)["alpha_vantage_data"]["instruments"]["TFMJ"]["state"], "REPAIRED")


if __name__ == "__main__":
    unittest.main()
