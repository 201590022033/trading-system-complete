import json
import os
import unittest
from unittest.mock import patch

from domain.broker.ig import IGConfig, IGReadOnlyAdapter


class IGDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def transport(method, url, headers, body, timeout):
            self.calls.append((method, url, headers, body))
            if url.endswith("/session"):
                return 200, {}, json.dumps({"cst": "CST-SECRET", "x-security-token": "SEC-SECRET"}).encode()
            if url.endswith("/accounts"):
                return 200, {}, json.dumps({"accounts": [{"accountId": "ACC", "accountName": "Demo", "currency": {"code": "ZAR"}, "preferred": True}]}).encode()
            if "/markets?" in url:
                return 200, {}, json.dumps({"markets": [{"epic": "CS.D.BRENT.CFD.IP", "instrumentName": "Brent", "instrument": {"type": "COMMODITIES", "currency": "USD"}}]}).encode()
            return 200, {}, json.dumps({"epic": "CS.D.BRENT.CFD.IP", "instrumentName": "Brent", "instrument": {"type": "COMMODITIES", "currency": "USD"}, "snapshot": {"marketStatus": "TRADEABLE"}}).encode()
        self.adapter = IGReadOnlyAdapter(IGConfig("API-SECRET", "user", "password", environment="DEMO"), transport)

    def test_demo_live_separation_and_missing_configuration(self):
        self.assertIn("demo-api", self.adapter.config.base_url)
        self.assertIn("api.ig.com", IGConfig("a", "u", "p", environment="LIVE").base_url)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): IGConfig.from_env()

    def test_authentication_is_normalized_and_secrets_not_logged(self):
        result = self.adapter.authenticate()
        self.assertEqual(result["environment"], "DEMO")
        self.assertNotIn("CST-SECRET", str(result))
        self.assertNotIn("SEC-SECRET", str(result))

    def test_accounts_search_and_market_detail(self):
        self.adapter.authenticate()
        self.assertEqual(self.adapter.get_accounts()[0].currency, "ZAR")
        markets = self.adapter.search_markets("Brent")
        self.assertEqual(markets[0].epic, "CS.D.BRENT.CFD.IP")
        self.assertEqual(self.adapter.get_market(markets[0].epic).market_status, "TRADEABLE")

    def test_mapping_preserves_epic_and_variants(self):
        self.adapter.authenticate()
        first = self.adapter.search_markets("Brent")[0]
        second = type(first)(first.epic + ".DATED", first.name, "FUTURES", first.currency, first.market_status,
                             "2026-12", first.minimum_deal_size, first.contract_size, first.lot_size,
                             first.tick_size, first.margin_factor, first.trading_hours, first.bid, first.offer,
                             first.metadata_status, first.environment, first.raw_identity)
        self.assertNotEqual(self.adapter.discover_instrument("BRENT_PROXY", first).epic,
                            self.adapter.discover_instrument("BRENT_PROXY", second).epic)

    def test_execution_methods_fail_closed_and_headers_are_not_cli_output(self):
        with self.assertRaises(RuntimeError): self.adapter.place_order({})
        self.adapter.authenticate()
        auth_header = self.calls[-1][2]
        self.assertNotIn("CST-SECRET", json.dumps(auth_header))  # token is only returned by transport, not stored in output
        self.assertEqual(self.adapter.capabilities()["order_submission"], False)


if __name__ == "__main__":
    unittest.main()
