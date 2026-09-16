import tempfile
import unittest
from pathlib import Path
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from shadow_learning import AdaptiveEvidence

class ShadowRepositoryParityTests(unittest.TestCase):
    def test_sqlite_exposes_shadow_contract(self):
        with tempfile.TemporaryDirectory() as d:
            repo = SQLiteRepository(Path(d) / "x.db")
            for name in ("save_observation", "save_shadow_decision", "save_outcome", "save_adaptive_evidence", "contribute_adaptive_evidence", "save_job", "learning_status"):
                self.assertTrue(callable(getattr(repo, name)))
            self.assertEqual(repo.learning_status()["database_backend"], "sqlite")
            repo.close()

    def test_postgres_schema_and_contract_are_present_without_connecting(self):
        repo = PostgresRepository("postgresql://redacted", connection_factory=lambda _: None)
        sql = repo.initialize_sql()
        for table in ("observations", "shadow_decisions", "outcome_labels", "adaptive_evidence", "adaptive_evidence_contributions", "worker_jobs", "worker_status"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", sql)
        for name in ("save_observation", "save_shadow_decision", "save_outcome", "save_adaptive_evidence", "contribute_adaptive_evidence", "save_job", "learning_status"):
            self.assertTrue(callable(getattr(repo, name)))

if __name__ == "__main__": unittest.main()
