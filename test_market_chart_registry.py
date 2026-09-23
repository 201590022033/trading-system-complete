import unittest
from time import sleep

from app import app
from dashboard_feeds import DashboardFeeds
from market_chart_registry import market_chart_list, resolve_market_chart


class FakeFetcher:
    def get_chart(self, symbol, period):
        return {"symbol": symbol, "period": period, "interval": "1d", "currency": "ZAR",
                "bars": [{"timestamp": "2026-09-22T00:00:00+02:00", "close": 100.0}],
                "source_timestamp": "2026-09-22T00:00:00+02:00"}


class MarketChartRegistryTests(unittest.TestCase):
    def test_catalog_separates_listed_etfs_from_cfd_references(self):
        rows = {item["instrument_id"]: item for item in market_chart_list()}
        self.assertEqual(rows["ETF_STX40"]["data_symbol"], "STX40.JO")
        self.assertEqual(rows["ETF_STX40"]["chart_basis"], "LISTED_SECURITY")
        self.assertEqual(rows["CFD_REF_BRENT"]["data_symbol"], "BZ=F")
        self.assertEqual(rows["CFD_REF_BRENT"]["instrument_type"], "proxy")
        self.assertFalse(rows["CFD_REF_BRENT"]["capabilities"]["broker_execution"])
        self.assertFalse(rows["ETF_STX40"]["capabilities"]["canonical_ranking"])

    def test_api_exposes_chart_only_catalog_without_execution(self):
        response = app.test_client().get("/api/market-chart-instruments")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(len(body["instruments"]), 8)
        self.assertFalse(body["canonical_ranking"])
        self.assertFalse(body["live_execution"])

    def test_reference_feed_preserves_proxy_boundary(self):
        feeds = DashboardFeeds(chart_fetcher=FakeFetcher())
        try:
            result = feeds.reference_chart("CFD_REF_BRENT", "3mo")
            for _ in range(100):
                if not result["refreshing"]:
                    break
                sleep(.005)
                result = feeds.reference_chart("CFD_REF_BRENT", "3mo")
            self.assertEqual(result["state"], "AVAILABLE")
            self.assertEqual(result["provider_symbol"], "BZ=F")
            self.assertEqual(result["chart_basis"], "UNDERLYING_FUTURES_PROXY")
            self.assertIn("not an IG CFD quote", result["note"])
        finally:
            feeds._pool.shutdown(wait=True)

    def test_unknown_chart_identity_fails_closed(self):
        with self.assertRaises(KeyError):
            resolve_market_chart("UNKNOWN")


if __name__ == "__main__":
    unittest.main()

