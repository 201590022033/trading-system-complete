import unittest

from domain.features.technical import (DEFAULT_FEATURE_REGISTRY,
                                        candidate_bollinger, candidate_donchian,
                                        candidate_rsi_wilder, legacy_breakout_signal,
                                        legacy_rsi, legacy_sma_signal,
                                        legacy_stochastic)
from domain.registry.feature import FeatureStatus
from data_pipeline import SignalGenerator


class FeatureRegistryTests(unittest.TestCase):
    def setUp(self):
        self.values = [100 + ((i * 7) % 19) - i * .11 for i in range(40)]

    def test_registry_ids_are_unique_and_lookup_is_versioned(self):
        ids = DEFAULT_FEATURE_REGISTRY.ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(DEFAULT_FEATURE_REGISTRY.definition("feat_rsi_legacy_v1").status, FeatureStatus.LEGACY)
        self.assertEqual(DEFAULT_FEATURE_REGISTRY.definition("feat_rsi_wilder_v2").status, FeatureStatus.CANDIDATE)

    def test_legacy_wrappers_match_signal_generator(self):
        generator = SignalGenerator(buffer_size=100)
        for value in self.values:
            generator.add_vwap("x", value)
        self.assertEqual(legacy_rsi(self.values).value, generator.calculate_rsi_signal("x")[0])
        self.assertEqual(legacy_sma_signal(self.values).value, generator.calculate_sma_signal("x"))
        self.assertEqual(legacy_breakout_signal(self.values).value, generator.calculate_breakout_signal("x"))
        window = self.values[-14:]
        expected = 50 if max(window) == min(window) else 100 * (window[-1] - min(window)) / (max(window) - min(window))
        self.assertEqual(legacy_stochastic(self.values).value, expected)

    def test_legacy_warmup_and_missing_behavior(self):
        for feature_id in ("feat_rsi_legacy_v1", "feat_sma_legacy_v1", "feat_breakout_close_legacy_v1", "feat_stoch_close_legacy_v1"):
            result = DEFAULT_FEATURE_REGISTRY.compute(feature_id, [])
            self.assertFalse(result.available)
            self.assertTrue(result.reason)

    def test_candidate_formulas_are_available_only_at_declared_warmup(self):
        self.assertFalse(candidate_rsi_wilder(self.values[:14]).available)
        self.assertFalse(candidate_donchian(self.values[:20]).available)
        self.assertFalse(candidate_bollinger(self.values[:19]).available)
        self.assertTrue(candidate_rsi_wilder(self.values).available)
        self.assertTrue(candidate_donchian(self.values).available)
        self.assertTrue(candidate_bollinger(self.values).available)

    def test_candidates_are_isolated_from_legacy(self):
        legacy = DEFAULT_FEATURE_REGISTRY.compute("feat_rsi_legacy_v1", self.values)
        candidate = DEFAULT_FEATURE_REGISTRY.compute("feat_rsi_wilder_v2", self.values)
        self.assertNotEqual(legacy.value, candidate.value)
        self.assertNotEqual(DEFAULT_FEATURE_REGISTRY.definition("feat_rsi_legacy_v1").feature_id,
                            DEFAULT_FEATURE_REGISTRY.definition("feat_rsi_wilder_v2").feature_id)

    def test_candidate_bollinger_is_causal_under_future_mutation(self):
        prefix = self.values[:25]
        original = candidate_bollinger(prefix).value
        mutated = candidate_bollinger(prefix + [999999]).value
        self.assertNotEqual(original, mutated)
        self.assertEqual(original, candidate_bollinger(prefix).value)


if __name__ == "__main__":
    unittest.main()
