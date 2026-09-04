import unittest

import pandas as pd

from hr9_evaluation import _metrics, _position


class HR9EvaluationTests(unittest.TestCase):
    def test_threshold_positions_are_horizon_specific_actions(self):
        self.assertEqual(_position(pd.Series([.36, .35, -.35, -.36])).tolist(), [1, 0, 0, -1])

    def test_execution_cost_uses_action_state_turnover(self):
        frame = pd.DataFrame({"forward_return": [.01, .01, .01]})
        metrics = _metrics(frame, pd.Series([1, 1, -1]), 10.0)
        self.assertEqual(metrics["turnover_units"], 3.0)
        self.assertAlmostEqual(metrics["mean_net_return_all_decisions"], (.009+.01-.012)/3)


if __name__ == "__main__":
    unittest.main()
