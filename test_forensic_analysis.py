import unittest

from forensic_analysis import analyse, matched_opportunity_analysis


class ForensicAnalysisTests(unittest.TestCase):
    def test_analysis_is_deterministic_and_has_24_ranked_rows(self):
        prices = {ticker: [100 + i * 0.2 + (i % 7) * 0.1 for i in range(80)]
                  for ticker in ("NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ")}
        snapshot = {"prices": prices}
        first = analyse(snapshot)
        second = analyse(snapshot)
        self.assertEqual(first, second)
        self.assertEqual(len(first["ranking"]), 24)
        self.assertTrue(all(row["diamond_tier"] in "ABC" for row in first["ranking"]))
        self.assertTrue(all(row["diamond_tier"] == "C" for row in first["ranking"]))
        self.assertTrue(all(row["adaptive_increment_vs_simple_technical"] == 0.0
                            for row in first["ranking"]))

    def test_frozen_close_only_design_records_missing_context_mechanism(self):
        prices = {ticker: [100 + i for i in range(40)]
                  for ticker in ("NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ")}
        result = analyse({"prices": prices})
        self.assertIn("normalize out", result["metadata"]["critical_design_fact"])

    def test_matched_opportunities_are_explicitly_constrained_and_aligned(self):
        prices = {ticker: [100 + i * 0.2 + (i % 7) * 0.1 for i in range(50)]
                  for ticker in ("NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ")}
        matched = matched_opportunity_analysis({"prices": prices})
        self.assertEqual(matched["status"], "INSUFFICIENT HISTORICAL INPUTS")
        self.assertEqual(matched["overall"]["opportunities"], 66)
        self.assertEqual(matched["overall"]["legacy_only_trades"], 0)
        for row in matched["opportunities"]:
            self.assertEqual(row["adaptive_score_price_only_reconstruction"],
                             row["simple_non_adaptive_technical_score"])
            self.assertEqual(set(row["subsequent_returns"]), {"1", "3", "5", "20"})


if __name__ == "__main__": unittest.main()
