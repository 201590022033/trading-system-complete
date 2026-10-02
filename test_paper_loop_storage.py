import tempfile
import unittest
from pathlib import Path
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from workers.paper_loop import PaperScheduler, FrozenPaperHandler
from workers.shadow_learning import ShadowWorker

NOW = "2026-09-19T12:00:00+00:00"


class PaperStorageTests(unittest.TestCase):
    def test_lossless_archive_preserves_immutability_and_latest_ranking_both_backends(self):
        for backend in ("sqlite", "postgresql"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/"archive.db"
                repo = SQLiteRepository(path) if backend == "sqlite" else PostgresRepository(
                    "postgresql://fixture", connection=SQLiteDBAPIForPostgres(path))
                if backend != "sqlite": repo.initialize()
                try:
                    repo.create_paper_account("a", {"mode":"PAPER", "ranking_record_id":"latest"})
                    payload = {"bars": [100]*1000}
                    for rid in ("old", "latest"):
                        repo.save_paper_record(rid,"a","ranking",NOW,payload)
                    repo.save_paper_record("outcome","a","candidate-outcome",NOW,payload)
                    self.assertEqual(repo.archive_paper_inputs("a",before="2026-10-01T00:00:00Z"),1)
                    self.assertEqual(repo.paper_record("old"),payload)
                    repo.save_paper_record("old","a","ranking",NOW,payload)
                    with self.assertRaises(ValueError):repo.save_paper_record("old","a","ranking",NOW,{"bars":[]})
                    self.assertEqual(len(repo.paper_records("a","ranking",as_of="2026-10-01T00:00:00Z")),1)
                    self.assertEqual(repo.paper_record("outcome"),payload)
                    self.assertEqual(repo.archive_paper_inputs("a",before="2026-10-01T00:00:00Z"),0)
                finally:repo.close()

    def test_both_backends_rollback_immutable_cutoff_and_job_replay(self):
        for backend in ("sqlite", "postgresql"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "paper.db"
                repo = (SQLiteRepository(path) if backend == "sqlite" else
                        PostgresRepository("postgresql://fixture", connection=SQLiteDBAPIForPostgres(path)))
                if backend != "sqlite":
                    repo.initialize()
                try:
                    repo.create_paper_account("a", {"mode": "PAPER", "cash": 100})
                    with self.assertRaises(RuntimeError):
                        with repo.paper_account_transaction("a") as state:
                            state["cash"] = 0
                            repo.save_paper_record("x", "a", "outcome", NOW, {"net": -.1})
                            raise RuntimeError("injected")
                    self.assertEqual(repo.paper_account("a")["cash"], 100)
                    self.assertIsNone(repo.paper_record("x"))
                    repo.save_paper_record("x", "a", "outcome", NOW, {"net": -.1})
                    repo.save_paper_record("x", "a", "outcome", NOW, {"net": -.1})
                    with self.assertRaises(ValueError):
                        repo.save_paper_record("x", "a", "outcome", NOW, {"net": .2})
                    self.assertEqual(repo.paper_records("a", "outcome", as_of="2026-09-18T12:00:00Z"), [])
                    calls, processed = [], []
                    def loader():
                        calls.append(1)
                        return {"charts": {}}
                    def processor(key, frozen):
                        processed.append(frozen)
                        if len(processed) == 1:
                            raise ValueError("retry after frozen input")
                        return {"state": "COMPLETED"}
                    handler = FrozenPaperHandler(repo, "a", loader, processor, lambda: NOW)
                    scheduler = PaperScheduler(repo, "a")
                    self.assertEqual(scheduler.enqueue(NOW), scheduler.enqueue(NOW))
                    worker = ShadowWorker(repo, "w", {"paper-cycle": handler}, clock=lambda: NOW)
                    self.assertEqual(worker.run_once(), 1)
                    self.assertEqual(worker.run_once(), 1)
                    self.assertEqual(worker.run_once(), 0)
                    self.assertEqual(calls, [1])
                    self.assertEqual(processed[0], processed[1])
                    self.assertEqual(repo.paper_records("b", "outcome", as_of=NOW), [])
                finally:
                    repo.close()
