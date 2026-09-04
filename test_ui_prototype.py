import unittest

from app import app


class UIPrototypeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_page_has_unmistakable_state_and_decision_hierarchy(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        for text in (b"SIMULATED", b"RESEARCH", b"NOT LIVE", b"CURRENT PRICE",
                     b"Horizon", b"Stop", b"Target", b"Maximum defined risk",
                     b"REJECTED RESEARCH", b"CONFIRM IN BROKER"):
            self.assertIn(text.lower(), page.data.lower())

    def test_snapshot_and_demo_api_are_non_live_and_rejected(self):
        snapshot = self.client.get("/api/snapshot").get_json()
        self.assertFalse(snapshot["live"])
        self.assertEqual(snapshot["data_state"], "SIMULATED")
        idea = self.client.get("/api/demo-suggestion").get_json()
        self.assertEqual(idea["state"], "rejected")
        self.assertFalse(idea["safety"]["actionable"])
        self.assertFalse(idea["safety"]["live_execution_available"])


if __name__ == "__main__":
    unittest.main()
