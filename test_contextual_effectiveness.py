import unittest
from datetime import datetime, timedelta, timezone

from domain.evaluation.effectiveness import ContextualEffectivenessLearner, EffectivenessConfig, FeatureOutcome
from indicator_effectiveness import signal_outcome
from domain.market_data.horizons import DailySessionHorizon, IntradayDurationHorizon


class ContextualEffectivenessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 20, tzinfo=timezone.utc)
        self.config = EffectivenessConfig(minimum_sample=3, prior_strength=2)

    def outcome(self, index, net=.01, instrument="SOL_CASH", horizon="intraday_30m", regime="bull", maturity_offset=0):
        evaluated = self.now - timedelta(days=index + 2)
        available = evaluated - timedelta(minutes=1)
        maturity = self.now + timedelta(minutes=1) if maturity_offset else evaluated + timedelta(minutes=1)
        return FeatureOutcome("rsi", "legacy-v1", "technical", instrument, horizon, "regime-v1", regime,
                              1, evaluated, available, maturity, net, net, f"r{index}")

    def test_matured_outcomes_and_sample_counts(self):
        result = ContextualEffectivenessLearner(self.config).estimate(
            [self.outcome(i) for i in range(3)] + [self.outcome(9, maturity_offset=1000)],
            feature_id="rsi", evaluated_at=self.now, instrument_id="SOL_CASH",
            horizon_id="intraday_30m", regime_state="bull", regime_version="regime-v1")
        self.assertEqual(result.sample_count, 3)
        self.assertEqual(result.status, "LEARNED")

    def test_hierarchical_fallback_and_shrinkage(self):
        outcomes = [self.outcome(i, instrument="OTHER") for i in range(3)]
        result = ContextualEffectivenessLearner(self.config).estimate(
            outcomes, feature_id="rsi", evaluated_at=self.now, instrument_id="SOL_CASH",
            horizon_id="intraday_30m", regime_state="bear", regime_version="regime-v1")
        self.assertEqual(result.fallback_level, "global")
        self.assertLess(result.expected_return_net, .01)
        self.assertEqual(result.status, "LEARNED")

    def test_future_mutation_and_feature_availability_cannot_leak(self):
        base = [self.outcome(i) for i in range(3)]
        learner = ContextualEffectivenessLearner(self.config)
        first = learner.estimate(base, feature_id="rsi", evaluated_at=self.now,
                                 instrument_id="SOL_CASH", horizon_id="intraday_30m", regime_state="bull")
        future = self.outcome(0, net=-1.0, maturity_offset=1000)
        second = learner.estimate(base + [future], feature_id="rsi", evaluated_at=self.now,
                                  instrument_id="SOL_CASH", horizon_id="intraday_30m", regime_state="bull")
        self.assertEqual(first, second)

    def test_sparse_cells_are_insufficient_and_negative_evidence_retained(self):
        result = ContextualEffectivenessLearner(self.config).estimate(
            [self.outcome(0, -.01)], feature_id="rsi", evaluated_at=self.now,
            instrument_id="SOL_CASH", horizon_id="intraday_30m", regime_state="bull")
        self.assertEqual(result.status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result.negative_outcomes, 1)
        self.assertEqual(result.evidence_grade, "INSUFFICIENT")

    def test_cost_and_horizon_semantics_remain_explicit(self):
        self.assertEqual(signal_outcome(1, 1, .01)[1], 0.0)
        self.assertNotEqual(IntradayDurationHorizon("intraday_30m", 30).horizon_id,
                            DailySessionHorizon().horizon_id)


if __name__ == "__main__":
    unittest.main()
