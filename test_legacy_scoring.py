"""Characterization tests for the legacy JSE signal score.

These tests freeze the current fixed scoring path while adaptive work is added
beside it. They intentionally use synthetic observations and make no network
or LLM calls.
"""

from types import SimpleNamespace
import unittest

from signal_pipeline import JSESignalEngine
from jse_adapter import DataSourceType


class LegacyScoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = JSESignalEngine(
            tickers=["NPN"],
            price_source=DataSourceType.MOCK,
            news_source="mock",
            use_macro=False,
        )

    def test_technical_weights_sum_to_one_for_all_positive_signals(self):
        indicators = SimpleNamespace(
            rsi_signal=1,
            sma_signal=1,
            breakout_signal=1,
            stochastic_signal=1,
        )
        observation = SimpleNamespace(indicators=indicators)
        self.assertAlmostEqual(self.engine._score_technical(observation), 1.0)

    def test_technical_weights_sum_to_negative_one_for_all_negative_signals(self):
        indicators = SimpleNamespace(
            rsi_signal=-1,
            sma_signal=-1,
            breakout_signal=-1,
            stochastic_signal=-1,
        )
        observation = SimpleNamespace(indicators=indicators)
        self.assertAlmostEqual(self.engine._score_technical(observation), -1.0)

    def test_score_fusion_preserves_threshold_and_confidence_clamp(self):
        indicators = SimpleNamespace(
            rsi_signal=1,
            sma_signal=1,
            breakout_signal=0,
            stochastic_signal=0,
            rsi=25.0,
        )
        observation = SimpleNamespace(
            price=100.0,
            news_sentiment_score=0.8,
            news_sentiment=SimpleNamespace(value="bullish"),
            news="Synthetic bullish news.",
            macro_factor="",
            indicators=indicators,
            recent_prices=[95.0, 100.0],
        )
        self.engine._add_market_data = lambda ticker: None
        self.engine._add_news = lambda ticker: None
        self.engine._macro_adjustment = lambda ticker: 0.0
        self.engine.pipeline.get_observation = lambda ticker: observation

        decision = self.engine.score_ticker("NPN")

        # technical = .35 + .30 = .65; combined = .60*.65 + .30*.80 = .63
        self.assertEqual(decision.action, "buy")
        self.assertEqual(decision.score, 0.63)
        self.assertEqual(decision.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
