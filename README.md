# Integrated Trading System - South Africa Edition

**A complete multi-agent trading system for the JSE (Johannesburg Stock Exchange) combining:**
- **Option A**: Multi-agent governance + decision system
- **Option B**: Real JSE data adapter with news sentiment

## Quick Start

```bash
# 1. Extract the ZIP
unzip trading-system.zip
cd trading-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the example
python main.py
```

That's it! The system will:
1. ✅ Load historical JSE data (mock by default)
2. ✅ Warm up technical indicators (SMA, RSI, Breakout)
3. ✅ Run multi-agent decision system
4. ✅ Generate trading signals with confidence & risk labels
5. ✅ Save all decisions to a log file

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Real Market Data (JSE, News, Emerging Markets)         │
│         [jse_adapter.py]                                │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  Unified Data Pipeline                                  │
│  [data_pipeline.py]                                     │
│  • Price buffering & SMA/RSI/Breakout indicators        │
│  • News sentiment aggregation                           │
│  • Emerging market correlation tracking                 │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  Multi-Agent Decision System [merged_simulation.py]     │
│                                                         │
│  Research Layer:                                        │
│  • Bullish Researcher (looks for buy signals)           │
│  • Bearish Researcher (looks for sell signals)          │
│  • General Researcher (LLM-based balanced view)         │
│                                                         │
│  Synthesis Layer:                                       │
│  • LLM Trader (proposes action + size + confidence)     │
│                                                         │
│  Governance Layer:                                      │
│  • Aggressive Risk Agent (allows 50% positions)         │
│  • Neutral Risk Agent (allows 25% positions)            │
│  • Conservative Risk Agent (allows 10% positions)       │
│  • Manager Agent (2/3 approval, median sizing)          │
│  • Execution Agent (updates portfolio)                  │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  Dashboard + Execution                                  │
│  • High/Medium/Low confidence labels                    │
│  • Aggressive/Moderate/Conservative risk levels         │
│  • Portfolio P&L tracking                               │
│  • (Future) MT5 & Standard Bank integration             │
└─────────────────────────────────────────────────────────┘
```

---

## File Guide

| File | Purpose |
|------|---------|
| `main.py` | **Start here** - Integration examples & quick start |
| `data_pipeline.py` | Core data handling: prices, sentiment, indicators |
| `merged_simulation.py` | Multi-agent decision system (Option A) |
| `jse_adapter.py` | Real JSE data source (Option B) |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## How to Use

### Option 1: Quick Test (Mock Data)

```python
from main import IntegratedTradingSystem

# Create system with mock data
system = IntegratedTradingSystem(
    jse_tickers=["NPN", "SASOL"],
    use_real_data=False  # No API keys needed
)

# Warm up technical indicators
system.warmup_indicators("NPN", days=30)

# Run one trading step
decision = system.step("NPN")

# Check the decision
print(f"Action: {decision['decision']['final_action']}")
print(f"Confidence: {decision['confidence_level']}")
print(f"Risk Level: {decision['risk_level']}")
```

### Option 2: Real JSE Data

```python
from main import IntegratedTradingSystem

# Create system with real Yahoo Finance data
system = IntegratedTradingSystem(
    jse_tickers=["NPN"],
    use_real_data=True  # Fetches real JSE prices
)

system.warmup_indicators("NPN")

# Get live decision
decision = system.step("NPN")
```

### Option 3: Live Trading Loop

```python
from main import IntegratedTradingSystem

system = IntegratedTradingSystem(
    jse_tickers=["NPN", "SASOL", "BHP"],
    use_real_data=True
)

# Warm up
for ticker in system.jse_tickers:
    system.warmup_indicators(ticker, days=30)

# Run live (fetches new price every 60 seconds)
system.run_live(duration_minutes=60, interval_seconds=60)

# Later: check performance
summary = system.get_performance_summary()
print(f"Total P&L: {summary['total_pnl_pct']}")
```

---

## Understanding the Output

When you run a trading step, you get a comprehensive decision record:

```python
decision = {
    "timestamp": "2026-08-29T14:35:42",
    "ticker": "NPN",
    "price": 120.50,
    
    # Market Context
    "news_sentiment": "bullish",
    "news_sentiment_score": 0.75,
    "indicators": {
        "rsi": 65.2,           # RSI > 70 is overbought
        "rsi_signal": 0,       # 1=oversold buy, -1=overbought sell
        "sma_signal": 1,       # 1=bullish crossover
        "breakout_signal": 0   # Price breakout/breakdown
    },
    
    # Research Phase
    "research": {
        "bullish": {
            "stance": "bullish",
            "confidence": 0.85,
            "analysis": "Bullish case: Positive sentiment, price up, SMA bullish..."
        },
        "bearish": {
            "stance": "neutral",
            "confidence": 0.10,
            "analysis": "Weak bearish signals..."
        },
        "general": {
            "stance": "bullish",
            "confidence": 0.80,
            "analysis": "Market analysis: Technical shows trend..."
        }
    },
    
    # Trader Proposal
    "proposal": {
        "action": "buy",
        "size": 2,
        "confidence": 0.85
    },
    
    # Risk Governance
    "risk_assessments": [
        {
            "agent": "AggressiveRisk",
            "approved": True,
            "suggested_size": 3,
            "risk_level": "aggressive"
        },
        {
            "agent": "NeutralRisk",
            "approved": True,
            "suggested_size": 2,
            "risk_level": "moderate"
        },
        {
            "agent": "ConservativeRisk",
            "approved": False,
            "suggested_size": 0,
            "risk_level": "conservative"
        }
    ],
    
    # Manager Decision
    "decision": {
        "approved": True,
        "final_action": "buy",
        "final_size": 2,  # Median of suggested sizes
        "confidence": 0.85,
        "comment": "✓ APPROVED by 2/3 risk agents"
    },
    
    # Labels for Dashboard
    "confidence_level": "high",      # high/medium/low
    "risk_level": "moderate",        # aggressive/moderate/conservative
    
    # Portfolio State
    "portfolio": {
        "cash": 756.00,
        "position": 2,
        "average_cost": 122.00,
        "value": 1012.00,
        "unrealized_pnl": 12.00,
        "unrealized_pnl_pct": 1.19
    }
}
```

### Key Labels

**Confidence Level:**
- `HIGH`: >70% confidence (strong signals, multiple agents agree)
- `MEDIUM`: 40-70% confidence (mixed signals)
- `LOW`: <40% confidence (weak signals, uncertain)

→ Use this to size your capital. High confidence = larger positions.

**Risk Level:**
- `AGGRESSIVE`: Approved for up to 50% of portfolio per position
- `MODERATE`: Approved for up to 25% of portfolio per position
- `CONSERVATIVE`: Approved for up to 10% of portfolio per position

→ This reflects how conservative the risk management layer is.

---

## Configuration

### Using Real Data

You'll need:

1. **JSE Prices**: Automatically fetches from Yahoo Finance (free)
2. **South African News** (optional):
   - Option A: Mock news (default, no API key needed)
   - Option B: Real news from NewsAPI.org (requires free API key)

```python
system = IntegratedTradingSystem(
    jse_tickers=["NPN", "SASOL"],
    use_real_data=True,
    newsapi_key="your-newsapi-key"  # Get free key from newsapi.org
)
```

### Customizing Tickers

```python
system = IntegratedTradingSystem(
    jse_tickers=["NPN", "SASOL", "BHP", "IMPJ", "SHPJ"]
)
```

Available JSE tickers (in `jse_adapter.py`):
- NPN (Naspers)
- SASOL (Energy company)
- BHP (Mining)
- IMPJ (Platinum)
- SHPJ (Shoprite)
- TFMJ (Foschini Group)
- ABSPJ (Absa Group)
- JDIJ (Jdgroup)

---

## Codespaces Integration (Kimi Agent)

### Setup in Codespaces

```bash
# 1. Open terminal in Codespaces
cd /workspace

# 2. Clone or extract the trading system
unzip trading-system.zip
cd trading-system

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

### With Kimi Agent

Ask Kimi to:
1. "Review the trading system architecture"
2. "Run the mock trading example"
3. "Explain how the multi-agent decision system works"
4. "Modify the technical indicators"
5. "Add support for [feature]"

Kimi can directly edit files, run commands, and test the system.

---

## Advanced: Paper Trading on MT5

(Coming next - integration with MetaTrader 5)

To execute trades on real brokers when ready:

1. Install MetaTrader 5 Python library
2. Create `execution_connector.py` to convert signals → MT5 orders
3. Integrate with `merged_simulation.py`
4. Test on paper account first
5. Monitor with live dashboard

---

## Troubleshooting

**Q: "No module named 'data_pipeline'"**
A: Make sure you're in the right directory and ran `pip install -r requirements.txt`

**Q: "All proposals are HOLD"**
A: Normal with fresh data. Indicators need ~50 price points. Run `warmup_indicators()` first.

**Q: "Certificate error when fetching data"**
A: Some systems need: `pip install certifi`

**Q: "How do I see the logs?"**
A: Logs are saved to `trading_log.jsonl` by default. View with:
```python
import pandas as pd
df = pd.read_json('trading_log.jsonl', lines=True)
print(df[['price', 'decision.final_action', 'confidence_level', 'portfolio.value']])
```

**Q: "How do I execute trades on MT5?"**
A: That's Option C (not built yet). Coming soon with MT5 Python integration.

---

## Next Steps

1. ✅ **Run the mock examples** (`python main.py`)
2. ✅ **Understand the decision flow** (read this README + docstrings)
3. 🔲 **Connect to real JSE data** (set `use_real_data=True`)
4. 🔲 **Set up NewsAPI for real news** (optional)
5. 🔲 **Build a Flask dashboard** (real-time visualization)
6. 🔲 **Integrate MT5 execution** (paper trading → real trading)
7. 🔲 **Deploy to production** (cloud + monitoring)

---

## Files Included

```
trading-system/
├── main.py                    # Integration examples
├── data_pipeline.py           # Data handling + indicators
├── merged_simulation.py        # Multi-agent system
├── jse_adapter.py             # JSE data source
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── trading_log.jsonl          # Created after running (historical decisions)
```

---

## Support

For issues or questions:
1. Check the docstrings in the Python files
2. Run the examples in `main.py`
3. Enable debug logging in your code
4. Ask Kimi Agent for help in Codespaces

---

## License

Use freely for learning and personal trading. Not financial advice.

---

**Ready to start?**

```bash
python main.py
```

Good luck! 🚀

## Short-term multi-instrument research (HR11)

Run `python hr11_research.py` for an offline universe/capability audit. Real
intraday inputs, session calendars and instrument cost schedules are explicit;
the default report shows insufficient evidence and places no orders.
See [HR11 method and input contracts](docs/research/HR11_METHOD.md) and
[HR11 completion report](docs/reports/HR11_REPORT.md).
