import unittest
from viewpoint_discovery import SensitiveCaptureError, ingest_sanitized_capture, sanitize_har_file
from pathlib import Path
import tempfile


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

    def test_har_conversion_keeps_structure_only(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "capture.har"
            target = Path(directory) / "safe.json"
            source.write_text('{"log":{"entries":[{"_resourceType":"fetch","request":{"method":"GET","url":"https://x.test/api?a=private"},"response":{"content":{"mimeType":"application/json","text":"{\\"cash\\":123,\\"positions\\":[]}"}}}]}}', encoding="utf-8")
            result = sanitize_har_file(source, target)
            self.assertEqual(result["entries"][0]["path"], "/api")
            self.assertIn("cash", result["entries"][0]["field_names"])
            self.assertNotIn("private", target.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
