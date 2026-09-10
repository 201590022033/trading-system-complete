import io
import json
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from domain.broker.ig import IGConfig, IGReadOnlyAdapter, IGRequestError
from domain.broker.ig_history import HISTORY_API_VERSION, PRICE_BASIS_VERSION, RESOLUTIONS
from domain.contracts.market import CanonicalBar
from intraday_instruments import DataGrade


def price(timestamp, base=100, *, local="2026/01/01 00:00:00"):
    def component(offset):
        return {"bid": base + offset, "ask": base + offset + 2, "lastTraded": base + offset + 1}
    return {"snapshotTimeUTC": timestamp, "snapshotTime": local,
            "openPrice": component(0), "highPrice": component(4),
            "lowPrice": component(-2), "closePrice": component(2), "lastTradedVolume": 7}


def response(prices, page=1, total=1):
    return {"prices": prices, "metadata": {"pageData": {"pageNumber": page, "pageSize": 500,
                                                           "totalPages": total},
                                            "allowance": {"remainingAllowance": 999}}}


class IGHistoryTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.payloads = {1: response([price("2026-01-01T00:00:00")])}

        def transport(method, url, headers, body, timeout):
            self.calls.append((method, url, headers, body))
            if url.endswith("/session"):
                return 200, {"CST": "CST-SECRET", "X-SECURITY-TOKEN": "TOKEN-SECRET"}, b"{}"
            page = int(parse_qs(urlparse(url).query)["pageNumber"][0])
            return 200, {}, json.dumps(self.payloads[page]).encode()

        self.adapter = IGReadOnlyAdapter(IGConfig("API-SECRET", "user", "password"), transport)
        self.adapter.authenticate()
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.end = datetime(2026, 1, 2, tzinfo=timezone.utc)
        self.retrieved = datetime(2026, 1, 3, tzinfo=timezone.utc)

    def fetch(self, **kwargs):
        return self.adapter.get_historical_prices("CC.D.LCO.BMU.IP", "MINUTE_5", self.start, self.end,
                                                  retrieved_at=self.retrieved, **kwargs)

    def test_success_uses_v3_range_and_canonical_normalization(self):
        series = self.fetch()
        self.assertEqual(len(series.bars), 1)
        bar = series.bars[0]
        self.assertIsInstance(bar.canonical, CanonicalBar)
        self.assertEqual((bar.canonical.open, bar.canonical.high, bar.canonical.low, bar.canonical.close),
                         (101, 105, 99, 103))
        self.assertEqual(bar.canonical.timeframe, "5m")
        self.assertEqual(self.calls[-1][2]["Accept-Version"], str(HISTORY_API_VERSION))
        query = parse_qs(urlparse(self.calls[-1][1]).query)
        self.assertEqual(query["resolution"], ["MINUTE_5"])
        self.assertIn("from", query)
        self.assertIn("to", query)

    def test_all_and_only_documented_resolution_mappings_are_explicit(self):
        self.assertEqual(RESOLUTIONS["MINUTE_30"], ("30m", 1800))
        self.assertEqual(RESOLUTIONS["DAY"], ("1d", 86400))
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.adapter.get_historical_prices("EPIC", "30_MINUTES", self.start, self.end)

    def test_bid_ask_last_and_versioned_mid_are_preserved(self):
        bar = self.fetch().bars[0]
        self.assertEqual(bar.bid.close, 102)
        self.assertEqual(bar.ask.close, 104)
        self.assertEqual(bar.last_traded.close, 103)
        self.assertEqual(bar.canonical.bid, 102)
        self.assertEqual(bar.canonical.ask, 104)
        self.assertEqual(bar.price_basis, "DERIVED_MID")
        self.assertEqual(bar.price_basis_version, PRICE_BASIS_VERSION)

    def test_utc_source_timestamp_and_dst_offset_range(self):
        from zoneinfo import ZoneInfo
        start = datetime(2026, 3, 29, 2, tzinfo=ZoneInfo("Europe/London"))
        end = datetime(2026, 3, 30, tzinfo=timezone.utc)
        self.payloads[1] = response([price("2026-03-29T01:00:00")])
        series = self.adapter.get_historical_prices(
            "EPIC", "MINUTE_5", start, end, retrieved_at=datetime(2026, 4, 1, tzinfo=timezone.utc))
        self.assertEqual(series.bars[0].canonical.interval_start.tzinfo, timezone.utc)
        self.assertEqual(parse_qs(urlparse(self.calls[-1][1]).query)["from"], ["2026-03-29T01:00:00"])

    def test_naive_ranges_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.adapter.get_historical_prices("EPIC", "DAY", datetime(2026, 1, 1), self.end)

    def test_incomplete_current_bar_is_excluded(self):
        self.payloads[1] = response([price("2026-01-01T23:58:00")])
        series = self.adapter.get_historical_prices(
            "CC.D.LCO.BMU.IP", "MINUTE_5", self.start, self.end,
            retrieved_at=datetime(2026, 1, 1, 23, 59, tzinfo=timezone.utc))
        self.assertEqual(len(series.bars), 0)
        self.assertEqual(series.excluded_incomplete, 1)

    def test_pagination_order_overlap_duplicates_gaps_and_allowance(self):
        self.payloads = {
            1: response([price("2026-01-01T00:10:00", 110), price("2026-01-01T00:00:00")], 1, 2),
            2: response([price("2026-01-01T00:10:00", 110), price("2026-01-01T00:15:00", 115)], 2, 2),
        }
        series = self.fetch()
        self.assertEqual(series.pages_received, 2)
        self.assertEqual(series.duplicates, 1)
        self.assertEqual(series.gaps, 1)
        self.assertEqual([b.canonical.interval_start.minute for b in series.bars], [0, 10, 15])
        self.assertEqual(series.remaining_allowance, 999)

    def test_max_points_and_max_pages_mark_truncation(self):
        self.payloads = {1: response([price("2026-01-01T00:00:00")], 1, 2)}
        series = self.fetch(max_points=1)
        self.assertTrue(series.truncated)
        self.assertEqual(series.completeness, "PARTIAL_TRUNCATED")

    def test_empty_history_is_explicit(self):
        self.payloads[1] = response([])
        series = self.fetch()
        self.assertEqual(series.completeness, "EMPTY")
        self.assertEqual(series.summary()["bars_received"], 0)

    def test_malformed_envelope_and_page_metadata_fail_safely(self):
        for payload in ({}, {"prices": [], "metadata": {}},
                        {"prices": [], "metadata": {"pageData": {"pageNumber": "x"}}}):
            with self.subTest(payload=payload):
                self.payloads[1] = payload
                with self.assertRaises(IGRequestError) as raised:
                    self.fetch()
                self.assertEqual(raised.exception.error_category, "MALFORMED_RESPONSE")

    def test_malformed_rows_are_excluded_not_fabricated(self):
        broken = price("2026-01-01T00:00:00")
        broken["openPrice"].pop("ask")
        self.payloads[1] = response([broken])
        series = self.fetch()
        self.assertEqual(series.excluded_malformed, 1)
        self.assertFalse(series.bars)
        self.assertEqual(series.completeness, "PARTIAL_MALFORMED")

    def test_historical_rate_limit_is_explicit(self):
        def transport(*args):
            return 403, {}, json.dumps({"errorCode":
                "error.public-api.exceeded-account-historical-data-allowance"}).encode()
        adapter = IGReadOnlyAdapter(self.adapter.config, transport)
        adapter._session = self.adapter._session
        with self.assertRaises(IGRequestError) as raised:
            adapter.get_historical_prices("EPIC", "DAY", self.start, self.end)
        self.assertEqual(raised.exception.error_category, "RATE_LIMITED")

    def test_summary_and_errors_do_not_expose_secrets(self):
        rendered = json.dumps(self.fetch().summary())
        for secret in ("API-SECRET", "password", "CST-SECRET", "TOKEN-SECRET"):
            self.assertNotIn(secret, rendered)

    def test_cli_history_prints_safe_summary_only(self):
        from scripts import ig_discovery
        class FakeAdapter:
            def __init__(self, config): pass
            def authenticate(self): return {"authenticated": True}
            def get_historical_prices(self, *args, **kwargs): return self
            def summary(self): return {"epic": "EPIC", "bars_received": 1}
        argv = ["ig_discovery", "history", "EPIC", "MINUTE_5",
                "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"]
        output = io.StringIO()
        with patch.object(sys, "argv", argv), \
             patch.object(ig_discovery.IGConfig, "from_env", return_value=object()), \
             patch.object(ig_discovery, "IGReadOnlyAdapter", FakeAdapter), patch("sys.stdout", output):
            ig_discovery.main()
        self.assertEqual(json.loads(output.getvalue()), {"bars_received": 1, "epic": "EPIC"})

    def test_m8_causal_semantics_and_lineage(self):
        bar = self.fetch().bars[0].canonical
        self.assertLess(bar.interval_start, bar.event_time)
        self.assertEqual(bar.event_time, bar.available_time)
        self.assertTrue(bar.input_record_ids[0].startswith("ig:DEMO:CC.D.LCO.BMU.IP:"))
        self.assertEqual(bar.source_policy.data_grade.value, "RESEARCH_DATA")

    def test_suitability_receives_factual_metadata_only(self):
        series = self.fetch()
        evidence = series.suitability_evidence()
        self.assertEqual(evidence.data_grade, DataGrade.RESEARCH)
        self.assertEqual(evidence.history_depth, 1)
        self.assertEqual(evidence.resolution, "5m")
        self.assertIsNone(evidence.missingness)
        self.assertFalse(hasattr(evidence, "attractiveness_score"))

    def test_execution_remains_disabled(self):
        self.assertTrue(self.adapter.capabilities()["historical_prices"])
        self.assertFalse(self.adapter.capabilities()["order_submission"])
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            self.adapter.place_order({})


if __name__ == "__main__":
    unittest.main()
