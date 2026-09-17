import copy
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_shadow_acceptance import production_fingerprint
from operational_intelligence import service
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import ObservationRecord
from shadow_learning_pipeline import production_shadow_decision, label_decision, aggregate_evidence
from shadow_test_fixtures import decision as fixture_decision, complete_label as label_decision

class ProductionImmutabilityTests(unittest.TestCase):
    def test_research_metadata_is_excluded_from_production_assessment(self):
        # The active BUY + evidence lifecycle is covered in FullAcceptance.
        # This case separately checks that research metadata cannot affect HOLD.
        before = production_fingerprint()
        before_run = service.analyze("NPN", allow_network=False)
        with tempfile.TemporaryDirectory() as d:
            repo = SQLiteRepository(Path(d) / "state.db")
            obs = ObservationRecord("immutable-o", "NPN", "2026-01-01T00:00:00+00:00", "1", {"close": 100}, research_context={"future_indicator": 999}, created_at="2026-01-01T00:00:00+00:00")
            repo.save_observation(obs)
            context = fixture_decision("d", obs.observation_id, "NPN", obs.observed_at, "1", "HOLD", {}).horizon_context
            decision = production_shadow_decision(service, "NPN", horizon="1", observation_id=obs.observation_id, decided_at=obs.observed_at, observation=obs, horizon_context=context)
            repo.save_shadow_decision(decision)
            out = label_decision(decision, now="2026-01-02T00:00:00+00:00", entry_price=100, exit_price=101)
            repo.save_outcome(out); aggregate_evidence(repo, out, instrument="NPN", horizon="1")
            # Research-only data is ledger metadata, not an input to analyze().
            changed=replace(obs,observation_id="immutable-r",source_version="research-metadata-variant",research_context={"different":"research"})
            repo.save_observation(changed)
            other=production_shadow_decision(service,"NPN",horizon="1",observation=changed,
                decided_at=changed.observed_at,horizon_context=context)
            self.assertEqual(decision.production_assessment,other.production_assessment)
            repo.close()
        after = production_fingerprint()
        after_run = service.analyze("NPN", allow_network=False)
        self.assertEqual(before, after)
        self.assertEqual(before_run["decision"], after_run["decision"])

if __name__ == "__main__": unittest.main()
