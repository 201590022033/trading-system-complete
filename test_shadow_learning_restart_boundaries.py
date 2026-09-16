import tempfile
import unittest
from pathlib import Path
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import ObservationRecord, ShadowDecision, JobCheckpoint
from shadow_learning_pipeline import label_decision, aggregate_evidence
from workers.shadow_learning import ShadowWorker
from shadow_test_fixtures import decision as ShadowDecision, complete_label as label_decision

class RestartBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name) / "state.db"
        self.t0 = "2026-01-01T00:00:00+00:00"
    def repo(self): return SQLiteRepository(self.path)
    def obs(self): return ObservationRecord("o", "TEST", self.t0, "1", {"close": 100}, created_at=self.t0)
    def dec(self): return ShadowDecision("d", "o", "TEST", self.t0, "1", "BUY", {})
    def tearDown(self): self.tmp.cleanup()

    def test_b1_observation_restart_then_decision_once(self):
        r = self.repo(); r.save_observation(self.obs()); r.close()
        r = self.repo(); r.save_shadow_decision(self.dec()); r.save_shadow_decision(self.dec())
        self.assertIsNotNone(r.get_observation("o")); self.assertEqual(r.store.counts()["shadow_decisions"], 1); r.close()

    def test_b2_pending_restart_then_matured_outcome_once(self):
        r = self.repo(); r.save_observation(self.obs()); r.save_shadow_decision(self.dec()); r.close()
        r = self.repo(); self.assertEqual(r.store.counts()["pending_outcomes"], 1)
        with self.assertRaises(ValueError): label_decision(self.dec(), now=self.t0, entry_price=100, exit_price=101)
        out = label_decision(self.dec(), now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101)
        r.save_outcome(out); r.close()
        r = self.repo(); r.save_outcome(out); self.assertEqual(r.store.counts()["labelled_outcomes"], 1); r.close()

    def test_b3_label_restart_then_evidence_once(self):
        r = self.repo(); r.save_observation(self.obs()); r.save_shadow_decision(self.dec()); out = label_decision(self.dec(), now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101); r.save_outcome(out); r.close()
        r = self.repo(); self.assertTrue(aggregate_evidence(r, out, instrument="TEST", horizon="1")); r.close()
        r = self.repo(); self.assertFalse(aggregate_evidence(r, out, instrument="TEST", horizon="1")); self.assertEqual(r.store.counts()["adaptive_updates"], 1); r.close()

    def test_b4_running_job_recovery_executes_once(self):
        r = self.repo(); job = JobCheckpoint("j", "observation-generation", self.t0, "RUNNING", "lost", 1, {}, True); r.save_job(job); r.close()
        r = self.repo(); w = ShadowWorker(r, "new", {"observation-generation": lambda _: {"created": "o"}}); recovered = w.recover_running([job]); self.assertEqual(recovered[0].status, "PENDING"); self.assertEqual(w.run_once(recovered), 1); r.close()

    def test_b5_completed_job_reencountered_after_restart(self):
        r = self.repo(); job = JobCheckpoint("j", "observation-generation", self.t0, "COMPLETED"); r.save_job(job); r.close()
        r = self.repo(); calls = []; self.assertEqual(ShadowWorker(r, "new", {job.job_type: lambda _: calls.append(1)}).run_once([job]), 0); self.assertFalse(calls); r.close()

    def test_b6_multiple_restarts_preserve_final_counts(self):
        r = self.repo(); r.save_observation(self.obs()); r.close(); r = self.repo(); r.save_shadow_decision(self.dec()); r.close(); r = self.repo(); out = label_decision(self.dec(), now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101); r.save_outcome(out); r.close(); r = self.repo(); aggregate_evidence(r, out, instrument="TEST", horizon="1"); aggregate_evidence(r, out, instrument="TEST", horizon="1"); self.assertEqual(r.store.counts(), {"observations": 1, "shadow_decisions": 1, "labelled_outcomes": 1, "adaptive_updates": 1, "pending_outcomes": 0}); r.close()

if __name__ == "__main__": unittest.main()
