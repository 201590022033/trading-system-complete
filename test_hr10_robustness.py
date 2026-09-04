import unittest

import pandas as pd

from hr10_robustness import (
    AdmissionRules, admission_state, benjamini_hochberg,
    block_bootstrap_ci, non_overlapping_trades, positions,
    purged_embargoed_folds, signal_state_returns,
)


class HR10RobustnessTests(unittest.TestCase):
    def test_purge_and_embargo_boundaries_prevent_horizon_leakage(self):
        for horizon in (1, 3, 5, 20):
            folds = purged_embargoed_folds(200, horizon)
            self.assertTrue(folds)
            for fold in folds:
                self.assertLess(max(fold["train_indices"]) + horizon,
                                min(fold["test_indices"]) - horizon + 1)
                self.assertEqual(fold["purge_sessions"], horizon)
                self.assertEqual(fold["embargo_sessions"], horizon)

    def test_non_overlap_ignores_signals_during_holding_period(self):
        trades = non_overlapping_trades(pd.Series(range(100, 111)),
                                        pd.Series([1] * 11), 3, 10)
        self.assertEqual(trades.entry_index.tolist(), [0, 3, 6])
        self.assertEqual(trades.exit_index.tolist(), [3, 6, 9])
        self.assertTrue((trades.turnover == 2).all())

    def test_signal_state_turnover_entry_hold_exit_reversal(self):
        result = signal_state_returns(pd.Series([100, 101, 102, 103, 104]),
                                      pd.Series([1, 1, 0, -1, 1]), 10)
        self.assertEqual(result.turnover.tolist(), [1, 0, 1, 1, 2])

    def test_missing_signals_become_flat_and_isolated(self):
        self.assertEqual(positions(pd.Series([None, .36, -.36])).tolist(), [0, 1, -1])

    def test_bh_known_values_and_validation(self):
        self.assertEqual([round(x, 3) for x in benjamini_hochberg([.01, .04, .03])], [.03, .04, .04])
        with self.assertRaises(ValueError):
            benjamini_hochberg([1.1])

    def test_block_bootstrap_is_deterministic(self):
        values = pd.Series([.01, -.01, .02, .03]).to_numpy()
        self.assertEqual(block_bootstrap_ci(values), block_bootstrap_ci(values))

    def test_admission_exact_sample_boundary_and_rejection(self):
        base = {"trades": 30, "mean_net_return": .01, "ci_low": .001,
                "maximum_drawdown": -.05}
        state, failures = admission_state(base, [.01, .01, -.01], .001,
                                           [.01, .01, -.01], .01, 0.0)
        self.assertEqual((state, failures), ("ADMIT_FOR_CONTINUED_SHADOW", []))
        insufficient = dict(base, trades=29)
        self.assertEqual(admission_state(insufficient, [.01]*3, .01, [.01]*3, .01, 0)[0],
                         "INSUFFICIENT_EVIDENCE")
        rejected = dict(base, mean_net_return=0.0)
        self.assertEqual(admission_state(rejected, [.01]*3, .01, [.01]*3, .01, 0)[0], "REJECT")

    def test_regime_instrument_horizon_grouping_is_not_implicit(self):
        # Core primitives accept one ordered cell only; callers must group first.
        a = non_overlapping_trades(pd.Series([100, 101]), positions(pd.Series([1, 1]), .35), 1, 0)
        b = non_overlapping_trades(pd.Series([200, 198]), positions(pd.Series([-1, -1]), .35), 1, 0)
        self.assertGreater(a.net_return.iloc[0], 0)
        self.assertGreater(b.net_return.iloc[0], 0)


if __name__ == "__main__":
    unittest.main()
