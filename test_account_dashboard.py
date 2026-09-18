import unittest
from account_dashboard import safe_status


class AccountDashboardTests(unittest.TestCase):
    def test_disabled_by_default_without_authentication(self):
        result = safe_status({})
        self.assertEqual(result["state"], "UNAVAILABLE")
        self.assertFalse(result["live_execution"])

    def test_live_environment_is_not_allowed(self):
        result = safe_status({"IG_ACCOUNT_STATUS_ENABLED": "1", "IG_ENVIRONMENT": "LIVE"})
        self.assertEqual(result["state"], "UNAVAILABLE")
        self.assertIn("DEMO", result["reason"])


if __name__ == "__main__":
    unittest.main()
