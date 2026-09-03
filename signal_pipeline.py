"""JSE signal pipeline for South African market data + sentiment scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from data_pipeline import MarketData, UnifiedDataPipeline
from jse_adapter import JSEDataAdapter, DataSourceType
from market_profiles import DEFAULT_PROFILE_REGISTRY, ProfileRegistry
from adaptive_fusion import AdaptiveFactor, AdaptiveFusionEngine
from regime_engine import classify_regime

try:
    from sentiment_analyzer import MacroSentimentScanner
    MACRO_AVAILABLE = True
except Exception:
    MACRO_AVAILABLE = False


@dataclass
class SignalDecision:
    ticker: str
    action: str
    confidence: float
    score: float
    technical_score: float
    sentiment_score: float
    reason: str
    metadata: Dict = field(default_factory=dict)


def legacy_technical_score(observation) -> float:
    """Return the characterized fixed technical score for an observation."""
    if observation.indicators is None:
        return 0.0
    score = 0.0
    for signal, weight in (
        (observation.indicators.rsi_signal, 0.35),
        (observation.indicators.sma_signal, 0.30),
        (observation.indicators.breakout_signal, 0.20),
        (observation.indicators.stochastic_signal, 0.15),
    ):
        if signal == 1:
            score += weight
        elif signal == -1:
            score -= weight
    return score


class JSESignalEngine:
    """Combines technical indicators, SA news sentiment and macro overlays."""

    def __init__(
        self,
        tickers: Optional[List[str]] = None,
        price_source: DataSourceType = DataSourceType.YAHOO_FINANCE,
        news_source: str = "mock",
        use_macro: bool = True,
        profile_registry: ProfileRegistry = DEFAULT_PROFILE_REGISTRY,
        adaptive_fusion: Optional[AdaptiveFusionEngine] = None,
    ):
        self.tickers = tickers or ["NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "ABSPJ"]
        self.pipeline = UnifiedDataPipeline(jse_tickers=self.tickers)
        self.adapter = JSEDataAdapter(
            price_source=price_source,
            news_source=news_source,
        )
        self.profile_registry = profile_registry
        self.adaptive_fusion = adaptive_fusion or AdaptiveFusionEngine()
        self.macro_report = None
        if use_macro and MACRO_AVAILABLE:
            try:
                scanner = MacroSentimentScanner()
                self.macro_report = scanner.scan(moneyweb_limit=10, sens_limit=6)
                self._apply_macro_news()
            except Exception as exc:
                print(f"[SIGNALS] macro scan skipped: {exc}")

    def _apply_macro_news(self) -> None:
        """Feed analyzed macro headlines into the pipeline as news items."""
        if not self.macro_report:
            return
        from data_pipeline import NewsItem, SentimentLabel
        for item in self.macro_report.items:
            label = SentimentLabel.NEUTRAL
            if item.sentiment == "bullish":
                label = SentimentLabel.BULLISH
            elif item.sentiment == "bearish":
                label = SentimentLabel.BEARISH
            news = NewsItem(
                ticker="JSE",
                headline=item.headline,
                source=item.source,
                timestamp=datetime.now(),
                sentiment_label=label,
                sentiment_score=item.score,
                text=item.summary,
            )
            for ticker in self.tickers:
                self.pipeline.add_news(ticker, news)

    def _macro_adjustment(self, ticker: str) -> float:
        """Combine this ticker's direct mentions with the macro overlay."""
        if not self.macro_report:
            return 0.0
        direct = self.macro_report.tickers.get(ticker)
        direct_score = direct["score"] if direct else 0.0

        macro = self.macro_report.macro
        macro_scores = {
            factor: values.get("score", 0.0)
            for factor, values in macro.items()
        }
        profile = self.profile_registry.select(ticker)
        return profile.macro_adjustment(macro_scores, direct_score)

    def _add_market_data(self, ticker: str) -> None:
        price = self.adapter.get_price(ticker)
        if price is None:
            return
        self.pipeline.add_market_data(
            MarketData(
                ticker=ticker,
                price=price,
                timestamp=datetime.now(),
                vwap=price,
            )
        )

    def _add_news(self, ticker: str) -> None:
        for news_item in self.adapter.get_news(ticker, limit=3):
            self.pipeline.add_news(ticker, news_item)

        for macro_item in self.adapter.get_moneyweb_news(limit=5):
            if macro_item.ticker == "JSE":
                for market_ticker in self.tickers:
                    self.pipeline.add_news(market_ticker, macro_item)

    def _score_technical(self, obs) -> float:
        return legacy_technical_score(obs)

    def score_ticker(self, ticker: str) -> SignalDecision:
        self._add_market_data(ticker)
        self._add_news(ticker)

        obs = self.pipeline.get_observation(ticker)

        technical_score = self._score_technical(obs)
        sentiment_score = float(obs.news_sentiment_score)
        macro_adjustment = self._macro_adjustment(ticker)
        profile = self.profile_registry.select(ticker)

        combined = (0.60 * technical_score) + (0.30 * sentiment_score) + macro_adjustment

        if combined > 0.35:
            action = "buy"
        elif combined < -0.35:
            action = "sell"
        else:
            action = "hold"

        confidence = min(0.95, max(0.2, abs(combined) + 0.45))

        recent_prices = [float(value) for value in obs.recent_prices]
        try:
            regime = classify_regime(recent_prices) if len(recent_prices) >= 2 else None
        except ValueError:
            # Shadow context must never make the characterized legacy path fail.
            regime = None
        adaptive = self.adaptive_fusion.fuse(
            (
                AdaptiveFactor("legacy_technical", "technical", technical_score, 0.50),
                AdaptiveFactor("aggregate_sentiment", "sentiment", sentiment_score, 0.25),
                AdaptiveFactor(
                    "profile_macro", "macro",
                    macro_adjustment / 0.15 if macro_adjustment else 0.0,
                    0.25,
                ),
            ),
            legacy_score=round(combined, 2),
            legacy_action=action,
            profile=profile,
            regime=regime,
        )

        reason_parts = [
            f"price={obs.price:.2f}",
            f"sentiment={obs.news_sentiment.value}",
            f"rsi={obs.indicators.rsi if obs.indicators else 0.0:.1f}",
            f"sma={obs.indicators.sma_signal if obs.indicators else 0}",
            f"macro={macro_adjustment:+.2f}",
        ]

        return SignalDecision(
            ticker=ticker,
            action=action,
            confidence=round(confidence, 2),
            score=round(combined, 2),
            technical_score=round(technical_score, 2),
            sentiment_score=round(sentiment_score, 2),
            reason=" | ".join(reason_parts),
            metadata={
                "news": obs.news,
                "macro_factor": obs.macro_factor,
                "recent_prices": [round(x, 2) for x in obs.recent_prices[-10:]],
                "market_profile": {
                    "id": profile.profile_id,
                    "sector": profile.sector,
                    "instrument_type": profile.instrument_type,
                    "version": profile.version,
                    "shadow_only": profile.shadow_only,
                },
                "adaptive_shadow": adaptive.to_dict(),
            },
        )

    def scan_market(self) -> List[SignalDecision]:
        return [self.score_ticker(ticker) for ticker in self.tickers]
