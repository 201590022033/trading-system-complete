"""
Merged Multi-Agent Trading Simulation
Combines rania321's governance + agent architecture with real data from data_pipeline.py

Core flow:
  MarketObservation (real data) 
    ↓
  Research Agents (bullish/bearish/general)
    ↓
  LLM Trader (synthesizes research, proposes action + size)
    ↓
  Risk Agents (evaluates risk)
    ↓
  Manager Agent (majority vote + approval)
    ↓
  Executor Agent (executes on portfolio)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

# Import from data_pipeline
from data_pipeline import (
    UnifiedDataPipeline,
    MarketObservation,
    TechnicalIndicators,
    SentimentLabel,
    PortfolioData
)


class ConfidenceLevel(Enum):
    """Confidence in trading signal"""
    HIGH = "high"      # 70%+ confidence
    MEDIUM = "medium"  # 40-70% confidence
    LOW = "low"        # <40% confidence


class RiskLevel(Enum):
    """Risk assessment level"""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"


# =========================
# Data Structures
# =========================

@dataclass
class Evidence:
    """Research agent output"""
    stance: str  # "bullish", "bearish", "neutral"
    text: str
    confidence: float  # 0.0 to 1.0


@dataclass
class TradeProposal:
    """LLM trader's trade proposal"""
    action: str  # "buy", "sell", "hold"
    size: int  # number of shares (0-3 for now)
    rationale: str
    confidence: float  # 0.0 to 1.0 (how confident in this proposal)


@dataclass
class RiskAssessment:
    """Risk agent evaluation"""
    agent_name: str
    approved: bool
    suggested_size: int
    comment: str
    risk_level: RiskLevel


@dataclass
class ManagerDecision:
    """Final decision from manager agent"""
    approved: bool
    final_action: str  # "buy", "sell", "hold"
    final_size: int
    comment: str
    confidence: float  # Median of risk agent confidence


# =========================
# Research Agents
# =========================

class BullishResearcher:
    """Analyzes market data from a bullish perspective"""
    
    def analyze(self, obs: MarketObservation) -> Evidence:
        """
        Look for bullish signals in the market observation
        """
        bullish_factors = []
        
        # Check sentiment
        if obs.news_sentiment == SentimentLabel.BULLISH:
            bullish_factors.append(f"Positive news sentiment ({obs.news_sentiment_score:.2f})")
        
        # Check price trend
        if len(obs.recent_prices) >= 2 and obs.recent_prices[-1] > obs.recent_prices[-2]:
            bullish_factors.append("Recent price trend is upward")
        
        # Check technical indicators
        if obs.indicators:
            if obs.indicators.sma_signal == 1:
                bullish_factors.append("SMA crossover: fast MA > slow MA (bullish)")
            if obs.indicators.rsi_signal == 1:
                bullish_factors.append(f"RSI oversold ({obs.indicators.rsi:.1f}), buy signal")
            if obs.indicators.breakout_signal == 1:
                bullish_factors.append("Price breaking out to upside")
        
        # Check emerging market context
        if obs.emerging_market_correlation > 0.3:
            bullish_factors.append(f"Emerging market tailwind (correlation: {obs.emerging_market_correlation:.2f})")
        
        # Build report
        if bullish_factors:
            text = "Bullish case:\n" + "\n".join(f"• {f}" for f in bullish_factors)
            confidence = min(0.95, len(bullish_factors) * 0.25)  # More factors = higher confidence
        else:
            text = "Weak bullish signals - limited upside factors visible"
            confidence = 0.1
        
        return Evidence("bullish", text, confidence)


class BearishResearcher:
    """Analyzes market data from a bearish perspective"""
    
    def analyze(self, obs: MarketObservation) -> Evidence:
        """
        Look for bearish signals in the market observation
        """
        bearish_factors = []
        
        # Check sentiment
        if obs.news_sentiment == SentimentLabel.BEARISH:
            bearish_factors.append(f"Negative news sentiment ({obs.news_sentiment_score:.2f})")
        
        # Check price trend
        if len(obs.recent_prices) >= 2 and obs.recent_prices[-1] < obs.recent_prices[-2]:
            bearish_factors.append("Recent price trend is downward")
        
        # Check technical indicators
        if obs.indicators:
            if obs.indicators.sma_signal == -1:
                bearish_factors.append("SMA crossover: fast MA < slow MA (bearish)")
            if obs.indicators.rsi_signal == -1:
                bearish_factors.append(f"RSI overbought ({obs.indicators.rsi:.1f}), sell signal")
            if obs.indicators.breakout_signal == -1:
                bearish_factors.append("Price breaking down to downside")
        
        # Check emerging market context
        if obs.emerging_market_correlation < -0.3:
            bearish_factors.append(f"Emerging market headwind (correlation: {obs.emerging_market_correlation:.2f})")
        
        # Build report
        if bearish_factors:
            text = "Bearish case:\n" + "\n".join(f"• {f}" for f in bearish_factors)
            confidence = min(0.95, len(bearish_factors) * 0.25)
        else:
            text = "Weak bearish signals - limited downside factors visible"
            confidence = 0.1
        
        return Evidence("bearish", text, confidence)


class GeneralResearchAgent:
    """Neutral LLM-based research agent (simplified for demo)"""
    
    def analyze(self, obs: MarketObservation) -> Evidence:
        """
        Provide balanced market analysis (in real deployment, call Claude API)
        """
        # In production, this would call: llm_interface.call_claude(prompt)
        # For now, simple heuristic
        
        signals = []
        
        if obs.indicators:
            if obs.indicators.sma_signal != 0:
                signals.append("Technical: SMA shows trend")
            if obs.indicators.rsi_signal != 0:
                signals.append("Technical: RSI at extremes")
        
        if obs.news_sentiment != SentimentLabel.NEUTRAL:
            signals.append(f"Sentiment: {obs.news_sentiment.value}")
        
        if len(signals) > 0:
            stance = "neutral"
            if obs.news_sentiment_score > 0.3:
                stance = "bullish"
            elif obs.news_sentiment_score < -0.3:
                stance = "bearish"
            
            text = f"Market analysis: {', '.join(signals)}"
            confidence = min(0.8, len(signals) * 0.2)
        else:
            text = "Insufficient signals for directional bias"
            stance = "neutral"
            confidence = 0.3
        
        return Evidence(stance, text, confidence)


# =========================
# LLM Trader Agent
# =========================

class LLMTraderAgent:
    """
    Portfolio manager who synthesizes research and decides on action
    Proposes: BUY/SELL/HOLD + position size (0-3)
    """
    
    def __init__(self):
        self.portfolio = PortfolioData(cash=1000.0, position=0)
    
    def propose_trade(
        self,
        obs: MarketObservation,
        bull: Evidence,
        bear: Evidence,
        general: Evidence
    ) -> TradeProposal:
        """
        Synthesize research into a trade proposal
        """
        # Weight the three research perspectives
        bull_score = bull.confidence if bull.stance == "bullish" else -bull.confidence
        bear_score = -bear.confidence if bear.stance == "bearish" else bear.confidence
        general_score = {
            "bullish": general.confidence,
            "bearish": -general.confidence,
            "neutral": 0.0
        }.get(general.stance, 0.0)
        
        # Average sentiment
        avg_sentiment = (bull_score + bear_score + general_score) / 3.0
        
        # Determine action
        if avg_sentiment > 0.3:
            action = "buy"
            action_confidence = min(0.95, abs(avg_sentiment))
        elif avg_sentiment < -0.3:
            action = "sell"
            action_confidence = min(0.95, abs(avg_sentiment))
        else:
            action = "hold"
            action_confidence = 0.7  # Hold is lower risk
        
        # Determine size based on confidence
        if action == "hold":
            size = 0
        elif action_confidence > 0.7:
            size = 3  # Large position
        elif action_confidence > 0.5:
            size = 2  # Medium position
        else:
            size = 1  # Small position
        
        # Build rationale
        rationale = f"{', '.join([bull.stance, bear.stance, general.stance])} research → {action.upper()} with size {size}"
        
        return TradeProposal(
            action=action,
            size=size,
            rationale=rationale,
            confidence=action_confidence
        )


# =========================
# Risk, Manager, Execution
# =========================

class RiskAgent:
    """
    Evaluates if a trade proposal is acceptable given risk parameters
    Three personalities: aggressive, neutral, conservative
    """
    
    def __init__(self, name: str, personality: str):
        self.name = name
        self.personality = personality  # "aggressive", "neutral", "conservative"
    
    def evaluate(
        self,
        proposal: TradeProposal,
        portfolio: PortfolioData,
        price: float
    ) -> RiskAssessment:
        """
        Evaluate the proposal's risk
        """
        if proposal.size == 0:
            return RiskAssessment(
                agent_name=self.name,
                approved=True,
                suggested_size=0,
                comment="HOLD is always approved",
                risk_level=RiskLevel.MODERATE
            )
        
        trade_value = proposal.size * price
        portfolio_value = portfolio.value(price)
        position_fraction = trade_value / portfolio_value if portfolio_value > 0 else 0.0
        
        approved = True
        suggested_size = proposal.size
        comment = ""
        
        if self.personality == "aggressive":
            # Allow up to 50% of portfolio in one position
            if position_fraction > 0.5:
                suggested_size = max(1, int(0.5 * portfolio_value / price))
                comment = f"Position too large ({position_fraction:.1%}), reducing to {suggested_size}"
            else:
                comment = f"Aggressive: position ({position_fraction:.1%}) acceptable"
            risk_level = RiskLevel.AGGRESSIVE
        
        elif self.personality == "neutral":
            # Allow up to 25% of portfolio
            if position_fraction > 0.25:
                suggested_size = max(0, int(0.25 * portfolio_value / price))
                comment = f"Position too large ({position_fraction:.1%}), reducing to {suggested_size}"
            else:
                comment = f"Neutral: position ({position_fraction:.1%}) acceptable"
            risk_level = RiskLevel.MODERATE
        
        else:  # conservative
            # Allow up to 10% of portfolio
            if position_fraction > 0.10:
                approved = False
                suggested_size = 0
                comment = f"Conservative: position ({position_fraction:.1%}) exceeds limit, REJECTED"
                risk_level = RiskLevel.CONSERVATIVE
            else:
                comment = f"Conservative: position ({position_fraction:.1%}) acceptable but small"
                risk_level = RiskLevel.CONSERVATIVE
        
        return RiskAssessment(
            agent_name=self.name,
            approved=approved,
            suggested_size=suggested_size,
            comment=comment,
            risk_level=risk_level
        )


class ManagerAgent:
    """
    Final decision maker
    Rules: 2/3 risk agents must approve. Size = median of suggested sizes.
    """
    
    def decide(
        self,
        proposal: TradeProposal,
        assessments: List[RiskAssessment]
    ) -> ManagerDecision:
        """
        Make final approval decision
        """
        approvals = sum(1 for a in assessments if a.approved)
        
        # Need at least 2 of 3 approvals
        if approvals >= 2 and proposal.action != "hold" and proposal.size > 0:
            # Use median suggested size
            sizes = sorted(a.suggested_size for a in assessments)
            median_size = sizes[len(sizes) // 2]
            
            if median_size <= 0:
                return ManagerDecision(
                    approved=False,
                    final_action="hold",
                    final_size=0,
                    comment=f"Approved by {approvals}/3 risk agents but median size=0, downgrading to HOLD",
                    confidence=0.4
                )
            
            confidence = min(0.9, proposal.confidence)
            return ManagerDecision(
                approved=True,
                final_action=proposal.action,
                final_size=median_size,
                comment=f"✓ APPROVED by {approvals}/3 risk agents. Final size={median_size}",
                confidence=confidence
            )
        
        return ManagerDecision(
            approved=False,
            final_action="hold",
            final_size=0,
            comment=f"✗ REJECTED: Only {approvals}/3 risk agents approved, or proposal is HOLD",
            confidence=0.3
        )


class ExecutionAgent:
    """
    Executes the manager's decision on the portfolio
    """
    
    def execute(
        self,
        decision: ManagerDecision,
        portfolio: PortfolioData,
        price: float
    ) -> bool:
        """
        Execute trade. Returns True if successful.
        """
        if not decision.approved or decision.final_action == "hold" or decision.final_size == 0:
            return False
        
        q = decision.final_size
        
        if decision.final_action == "buy":
            cost = q * price
            if portfolio.cash >= cost:
                portfolio.cash -= cost
                avg_cost = (
                    (portfolio.average_cost * portfolio.position + cost) /
                    (portfolio.position + q)
                )
                portfolio.position += q
                portfolio.average_cost = avg_cost
                return True
            return False
        
        elif decision.final_action == "sell":
            if portfolio.position >= q:
                proceeds = q * price
                portfolio.cash += proceeds
                portfolio.position -= q
                return True
            return False
        
        return False


# =========================
# Main Merged Simulation
# =========================

class MergedSimulation:
    """
    Complete multi-agent trading system combining:
    - Real market data (from data_pipeline)
    - Research agents (bullish/bearish/general)
    - LLM trader (synthesizer)
    - Risk agents (governance)
    - Manager (approval)
    - Executor (execution)
    """
    
    def __init__(self, pipeline: UnifiedDataPipeline):
        self.pipeline = pipeline
        
        # Initialize agents
        self.bull_researcher = BullishResearcher()
        self.bear_researcher = BearishResearcher()
        self.general_researcher = GeneralResearchAgent()
        
        self.llm_trader = LLMTraderAgent()
        
        self.risk_team = [
            RiskAgent("AggressiveRisk", "aggressive"),
            RiskAgent("NeutralRisk", "neutral"),
            RiskAgent("ConservativeRisk", "conservative"),
        ]
        
        self.manager = ManagerAgent()
        self.executor = ExecutionAgent()
    
    def step(self, ticker: str) -> Dict:
        """
        Execute one trading step for a ticker
        Returns complete decision info for dashboard/logging
        """
        # 1. Get market observation (real data)
        obs = self.pipeline.get_observation(ticker)
        price = obs.price
        
        # 2. Research phase
        bull_ev = self.bull_researcher.analyze(obs)
        bear_ev = self.bear_researcher.analyze(obs)
        general_ev = self.general_researcher.analyze(obs)
        
        # 3. LLM trader proposes
        proposal = self.llm_trader.propose_trade(obs, bull_ev, bear_ev, general_ev)
        
        # 4. Risk agents evaluate
        assessments = [
            r.evaluate(proposal, self.llm_trader.portfolio, price)
            for r in self.risk_team
        ]
        
        # 5. Manager decides
        decision = self.manager.decide(proposal, assessments)
        
        # 6. Execute
        execution_success = self.executor.execute(decision, self.llm_trader.portfolio, price)
        
        # 7. Calculate confidence level
        if decision.confidence > 0.7:
            confidence_level = ConfidenceLevel.HIGH
        elif decision.confidence > 0.4:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        # 8. Calculate overall risk level
        approved_counts = {
            "aggressive": sum(1 for a in assessments if a.approved and a.risk_level == RiskLevel.AGGRESSIVE),
            "moderate": sum(1 for a in assessments if a.approved and a.risk_level == RiskLevel.MODERATE),
            "conservative": sum(1 for a in assessments if a.approved and a.risk_level == RiskLevel.CONSERVATIVE),
        }
        
        if approved_counts["conservative"] >= 2:
            overall_risk = RiskLevel.CONSERVATIVE
        elif approved_counts["aggressive"] >= 2:
            overall_risk = RiskLevel.AGGRESSIVE
        else:
            overall_risk = RiskLevel.MODERATE
        
        # Return comprehensive step output
        return {
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "price": round(price, 2),
            "recent_prices": [round(p, 2) for p in obs.recent_prices[-10:]],
            
            # Market context
            "news": obs.news,
            "news_sentiment": obs.news_sentiment.value,
            "news_sentiment_score": round(obs.news_sentiment_score, 2),
            "macro_factor": obs.macro_factor,
            "em_correlation": round(obs.emerging_market_correlation, 2),
            
            # Technical indicators
            "indicators": {
                "rsi": round(obs.indicators.rsi, 1) if obs.indicators else None,
                "rsi_signal": obs.indicators.rsi_signal if obs.indicators else 0,
                "sma_signal": obs.indicators.sma_signal if obs.indicators else 0,
                "breakout_signal": obs.indicators.breakout_signal if obs.indicators else 0,
                "stochastic": round(obs.indicators.stochastic_oscillator, 1) if obs.indicators else None,
            },
            
            # Research phase
            "research": {
                "bullish": {
                    "stance": bull_ev.stance,
                    "confidence": round(bull_ev.confidence, 2),
                    "analysis": bull_ev.text
                },
                "bearish": {
                    "stance": bear_ev.stance,
                    "confidence": round(bear_ev.confidence, 2),
                    "analysis": bear_ev.text
                },
                "general": {
                    "stance": general_ev.stance,
                    "confidence": round(general_ev.confidence, 2),
                    "analysis": general_ev.text
                }
            },
            
            # Trader proposal
            "proposal": {
                "action": proposal.action,
                "size": proposal.size,
                "confidence": round(proposal.confidence, 2),
                "rationale": proposal.rationale
            },
            
            # Risk assessments
            "risk_assessments": [
                {
                    "agent": a.agent_name,
                    "approved": a.approved,
                    "suggested_size": a.suggested_size,
                    "risk_level": a.risk_level.value,
                    "comment": a.comment
                }
                for a in assessments
            ],
            
            # Manager decision
            "decision": {
                "approved": decision.approved,
                "final_action": decision.final_action,
                "final_size": decision.final_size,
                "confidence": round(decision.confidence, 2),
                "comment": decision.comment
            },
            
            # Execution
            "execution": {
                "success": execution_success,
                "action_taken": decision.final_action if execution_success else "none"
            },
            
            # Labels for dashboard
            "confidence_level": confidence_level.value,
            "risk_level": overall_risk.value,
            
            # Portfolio state
            "portfolio": self.pipeline.get_portfolio_state(price)
        }


# =========================
# Example Usage
# =========================

if __name__ == "__main__":
    # Demo: Run simulation with mock data
    from data_pipeline import MockDataGenerator, MarketData
    
    print("Initializing Merged Simulation...")
    
    # Create pipeline
    pipeline = UnifiedDataPipeline(jse_tickers=["NPN"])
    sim = MergedSimulation(pipeline)
    
    # Generate mock data
    gen = MockDataGenerator(base_price=120.0)
    
    print("\n" + "="*80)
    print("Running 10 simulation steps with mock data")
    print("="*80 + "\n")
    
    for step in range(10):
        # Add price data
        price = gen.next_price()
        pipeline.add_market_data(MarketData("NPN", price, datetime.now(), vwap=price))
        
        # Add occasional news
        if step % 3 == 0:
            trend = ["bullish", "bearish", "neutral"][step % 3]
            news = gen.generate_news("NPN", trend=trend)
            pipeline.add_news("NPN", news)
        
        # Run simulation step
        result = sim.step("NPN")
        
        # Display results
        print(f"STEP {step + 1}: {result['ticker']} @ €{result['price']}")
        print(f"  Sentiment: {result['news_sentiment'].upper()} ({result['news_sentiment_score']:+.2f})")
        print(f"  Proposal: {result['proposal']['action'].upper()} size={result['proposal']['size']} (conf={result['proposal']['confidence']:.0%})")
        print(f"  Decision: {'✓ APPROVED' if result['decision']['approved'] else '✗ REJECTED'} - {result['decision']['comment']}")
        print(f"  Risk Level: {result['risk_level'].upper()}")
        print(f"  Portfolio: ${result['portfolio']['value']:.2f} (pos={result['portfolio']['position']})")
        print()
