import copy
import tempfile
import unittest
from pathlib import Path

import adaptive_technical_ensemble as adaptive
from operational_intelligence import service
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import ObservationRecord
from shadow_learning_pipeline import production_shadow_decision, label_decision, aggregate_evidence
from shadow_test_fixtures import decision as fixture_decision, complete_label as label_decision

class ProductionImmutabilityTests(unittest.TestCase):
    def test_complete_shadow_lifecycle_does_not_change_production_state(self):
        # These are the authoritative admitted research/production boundary
        # constants; the shadow ledger has no write path into this module.
        before = {name: copy.deepcopy(getattr(adaptive, name)) for name in ("VERSION", "HORIZON_ROLES", "OUTPUT", "SUMMARY")}
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
            repo.save_observation(copy.copy(obs).__class__("immutable-r", "NPN", obs.observed_at, "1", obs.market_data, research_context={"different": "research"}, created_at=obs.created_at))
            repo.close()
        after = {name: copy.deepcopy(getattr(adaptive, name)) for name in before}
        after_run = service.analyze("NPN", allow_network=False)
        self.assertEqual(before, after)
        self.assertEqual(before_run["decision"], after_run["decision"])
        self.assertFalse(any("SHADOW_ADAPTIVE_EVIDENCE" in str(value) for value in before.values()))

if __name__ == "__main__": unittest.main()
