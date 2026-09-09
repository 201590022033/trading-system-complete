import unittest
from datetime import datetime, timedelta, timezone

from domain.features.regime import (
    CANDIDATE_V2, DEFAULT_REGIME_REGISTRY, LEGACY_DAILY, MarketRegime,
    RegimeParameters, UNAVAILABLE, UNKNOWN, classify_candidate, legacy_daily,
)
from regime_engine import classify_regime


class RegimeEngineV2Tests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 5, 12, tzinfo=timezone.utc)
        self.prices = [100 + index * .5 for index in range(25)]
        self.parameters = RegimeParameters(.02, .025, .008)

    def test_legacy_parity_and_reference_registration(self):
        expected = classify_regime(self.prices)
        actual = legacy_daily(self.prices)
        self.assertEqual(actual, expected)
        self.assertEqual(DEFAULT_REGIME_REGISTRY.get(LEGACY_DAILY.regime_id, LEGACY_DAILY.version), LEGACY_DAILY)
        self.assertEqual(DEFAULT_REGIME_REGISTRY.get(CANDIDATE_V2.regime_id, CANDIDATE_V2.version).governance_state,
                         "RESEARCH / CANDIDATE")

    def test_typed_states_and_missing_data_are_explicit(self):
        result = classify_candidate(self.prices[:5], self.now, self.parameters)
        self.assertEqual(result.availability, UNAVAILABLE)
        self.assertEqual(result.trend_state, UNKNOWN)
        with self.assertRaises(ValueError):
            MarketRegime(self.now.replace(tzinfo=None), "v1")

    def test_thresholds_are_configurable_and_deterministic(self):
        first = classify_candidate(self.prices, self.now, self.parameters)
        second = classify_candidate(self.prices, self.now, self.parameters)
        self.assertEqual(first, second)
        flatter = classify_candidate(self.prices, self.now, RegimeParameters(.20, .025, .008))
        self.assertNotEqual(first.trend_state, flatter.trend_state)

    def test_causal_timestamp_and_future_mutation_invariance(self):
        times = tuple(self.now - timedelta(minutes=5 * (24 - i)) for i in range(25))
        with self.assertRaises(ValueError):
            classify_candidate(self.prices, self.now, self.parameters,
                               available_times=times[:-1])
        earlier = self.now - timedelta(minutes=5)
        prefix = self.prices[:-1]
        prefix_times = tuple(times[:-1])
        before = classify_candidate(prefix, earlier, self.parameters, available_times=prefix_times)
        changed = classify_candidate(prefix + [9999], earlier, self.parameters,
                                     available_times=prefix_times + (earlier + timedelta(minutes=5),))
        self.assertEqual(before, changed)

    def test_candidate_and_legacy_are_isolated(self):
        result = classify_candidate(self.prices, self.now, self.parameters)
        self.assertNotEqual(result.regime_version, LEGACY_DAILY.version)
        self.assertEqual(LEGACY_DAILY.governance_state, "REFERENCE / LEGACY")


if __name__ == "__main__":
    unittest.main()
