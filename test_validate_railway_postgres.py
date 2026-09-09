import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import scripts.validate_railway_postgres as validation


class ValidationUtilityTests(unittest.TestCase):
    def test_module_invocation_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.validate_railway_postgres", "verify"],
            cwd=Path(__file__).resolve().parent,
            env={key: value for key, value in os.environ.items() if key != "DATABASE_URL"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("ModuleNotFoundError: No module named 'domain'", result.stderr)
        self.assertIn("DATABASE_URL is required", result.stderr)

    def test_database_url_is_required(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(RuntimeError):
            validation.repository()

    def test_ids_are_stable_and_prefixed(self):
        self.assertTrue(all(value.startswith("M7_VALIDATION_") for value in validation.IDS.values()))
        left = validation.records()
        right = validation.records()
        self.assertEqual(left[1].evidence_id, right[1].evidence_id)
        self.assertEqual(left[2].event_id, right[2].event_id)


if __name__ == "__main__":
    unittest.main()
