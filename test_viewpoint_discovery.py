import unittest
from viewpoint_discovery import SensitiveCaptureError, ingest_sanitized_capture


class DiscoverySafetyTests(unittest.TestCase):
    def test_structural_summary_discards_values(self):
        result = ingest_sanitized_capture({"sanitized": True, "entries": [{
            "method": "GET", "path": "/redacted/path", "content_type": "application/json",
            "transport": "fetch", "field_names": ["availableCash", "positions"]} ]})
        self.assertEqual(result["entries"][0]["transport"], "fetch")
        self.assertNotIn("value", result)

    def test_unmarked_or_sensitive_capture_fails_closed(self):
        with self.assertRaises(SensitiveCaptureError): ingest_sanitized_capture({"entries": []})
        with self.assertRaises(SensitiveCaptureError):
            ingest_sanitized_capture({"sanitized": True, "entries": [{"Authorization": "redacted"}]})


if __name__ == "__main__": unittest.main()
