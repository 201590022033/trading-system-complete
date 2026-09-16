import tempfile
import unittest
from pathlib import Path
from runtime_persistence import runtime_repository
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from workers.shadow_learning import configured_repository

class RuntimeRoutingTests(unittest.TestCase):
    def test_local_web_and_worker_select_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "state.db")
            web = runtime_repository(database_url="", sqlite_path=path); worker = configured_repository(database_url="", sqlite_path=path)
            self.assertIsInstance(web, SQLiteRepository); self.assertIsInstance(worker, SQLiteRepository)
            web.close(); worker.close()
    def test_postgres_web_and_worker_select_shared_postgres_backend(self):
        web = runtime_repository(database_url="postgresql://fixture")
        worker = configured_repository(database_url="postgresql://fixture")
        self.assertIsInstance(web, PostgresRepository); self.assertIsInstance(worker, PostgresRepository)
        self.assertEqual(web.database_url, worker.database_url)

if __name__ == "__main__": unittest.main()
