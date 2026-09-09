import os
import unittest
from unittest.mock import patch

from app import app
from workers.heartbeat import heartbeat


class RailwayFoundationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_local_mode_is_structured_and_safe(self):
        with patch.dict(os.environ, {"APP_MODE": "DEVELOPMENT"}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["database"], "LOCAL_SQLITE")
        self.assertFalse(body["live_execution"])
        self.assertNotIn("DATABASE_URL", str(body))

    def test_health_fails_closed_for_production_without_postgres(self):
        with patch.dict(os.environ, {"APP_MODE": "RESEARCH"}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            self.assertEqual(self.client.get("/health").status_code, 200)
        with patch.dict(os.environ, {"APP_MODE": "RAILWAY", "DATABASE_URL": ""}, clear=False):
            self.assertEqual(self.client.get("/health").status_code, 503)

    def test_health_recognizes_postgres_without_exposing_url(self):
        secret_url = "postgresql://user:secret@example.test/db"
        with patch.dict(os.environ, {"APP_MODE": "RAILWAY", "DATABASE_URL": secret_url}, clear=False):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["database"], "CONFIGURED_POSTGRES")
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_worker_heartbeat_is_non_sensitive_and_deterministic_shape(self):
        with patch.dict(os.environ, {"APP_MODE": "RESEARCH", "COMMIT_SHA": "test"}, clear=False):
            result = heartbeat("worker-test")
        self.assertEqual(result["worker_id"], "worker-test")
        self.assertEqual(result["status"], "RUNNING")
        self.assertEqual(result["mode"], "RESEARCH")
        self.assertNotIn("DATABASE_URL", result)


if __name__ == "__main__":
    unittest.main()
