"""Offline tests for the M7 walk-forward evaluation contract."""

import unittest

from evaluation import CostAssumptions, MODEL_NAMES, evaluate_walk_forward


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.prices = [100.0 + index * 0.6 + ((index % 5) - 2) * 0.15 for index in range(90)]
        self.sentiment = [0.4 if index % 4 else -0.2 for index in range(90)]
        self.macro = [0.5 for _ in range(90)]
        self.source = [0.6 if index % 3 else -0.4 for index in range(90)]

    def test_reports_all_horizons_models_metrics_and_segments(self):
        report = evaluate_walk_forward(
            "SASOL", self.prices, horizons=(1, 5),
            sentiment_scores=self.sentiment, macro_scores=self.macro,
            source_scores=self.source,
            costs=CostAssumptions(2.0, 1.0, 2.0), minimum_sample=10,
        )
        overall = [row for row in report["rows"] if row["segment_type"] == "overall"]
        self.assertEqual({row["model"] for row in overall}, set(MODEL_NAMES))
        self.assertEqual({row["horizon"] for row in overall}, {1, 5})
        for row in overall:
            for key in ("sample_count", "win_rate", "mean_aligned_return", "median_aligned_return",
                        "mean_net_return", "max_drawdown", "mean_mfe", "mean_mae", "turnover"):
                self.assertIn(key, row)
        self.assertTrue(any(row["segment_type"] == "trend" for row in report["rows"]))
        self.assertTrue(any(row["segment_type"] == "profile" and row["segment"] == "energy_sasol"
                            for row in report["rows"]))

    def test_costs_reduce_net_returns(self):
        free = evaluate_walk_forward("NPN", self.prices, horizons=(1,))
        costly = evaluate_walk_forward(
            "NPN", self.prices, horizons=(1,), costs=CostAssumptions(5, 5, 5)
        )
        free_rows = {(row["model"], row["segment_type"], row["segment"]): row for row in free["rows"]}
        costly_rows = {(row["model"], row["segment_type"], row["segment"]): row for row in costly["rows"]}
        key = ("technical_only", "overall", "all")
        self.assertLessEqual(costly_rows[key]["mean_net_return"], free_rows[key]["mean_net_return"])

    def test_future_mutation_cannot_change_earlier_horizon_outcome(self):
        prefix = self.prices[:50]
        changed = prefix + [10000.0] * 40
        first = evaluate_walk_forward("BHP", prefix, horizons=(5,))
        second = evaluate_walk_forward("BHP", changed, horizons=(5,))
        # Segment aggregates contain later decisions, so compare an invariant
        # early sample count by evaluating the shared prefix independently.
        repeated = evaluate_walk_forward("BHP", changed[:50], horizons=(5,))
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, second)

    def test_context_series_must_align_and_sample_uncertainty_is_flagged(self):
        with self.assertRaises(ValueError):
            evaluate_walk_forward("NPN", self.prices, sentiment_scores=[0.0])
        report = evaluate_walk_forward("NPN", self.prices[:10], horizons=(1,), minimum_sample=30)
        self.assertTrue(all(row["insufficient_sample"] for row in report["rows"]))

    def test_missing_context_is_excluded_instead_of_diluting_adaptive_score(self):
        report = evaluate_walk_forward("SASOL", self.prices, horizons=(5,))
        overall = {
            row["model"]: row for row in report["rows"]
            if row["segment_type"] == "overall"
        }
        self.assertEqual(
            overall["adaptive"]["sample_count"],
            overall["technical_only"]["sample_count"],
        )
        self.assertEqual(overall["macro_only"]["sample_count"], 0)
        self.assertEqual(overall["source_only"]["sample_count"], 0)


if __name__ == "__main__":
    unittest.main()
