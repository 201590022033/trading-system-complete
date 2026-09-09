import unittest
from datetime import datetime, timezone

from domain.evaluation.effectiveness import FeatureEffectiveness
from domain.evaluation.suitability import CostEvidence, DiscoveredInstrument, LiquidityEvidence, SuitabilityEvidence, evaluate_suitability
from intraday_instruments import DataGrade, DEFAULT_REGISTRY


class InstrumentSuitabilityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 20, tzinfo=timezone.utc)
        self.instrument = DEFAULT_REGISTRY.get("SOL_CASH")
        self.data = SuitabilityEvidence("AVAILABLE", DataGrade.RESEARCH, "validated-history", "1d", 500, 0.0, "UTC")
        self.costs = CostEvidence("ASSUMED", 12.0, "research-assumption")
        self.liquidity = LiquidityEvidence("UNKNOWN", False, "no execution-grade spread")

    def feature(self, value=.01, status="LEARNED"):
        return FeatureEffectiveness("rsi", "legacy-v1", "technical", "SOL_CASH", "1d", "regime-v1", "bull",
                                    self.now, self.now, 30, 30, 20, 10, 0, value, value, .66, .01, .01, .5,
                                    status, status, "global", value, 0.0, 0.0, "v1", ())

    def evaluate(self, **kwargs):
        features = kwargs.pop("features", (self.feature(), self.feature(.02)))
        return evaluate_suitability(self.instrument, "1d", self.now, data=self.data,
                                    features=features, costs=self.costs,
                                    liquidity=self.liquidity, **kwargs)

    def test_hard_block_wins_over_soft_evidence(self):
        result = self.evaluate(manually_blocked=True)
        self.assertEqual(result.overall_status, "BLOCKED")
        self.assertFalse(result.hard_eligible)

    def test_unsupported_horizon_and_missing_intraday_data(self):
        data = SuitabilityEvidence("UNAVAILABLE", DataGrade.RESEARCH, "public", "5m", 0)
        result = evaluate_suitability(DEFAULT_REGISTRY.get("PALLADIUM_PROXY"), "intraday_30m", self.now, data=data, features=())
        self.assertEqual(result.overall_status, "UNSUPPORTED")
        self.assertIn("UNSUPPORTED_HORIZON", result.blockers)

    def test_research_and_execution_suitability_are_distinct(self):
        research = self.evaluate(execution_required=False)
        execution = self.evaluate(execution_required=True)
        self.assertEqual(research.execution_suitability, "RESEARCH-ONLY")
        self.assertIn("MISSING_EXECUTION_SYMBOL", execution.blockers)

    def test_unknown_liquidity_is_not_bad_liquidity(self):
        result = self.evaluate()
        self.assertEqual(result.liquidity_status, "UNKNOWN")
        self.assertIn("LIQUIDITY_UNAVAILABLE", result.reasons)

    def test_feature_evidence_and_negative_evidence_retained(self):
        result = self.evaluate()
        self.assertEqual(result.learned_feature_count, 2)
        self.assertEqual(result.negative_evidence_count, 0)
        insufficient = self.evaluate(features=(self.feature(-.1, "INSUFFICIENT_EVIDENCE"),))
        self.assertEqual(insufficient.feature_evidence_status, "INSUFFICIENT_EVIDENCE")

    def test_assumed_cost_and_candidate_discovery(self):
        result = self.evaluate()
        self.assertEqual(result.cost_status, "ASSUMED")
        candidate = DiscoveredInstrument("NEW", "New", "manual")
        self.assertEqual(candidate.candidate_state, "CANDIDATE / RESEARCH")
        self.assertFalse(candidate.human_permitted)


if __name__ == "__main__":
    unittest.main()
