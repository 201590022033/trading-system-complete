import json
import os
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.parse import urlparse

from domain.broker.ig import IGConfig, IGReadOnlyAdapter
from scripts import ig_discovery


class IGDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def transport(method, url, headers, body, timeout):
            self.calls.append((method, url, headers, body))
            if url.endswith("/session"):
                return 200, {"CST": "CST-SECRET", "X-SECURITY-TOKEN": "SEC-SECRET"}, b"{}"
            if url.endswith("/accounts"):
                return 200, {}, json.dumps({"accounts": [{"accountId": "ACC", "accountName": "Demo", "currency": {"code": "ZAR"}, "preferred": True}]}).encode()
            if "/markets?" in url:
                return 200, {}, json.dumps({"markets": [{"epic": "CS.D.BRENT.CFD.IP", "instrumentName": "Brent", "instrument": {"type": "COMMODITIES", "currency": "USD"}}]}).encode()
            return 200, {}, json.dumps({"epic": "CS.D.BRENT.CFD.IP", "instrumentName": "Brent", "instrument": {"type": "COMMODITIES", "currency": "USD"}, "snapshot": {"marketStatus": "TRADEABLE"}}).encode()
        self.adapter = IGReadOnlyAdapter(IGConfig("API-SECRET", "user", "password", environment="DEMO"), transport)

    def failing_adapter(self, status, payload):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        return IGReadOnlyAdapter(
            IGConfig("API-SECRET", "user", "password", environment="LIVE"),
            lambda *args: (status, {}, raw),
        )

    def test_demo_live_separation_and_missing_configuration(self):
        self.assertIn("demo-api", self.adapter.config.base_url)
        self.assertIn("api.ig.com", IGConfig("a", "u", "p", environment="LIVE").base_url)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): IGConfig.from_env()

    def test_discovery_cli_uses_canonical_environment_loader(self):
        captured = {}
        class StubConfig:
            pass
        class StubAdapter:
            def __init__(self, config):
                captured["config"] = config
            def authentication_status(self):
                return {"authenticated": False, "environment": "DEMO", "message": "missing"}
        with patch.object(ig_discovery, "project_environment", return_value={"IG_API_KEY": "key"}) as loader:
            with patch.object(ig_discovery, "IGConfig", from_env=lambda values: values):
                with patch.object(ig_discovery, "IGReadOnlyAdapter", StubAdapter):
                    with patch("sys.argv", ["ig_discovery", "status"]):
                        with patch("builtins.print") as printer:
                            ig_discovery.main()
        loader.assert_called_once_with()
        self.assertEqual(captured["config"], {"IG_API_KEY": "key"})
        output = json.dumps(printer.call_args.args[0])
        self.assertNotIn("key", output)

    def test_canonical_environment_explicit_process_values_take_precedence(self):
        with patch("ai_config.dotenv_values", return_value={"IG_ENVIRONMENT": "DEMO", "IG_API_KEY": "from-file"}):
            values = __import__("ai_config").project_environment({"IG_API_KEY": "from-process"})
        self.assertEqual(values["IG_API_KEY"], "from-process")
        self.assertEqual(values["IG_ENVIRONMENT"], "DEMO")

    def test_explicit_identifier_maps_to_auth_payload_and_not_account_id(self):
        calls = []
        def transport(method, url, headers, body, timeout):
            calls.append(json.loads(body))
            return 200, {"CST": "CST-SECRET", "X-SECURITY-TOKEN": "SEC-SECRET"}, b"{}"
        config = IGConfig("API-SECRET", "legacy-name", "password", account_id="ACCOUNT-123",
                          identifier="ApiLogin_1")
        IGReadOnlyAdapter(config, transport).authenticate()
        self.assertEqual(calls[0]["identifier"], "ApiLogin_1")
        self.assertNotEqual(calls[0]["identifier"], config.account_id)
        self.assertNotIn("accountId", calls[0])

    def test_identifier_configuration_and_legacy_alias(self):
        explicit = IGConfig.from_env({"IG_API_KEY": "key", "IG_IDENTIFIER": "ApiLogin_1",
                                      "IG_PASSWORD": "secret", "IG_ACCOUNT_ID": "ACC-1"})
        alias = IGConfig.from_env({"IG_API_KEY": "key", "IG_USERNAME": "LegacyLogin",
                                   "IG_PASSWORD": "secret"})
        self.assertEqual(explicit.auth_identifier, "ApiLogin_1")
        self.assertEqual(alias.auth_identifier, "LegacyLogin")
        self.assertEqual(explicit.account_id, "ACC-1")

    def test_malformed_identifier_is_rejected_locally_without_echo(self):
        for invalid in ("name@example.com", "contains space", "x" * 31):
            with self.assertRaisesRegex(ValueError, "IG_IDENTIFIER") as raised:
                IGConfig("key", "", "secret", identifier=invalid)
            self.assertNotIn(invalid, str(raised.exception))

    def test_authentication_is_normalized_and_secrets_not_logged(self):
        result = self.adapter.authenticate()
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["environment"], "DEMO")
        self.assertNotIn("CST-SECRET", str(result))
        self.assertNotIn("SEC-SECRET", str(result))

    def test_session_headers_are_case_insensitive(self):
        adapter = IGReadOnlyAdapter(
            self.adapter.config,
            lambda *args: (200, {"cSt": "CST-SECRET", "x-SeCuRiTy-ToKeN": "SEC-SECRET"}, b"{}"),
        )
        self.assertTrue(adapter.authenticate()["authenticated"])

    def test_success_requires_both_v2_session_headers(self):
        for headers in ({"CST": "CST-SECRET"}, {"X-SECURITY-TOKEN": "SEC-SECRET"}, {}):
            with self.subTest(headers=tuple(headers)):
                adapter = IGReadOnlyAdapter(self.adapter.config, lambda *args, h=headers: (200, h, b"{}"))
                result = adapter.authentication_status()
                self.assertEqual(result["error_category"], "MALFORMED_RESPONSE")
                self.assertNotIn("SECRET", json.dumps(result))

    def test_v2_does_not_accept_v3_oauth_body_as_session_tokens(self):
        body = json.dumps({"oauthToken": {"access_token": "BEARER-SECRET"}}).encode()
        result = IGReadOnlyAdapter(self.adapter.config, lambda *args: (200, {}, body)).authentication_status()
        self.assertEqual(result["error_category"], "MALFORMED_RESPONSE")
        self.assertNotIn("BEARER-SECRET", json.dumps(result))

    def test_accounts_search_and_market_detail(self):
        self.adapter.authenticate()
        self.assertEqual(self.adapter.get_accounts()[0].currency, "ZAR")
        markets = self.adapter.search_markets("Brent")
        self.assertEqual(markets[0].epic, "CS.D.BRENT.CFD.IP")
        self.assertEqual(self.adapter.get_market(markets[0].epic).market_status, "TRADEABLE")

    def test_all_routes_remain_under_gateway_and_use_official_version_header(self):
        self.adapter.authenticate()
        self.adapter.get_accounts()
        self.adapter.search_markets("Brent crude")
        self.adapter.get_market("CS.D.BRENT.CFD.IP")
        paths = [urlparse(call[1]).path for call in self.calls]
        self.assertEqual(paths, ["/gateway/deal/session", "/gateway/deal/accounts",
                                 "/gateway/deal/markets", "/gateway/deal/markets/CS.D.BRENT.CFD.IP"])
        self.assertEqual([call[2]["Version"] for call in self.calls], ["2", "1", "1", "3"])
        self.assertTrue(all("Accept-Version" not in call[2] for call in self.calls))

        leading = self.adapter.request_route("GET", "/prices/CC.D.LCO.BMU.IP?from=private", 3)
        plain = self.adapter.request_route("GET", "prices/CC.D.LCO.BMU.IP", 3)
        expected = {"environment": "DEMO", "method": "GET", "host": "demo-api.ig.com",
                    "path": "/gateway/deal/prices/CC.D.LCO.BMU.IP", "version": 3}
        self.assertEqual(leading, expected)
        self.assertEqual(plain, expected)
        self.assertNotIn("private", repr(leading))
        with self.assertRaises(ValueError):
            self.adapter.request_route("GET", "https://example.invalid/prices/EPIC", 3)
        with self.assertRaises(ValueError):
            self.adapter.request_route("GET", "../prices/EPIC", 3)

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
        accounts = self.adapter.get_accounts()
        auth_header = self.calls[-1][2]
        self.assertEqual(auth_header["CST"], "CST-SECRET")
        self.assertEqual(auth_header["X-SECURITY-TOKEN"], "SEC-SECRET")
        self.assertNotIn("CST-SECRET", repr(accounts))
        self.assertNotIn("SEC-SECRET", repr(accounts))
        self.assertEqual(self.adapter.capabilities()["order_submission"], False)

    def test_invalid_username_or_password(self):
        result = self.failing_adapter(401, {"errorCode": "error.security.invalid-details"}).authentication_status()
        self.assertEqual(result["error_category"], "AUTHENTICATION_FAILED")
        self.assertEqual(result["http_status"], 401)

    def test_invalid_api_key(self):
        result = self.failing_adapter(401, {"errorCode": "error.security.invalid-api-key"}).authentication_status()
        self.assertEqual(result["error_category"], "INVALID_API_KEY")

    def test_generic_401_auth_failure(self):
        result = self.failing_adapter(401, {"message": "unauthorized"}).authentication_status()
        self.assertEqual(result["error_category"], "AUTHENTICATION_FAILED")

    def test_403_permission_failure(self):
        result = self.failing_adapter(403, {"message": "forbidden"}).authentication_status()
        self.assertEqual(result["error_category"], "PERMISSION_DENIED")

    def test_explicit_environment_mismatch_code(self):
        result = self.failing_adapter(401, {"errorCode": "error.security.environment-mismatch"}).authentication_status()
        self.assertEqual(result["error_category"], "ENVIRONMENT_MISMATCH")

    def test_rate_limit_response(self):
        result = self.failing_adapter(429, {"errorCode": "error.public-api.exceeded-api-key-allowance"}).authentication_status()
        self.assertEqual(result["error_category"], "RATE_LIMITED")

    def test_network_failure_is_sanitized(self):
        def transport(*args):
            raise URLError("password API-SECRET CST=CST-SECRET")
        result = IGReadOnlyAdapter(self.adapter.config, transport).authentication_status()
        self.assertEqual(result["error_category"], "NETWORK_ERROR")
        self.assertNotIn("API-SECRET", str(result))

    def test_malformed_error_body(self):
        result = self.failing_adapter(500, b"not-json").authentication_status()
        self.assertEqual(result["error_category"], "MALFORMED_RESPONSE")
        self.assertIsNone(result["ig_error_code"])

    def test_malformed_request_and_unexpected_ig_failure_remain_distinct(self):
        malformed = self.failing_adapter(400, {"message": "bad request"}).authentication_status()
        unexpected = self.failing_adapter(500, {"errorCode": "error.system.unexpected-error"}).authentication_status()
        self.assertEqual(malformed["error_category"], "MALFORMED_REQUEST")
        self.assertEqual(unexpected["error_category"], "UNKNOWN_IG_ERROR")

    def test_known_ig_error_code_is_preserved(self):
        code = "error.security.account-not-enabled-for-api"
        result = self.failing_adapter(403, {"errorCode": code}).authentication_status()
        self.assertEqual(result["ig_error_code"], code)
        self.assertEqual(result["error_category"], "PERMISSION_DENIED")

    def test_two_factor_requirement_is_reported_without_password_changes(self):
        calls = []
        def transport(method, url, headers, body, timeout):
            calls.append(json.loads(body))
            return 401, {}, json.dumps({"errorCode": "error.security.two-factor-authentication-required"}).encode()
        result = IGReadOnlyAdapter(self.adapter.config, transport).authentication_status()
        self.assertEqual(result["error_category"], "TWO_FACTOR_REQUIRED")
        self.assertEqual(calls[0]["password"], "password")

    def test_all_authentication_secrets_are_redacted(self):
        response = {"errorCode": "error.security.invalid-details",
                    "message": "password=PASSWORD-SECRET api_key=API-SECRET account_id=ACCOUNT-SECRET CST=CST-SECRET X-SECURITY-TOKEN=SEC-SECRET"}
        raw = json.dumps(response).encode()
        adapter = IGReadOnlyAdapter(IGConfig("API-SECRET", "USER-SECRET", "PASSWORD-SECRET",
                                             account_id="ACCOUNT-SECRET", environment="LIVE"),
                                    lambda *args: (401, {}, raw))
        result = adapter.authentication_status()
        rendered = json.dumps(result)
        for secret in ("PASSWORD-SECRET", "API-SECRET", "USER-SECRET", "ACCOUNT-SECRET",
                       "CST-SECRET", "SEC-SECRET"):
            self.assertNotIn(secret, rendered)

    def test_successful_status_authenticates_without_exposing_tokens(self):
        result = self.adapter.authentication_status()
        self.assertEqual(result, {"authenticated": True, "environment": "DEMO"})
        self.assertNotIn("CST-SECRET", json.dumps(result))

    def test_malformed_success_response_is_reported(self):
        result = self.failing_adapter(200, b"not-json").authentication_status()
        self.assertEqual(result["error_category"], "MALFORMED_RESPONSE")


if __name__ == "__main__":
    unittest.main()
