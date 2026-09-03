import unittest

from forensic_analysis import analyse


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

    def test_frozen_close_only_design_records_missing_context_mechanism(self):
        prices = {ticker: [100 + i for i in range(40)]
                  for ticker in ("NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ")}
        result = analyse({"prices": prices})
        self.assertIn("normalize out", result["metadata"]["critical_design_fact"])


if __name__ == "__main__": unittest.main()
