import io
import os
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from scripts import deployment_preflight


BASE = {
    "DATABASE_URL": "postgresql://redacted@localhost:5433/app",
    "APP_MODE": "RESEARCH",
    "PORT": "8080",
    "COMMIT_SHA": "abc123",
    "WORKER_ID": "worker-test",
}


class DeploymentPreflightTests(unittest.TestCase):
    def test_validates_required_safe_configuration_without_echoing_secrets(self):
        result = deployment_preflight.validate_environment(BASE)
        self.assertIn("postgresql", result.checks)

    def test_refuses_live_mode(self):
        env = {**BASE, "APP_MODE": "LIVE"}
        with self.assertRaisesRegex(RuntimeError, "LIVE"):
            deployment_preflight.validate_environment(env)

    def test_missing_configuration_is_safe_and_does_not_print_values(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stderr(output):
            code = deployment_preflight.main([])
        self.assertEqual(code, 1)
        self.assertIn("missing required deployment variables", output.getvalue())
        self.assertNotIn("postgresql://", output.getvalue())
        self.assertNotIn("redacted", output.getvalue())


if __name__ == "__main__":
    unittest.main()
