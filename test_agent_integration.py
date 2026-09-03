"""Compatibility and telemetry tests for M9 multi-agent integration."""

from datetime import datetime
import unittest

from data_pipeline import MarketData, UnifiedDataPipeline
from merged_simulation import MergedSimulation


def pipeline_with_history():
    pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
    for index in range(40):
        price = 100.0 + index
        pipeline.add_market_data(MarketData("NPN", price, datetime.now(), vwap=price))
    return pipeline


class AgentIntegrationTests(unittest.TestCase):
    def test_context_reaches_research_and_disagreement_telemetry(self):
        result = MergedSimulation(pipeline_with_history()).step("NPN")
        self.assertTrue(result["intelligence_context"]["shadow_only"])
        self.assertEqual(result["intelligence_context"]["profile"]["id"], "offshore_earner")
        self.assertIn("contributions", result["intelligence_context"]["adaptive"])
        self.assertIn("legacy_adaptive_disagree", result["disagreement"])
        self.assertIn("Shadow context:", result["research"]["general"]["analysis"])

    def test_governance_outputs_are_unchanged_by_explanatory_context(self):
        contextual = MergedSimulation(pipeline_with_history(), True).step("NPN")
        baseline = MergedSimulation(pipeline_with_history(), False).step("NPN")
        self.assertEqual(contextual["proposal"], baseline["proposal"])
        self.assertEqual(contextual["risk_assessments"], baseline["risk_assessments"])
        self.assertEqual(contextual["decision"], baseline["decision"])

    def test_execution_is_explicitly_paper_only(self):
        result = MergedSimulation(pipeline_with_history()).step("NPN")
        self.assertEqual(result["execution"]["mode"], "paper")


if __name__ == "__main__":
    unittest.main()
