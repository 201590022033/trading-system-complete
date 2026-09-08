import unittest

from app import app


class UIPrototypeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_page_has_unmistakable_state_and_decision_hierarchy(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        for text in (b"HISTORICAL", b"RESEARCH", b"NOT LIVE", b"Market",
                     b"Horizon", b"Technical", b"News & macro", b"30 confidence gates",
                     b"Manual broker handoff", b"CONFIRM IN BROKER"):
            self.assertIn(text.lower(), page.data.lower())

    def test_dashboard_ids_are_unique_and_navigation_targets_exist(self):
        from html.parser import HTMLParser
        class Elements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids, self.tabs = [], []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if "id" in attrs:
                    self.ids.append(attrs["id"])
                if "data-tab" in attrs:
                    self.tabs.append(attrs["data-tab"])
        elements = Elements()
        elements.feed(self.client.get("/").get_data(as_text=True))
        self.assertEqual(len(elements.ids), len(set(elements.ids)))
        self.assertTrue(set(elements.tabs).issubset(elements.ids))

    def test_sources_work_across_request_threads(self):
        from concurrent.futures import ThreadPoolExecutor
        def request_sources():
            with app.test_client() as client:
                response = client.get("/api/market-intelligence/sources")
                return response.status_code, response.get_json()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: request_sources(), range(4)))
        for status, payload in results:
            self.assertEqual(status, 200)
            self.assertTrue(payload["sources"])

    def test_snapshot_and_demo_api_are_non_live_and_rejected(self):
        snapshot = self.client.get("/api/snapshot").get_json()
        self.assertFalse(snapshot["live"])
        self.assertEqual(snapshot["data_state"], "HISTORICAL")
        idea = self.client.get("/api/demo-suggestion").get_json()
        self.assertEqual(idea["state"], "rejected")
        self.assertFalse(idea["safety"]["actionable"])
        self.assertFalse(idea["safety"]["live_execution_available"])


if __name__ == "__main__":
    unittest.main()
