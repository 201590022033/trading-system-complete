import tempfile
import unittest
from pathlib import Path
from reliability_store import ReliabilityStore, SourceDefinition, runtime_reliability_store, runtime_repository_reliability
from persistence.sqlite_repository import SQLiteRepository

class RuntimeReliabilityTests(unittest.TestCase):
    def test_runtime_state_survives_reconstruction(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "reliability.db"
            first = runtime_reliability_store(path)
            first.register_source(SourceDefinition("s", "Source", "public", 1))
            first.record_outcome(evidence_id="e", source_id="s", scope_key="global", horizon="5d", observed_at="2026-01-01T00:00:00+00:00", evaluated_at="2026-01-06T00:00:00+00:00", direction=1, forward_return=.1)
            first.close()
            second = runtime_reliability_store(path)
            self.assertEqual(second.summarize("s").samples, 1)
            second.close()

    def test_memory_mode_remains_explicit_for_isolated_tests(self):
        store = ReliabilityStore(":memory:")
        self.assertEqual(store.summarize("missing").samples, 0)
        store.close()
        with self.assertRaises(ValueError): runtime_reliability_store(":memory:")

    def test_shared_repository_reliability_is_visible_to_web_and_worker(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "shared.db"
            web = runtime_repository_reliability(SQLiteRepository(path))
            web.record_outcome(evidence_id="e", source_id="s", scope_key="global", horizon="5d", observed_at="2026-01-01T00:00:00+00:00", evaluated_at="2026-01-06T00:00:00+00:00", direction=1, forward_return=.1)
            worker_repo = SQLiteRepository(path); worker = runtime_repository_reliability(worker_repo)
            self.assertEqual(worker.summarize("s").samples, 1)
            worker.record_outcome(evidence_id="e2", source_id="s", scope_key="global", horizon="5d", observed_at="2026-01-02T00:00:00+00:00", evaluated_at="2026-01-07T00:00:00+00:00", direction=-1, forward_return=.1)
            web_repo = SQLiteRepository(path); self.assertEqual(runtime_repository_reliability(web_repo).summarize("s").samples, 2)
            web.close(); worker.close(); web_repo.close()

if __name__ == "__main__": unittest.main()
