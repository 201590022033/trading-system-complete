# merged_simulation.py - User Guide

## What It Does

This is the **heart of your trading system**. It combines:
- ✅ **Real market data** (from `data_pipeline.py`)
- ✅ **Multi-agent governance** (from rania321)
- ✅ **Risk management** (aggressive/neutral/conservative approval layers)
- ✅ **Clear decision pipeline** with confidence + risk labels

## Architecture Flow

```
MarketObservation (1 price point, news, indicators)
        ↓
    Research Layer (3 agents analyze independently)
    ├─ BullishResearcher
    ├─ BearishResearcher
    └─ GeneralResearchAgent
        ↓
    LLMTraderAgent (synthesizes research → proposes action + size)
        ↓
    RiskAgents (3 agents evaluate proposal)
    ├─ AggressiveRisk (allows up to 50% position)
    ├─ NeutralRisk (allows up to 25% position)
    └─ ConservativeRisk (allows up to 10% position)
        ↓
    ManagerAgent (majority vote: need 2/3 approvals, uses median sizing)
        ↓
    ExecutionAgent (updates portfolio if approved)
        ↓
    Output: Complete decision record for dashboard
```

---

## Basic Usage

### 1. Import and Initialize

```python
from data_pipeline import UnifiedDataPipeline, MarketData, NewsItem, SentimentLabel
from merged_simulation import MergedSimulation
from datetime import datetime

# Create data pipeline (where market data flows in)
pipeline = UnifiedDataPipeline(jse_tickers=["NPN", "SASOL", "BHP"])

# Create simulation (the multi-agent system)
sim = MergedSimulation(pipeline)
```

### 2. Feed Data

```python
# Add price data point
pipeline.add_market_data(MarketData(
    ticker="NPN",
    price=120.50,
    timestamp=datetime.now(),
    volume=1000000,
    vwap=120.45
))

# Add news (if available)
pipeline.add_news("NPN", NewsItem(
    ticker="NPN",
    headline="Naspers announces AI investment",
    source="Business Day",
    timestamp=datetime.now(),
    sentiment_label=SentimentLabel.BULLISH,
    sentiment_score=0.8,
    text="Strong positive development..."
))
```

### 3. Run One Trading Step

```python
# Execute one complete decision cycle
result = sim.step("NPN")

# Result is a dictionary with everything:
print(f"Price: {result['price']}")
print(f"Decision: {result['decision']['final_action']} {result['decision']['final_size']} units")
print(f"Confidence: {result['confidence_level']}")  # high/medium/low
print(f"Risk Level: {result['risk_level']}")        # aggressive/moderate/conservative
```

### 4. Loop It

```python
# Run continuously (60-second intervals typical)
import time

for i in range(100):  # 100 steps = ~1.67 hours at 60-second intervals
    # Get price from JSE API/WebSocket
    price = get_current_price("NPN")
    
    # Get news if available
    news_items = fetch_news("NPN")
    for news in news_items:
        pipeline.add_news("NPN", news)
    
    # Add price
    pipeline.add_market_data(MarketData("NPN", price, datetime.now(), vwap=price))
    
    # Run decision cycle
    result = sim.step("NPN")
    
    # Use result for dashboard, logging, etc.
    emit_to_dashboard(result)  # WebSocket push
    log_to_database(result)    # Store history
    
    time.sleep(60)  # Wait 60 seconds before next step
```

---

## Understanding the Output

When you call `sim.step(ticker)`, you get a comprehensive decision record:

```python
{
    "timestamp": "2026-08-29T14:35:42.123456",
    "ticker": "NPN",
    "price": 120.50,
    "recent_prices": [118.50, 119.20, 120.10, 120.50],  # Last 10
    
    # Market Context
    "news": "Naspers invests in AI; Strong momentum",
    "news_sentiment": "bullish",           # bullish/neutral/bearish
    "news_sentiment_score": 0.75,         # -1.0 to 1.0
    "macro_factor": "Commodity rally",     # Current macro driver
    "em_correlation": 0.65,                # Brazil market strength
    
    # Technical Indicators (for 50 price points)
    "indicators": {
        "rsi": 65.2,                       # 0-100 (30=oversold, 70=overbought)
        "rsi_signal": 0,                   # 1=buy, -1=sell, 0=hold
        "sma_signal": 1,                   # 1=bullish crossover, -1=bearish
        "breakout_signal": 0,              # 1=up breakout, -1=breakdown
        "stochastic": 78.5
    },
    
    # ========== RESEARCH LAYER ==========
    "research": {
        "bullish": {
            "stance": "bullish",
            "confidence": 0.85,            # 0-1 how sure about this stance
            "analysis": "Bullish case:\n• Positive news sentiment (0.75)..."
        },
        "bearish": {
            "stance": "neutral",
            "confidence": 0.10,
            "analysis": "Weak bearish signals..."
        },
        "general": {
            "stance": "bullish",
            "confidence": 0.80,
            "analysis": "Market analysis: Technical: SMA shows trend; Sentiment: bullish"
        }
    },
    
    # ========== TRADER PROPOSAL ==========
    "proposal": {
        "action": "buy",                   # buy/sell/hold
        "size": 2,                         # 0-3 shares
        "confidence": 0.85,                # Confidence in this proposal
        "rationale": "bullish, bullish, bullish research → BUY with size 2"
    },
    
    # ========== RISK ASSESSMENTS ==========
    "risk_assessments": [
        {
            "agent": "AggressiveRisk",
            "approved": True,
            "suggested_size": 3,
            "risk_level": "aggressive",
            "comment": "Aggressive: position (2.5%) acceptable"
        },
        {
            "agent": "NeutralRisk",
            "approved": True,
            "suggested_size": 2,
            "risk_level": "moderate",
            "comment": "Neutral: position (2.5%) acceptable"
        },
        {
            "agent": "ConservativeRisk",
            "approved": False,
            "suggested_size": 0,
            "risk_level": "conservative",
            "comment": "Conservative: position (2.5%) exceeds limit, REJECTED"
        }
    ],
    
    # ========== MANAGER DECISION ==========
    "decision": {
        "approved": True,                  # Final yes/no
        "final_action": "buy",            # What gets executed
        "final_size": 2,                  # Median of suggested sizes
        "confidence": 0.85,               # Confidence in decision
        "comment": "✓ APPROVED by 2/3 risk agents. Final size=2"
    },
    
    # ========== EXECUTION ==========
    "execution": {
        "success": True,
        "action_taken": "buy"             # "buy", "sell", "hold", or "none" (if failed)
    },
    
    # ========== DASHBOARD LABELS ==========
    "confidence_level": "high",           # high/medium/low
    "risk_level": "moderate",             # aggressive/moderate/conservative
    
    # ========== PORTFOLIO STATE ==========
    "portfolio": {
        "cash": 756.00,                   # Cash remaining
        "position": 2,                    # Shares held
        "average_cost": 122.00,           # Average entry price
        "value": 1012.00,                 # Total portfolio value
        "unrealized_pnl": 12.00,          # Unrealized gain/loss
        "unrealized_pnl_pct": 1.19        # As percentage
    }
}
```

---

## Key Concepts

### Confidence Level

- **HIGH** (>70%): Multiple research agents agree, strong signals
- **MEDIUM** (40-70%): Mixed signals, some agreement
- **LOW** (<40%): Weak signals, high uncertainty

→ Use this to size your capital allocation. High confidence = larger position.

### Risk Level

- **AGGRESSIVE**: Approved for sizes 1-3 (50% portfolio max per position)
- **MODERATE**: Approved for sizes 1-2 (25% portfolio max per position)
- **CONSERVATIVE**: Approved for size 1 only (10% portfolio max per position)

→ This reflects how conservative the risk agents collectively are.

### The Three Research Agents

1. **BullishResearcher**: Looks for reasons to BUY
   - Positive sentiment, upward price trend, bullish technical signals
   
2. **BearishResearcher**: Looks for reasons to SELL
   - Negative sentiment, downward price trend, bearish technical signals
   
3. **GeneralResearchAgent**: Balanced view
   - Weights all factors equally, provides neutral perspective

→ If all 3 agree (all bullish/bearish), confidence is very high.

### The Three Risk Agents

1. **AggressiveRisk**: "Let it run" - allows up to 50% of portfolio
2. **NeutralRisk**: "Balanced" - allows up to 25% of portfolio
3. **ConservativeRisk**: "Protect capital" - allows up to 10% of portfolio

→ Manager needs 2/3 approval. If conservative agent rejects but others approve, trade goes ahead (but sized down).

---

## Real-World Example

**Scenario**: Naspers (NPN) announcement + bullish market

```
Step 1: Add price €120.50
Step 2: Add news "Naspers AI investment"
Step 3: Run sim.step("NPN")

OUTPUT:
├─ Bullish researcher: "Positive news, price up, SMA bullish" → confidence 85%
├─ Bearish researcher: "Nothing bearish visible" → confidence 10%
├─ General researcher: "Bullish market analysis" → confidence 80%
│
├─ Trader synthesizes: "Bullish, bullish, bullish → BUY size 2" (85% confidence)
│
├─ Aggressive risk: "25% position? OK, approved" → size 3
├─ Neutral risk: "25% position? OK, approved" → size 2
├─ Conservative risk: "25% position? Too big, REJECT" → size 0
│
├─ Manager: "2/3 approve, median size = 2, execute BUY"
│
└─ Executor: "Buying 2 units @ €120.50" ✓ SUCCESS
   Portfolio: €1000 cash → €759 cash + 2 NPN @ €120.50

DASHBOARD LABELS:
- Confidence: HIGH (85%)
- Risk Level: MODERATE (2/3 approved, but conservative voted no)
```

---

## Testing the System

### Test 1: Run the demo

```bash
cd /home/claude
python merged_simulation.py
```

This runs 10 mock trading steps and prints the output.

### Test 2: Test with different market conditions

```python
from merged_simulation import MergedSimulation
from data_pipeline import UnifiedDataPipeline, MockDataGenerator, MarketData, NewsItem, SentimentLabel

pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
sim = MergedSimulation(pipeline)
gen = MockDataGenerator(base_price=120.0)

# Simulate bullish run
print("=== BULLISH SCENARIO ===")
for i in range(20):
    price = gen.next_price()
    pipeline.add_market_data(MarketData("NPN", price, datetime.now(), vwap=price))
    
    if i % 5 == 0:
        news = gen.generate_news("NPN", trend="bullish")
        pipeline.add_news("NPN", news)
    
    result = sim.step("NPN")
    if result['decision']['approved']:
        print(f"Step {i+1}: {result['decision']['final_action'].upper()} {result['decision']['final_size']} "
              f"(conf={result['confidence_level']}, risk={result['risk_level']})")
```

### Test 3: Test risk management

```python
# Verify that position sizing respects risk limits
pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
sim = MergedSimulation(pipeline)

# Force a large proposal
sim.llm_trader.portfolio.cash = 1000.0

# Manually create a large proposal and run risk assessment
large_proposal = TradeProposal(action="buy", size=10, rationale="Test", confidence=0.9)
assessments = [r.evaluate(large_proposal, sim.llm_trader.portfolio, 100.0) for r in sim.risk_team]

# Verify conservative agent rejects it
assert assessments[2].approved == False  # Conservative should reject 1000% position
print("✓ Risk management working: Conservative agent correctly rejected oversized position")
```

---

## Integration Points

### With Flask Dashboard

```python
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
sim = MergedSimulation(pipeline)

@socketio.on('start_trading')
def start_trading():
    for i in range(1000):  # Run indefinitely
        # Fetch real price
        price = get_jse_price("NPN")
        pipeline.add_market_data(MarketData("NPN", price, datetime.now()))
        
        # Run step
        result = sim.step("NPN")
        
        # Emit to connected browsers
        socketio.emit('trading_update', result)
        socketio.sleep(60)
```

### With MT5 Execution

```python
# After decision is made:
if result['decision']['approved']:
    order = convert_to_mt5_order(result)
    mt5_executor.place_order(order)
    print(f"Placed {order.action} order for {order.volume} units")
```

### With Logging

```python
import json

# Log every step
with open('trading_log.jsonl', 'a') as f:
    f.write(json.dumps(result) + '\n')

# Later: analyze what happened
import pandas as pd
df = pd.read_json('trading_log.jsonl', lines=True)
print(df[['price', 'decision.final_action', 'confidence_level', 'portfolio.value']])
```

---

## Next: Integration with Dashboard

Once merged_simulation.py is tested, you can:

1. **Use it in Flask app** to provide live trading signals
2. **Connect to MT5** for paper trading
3. **Build dashboard** to visualize decisions
4. **Add JSE data adapter** to use real prices instead of mock

The architecture is complete—you just need to plug in real data sources!

---

## Troubleshooting

**Q: All proposals are HOLD. Why?**
A: Not enough data points. Technical indicators need ~50 price points to generate signals. Run for longer, or feed historical data first.

**Q: Aggressive risk always approves but conservative rejects?**
A: Correct behavior. That's why the manager exists—to balance perspectives. This is why we need 2/3 approval.

**Q: Position sizes are too small?**
A: Adjust `TradeProposal.size` generation logic in `LLMTraderAgent.propose_trade()`. Currently capped at 0-3.

**Q: Why is portfolio value decreasing?**
A: If you're selling at a loss, or trading costs (not implemented yet). Check `portfolio.average_cost` vs current price.

**Q: How do I test with real JSE data?**
A: Next step—build `jse_adapter.py` to pull real prices from Yahoo Finance or JSE API.

---

## Files Summary

| File | Purpose |
|------|---------|
| `data_pipeline.py` | Data ingestion + buffering + signal generation |
| `merged_simulation.py` | Multi-agent decision system (use this!) |
| `merged_simulation.py:MergedSimulation.step()` | Core method—run once per price tick |
| Flask app (next) | Web UI + Socket.IO for live updates |
| `jse_adapter.py` (next) | Real JSE data source |

You're ready to build!
