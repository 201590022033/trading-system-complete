"""
Unified Data Pipeline Module
Merges real-time price data, news sentiment, and technical indicators
Designed for JSE + Emerging Market analysis
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import deque
import numpy as np
from enum import Enum


class DataSource(Enum):
    """Supported data sources"""
    FINNHUB = "finnhub"  # US stocks
    JSE = "jse"  # Johannesburg Stock Exchange
    YAHOO = "yahoo"  # Yahoo Finance
    MOCK = "mock"  # For testing


class SentimentLabel(Enum):
    """Sentiment classification"""
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


@dataclass
class MarketData:
    """Single market data point"""
    ticker: str
    price: float
    timestamp: datetime
    volume: int = 0
    vwap: float = 0.0


@dataclass
class NewsItem:
    """News article with sentiment"""
    ticker: str
    headline: str
    source: str
    timestamp: datetime
    sentiment_label: SentimentLabel
    sentiment_score: float  # -1.0 to 1.0
    text: str = ""
    url: str = ""
    timestamp_kind: str = "published"


@dataclass
class TechnicalIndicators:
    """Technical analysis signals"""
    rsi: float  # 0-100
    rsi_signal: int  # 1=buy (oversold), -1=sell (overbought), 0=hold
    
    sma_fast: float
    sma_slow: float
    sma_signal: int  # 1=buy (fast>slow crossover), -1=sell, 0=hold
    
    breakout_signal: int  # 1=breakout up, -1=breakdown, 0=none
    stochastic_oscillator: float  # 0-100
    stochastic_signal: int  # 1=buy, -1=sell, 0=hold


@dataclass
class MarketObservation:
    """Complete market observation for one timestamp"""
    ticker: str
    price: float
    recent_prices: List[float] = field(default_factory=list)  # Last 40 prices
    news: str = ""  # Summary of recent news
    news_sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    news_sentiment_score: float = 0.0
    indicators: Optional[TechnicalIndicators] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Emerging market context (for SA)
    emerging_market_correlation: float = 0.0  # -1 to 1, e.g., Brazil → SA correlation
    macro_factor: str = ""  # e.g., "commodity rally", "rand weakness"
    intelligence_context: Dict = field(default_factory=dict)  # research/shadow explanations


@dataclass
class PortfolioData:
    """Portfolio state"""
    cash: float
    position: int  # shares held
    average_cost: float = 0.0
    
    def value(self, current_price: float) -> float:
        return self.cash + self.position * current_price
    
    def unrealized_pnl(self, current_price: float) -> float:
        if self.position == 0:
            return 0.0
        return (current_price - self.average_cost) * self.position


class DataBuffer:
    """Sliding window buffer for time-series data"""
    
    def __init__(self, max_size: int = 100):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size
    
    def add(self, value: float) -> None:
        self.buffer.append(value)
    
    def get_array(self) -> np.ndarray:
        return np.array(list(self.buffer))
    
    def get_last_n(self, n: int) -> List[float]:
        return list(self.buffer)[-n:]
    
    def is_ready(self, required_size: int) -> bool:
        return len(self.buffer) >= required_size


class SignalGenerator:
    """Generate technical trading signals from price data"""
    
    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self.vwap_buffers: Dict[str, DataBuffer] = {}
    
    def add_vwap(self, ticker: str, vwap: float) -> None:
        """Add VWAP data point"""
        if ticker not in self.vwap_buffers:
            self.vwap_buffers[ticker] = DataBuffer(self.buffer_size)
        self.vwap_buffers[ticker].add(vwap)
    
    def calculate_sma_signal(
        self,
        ticker: str,
        fast_period: int = 5,
        slow_period: int = 20
    ) -> Tuple[float, float, int]:
        """
        Calculate SMA trend signal
        Returns: (fast_sma, slow_sma, signal)
        signal: 1=buy (fast>slow, uptrend), -1=sell (fast<slow, downtrend), 0=flat

        Note: previously this only fired on the exact crossover bar, which meant
        it returned 0 almost all the time. Trend-following is more useful for
        continuous confidence scoring.
        """
        if ticker not in self.vwap_buffers:
            return 0.0, 0.0, 0

        prices = self.vwap_buffers[ticker].get_array()
        if len(prices) < slow_period:
            return 0.0, 0.0, 0

        fast_sma = np.mean(prices[-fast_period:])
        slow_sma = np.mean(prices[-slow_period:])

        # Trend signal: fast above slow = uptrend, below = downtrend.
        # Small deadband (0.1%) to avoid flip-flopping when SMAs are equal.
        diff_pct = (fast_sma - slow_sma) / slow_sma if slow_sma else 0.0
        if diff_pct > 0.001:
            signal = 1
        elif diff_pct < -0.001:
            signal = -1
        else:
            signal = 0

        return fast_sma, slow_sma, signal
    
    def calculate_rsi_signal(
        self,
        ticker: str,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0
    ) -> Tuple[float, int]:
        """
        Calculate RSI and signal
        Returns: (rsi_value, signal)
        signal: 1=oversold buy, -1=overbought sell, 0=hold
        """
        if ticker not in self.vwap_buffers:
            return 0.0, 0
        
        prices = self.vwap_buffers[ticker].get_array()
        if len(prices) < period + 1:
            return 0.0, 0
        
        deltas = np.diff(prices[-period - 1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        
        signal = 0
        if rsi < oversold:
            signal = 1  # Oversold, buy
        elif rsi > overbought:
            signal = -1  # Overbought, sell
        
        return rsi, signal
    
    def calculate_breakout_signal(
        self,
        ticker: str,
        lookback: int = 20
    ) -> int:
        """
        Detect price breakout/breakdown
        signal: 1=breakout up, -1=breakdown, 0=none
        """
        if ticker not in self.vwap_buffers:
            return 0
        
        prices = self.vwap_buffers[ticker].get_array()
        if len(prices) < lookback:
            return 0
        
        recent = prices[-lookback:]
        high = np.max(recent[:-1])
        low = np.min(recent[:-1])
        current = recent[-1]
        
        if current > high:
            return 1  # Breakout
        elif current < low:
            return -1  # Breakdown
        return 0
    
    def generate_indicators(self, ticker: str) -> Optional[TechnicalIndicators]:
        """Generate all technical indicators for a ticker"""
        if ticker not in self.vwap_buffers:
            return None
        
        rsi, rsi_signal = self.calculate_rsi_signal(ticker)
        sma_fast, sma_slow, sma_signal = self.calculate_sma_signal(ticker)
        breakout_signal = self.calculate_breakout_signal(ticker)
        
        # Stochastic (simplified)
        prices = self.vwap_buffers[ticker].get_array()
        if len(prices) >= 14:
            high = np.max(prices[-14:])
            low = np.min(prices[-14:])
            close = prices[-1]
            if high - low == 0:
                stochastic = 50.0
            else:
                stochastic = 100.0 * (close - low) / (high - low)
            stochastic_signal = 1 if stochastic < 20 else (-1 if stochastic > 80 else 0)
        else:
            stochastic = 0.0
            stochastic_signal = 0
        
        return TechnicalIndicators(
            rsi=rsi,
            rsi_signal=rsi_signal,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
            sma_signal=sma_signal,
            breakout_signal=breakout_signal,
            stochastic_oscillator=stochastic,
            stochastic_signal=stochastic_signal
        )


class SentimentAggregator:
    """Aggregate sentiment from multiple news sources"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.news_buffer: Dict[str, deque] = {}
    
    def add_news(self, ticker: str, news_item: NewsItem) -> None:
        """Add a news item"""
        if ticker not in self.news_buffer:
            self.news_buffer[ticker] = deque(maxlen=self.window_size)
        self.news_buffer[ticker].append(news_item)
    
    def get_aggregated_sentiment(self, ticker: str) -> Tuple[SentimentLabel, float, str]:
        """
        Get aggregate sentiment for ticker
        Returns: (sentiment_label, score, summary_text)
        """
        if ticker not in self.news_buffer or len(self.news_buffer[ticker]) == 0:
            return SentimentLabel.NEUTRAL, 0.0, "No recent news"
        
        items = list(self.news_buffer[ticker])
        scores = [item.sentiment_score for item in items]
        avg_score = np.mean(scores)
        
        # Classify
        if avg_score > 0.2:
            label = SentimentLabel.BULLISH
        elif avg_score < -0.2:
            label = SentimentLabel.BEARISH
        else:
            label = SentimentLabel.NEUTRAL
        
        # Summary
        recent_headlines = "; ".join([f"'{item.headline}'" for item in items[-3:]])
        
        return label, avg_score, recent_headlines


class UnifiedDataPipeline:
    """
    Main data pipeline orchestrating all data sources
    
    Usage:
        pipeline = UnifiedDataPipeline(data_source=DataSource.MOCK)
        obs = pipeline.get_observation("NPN")  # JSE Naspers
    """
    
    def __init__(
        self,
        data_source: DataSource = DataSource.MOCK,
        jse_tickers: Optional[List[str]] = None,
        buffer_size: int = 100
    ):
        self.data_source = data_source
        self.jse_tickers = jse_tickers or ["NPN", "SASOL", "BHP", "IMPJ"]
        
        self.signal_generator = SignalGenerator(buffer_size)
        self.sentiment_aggregator = SentimentAggregator()
        
        # Price buffers
        self.price_buffers: Dict[str, DataBuffer] = {
            ticker: DataBuffer(buffer_size) for ticker in self.jse_tickers
        }
        
        # Portfolio state
        self.portfolio = PortfolioData(cash=1000.0, position=0)
    
    def add_market_data(self, market_data: MarketData) -> None:
        """Ingest market data point"""
        ticker = market_data.ticker
        if ticker not in self.price_buffers:
            self.price_buffers[ticker] = DataBuffer(100)
        
        self.price_buffers[ticker].add(market_data.price)
        self.signal_generator.add_vwap(ticker, market_data.vwap or market_data.price)
    
    def add_news(self, ticker: str, news_item: NewsItem) -> None:
        """Ingest news sentiment"""
        self.sentiment_aggregator.add_news(ticker, news_item)
    
    def get_observation(
        self,
        ticker: str,
        include_emerging_market_context: bool = False
    ) -> MarketObservation:
        """
        Build complete market observation for a ticker
        This is what the multi-agent system uses for decisions
        """
        if ticker not in self.price_buffers:
            raise ValueError(f"Ticker {ticker} not in pipeline")
        
        price_buffer = self.price_buffers[ticker]
        prices = price_buffer.get_array()
        
        if len(prices) == 0:
            current_price = 0.0
            recent_prices = []
        else:
            current_price = float(prices[-1])
            recent_prices = list(prices)[-40:]
        
        # Get sentiment
        sentiment_label, sentiment_score, news_text = \
            self.sentiment_aggregator.get_aggregated_sentiment(ticker)
        
        # Get technical indicators
        indicators = self.signal_generator.generate_indicators(ticker)
        
        # Emerging market context (placeholder for now)
        em_correlation = 0.0
        macro_factor = ""
        if include_emerging_market_context:
            # In phase 2, this will pull Brazil market data
            em_correlation = np.random.uniform(-1, 1)  # Mock
            macro_factor = "Commodity prices + ZAR weakness"
        
        return MarketObservation(
            ticker=ticker,
            price=current_price,
            recent_prices=recent_prices,
            news=news_text,
            news_sentiment=sentiment_label,
            news_sentiment_score=sentiment_score,
            indicators=indicators,
            timestamp=datetime.now(),
            emerging_market_correlation=em_correlation,
            macro_factor=macro_factor
        )
    
    def update_portfolio(
        self,
        action: str,  # "buy", "sell", "hold"
        size: int,  # number of shares
        current_price: float
    ) -> bool:
        """Execute trade on portfolio"""
        if action == "buy":
            cost = size * current_price
            if self.portfolio.cash >= cost:
                self.portfolio.cash -= cost
                avg_cost = (
                    (self.portfolio.average_cost * self.portfolio.position + cost) /
                    (self.portfolio.position + size)
                )
                self.portfolio.position += size
                self.portfolio.average_cost = avg_cost
                return True
            return False
        
        elif action == "sell":
            if self.portfolio.position >= size:
                proceeds = size * current_price
                self.portfolio.cash += proceeds
                self.portfolio.position -= size
                return True
            return False
        
        elif action == "hold":
            return True
        
        return False
    
    def get_portfolio_state(self, current_price: float) -> Dict:
        """Get current portfolio state"""
        return {
            "cash": round(self.portfolio.cash, 2),
            "position": self.portfolio.position,
            "average_cost": round(self.portfolio.average_cost, 2),
            "value": round(self.portfolio.value(current_price), 2),
            "unrealized_pnl": round(self.portfolio.unrealized_pnl(current_price), 2),
            "unrealized_pnl_pct": round(
                (self.portfolio.unrealized_pnl(current_price) / 
                 (self.portfolio.position * self.portfolio.average_cost) * 100)
                if self.portfolio.position > 0 else 0, 2
            )
        }


# Mock data generator for testing
class MockDataGenerator:
    """Generate realistic mock market data for testing"""
    
    def __init__(self, base_price: float = 120.0, volatility: float = 0.02):
        self.price = base_price
        self.volatility = volatility
    
    def next_price(self) -> float:
        """Generate next realistic price"""
        change = np.random.normal(0, self.volatility)
        self.price *= (1 + change)
        return self.price
    
    def generate_news(self, ticker: str, trend: str = "neutral") -> NewsItem:
        """Generate mock news"""
        sentiments = {
            "bullish": ("strong", 0.7, SentimentLabel.BULLISH),
            "bearish": ("weak", -0.7, SentimentLabel.BEARISH),
            "neutral": ("stable", 0.0, SentimentLabel.NEUTRAL)
        }
        
        adjective, score, label = sentiments.get(trend, sentiments["neutral"])
        headlines = [
            f"{ticker} shows {adjective} earnings",
            f"Analyst upgrades {ticker} outlook",
            f"{ticker} navigates market volatility"
        ]
        
        return NewsItem(
            ticker=ticker,
            headline=np.random.choice(headlines),
            source="Mock News",
            timestamp=datetime.now(),
            sentiment_label=label,
            sentiment_score=score
        )
