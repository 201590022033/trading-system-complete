import unittest
from datetime import date, datetime, timedelta, timezone
from threading import Event
from time import sleep

from flask import Flask
from application.opportunities.api import create_blueprint
from application.opportunities.public_research import (
    candidate_from_chart, public_instrument_classes, public_share_catalog, public_share_list,
    refresh_public_research,
)
from application.opportunities.refresh import OpportunityRefresh
from application.opportunities.service import OpportunityService
from domain.evaluation.opportunity import rank_opportunities
from app import app


NOW = datetime(2026, 9, 18, 12, tzinfo=timezone.utc)


def chart(symbol, count=185, *, stale=False):
    dates = []
    day = date(2026, 1, 1)
    while len(dates) < count:
        if day.weekday() < 5:
            dates.append(day)
        day += timedelta(days=1)
    if stale:
        dates = dates[:-25]
    bars = [{"timestamp": d.isoformat(), "close": 100 + i * .4 + (i % 7) * .1}
            for i, d in enumerate(dates)]
    return {"symbol": symbol, "interval": "1d", "currency": "ZAR", "bars": bars}


class FakeFetcher:
    def get_chart(self, symbol, period):
        assert period == "1y"
        return chart(symbol)


class PublicResearchRefreshTests(unittest.TestCase):
    def test_broad_catalog_preserves_legacy_but_does_not_stop_at_six(self):
        self.assertGreaterEqual(len(public_share_catalog()), 18)
        shares = {item["instrument_id"]: item for item in public_share_list()}
        self.assertNotIn("JDIJ", shares)
        self.assertEqual(shares["CLS"]["yahoo_symbol"], "CLS.JO")
        self.assertEqual(shares["CLS"]["name"], "Clicks Group")
        self.assertIn("TFMJ", shares)
        self.assertEqual(shares["TFMJ"]["display_symbol"], "TFG")
        self.assertFalse(shares["TFMJ"]["capabilities"]["operational_analysis"])
        self.assertTrue(shares["TFMJ"]["capabilities"]["automatic_technical_screen"])
        self.assertEqual(shares["TFMJ"]["instrument_type"], "cash_equity")
        self.assertTrue(shares["SASOL"]["capabilities"]["operational_analysis"])
        response = app.test_client().get("/api/public-shares")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertFalse(body["live_execution"])
        classes = {item["class_id"]: item for item in body["classes"]}
        self.assertEqual(classes["cash_equity"]["state"], "AVAILABLE")
        self.assertEqual(classes["cash_equity"]["instrument_count"], len(shares))
        self.assertEqual(classes["index_etf"]["state"], "CHART_ONLY_NOT_RANKED")
        self.assertEqual(classes["index_etf"]["instrument_count"], 4)
        self.assertEqual(classes["cfd"]["state"], "BLOCKED_CONTRACT_EVIDENCE")
        self.assertEqual(classes["ssf"]["state"], "BLOCKED_CONTRACT_EVIDENCE")

    def test_unavailable_instrument_classes_explain_their_evidence_gates(self):
        classes = {item["class_id"]: item for item in public_instrument_classes()}
        self.assertIn("liquidity", classes["index_etf"]["reason"])
        self.assertIn("financing", classes["cfd"]["reason"])
        self.assertIn("expiry", classes["ssf"]["reason"])

    def test_new_share_can_rank_with_matured_evidence_and_source_lineage(self):
        result = refresh_public_research(fetcher=FakeFetcher(), evaluated_at=NOW,
                                         universe=("TFMJ", "NPN"), max_workers=2)
        self.assertEqual(result.scanned, 2)
        self.assertFalse(result.unavailable)
        ranked = [item for item in result.opportunities if item.rank is not None]
        self.assertEqual(len(ranked), 2)
        self.assertIn("EQ_ZAR_TFMJ", {item.instrument_id for item in ranked})
        self.assertTrue(all(item.execution_suitability == "RESEARCH-ONLY" for item in ranked))
        self.assertTrue(all(item.provenance["cost_assumption_bps"] == 10 for item in ranked))
        self.assertTrue(all(item.provenance["data_symbol"].endswith(".JO") for item in ranked))
        self.assertTrue(all(item.sample_count >= 30 for item in ranked))
        self.assertTrue(all(item.input_evidence["regime"]["availability"] == "AVAILABLE"
                            for item in ranked))
        self.assertTrue(all(item.input_evidence["news_macro"]["state"] == "UNAVAILABLE"
                            for item in ranked))

    def test_canonical_record_carries_only_causal_learned_input(self):
        instrument_id = "EQ_ZAR_TFMJ"
        past = {"state": "OBSERVED", "evaluated_at": "2026-09-17T12:00:00+00:00",
                "sample_count": 4}
        future = {"state": "OBSERVED", "evaluated_at": "2026-09-19T12:00:00+00:00",
                  "sample_count": 999}
        result = refresh_public_research(
            fetcher=FakeFetcher(), evaluated_at=NOW, universe=("TFMJ",),
            learned_evidence={instrument_id: past})
        record = result.opportunities[0]
        self.assertEqual(record.input_evidence["learned_effectiveness"]["sample_count"], 4)
        result = refresh_public_research(
            fetcher=FakeFetcher(), evaluated_at=NOW, universe=("TFMJ",),
            learned_evidence={instrument_id: future})
        record = result.opportunities[0]
        self.assertNotIn("learned_effectiveness", record.input_evidence)

    def test_stale_identity_mismatch_and_short_history_cannot_rank(self):
        symbol = public_share_catalog()["TFMJ"]["yahoo_symbol"]
        for bad in (chart(symbol, stale=True), chart("WRONG.JO"), chart(symbol, count=20)):
            result = refresh_public_research(
                fetcher=type("Fetcher", (), {"get_chart": lambda self, s, p: bad})(),
                evaluated_at=NOW, universe=("TFMJ",))
            self.assertFalse([item for item in result.opportunities if item.rank is not None])
            self.assertTrue(result.unavailable or result.opportunities)

    def test_current_bar_is_not_used_as_matured_outcome(self):
        symbol = public_share_catalog()["TFMJ"]["yahoo_symbol"]
        base = chart(symbol)
        first = candidate_from_chart("TFMJ", base, evaluated_at=NOW)
        future = {**base, "bars": base["bars"] + [{"timestamp": "2026-09-18", "close": 1.0}]}
        second = candidate_from_chart("TFMJ", future, evaluated_at=NOW)
        self.assertEqual(first, second)

    def test_background_refresh_is_single_flight_and_serves_ranked_records(self):
        started, release = Event(), Event()
        calls = []

        def run():
            calls.append(1)
            started.set()
            self.assertTrue(release.wait(5))
            return refresh_public_research(fetcher=FakeFetcher(), evaluated_at=NOW,
                                           universe=("TFMJ", "NPN"), max_workers=2)

        service = OpportunityService()
        refresh = OpportunityRefresh(service, runner=run)
        local = Flask(__name__)
        local.register_blueprint(create_blueprint(service, refresh))
        try:
            with local.test_client() as client:
                first = client.post("/api/v1/opportunities/refresh")
                self.assertEqual(first.status_code, 202)
                self.assertTrue(first.get_json()["running"])
                self.assertTrue(started.wait(5))
                client.post("/api/v1/opportunities/refresh")
                self.assertEqual(len(calls), 1)
                release.set()
                for _ in range(100):
                    if refresh.status()["state"] == "AVAILABLE" and not refresh.status()["running"]:
                        break
                    sleep(.01)
                listing = client.get("/api/v1/opportunities?limit=5").get_json()
                self.assertEqual(listing["count"], 2)
                self.assertEqual(listing["refresh"]["scanned"], 2)
                self.assertFalse(listing["live_execution"])
                client.post("/api/v1/opportunities/refresh")
                self.assertEqual(len(calls), 1)
        finally:
            release.set()
            refresh._pool.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()
