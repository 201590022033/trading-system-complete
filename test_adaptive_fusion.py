"""Tests for explainable M6 adaptive shadow fusion."""

from types import SimpleNamespace
import unittest

from adaptive_fusion import AdaptiveFactor, AdaptiveFusionEngine
from jse_adapter import DataSourceType
from market_profiles import DEFAULT_PROFILE_REGISTRY
from regime_engine import MarketRegime
from signal_pipeline import JSESignalEngine


class AdaptiveFusionTests(unittest.TestCase):
    def setUp(self):
        self.fusion = AdaptiveFusionEngine(minimum_reliability_samples=20)
        self.profile = DEFAULT_PROFILE_REGISTRY.select("SASOL")
        self.regime = MarketRegime("bull", "normal", "risk_on", 0.8, "test", {})

    def test_contributions_are_complete_and_normalized(self):
        result = self.fusion.fuse(
            (
                AdaptiveFactor("technical", "technical", 0.8, 0.5),
                AdaptiveFactor("macro", "macro", -0.2, 0.3),
                AdaptiveFactor("source", "authoritative_event", 0.6, 0.2),
            ),
            legacy_score=0.2, legacy_action="hold", profile=self.profile, regime=self.regime,
        )
        self.assertAlmostEqual(sum(item.normalized_weight for item in result.contributions), 1.0, places=5)
        self.assertAlmostEqual(sum(item.contribution for item in result.contributions), result.score, places=5)
        self.assertTrue(result.shadow_only)
        self.assertEqual(result.legacy_action, "hold")

    def test_reliability_waits_for_minimum_sample_gate(self):
        low_sample = AdaptiveFactor("source", "community", 1.0, 1.0, reliability=0.9, reliability_samples=19)
        mature = AdaptiveFactor("source", "community", 1.0, 1.0, reliability=0.9, reliability_samples=20)
        prior = self.fusion.fuse((low_sample,), legacy_score=0, legacy_action="hold", profile=self.profile)
        learned = self.fusion.fuse((mature,), legacy_score=0, legacy_action="hold", profile=self.profile)
        self.assertEqual(prior.contributions[0].reliability_multiplier, 1.0)
        self.assertEqual(learned.contributions[0].reliability_multiplier, 1.5)

    def test_regime_and_profile_multipliers_are_logged(self):
        result = self.fusion.fuse(
            (AdaptiveFactor("macro", "macro", 0.5, 1.0),),
            legacy_score=0, legacy_action="hold", profile=self.profile,
            regime=MarketRegime("bear", "high", "risk_off", 0.8, "test", {}),
        )
        item = result.contributions[0]
        self.assertEqual(item.regime_multiplier, 1.1)
        self.assertEqual(item.profile_multiplier, 1.1)

    def test_signal_engine_keeps_legacy_action_and_logs_shadow_comparison(self):
        engine = JSESignalEngine(
            tickers=["NPN"], price_source=DataSourceType.MOCK,
            news_source="mock", use_macro=False,
        )
        indicators = SimpleNamespace(
            rsi_signal=1, sma_signal=1, breakout_signal=0,
            stochastic_signal=0, rsi=25.0,
        )
        observation = SimpleNamespace(
            price=100.0, news_sentiment_score=0.8,
            news_sentiment=SimpleNamespace(value="bullish"), news="synthetic",
            macro_factor="", indicators=indicators,
            recent_prices=[90.0 + index for index in range(11)],
        )
        engine._add_market_data = lambda ticker: None
        engine._add_news = lambda ticker: None
        engine._macro_adjustment = lambda ticker: 0.0
        engine.pipeline.get_observation = lambda ticker: observation
        decision = engine.score_ticker("NPN")
        self.assertEqual(decision.action, "buy")
        self.assertEqual(decision.score, 0.63)
        shadow = decision.metadata["adaptive_shadow"]
        self.assertTrue(shadow["shadow_only"])
        self.assertEqual(shadow["legacy_action"], decision.action)
        self.assertEqual(shadow["legacy_score"], decision.score)
        self.assertIn("contributions", shadow)

    def test_unavailable_regime_does_not_break_legacy_scoring(self):
        engine = JSESignalEngine(
            tickers=["NPN"], price_source=DataSourceType.MOCK,
            news_source="mock", use_macro=False,
        )
        observation = SimpleNamespace(
            price=0.0, news_sentiment_score=0.0,
            news_sentiment=SimpleNamespace(value="neutral"), news="none",
            macro_factor="", indicators=None, recent_prices=[0.0, 0.0],
        )
        engine._add_market_data = lambda ticker: None
        engine._add_news = lambda ticker: None
        engine.pipeline.get_observation = lambda ticker: observation
        decision = engine.score_ticker("NPN")
        self.assertEqual(decision.action, "hold")
        self.assertEqual(decision.metadata["adaptive_shadow"]["regime"], {"status": "unavailable"})


if __name__ == "__main__":
    unittest.main()
