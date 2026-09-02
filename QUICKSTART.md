# Merged Trading System - Quick Start Guide

## What You Now Have

You've got **two complete trading systems** that we're merging:

1. **rania321**: Excellent governance + UI (simulated data)
2. **Ronitt272**: Real data + sentiment analysis (no UI/governance)

**Result**: A unified system combining the best of both, tailored for South Africa.

---

## Files Created for You

### 1. **MERGER_STRATEGY.md**
Complete analysis of both systems and how to integrate them step-by-step.

**Contains:**
- Side-by-side comparison of both architectures
- What to keep/change from each
- Detailed data flow examples
- Phase-by-phase integration checklist

**Read this first** to understand the big picture.

---

### 2. **data_pipeline.py**
Unified data ingestion module (Phase 1 of integration).

**Provides:**
- `UnifiedDataPipeline`: Main class that orchestrates data
- `SignalGenerator`: Technical indicators (SMA, RSI, Breakout, Stochastic)
- `SentimentAggregator`: News sentiment aggregation
- `MarketObservation`: Clean data structure for multi-agent system
- `MockDataGenerator`: For testing without real APIs

**Example Usage:**
```python
from data_pipeline import UnifiedDataPipeline, MarketData, NewsItem, SentimentLabel
from datetime import datetime

# Initialize pipeline
pipeline = UnifiedDataPipeline(jse_tickers=["NPN", "SASOL", "BHP"])

# Add price data
market_data = MarketData(
    ticker="NPN",
    price=120.50,
    timestamp=datetime.now(),
    volume=1000000,
    vwap=120.45
)
pipeline.add_market_data(market_data)

# Add news sentiment
from data_pipeline import NewsItem, SentimentLabel
news = NewsItem(
    ticker="NPN",
    headline="Naspers invests in AI",
    source="Business Day",
    timestamp=datetime.now(),
    sentiment_label=SentimentLabel.BULLISH,
    sentiment_score=0.8,
    text="Positive moves in tech sector..."
)
pipeline.add_news("NPN", news)

# Get complete market observation (what the multi-agent system uses)
obs = pipeline.get_observation("NPN")
print(obs)
# Output: MarketObservation(
#   ticker='NPN',
#   price=120.50,
#   recent_prices=[...],
#   news="Naspers invests in AI",
#   news_sentiment=SentimentLabel.BULLISH,
#   news_sentiment_score=0.8,
#   indicators=TechnicalIndicators(rsi=52, sma_signal=1, ...),
#   emerging_market_correlation=0.65
# )
```

---

## Integration Steps (Recommended Order)

### Step 1: Get data_pipeline working
```bash
# Test the data pipeline
python -c "
from data_pipeline import UnifiedDataPipeline, MockDataGenerator
import time

pipeline = UnifiedDataPipeline(jse_tickers=['NPN'])
gen = MockDataGenerator(base_price=120.0)

# Simulate 50 price points
for i in range(50):
    from data_pipeline import MarketData
    from datetime import datetime
    price = gen.next_price()
    pipeline.add_market_data(MarketData('NPN', price, datetime.now(), vwap=price))
    
    # Add occasional news
    if i % 10 == 0:
        news = gen.generate_news('NPN', trend=['bullish', 'bearish', 'neutral'][i % 3])
        pipeline.add_news('NPN', news)

# Get observation
obs = pipeline.get_observation('NPN')
print(f'Price: {obs.price}')
print(f'News sentiment: {obs.news_sentiment}')
print(f'RSI: {obs.indicators.rsi:.1f}')
print(f'SMA Signal: {obs.indicators.sma_signal}')
"
```

### Step 2: Extract & adapt rania321's multi-agent system

**From rania321's `simulation.py`, keep:**
- `BullishResearcher`
- `BearishResearcher`
- `GeneralResearchAgent` (LLM-based)
- `LLMTraderAgent` (proposes trades)
- `RiskAgent` (aggressive/neutral/conservative)
- `ManagerAgent` (majority vote)
- `ExecutionAgent` (executes trades)

**Modify to use real data:**
```python
# Replace this (rania321):
obs = self.market.get_obs()  # Simulated data

# With this:
obs = pipeline.get_observation("NPN")  # Real data from data_pipeline

# The rest of the agent logic stays the same!
```

### Step 3: Build merged_simulation.py

Create new file that:
1. Imports rania321's agents (with modifications for real data)
2. Uses `UnifiedDataPipeline` for data
3. Keeps the governance layer intact
4. Outputs signal + confidence + risk labels

**Structure:**
```python
from data_pipeline import UnifiedDataPipeline
from agents import BullishResearcher, BearishResearcher, GeneralResearchAgent, LLMTraderAgent
from risk import RiskAgent, ManagerAgent, ExecutionAgent

class MergedSimulation:
    def __init__(self):
        self.pipeline = UnifiedDataPipeline(jse_tickers=["NPN", "SASOL"])
        self.researchers = [...]  # From rania321
        self.risk_team = [...]    # From rania321
        
    def step(self, ticker: str):
        # Get real data
        obs = self.pipeline.get_observation(ticker)
        
        # Run agent pipeline (from rania321)
        proposal = self.llm_trader.propose_trade(obs, ...)
        assessments = self.risk_team.evaluate(proposal, ...)
        decision = self.manager.decide(proposal, assessments)
        
        # Execute
        self.pipeline.update_portfolio(decision.action, decision.size, obs.price)
        
        return {
            "price": obs.price,
            "signal": decision,
            "confidence": calculate_confidence(assessments),
            "risk_label": calculate_risk_level(assessments)
        }
```

### Step 4: Update Flask app

Replace rania321's `simulation()` with real data:

```python
# Before (rania321):
sim = Simulation()
for step in range(30):
    data = sim.step()  # Simulated

# After (merged):
pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
merged_sim = MergedSimulation(pipeline)
while True:
    obs = pipeline.get_observation("NPN")  # Real data
    data = merged_sim.step("NPN")
    socketio.emit("update", data)
    sleep(60)  # Update every minute
```

### Step 5: Add JSE data source

Create `jse_adapter.py`:
```python
class JSEDataAdapter:
    """Fetch real JSE data"""
    
    def __init__(self):
        # Option 1: Use Yahoo Finance (yfinance library)
        # Option 2: Use JSE API directly
        # Option 3: Use newsapi for SA news sources
        pass
    
    def get_price(self, ticker: str) -> float:
        """Fetch current JSE price"""
        pass
    
    def get_news(self, ticker: str) -> List[NewsItem]:
        """Fetch SA news for ticker"""
        pass
```

### Step 6: Add emerging market correlation

Create `emerging_market_analysis.py`:
```python
class EmergingMarketAnalysis:
    """Track Brazil/SA correlations"""
    
    def __init__(self):
        self.brazil_data = []  # Brazil commodity prices
        self.sa_data = []      # SA mining stocks
    
    def calculate_correlation(self) -> float:
        """Brazilian commodity rally → SA mining stock strength"""
        pass
    
    def get_em_signal(self) -> str:
        """'tailwind', 'headwind', or 'neutral'"""
        pass
```

---

## Your Current Architecture (After Merge)

```
Market Data (Real)
    ↓
data_pipeline.py (UnifiedDataPipeline)
    ├── Price buffer (SMA, RSI, Breakout)
    ├── News aggregator (sentiment scores)
    └── EM correlation (Brazil → SA)
         ↓
merged_simulation.py (Multi-agent governance)
    ├── Research agents (bullish/bearish/general)
    ├── LLM trader (proposes action + size)
    ├── Risk agents (aggressive/neutral/conservative)
    ├── Manager (approval logic)
    └── Executor (portfolio updates)
         ↓
Flask + Socket.IO (Real-time dashboard)
    ├── Live price chart
    ├── Sentiment panel
    ├── Signal + Confidence labels
    ├── Risk assessment display
    └── Portfolio tracking
         ↓
Trading Execution
    ├── MT5 connector (paper trading first)
    └── Standard Bank API (when ready)
```

---

## Testing Workflow

### 1. Test data_pipeline alone
```bash
python test_data_pipeline.py
# Should show: prices, indicators, sentiment, portfolio state
```

### 2. Test merged_simulation with mock data
```bash
python test_merged_simulation.py
# Should show: agent decisions, risk assessments, final execution
```

### 3. Test Flask app locally
```bash
python app.py
# Open http://127.0.0.1:5000
# Should show: live dashboard with real decisions
```

### 4. Paper trade on MT5
- Don't risk real capital yet
- Run for 2-4 weeks
- Track accuracy vs. confidence labels

### 5. Deploy with small real capital
- Start with 1000 rand
- Size positions conservatively
- Monitor daily

---

## What's Next?

**I can help you build:**

1. **merged_simulation.py** — Integrate rania321's agents with data_pipeline
2. **jse_adapter.py** — Pull real JSE data
3. **emerging_market_analysis.py** — Brazil/SA correlation tracking
4. **execution_connector.py** — Connect to MT5 + Standard Bank
5. **Enhanced dashboard** — Real-time live updates

**Which would you like to tackle first?**

---

## Key Differences from Originals

| Feature | rania321 | Ronitt272 | **Merged** |
|---------|----------|-----------|-----------|
| UI | ✅ Beautiful | ❌ Basic HTML | ✅ Real-time dashboard |
| Governance | ✅ Risk agents + Manager | ❌ None | ✅ Full approval layer |
| Real Data | ❌ Simulated | ✅ Live feeds | ✅ JSE + emerging markets |
| Sentiment | ❌ Basic | ✅ LLM-based | ✅ Multi-source, aggregated |
| Technical Indicators | ❌ None | ✅ SMA, RSI, etc. | ✅ All indicators |
| South Africa focus | ❌ Generic | ❌ US-only | ✅ JSE + EM optimized |
| Portfolio Management | ✅ Tracking | ✅ Tracking | ✅ Enhanced tracking + PnL |
| Execution API | ❌ None | ❌ None | ✅ MT5 + Standard Bank |

---

## Files Reference

### From rania321 (Keep These)
- `simulation.py` → extract agent classes
- `agents.py` → classic traders (optional)
- `llm_module.py` → adapt for Claude/Ollama
- `templates/dashboard.html` → enhance
- `static/` → keep CSS/JS, enhance with new features

### From Ronitt272 (Adapted)
- `TextFetchPipeline.py` → adapt for SA news sources
- `LiveStockPricePipeline.py` → replace with JSE adapter
- `SignalGenerator.py` → integrated into data_pipeline.py
- Main logic → keep for reference

### New Files (Created)
- `data_pipeline.py` ← **USE THIS**
- `merged_simulation.py` ← Next to build
- `jse_adapter.py` ← Need to create
- `emerging_market_analysis.py` ← Need to create
- `execution_connector.py` ← Need to create

---

## Resources

- **JSE Data**: Yahoo Finance (yfinance) or JSE API documentation
- **South African News**: NewsAPI, Reuters, Business Day, FT
- **Sentiment Models**: OpenAI API, HuggingFace FinGPT, Claude API
- **MT5**: MetaTrader 5 Python library
- **Standard Bank**: REST API documentation

Ready? Let me know which module you want to build next.
