"""
Main Trading System Integration
Combines:
- Option A: merged_simulation.py (Multi-agent decision system)
- Option B: jse_adapter.py (Real JSE data source)

This file serves as the shared launch point for the project and is designed
as a clean starting base for further JSE trading work.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_pipeline import UnifiedDataPipeline, MarketData
from merged_simulation import MergedSimulation
from jse_adapter import JSEDataAdapter, DataSourceType


class IntegratedTradingSystem:
    """
    Complete trading system combining data adapter + multi-agent simulator
    
    Workflow:
    1. Initialize pipeline + simulator
    2. Backfill historical data (warm up indicators)
    3. Loop: fetch live data → run agent decisions → log results
    4. (Optional) Execute on MT5 when ready
    """
    
    def __init__(
        self,
        jse_tickers: List[str] = None,
        use_real_data: bool = False,
        newsapi_key: str = None,
        log_file: str = "trading_log.jsonl"
    ):
        """
        Initialize trading system
        
        Args:
            jse_tickers: List of JSE tickers to trade (e.g., ["NPN", "SASOL"])
            use_real_data: True for real JSE data, False for mock
            newsapi_key: Optional NewsAPI key for real news
            log_file: File to log all decisions
        """
        
        self.jse_tickers = jse_tickers or ["NPN", "SASOL", "BHP"]
        self.log_file = log_file
        self.trading_log = []
        
        # Initialize pipeline
        print(f"[{datetime.now()}] Initializing pipeline with tickers: {self.jse_tickers}")
        self.pipeline = UnifiedDataPipeline(jse_tickers=self.jse_tickers)
        
        # Initialize simulator (multi-agent system)
        print(f"[{datetime.now()}] Initializing multi-agent simulator")
        self.simulator = MergedSimulation(self.pipeline)
        
        # Initialize data adapter
        price_source = DataSourceType.YAHOO_FINANCE if use_real_data else DataSourceType.MOCK
        print(f"[{datetime.now()}] Initializing JSE adapter (real_data={use_real_data})")
        self.adapter = JSEDataAdapter(
            price_source=price_source,
            news_source="newsapi" if newsapi_key else "mock",
            newsapi_key=newsapi_key
        )
        
        self.step_count = 0
        self.last_decisions = {}
    
    def warmup_indicators(self, ticker: str, days: int = 30):
        """
        Backfill with historical data to warm up technical indicators
        Should be called before starting live trading
        
        Args:
            ticker: JSE ticker symbol
            days: Number of days of historical data to load
        """
        print(f"\n[{datetime.now()}] Warming up indicators for {ticker}...")
        count = self.adapter.backfill_historical_data(self.pipeline, ticker, days=days)
        print(f"  Loaded {count} historical data points")
        
        # Run a few test steps (without executing) to verify indicators work
        obs = self.pipeline.get_observation(ticker)
        if obs.indicators:
            print(f"  ✓ Indicators ready (RSI={obs.indicators.rsi:.1f}, SMA signal={obs.indicators.sma_signal})")
        else:
            print(f"  ✓ Will calculate indicators after more data points")
    
    def step(self, ticker: str) -> Dict:
        """
        Execute one trading cycle for a ticker
        
        Args:
            ticker: JSE ticker symbol
            
        Returns:
            Complete decision record
        """
        self.step_count += 1
        
        # 1. Fetch live data from adapter
        success = self.adapter.feed_to_pipeline(
            self.pipeline,
            ticker,
            include_news=True  # Fetch news too
        )
        
        if not success:
            print(f"[{datetime.now()}] Failed to fetch data for {ticker}")
            return None
        
        # 2. Run multi-agent decision system
        decision = self.simulator.step(ticker)
        
        # 3. Store result
        self.last_decisions[ticker] = decision
        self.trading_log.append(decision)
        
        return decision
    
    def run_live(self, duration_minutes: int = 60, interval_seconds: int = 60):
        """
        Run live trading loop
        
        Args:
            duration_minutes: How long to run (0 = infinite)
            interval_seconds: Wait between price fetches
        """
        start_time = datetime.now()
        
        print(f"\n[{datetime.now()}] Starting live trading...")
        print(f"Duration: {duration_minutes} minutes, Update interval: {interval_seconds}s\n")
        
        try:
            step = 0
            while True:
                # Check duration
                if duration_minutes > 0:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed > duration_minutes:
                        break
                
                step += 1
                print(f"\n{'='*80}")
                print(f"TRADING STEP {step} - {datetime.now()}")
                print(f"{'='*80}")
                
                # Run one cycle for each ticker
                for ticker in self.jse_tickers:
                    decision = self.step(ticker)
                    
                    if decision:
                        self._print_decision(decision)
                
                # Save log
                self._save_log()
                
                # Wait before next step
                print(f"\nWaiting {interval_seconds}s until next update...")
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("\n\n[User interrupted] Saving log and shutting down...")
            self._save_log()
    
    def _print_decision(self, decision: Dict):
        """Pretty-print a decision record"""
        print(f"\n[{decision['ticker']}] Price: €{decision['price']:.2f}")
        print(f"  News sentiment: {decision['news_sentiment'].upper()} ({decision['news_sentiment_score']:+.2f})")
        
        if decision['indicators']:
            print(f"  Technical: RSI={decision['indicators']['rsi']:.1f}, SMA signal={decision['indicators']['sma_signal']}")
        
        # Research summary
        print(f"  Research:")
        print(f"    • Bullish: {decision['research']['bullish']['confidence']:.0%}")
        print(f"    • Bearish: {decision['research']['bearish']['confidence']:.0%}")
        print(f"    • General: {decision['research']['general']['confidence']:.0%}")
        
        # Proposal
        print(f"  Proposal: {decision['proposal']['action'].upper()} size={decision['proposal']['size']} "
              f"(conf={decision['proposal']['confidence']:.0%})")
        
        # Risk assessments
        approvals = sum(1 for a in decision['risk_assessments'] if a['approved'])
        print(f"  Risk approval: {approvals}/3")
        
        # Final decision
        if decision['decision']['approved']:
            print(f"  ✓ DECISION: {decision['decision']['final_action'].upper()} "
                  f"{decision['decision']['final_size']} units")
            print(f"    Confidence: {decision['confidence_level'].upper()}")
            print(f"    Risk level: {decision['risk_level'].upper()}")
        else:
            print(f"  ✗ DECISION: REJECTED - {decision['decision']['comment']}")
        
        # Portfolio
        port = decision['portfolio']
        print(f"  Portfolio: €{port['value']:.2f} (cash=€{port['cash']:.2f}, pos={port['position']})")
    
    def _save_log(self):
        """Save trading log to file"""
        try:
            with open(self.log_file, 'w') as f:
                for record in self.trading_log:
                    f.write(json.dumps(record, default=str) + '\n')
            print(f"✓ Saved {len(self.trading_log)} records to {self.log_file}")
        except Exception as e:
            print(f"✗ Error saving log: {e}")
    
    def get_performance_summary(self) -> Dict:
        """
        Calculate performance metrics from trading log
        
        Returns:
            Dict with metrics: total_trades, win_rate, avg_confidence, etc.
        """
        if not self.trading_log:
            return {"error": "No trades recorded"}
        
        total_steps = len(self.trading_log)
        executed_trades = sum(1 for r in self.trading_log if r['decision']['approved'])
        
        confidences = [r['confidence_level'] == 'high' for r in self.trading_log]
        high_confidence_count = sum(confidences)
        
        # Portfolio value progression
        portfolio_values = [r['portfolio']['value'] for r in self.trading_log]
        
        return {
            "total_steps": total_steps,
            "executed_trades": executed_trades,
            "execution_rate": f"{executed_trades/total_steps:.1%}",
            "high_confidence_trades": high_confidence_count,
            "starting_value": portfolio_values[0] if portfolio_values else 0,
            "ending_value": portfolio_values[-1] if portfolio_values else 0,
            "total_pnl": portfolio_values[-1] - portfolio_values[0] if portfolio_values else 0,
            "total_pnl_pct": f"{((portfolio_values[-1] / portfolio_values[0]) - 1) * 100:.2f}%" if portfolio_values else "0%"
        }


# =========================
# Run Examples
# =========================

def example_1_mock_trading():
    """Example 1: Run with mock data (no API keys needed)"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Mock Trading System")
    print("="*80)
    
    system = IntegratedTradingSystem(
        jse_tickers=["NPN", "SASOL"],
        use_real_data=False,
        log_file="trading_log_mock.jsonl"
    )
    
    # Warm up
    for ticker in system.jse_tickers:
        system.warmup_indicators(ticker, days=30)
    
    # Run for 10 steps
    print("\nRunning 10 trading steps...")
    for i in range(10):
        print(f"\n--- Step {i+1} ---")
        for ticker in system.jse_tickers:
            decision = system.step(ticker)
            if decision and decision['decision']['approved']:
                print(f"✓ {ticker}: {decision['decision']['final_action'].upper()}")
    
    # Show summary
    summary = system.get_performance_summary()
    print("\n" + "="*80)
    print("Performance Summary")
    print("="*80)
    for key, value in summary.items():
        print(f"  {key}: {value}")


def example_2_real_jse_data():
    """Example 2: Run with real JSE data from Yahoo Finance"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Real JSE Data")
    print("="*80)
    
    system = IntegratedTradingSystem(
        jse_tickers=["NPN"],
        use_real_data=True,
        log_file="trading_log_real.jsonl"
    )
    
    # Warm up
    system.warmup_indicators("NPN", days=30)
    
    # Run one step
    print("\nFetching live data and running decision cycle...")
    decision = system.step("NPN")
    if decision:
        system._print_decision(decision)


def example_3_live_trading():
    """Example 3: Run live trading loop (runs forever)"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Live Trading Loop")
    print("="*80)
    
    system = IntegratedTradingSystem(
        jse_tickers=["NPN", "SASOL"],
        use_real_data=False,  # Change to True for real data
        log_file="trading_log_live.jsonl"
    )
    
    # Warm up
    for ticker in system.jse_tickers:
        system.warmup_indicators(ticker, days=30)
    
    # Run live trading (60 minutes, 60-second intervals)
    # Comment out for testing - this runs forever unless duration set
    # system.run_live(duration_minutes=60, interval_seconds=60)
    
    print("\nLive trading not started (would run for 60 minutes)")
    print("Uncomment system.run_live() in example_3_live_trading() to start")


def main():
    """Run the default smoke test for the JSE trading prototype."""
    print("\nIntegrated Trading System - Examples")
    print("="*80)

    # Run example 1 (mock data, quick)
    example_1_mock_trading()

    # Uncomment to run other examples:
    # example_2_real_jse_data()
    # example_3_live_trading()


def demo_bank_provider_setup():
    """Illustrates how a user can plug in their own bank provider configuration."""
    from jse_adapter import BankProviderFactory

    print("\nBank provider modularity example")
    print("="*80)

    # Public-safe flow: users configure their own provider and credentials in env/config.
    # This keeps the app portable across banks and user-owned login details.
    provider_name = "standardbank_ost"
    provider = BankProviderFactory.create(provider_name, username="your_username", password="your_password")
    print(f"Provider created: {provider.provider_name}")
    print("Use this pattern to attach a real provider implementation per user account.")


def demo_signal_scan():
    """Run a simple market scan using JSE data, SA news, and technical indicators."""
    from signal_pipeline import JSESignalEngine
    from jse_adapter import DataSourceType

    print("\nJSE signal scan")
    print("="*80)

    engine = JSESignalEngine(
        tickers=["NPN", "SASOL", "BHP", "IMPJ", "SHPJ"],
        price_source=DataSourceType.YAHOO_FINANCE,
        news_source="mock",
    )

    for decision in engine.scan_market():
        print(f"{decision.ticker}: {decision.action.upper()} | confidence={decision.confidence:.2f} | score={decision.score:.2f} | reason={decision.reason}")


if __name__ == "__main__":
    main()
    # demo_bank_provider_setup()
    demo_signal_scan()
