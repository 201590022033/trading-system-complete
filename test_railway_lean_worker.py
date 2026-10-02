import unittest
from workers.railway_entrypoint import command
from scripts.railway_storage_report import retention_capacity


class LeanWorkerTests(unittest.TestCase):
    def test_worker_exits_and_web_role_still_serves(self):
        self.assertEqual(command({"RAILWAY_START_ROLE":"worker"})[-1],"--scheduled")
        self.assertEqual(command({"PORT":"1234"})[2],"0.0.0.0:1234")
        with self.assertRaises(ValueError):command({"RAILWAY_START_ROLE":"live"})

    def test_storage_forecast_keeps_evidence_and_reserves_space(self):
        result=retention_capacity(volume_used_bytes=143_000_000,compact_session_bytes=46_000,
                                 archived_session_bytes=20_000,recent_session_bytes=90_000)
        self.assertGreater(result["projected_years_to_storage_review"],7)
        self.assertFalse(result["automatic_evidence_deletion"])
        full=retention_capacity(volume_used_bytes=450_000_000,compact_session_bytes=46_000,
                               archived_session_bytes=20_000,recent_session_bytes=90_000)
        self.assertEqual(full["projected_years_to_storage_review"],0)
