import unittest

from indicator_effectiveness import ReliabilityAccumulator, estimate_reliability, signal_outcome, walk_forward_weights


class IndicatorEffectivenessTests(unittest.TestCase):
    def test_minimum_sample_gate_shrinks_to_neutral_weight(self):
        estimate = estimate_reliability([.01]*12, [.011]*12)
        self.assertFalse(estimate.sample_gate_passed)
        self.assertEqual(estimate.current_reliability_weight, 1.0)
        self.assertLess(estimate.shrunk_hit_rate, 1.0)

    def test_mature_stable_evidence_can_change_bounded_weight(self):
        estimate = estimate_reliability([.01]*40, [.011]*40)
        self.assertTrue(estimate.sample_gate_passed)
        self.assertGreater(estimate.current_reliability_weight, 1.0)
        self.assertLessEqual(estimate.current_reliability_weight, 1.5)

    def test_walk_forward_does_not_use_outcome_before_horizon_elapses(self):
        signals = [1]*50
        returns = [.01]*50
        weights = walk_forward_weights(signals, returns, horizon=20)
        self.assertTrue(all(value == 1.0 for value in weights[:49]))
        self.assertGreater(weights[49], 1.0)

    def test_future_outcome_mutation_cannot_change_earlier_weight(self):
        signals = [1]*80
        first = walk_forward_weights(signals, [.01]*80, horizon=5)
        second_returns = [.01]*80
        second_returns[60:] = [-.5]*20
        second = walk_forward_weights(signals, second_returns, horizon=5)
        self.assertEqual(first[:65], second[:65])

    def test_incremental_accumulator_matches_bounded_gate(self):
        state = ReliabilityAccumulator()
        for _ in range(40):
            state.update(.01, .011)
        self.assertEqual(state.count, 40)
        self.assertGreater(state.weight(), 1.0)
        self.assertLessEqual(state.weight(), 1.5)

    def test_cost_is_charged_on_signal_state_turnover(self):
        for actual, expected in zip(signal_outcome(1, 0, .01), (.01, 1.0, .009)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(signal_outcome(1, 1, .01), (.01, 0.0, .01)):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(signal_outcome(-1, 1, .01), (-.01, 2.0, -.012)):
            self.assertAlmostEqual(actual, expected)

    def test_walk_forward_repeated_position_does_not_pay_daily_entry_cost(self):
        weights = walk_forward_weights([1] * 40, [.001] * 40, horizon=1)
        self.assertGreater(weights[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
