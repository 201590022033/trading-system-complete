import unittest
from technical_governance import IndicatorStatus, assess

class GovernanceTests(unittest.TestCase):
    def test_small_sample_is_not_positive_evidence(self):
        result=assess("ichimoku", sample_count=29, reliability=0.9, instrument="USDZAR", horizon="5", regime="bull")
        self.assertEqual(result.status, IndicatorStatus.INSUFFICIENT_EVIDENCE)
        self.assertFalse(result.production)

    def test_validated_is_still_not_production(self):
        result=assess("macd", sample_count=40, reliability=.6)
        self.assertEqual(result.status, IndicatorStatus.VALIDATED)
        self.assertFalse(result.production)

    def test_negative_evidence_is_rejected(self):
        self.assertEqual(assess("rsi", sample_count=40, reliability=0).status, IndicatorStatus.REJECTED)

if __name__ == "__main__": unittest.main()
