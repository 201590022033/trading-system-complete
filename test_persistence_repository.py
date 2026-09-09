import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from domain.intelligence.clustering import ClusteredEvent
from domain.registry.source import default_canonical_policies
from evidence import EvidenceRecord
from persistence.postgres_repository import PostgresRepository
from persistence.repository import get_storage_repository
from persistence.sqlite_repository import SQLiteRepository


class PersistenceRepositoryTests(unittest.TestCase):
    def test_factory_selects_sqlite_without_database_url(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = get_storage_repository(database_url="", sqlite_path=Path(directory) / "db.sqlite")
            self.assertIsInstance(repository, SQLiteRepository)
            repository.close()

    def test_factory_selects_postgres_only_for_postgres_url(self):
        repository = get_storage_repository(database_url="postgresql://user:pass@localhost/db")
        self.assertIsInstance(repository, PostgresRepository)
        self.assertFalse(repository.connected)
        self.assertIn("CREATE TABLE", repository.initialize_sql())

    def test_sqlite_cluster_round_trip_and_restart(self):
        event = ClusteredEvent("event-1", "research", "v1", "2026-01-01T10:00:00+00:00",
                               "2026-01-01T10:05:00+00:00", "Naspers event", ("e1", "e2"),
                               ("wire", "moneyweb"), ("NPN",), ("gold",), 1, .5, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db.sqlite"
            first = SQLiteRepository(path)
            first.save_clustered_event(event)
            first.close()
            second = SQLiteRepository(path)
            self.assertEqual(second.list_clustered_events(), [event])
            second.close()

    def test_sqlite_source_evidence_and_audit_contract(self):
        record = EvidenceRecord("e1", "moneyweb_rss", "Moneyweb", "financial_media", 3,
                                "Naspers event", "body", None, "2026-01-01T10:00:00+00:00",
                                "2026-01-01T10:00:00+00:00", "2026-01-01T10:01:00+00:00",
                                ["NPN"], [], [], "neutral", 0.0, 0.0, None, metadata={})
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "db.sqlite")
            policy = default_canonical_policies()[0]
            repository.save_source_policy(policy)
            self.assertEqual(repository.get_source_policy(policy.source_id).source_id, policy.source_id)
            repository.save_evidence(record)
            self.assertEqual(repository.get_evidence("e1"), record)
            repository.append_audit_event("test", "evidence", "e1", {"ok": True})
            count = repository.store._connection.execute("SELECT COUNT(*) FROM audit_log WHERE action='test'").fetchone()[0]
            self.assertEqual(count, 1)
            repository.close()

    def test_sqlite_transaction_rolls_back_direct_statement(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "db.sqlite")
            with self.assertRaises(RuntimeError):
                with repository.transaction():
                    repository.store._connection.execute("INSERT INTO audit_log (occurred_at, action) VALUES (?, ?)",
                                                         (datetime.now(timezone.utc).isoformat(), "rollback-test"))
                    raise RuntimeError("rollback")
            row = repository.store._connection.execute("SELECT COUNT(*) FROM audit_log WHERE action='rollback-test'").fetchone()
            self.assertEqual(row[0], 0)
            repository.close()

    def test_postgres_adapter_requires_real_connection(self):
        repository = PostgresRepository("postgresql://localhost/db")
        with self.assertRaises(RuntimeError):
            with repository.transaction():
                pass


if __name__ == "__main__":
    unittest.main()
