import tempfile
import unittest
from pathlib import Path

from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel, AdaptiveEvidence, JobCheckpoint
from shadow_learning_pipeline import label_decision, aggregate_evidence
from workers.shadow_learning import ShadowWorker
from shadow_test_fixtures import decision as ShadowDecision, complete_label as label_decision


class ShadowLearningFoundationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repo = SQLiteRepository(Path(self.directory.name) / "learning.db")
        self.t0 = "2026-01-01T00:00:00+00:00"

    def tearDown(self):
        self.repo.close(); self.directory.cleanup()

    def test_full_loop_is_idempotent_and_survives_restart(self):
        observation = ObservationRecord("obs-1", "TEST", self.t0, "1", {"close": 100},
                                       production_context={"action": "BUY"}, created_at=self.t0)
        decision = ShadowDecision("dec-1", "obs-1", "TEST", self.t0, "1", "BUY", {"action": "BUY"})
        self.repo.save_observation(observation); self.repo.save_observation(observation)
        self.repo.save_shadow_decision(decision); self.repo.save_shadow_decision(decision)
        self.assertEqual(self.repo.store.counts()["pending_outcomes"], 1)
        outcome = label_decision(decision, now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101)
        self.repo.save_outcome(outcome); self.repo.save_outcome(outcome)
        evidence = aggregate_evidence(self.repo, outcome, instrument="TEST", horizon="1")
        self.assertTrue(evidence)
        self.assertFalse(aggregate_evidence(self.repo, outcome, instrument="TEST", horizon="1"))
        self.assertEqual(self.repo.store.counts()["labelled_outcomes"], 1)
        self.repo.close(); self.repo = SQLiteRepository(Path(self.directory.name) / "learning.db")
        self.assertEqual(self.repo.store.counts()["adaptive_updates"], 1)
        self.assertEqual(self.repo.learning_status()["pending_outcomes"], 0)

    def test_pre_maturity_and_unavailable_are_safe(self):
        decision = ShadowDecision("dec-2", "obs-2", "TEST", self.t0, "1", "HOLD", {})
        with self.assertRaises(ValueError):
            label_decision(decision, now=self.t0, entry_price=100, exit_price=101)
        outcome = label_decision(decision, now="2026-01-02T00:00:00+00:00", entry_price=None, exit_price=None)
        self.assertEqual(outcome.label, "OUTCOME_DATA_UNAVAILABLE")
        self.assertFalse(aggregate_evidence(self.repo, outcome, instrument="TEST", horizon="1"))

    def test_completed_job_is_not_rerun(self):
        job = JobCheckpoint("job-1", "observation-generation", self.t0)
        calls = []
        worker = ShadowWorker(self.repo, "worker-1", {job.job_type: lambda _: calls.append(1) or {"done": True}})
        self.assertEqual(worker.run_once([job]), 1)
        completed = JobCheckpoint("job-1", job.job_type, self.t0, "COMPLETED")
        self.assertEqual(worker.run_once([completed]), 0)
        self.assertEqual(len(calls), 1)

    def test_running_job_is_recovered_after_restart(self):
        job = JobCheckpoint("job-running", "outcome-labelling", self.t0, "RUNNING", "dead-worker", 1)
        self.repo.save_job(job)
        recovered = ShadowWorker(self.repo, "new-worker").recover_running([job])
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].status, "PENDING")
        self.assertEqual(recovered[0].error_category, "WORKER_RESTART")


if __name__ == "__main__": unittest.main()
