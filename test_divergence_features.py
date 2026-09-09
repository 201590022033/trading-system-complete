import unittest
from datetime import datetime, timedelta, timezone

from domain.features.divergence import DivergenceConfig, SignalEvidence, summarize
from domain.market_data.horizons import DailySessionHorizon, IntradayDurationHorizon
from domain.features.regime import RegimeParameters, classify_candidate


class DivergenceFeatureTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 5, 12, tzinfo=timezone.utc)
        self.config = DivergenceConfig(expected_signal_count=3, minimum_active_count=2)

    def signal(self, name, state, minutes=0, value=None, horizon="intraday_30m"):
        return SignalEvidence(name, "fixture-v1", state, self.now - timedelta(minutes=minutes),
                              value, "SOL_CASH", horizon, "technical")

    def test_conflict_is_not_low_evidence_or_cancellation(self):
        conflict = summarize((self.signal("a", 1, value=1), self.signal("b", -1, value=-1)), self.now, self.config)
        neutral = summarize((self.signal("a", 0), self.signal("b", 0)), self.now, self.config)
        missing = summarize((self.signal("a", None), self.signal("b", None)), self.now, self.config)
        self.assertEqual(conflict.state, "HIGH_DISAGREEMENT")
        self.assertNotEqual(conflict.state, neutral.state)
        self.assertEqual(missing.state, "LOW_EVIDENCE")
        self.assertNotEqual(conflict.state, missing.state)

    def test_dominance_retains_residual_conflict(self):
        result = summarize((self.signal("a", 1), self.signal("b", 1), self.signal("c", -1)), self.now, self.config)
        self.assertEqual(result.state, "DOMINANT_WITH_CONFLICT")
        self.assertEqual((result.dominant_direction, result.positive_signal_count, result.negative_signal_count), (1, 2, 1))
        self.assertGreater(result.disagreement_ratio, 0)

    def test_coverage_unavailable_and_provenance(self):
        late = self.signal("future", 1, minutes=-5)
        missing = self.signal("missing", None)
        result = summarize((self.signal("a", 1, value=.5), missing, late), self.now, DivergenceConfig(4),
                           instrument_id="SOL_CASH", horizon_id="intraday_30m")
        self.assertEqual(result.unavailable_signal_count, 1)
        self.assertEqual(result.evidence_coverage, .5)
        self.assertEqual(result.contributing_feature_ids, ("a", "missing"))
        self.assertEqual(result.feature_version, "divergence-v1")

    def test_future_mutation_invariance_and_regime_metadata(self):
        first = summarize((self.signal("a", 1),), self.now, DivergenceConfig(1))
        future = self.signal("future", -1, minutes=-10)
        changed = summarize((self.signal("a", 1), future), self.now, DivergenceConfig(1))
        self.assertEqual(first, changed)
        regime = classify_candidate([100 + i for i in range(25)], self.now, RegimeParameters(.02, .025, .008))
        contextual = summarize((self.signal("a", 1),), self.now, DivergenceConfig(1), regime=regime)
        self.assertEqual(contextual.regime_version, regime.regime_version)

    def test_horizons_remain_distinct(self):
        self.assertNotEqual(IntradayDurationHorizon("intraday_30m", 30).horizon_id,
                            DailySessionHorizon().horizon_id)


if __name__ == "__main__":
    unittest.main()
