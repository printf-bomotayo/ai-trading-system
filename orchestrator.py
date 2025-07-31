"""
AI Trading System - Phase 1: Core Architecture & Base Classes
================================================================

This is the foundational backend for our collaborative AI trading system.
We'll build this incrementally, starting with the core interfaces and base classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
import json
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketEventType(Enum):
    """Types of significant market events that trigger performance recalibration"""
    EARNINGS_SURPRISE = "earnings_surprise"
    FED_ANNOUNCEMENT = "fed_announcement"
    GEOPOLITICAL_SHOCK = "geopolitical_shock"
    SECTOR_ROTATION = "sector_rotation"
    VIX_SPIKE = "vix_spike"
    MAJOR_NEWS = "major_news"

class AgentType(Enum):
    """Types of AI agents in our system"""
    NEWS_INTELLIGENCE = "news_intelligence"
    MARKET_ANALYSIS = "market_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    EXECUTION_STRATEGY = "execution_strategy"
    VISUALIZATION = "visualization"

class TradeAction(Enum):
    """Possible trading actions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    SHORT = "short"
    COVER = "cover"

@dataclass
class MarketData:
    """Real-time market data structure"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: float
    ask: float
    vix: Optional[float] = None
    sector: Optional[str] = None
    
@dataclass
class NewsEvent:
    """News event data structure"""
    id: str
    title: str
    content: str
    source: str
    timestamp: datetime
    relevance_score: float
    symbols_mentioned: List[str]
    sentiment_score: float
    event_type: Optional[MarketEventType] = None

@dataclass
class AgentResponse:
    """Standardized response from any AI agent"""
    agent_type: AgentType
    confidence: float  # 0.0 to 1.0
    recommendation: TradeAction
    reasoning: str
    supporting_data: Dict[str, Any]
    timestamp: datetime
    risk_score: Optional[float] = None  # 0.0 to 1.0, higher = more risky
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

@dataclass
class PerformanceMetric:
    """Agent performance tracking"""
    agent_type: AgentType
    accuracy_rate: float
    confidence_calibration: float  # How well confidence correlates with success
    last_updated: datetime
    total_predictions: int
    correct_predictions: int
    performance_by_event_type: Dict[MarketEventType, float] = field(default_factory=dict)

class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.performance_history = []
        self.confidence_history = []
        
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Each agent must implement its analysis method"""
        pass
    
    def update_performance(self, prediction_correct: bool, confidence: float):
        """Update agent's performance metrics"""
        self.performance_history.append(prediction_correct)
        self.confidence_history.append(confidence)
        
    def get_current_accuracy(self) -> float:
        """Calculate current accuracy rate"""
        if not self.performance_history:
            return 0.5  # Default neutral accuracy
        return sum(self.performance_history) / len(self.performance_history)

class MarketEventDetector:
    """Detects significant market events that trigger performance recalibration"""
    
    def __init__(self):
        self.vix_threshold = 25.0  # VIX spike threshold
        self.price_move_threshold = 0.05  # 5% price movement threshold
        
    def is_significant_event(self, market_data: MarketData, news_events: List[NewsEvent]) -> Tuple[bool, Optional[MarketEventType]]:
        """Determine if current market conditions constitute a significant event"""
        
        # Check VIX spike
        if market_data.vix and market_data.vix > self.vix_threshold:
            return True, MarketEventType.VIX_SPIKE
            
        # Check for major news events
        for event in news_events:
            if event.relevance_score > 0.8 and event.event_type:
                return True, event.event_type
                
        return False, None

class PerformanceTracker:
    """Tracks and manages agent performance metrics"""
    
    def __init__(self):
        self.agent_metrics: Dict[AgentType, PerformanceMetric] = {}
        self.last_recalibration = datetime.now()
        
    def initialize_agent(self, agent_type: AgentType):
        """Initialize performance tracking for an agent"""
        self.agent_metrics[agent_type] = PerformanceMetric(
            agent_type=agent_type,
            accuracy_rate=0.5,  # Start with neutral accuracy
            confidence_calibration=1.0,
            last_updated=datetime.now(),
            total_predictions=0,
            correct_predictions=0
        )
    
    def update_performance(self, agent_type: AgentType, was_correct: bool, confidence: float, event_type: Optional[MarketEventType] = None):
        """Update agent performance after a significant market event"""
        if agent_type not in self.agent_metrics:
            self.initialize_agent(agent_type)
            
        metric = self.agent_metrics[agent_type]
        metric.total_predictions += 1
        
        if was_correct:
            metric.correct_predictions += 1
            
        metric.accuracy_rate = metric.correct_predictions / metric.total_predictions
        
        # Update performance by event type if specified
        if event_type:
            if event_type not in metric.performance_by_event_type:
                metric.performance_by_event_type[event_type] = 0.5
            # Simple weighted update (can be made more sophisticated)
            current_perf = metric.performance_by_event_type[event_type]
            metric.performance_by_event_type[event_type] = (current_perf * 0.8) + (float(was_correct) * 0.2)
        
        metric.last_updated = datetime.now()
        
    def get_agent_weight(self, agent_type: AgentType, confidence: float, current_event_type: Optional[MarketEventType] = None) -> float:
        """Calculate weighted score for agent recommendation"""
        if agent_type not in self.agent_metrics:
            return confidence * 0.5  # Default weight
            
        metric = self.agent_metrics[agent_type]
        
        # Base weight from confidence and historical accuracy
        base_weight = confidence * metric.accuracy_rate
        
        # Adjust based on event-specific performance if applicable
        if current_event_type and current_event_type in metric.performance_by_event_type:
            event_performance = metric.performance_by_event_type[current_event_type]
            base_weight = base_weight * event_performance
            
        return base_weight

class OrchestratorCore:
    """Core orchestrator that coordinates all AI agents"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.performance_tracker = PerformanceTracker()
        self.event_detector = MarketEventDetector()
        self.decision_history = []
        
    def register_agent(self, agent: BaseAgent):
        """Register an AI agent with the orchestrator"""
        self.agents[agent.agent_type] = agent
        self.performance_tracker.initialize_agent(agent.agent_type)
        logger.info(f"Registered {agent.agent_type.value} agent")
        
    async def coordinate_analysis(self, symbol: str, market_data: MarketData, news_events: List[NewsEvent]) -> Dict[str, Any]:
        """Coordinate analysis across all agents and make decision"""
        
        # Detect if this is a significant market event
        is_significant, event_type = self.event_detector.is_significant_event(market_data, news_events)
        
        # Prepare context for agents
        context = {
            "symbol": symbol,
            "market_data": market_data,
            "news_events": news_events,
            "event_type": event_type,
            "is_significant_event": is_significant
        }
        
        # Collect responses from all agents
        agent_responses = []
        for agent_type, agent in self.agents.items():
            try:
                response = await agent.analyze(context)
                agent_responses.append(response)
                logger.info(f"{agent_type.value} response: {response.recommendation.value} (confidence: {response.confidence:.2f})")
            except Exception as e:
                logger.error(f"Error getting response from {agent_type.value}: {e}")
        
        # Make coordinated decision
        decision = self._make_decision(agent_responses, event_type)
        
        # Log decision for future performance tracking
        decision_record = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "decision": decision,
            "agent_responses": agent_responses,
            "event_type": event_type,
            "is_significant": is_significant
        }
        self.decision_history.append(decision_record)
        
        return decision
    
    def _make_decision(self, responses: List[AgentResponse], event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Make final trading decision based on weighted agent responses"""
        
        if not responses:
            return {"action": TradeAction.HOLD, "confidence": 0.0, "reasoning": "No agent responses"}
        
        # Calculate weighted votes
        weighted_votes = {}
        total_weight = 0
        
        for response in responses:
            weight = self.performance_tracker.get_agent_weight(
                response.agent_type, 
                response.confidence, 
                event_type
            )
            
            if response.recommendation not in weighted_votes:
                weighted_votes[response.recommendation] = 0
            
            weighted_votes[response.recommendation] += weight
            total_weight += weight
        
        # Find recommendation with highest weighted vote
        if total_weight == 0:
            final_action = TradeAction.HOLD
            final_confidence = 0.0
        else:
            final_action = max(weighted_votes.items(), key=lambda x: x[1])[0]
            final_confidence = weighted_votes[final_action] / total_weight
        
        # Compile reasoning from top contributing agents
        reasoning = self._compile_reasoning(responses, final_action)
        
        return {
            "action": final_action,
            "confidence": final_confidence,
            "reasoning": reasoning,
            "weighted_votes": weighted_votes,
            "total_weight": total_weight,
            "event_type": event_type
        }
    
    def _compile_reasoning(self, responses: List[AgentResponse], final_action: TradeAction) -> str:
        """Compile reasoning from agents that supported the final decision"""
        supporting_reasoning = []
        
        for response in responses:
            if response.recommendation == final_action:
                supporting_reasoning.append(f"{response.agent_type.value}: {response.reasoning}")
        
        if not supporting_reasoning:
            supporting_reasoning = [f"Default action: {final_action.value}"]
            
        return " | ".join(supporting_reasoning)


# Example usage and testing
if __name__ == "__main__":
    async def test_system():
        """Test the core system with mock data"""
        
        # Initialize orchestrator
        orchestrator = OrchestratorCore()
        
        # Create mock market data
        market_data = MarketData(
            symbol="AAPL",
            price=150.0,
            volume=1000000,
            timestamp=datetime.now(),
            bid=149.95,
            ask=150.05,
            vix=22.5,
            sector="Technology"
        )
        
        # Create mock news events
        news_events = [
            NewsEvent(
                id=str(uuid.uuid4()),
                title="Apple Reports Strong Q4 Earnings",
                content="Apple exceeded expectations...",
                source="Reuters",
                timestamp=datetime.now(),
                relevance_score=0.9,
                symbols_mentioned=["AAPL"],
                sentiment_score=0.8,
                event_type=MarketEventType.EARNINGS_SURPRISE
            )
        ]
        
        print("✓ Core architecture initialized")
        print("✓ Data structures defined")
        print("✓ Performance tracking system ready")
        print("✓ Event detection system ready")
        print("\nReady for Phase 2: Individual Agent Implementation")
    
    # Run test
    asyncio.run(test_system())