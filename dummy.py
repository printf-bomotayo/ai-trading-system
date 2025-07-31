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

class NewsIntelligenceAgent(BaseAgent):
    """
    AI Agent specialized in processing news events and determining market impact.
    This agent monitors news feeds, analyzes content relevance, and predicts price impact.
    """
    
    def __init__(self):
        super().__init__(AgentType.NEWS_INTELLIGENCE)
        self.news_sources = [
            "Reuters", "Bloomberg", "CNBC", "SEC Filings", 
            "Company Press Releases", "Fed Announcements"
        ]
        self.impact_keywords = {
            "high_impact": ["earnings", "merger", "acquisition", "FDA approval", "bankruptcy", "investigation"],
            "medium_impact": ["guidance", "upgrade", "downgrade", "partnership", "expansion"],
            "low_impact": ["appointment", "conference", "interview", "routine"]
        }
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze news events and determine trading recommendation"""
        
        market_data = context["market_data"]
        news_events = context["news_events"]
        symbol = context["symbol"]
        
        # Filter news relevant to the symbol
        relevant_news = [event for event in news_events if symbol in event.symbols_mentioned]
        
        if not relevant_news:
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.3,
                recommendation=TradeAction.HOLD,
                reasoning="No relevant news found for symbol",
                supporting_data={"relevant_news_count": 0},
                timestamp=datetime.now()
            )
        
        # Analyze news impact
        impact_analysis = self._analyze_news_impact(relevant_news, market_data)
        
        # Determine recommendation based on analysis
        recommendation = self._determine_recommendation(impact_analysis)
        
        return AgentResponse(
            agent_type=self.agent_type,
            confidence=impact_analysis["confidence"],
            recommendation=recommendation,
            reasoning=impact_analysis["reasoning"],
            supporting_data=impact_analysis,
            timestamp=datetime.now(),
            target_price=impact_analysis.get("target_price"),
            risk_score=impact_analysis.get("risk_score", 0.5)
        )
    
    def _analyze_news_impact(self, news_events: List[NewsEvent], market_data: MarketData) -> Dict[str, Any]:
        """Analyze the collective impact of news events"""
        
        total_sentiment = 0
        total_relevance = 0
        high_impact_count = 0
        latest_event_time = None
        key_events = []
        
        for event in news_events:
            total_sentiment += event.sentiment_score * event.relevance_score
            total_relevance += event.relevance_score
            
            # Check for high-impact keywords
            if self._is_high_impact_news(event):
                high_impact_count += 1
                key_events.append(event.title)
            
            if not latest_event_time or event.timestamp > latest_event_time:
                latest_event_time = event.timestamp
        
        # Calculate weighted sentiment
        weighted_sentiment = total_sentiment / max(total_relevance, 1)
        
        # Calculate confidence based on relevance and recency
        recency_factor = self._calculate_recency_factor(latest_event_time) if latest_event_time else 0
        confidence = min(0.95, (total_relevance / len(news_events)) * recency_factor)
        
        # Determine impact magnitude
        impact_magnitude = self._calculate_impact_magnitude(weighted_sentiment, high_impact_count, total_relevance)
        
        # Calculate risk score
        risk_score = min(1.0, (high_impact_count * 0.3) + (abs(weighted_sentiment) * 0.7))
        
        # Estimate target price based on sentiment and impact
        current_price = market_data.price
        price_impact = weighted_sentiment * impact_magnitude * 0.05  # Max 5% impact
        target_price = current_price * (1 + price_impact)
        
        reasoning = self._build_reasoning(weighted_sentiment, high_impact_count, key_events, impact_magnitude)
        
        return {
            "confidence": confidence,
            "weighted_sentiment": weighted_sentiment,
            "impact_magnitude": impact_magnitude,
            "high_impact_events": high_impact_count,
            "key_events": key_events,
            "target_price": target_price,
            "risk_score": risk_score,
            "reasoning": reasoning,
            "news_count": len(news_events)
        }
    
    def _is_high_impact_news(self, event: NewsEvent) -> bool:
        """Determine if news event is high impact"""
        content_lower = (event.title + " " + event.content).lower()
        
        for keyword in self.impact_keywords["high_impact"]:
            if keyword in content_lower:
                return True
        
        # Also consider relevance score and source credibility
        if event.relevance_score > 0.85 and event.source in ["Reuters", "Bloomberg", "SEC Filings"]:
            return True
            
        return False
    
    def _calculate_recency_factor(self, event_time: datetime) -> float:
        """Calculate how recent the news is (more recent = higher factor)"""
        time_diff = datetime.now() - event_time
        hours_ago = time_diff.total_seconds() / 3600
        
        if hours_ago < 1:
            return 1.0
        elif hours_ago < 6:
            return 0.8
        elif hours_ago < 24:
            return 0.6
        else:
            return 0.3
    
    def _calculate_impact_magnitude(self, sentiment: float, high_impact_count: int, total_relevance: float) -> float:
        """Calculate the magnitude of expected market impact"""
        base_magnitude = abs(sentiment) * (total_relevance / 5.0)  # Normalize relevance
        impact_bonus = high_impact_count * 0.2  # Bonus for high-impact events
        
        return min(1.0, base_magnitude + impact_bonus)
    
    def _determine_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine trading recommendation based on news analysis"""
        sentiment = analysis["weighted_sentiment"]
        impact_magnitude = analysis["impact_magnitude"]
        confidence = analysis["confidence"]
        
        # Only make strong recommendations if confidence and impact are high
        if confidence < 0.5 or impact_magnitude < 0.3:
            return TradeAction.HOLD
        
        # Strong positive sentiment with high impact
        if sentiment > 0.6 and impact_magnitude > 0.6:
            return TradeAction.BUY
        
        # Strong negative sentiment with high impact
        if sentiment < -0.6 and impact_magnitude > 0.6:
            return TradeAction.SELL
        
        # Moderate signals
        if sentiment > 0.3:
            return TradeAction.BUY
        elif sentiment < -0.3:
            return TradeAction.SELL
        
        return TradeAction.HOLD
    
    def _build_reasoning(self, sentiment: float, high_impact_count: int, key_events: List[str], impact_magnitude: float) -> str:
        """Build human-readable reasoning for the recommendation"""
        
        sentiment_desc = "positive" if sentiment > 0 else "negative" if sentiment < 0 else "neutral"
        impact_desc = "high" if impact_magnitude > 0.7 else "moderate" if impact_magnitude > 0.4 else "low"
        
        reasoning = f"News sentiment is {sentiment_desc} ({sentiment:.2f}) with {impact_desc} expected impact ({impact_magnitude:.2f})"
        
        if high_impact_count > 0:
            reasoning += f". {high_impact_count} high-impact events detected"
            if key_events:
                reasoning += f": {', '.join(key_events[:3])}"  # Show top 3 events
        
        return reasoning


class MarketAnalysisAgent(BaseAgent):
    """
    AI Agent specialized in technical analysis, price patterns, and market microstructure.
    Analyzes price movements, volume patterns, support/resistance levels, and market trends.
    """
    
    def __init__(self):
        super().__init__(AgentType.MARKET_ANALYSIS)
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        self.technical_indicators = [
            "RSI", "MACD", "Bollinger_Bands", "Moving_Averages", 
            "Volume_Profile", "Support_Resistance"
        ]
        self.pattern_library = [
            "double_top", "double_bottom", "head_shoulders", "triangle",
            "flag", "pennant", "cup_handle", "breakout"
        ]
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze market data and determine trading recommendation based on technical analysis"""
        
        market_data = context["market_data"]
        symbol = context["symbol"]
        event_type = context.get("event_type")
        
        # Perform comprehensive technical analysis
        technical_analysis = self._perform_technical_analysis(market_data, symbol)
        
        # Analyze market microstructure
        microstructure_analysis = self._analyze_market_microstructure(market_data)
        
        # Pattern recognition
        pattern_analysis = self._detect_patterns(market_data)
        
        # Volume analysis
        volume_analysis = self._analyze_volume(market_data)
        
        # Combine all analyses
        combined_analysis = self._combine_analyses(
            technical_analysis, microstructure_analysis, 
            pattern_analysis, volume_analysis, event_type
        )
        
        # Determine final recommendation
        recommendation = self._determine_recommendation(combined_analysis)
        
        return AgentResponse(
            agent_type=self.agent_type,
            confidence=combined_analysis["confidence"],
            recommendation=recommendation,
            reasoning=combined_analysis["reasoning"],
            supporting_data=combined_analysis,
            timestamp=datetime.now(),
            target_price=combined_analysis.get("target_price"),
            stop_loss=combined_analysis.get("stop_loss"),
            risk_score=combined_analysis.get("risk_score", 0.5)
        )
    
    def _perform_technical_analysis(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Perform comprehensive technical analysis"""
        
        current_price = market_data.price
        
        # Mock technical indicators (in real implementation, these would be calculated from historical data)
        # RSI analysis
        rsi_value = self._calculate_mock_rsi(current_price)
        rsi_signal = "oversold" if rsi_value < 30 else "overbought" if rsi_value > 70 else "neutral"
        
        # Moving averages
        ma_20 = current_price * 0.98  # Mock 20-day MA
        ma_50 = current_price * 0.96  # Mock 50-day MA
        ma_trend = "bullish" if current_price > ma_20 > ma_50 else "bearish" if current_price < ma_20 < ma_50 else "mixed"
        
        # MACD analysis
        macd_signal = self._calculate_mock_macd_signal(current_price)
        
        # Bollinger Bands
        bb_analysis = self._analyze_bollinger_bands(current_price)
        
        # Support and Resistance levels
        support_resistance = self._identify_support_resistance(current_price)
        
        return {
            "rsi": {"value": rsi_value, "signal": rsi_signal},
            "moving_averages": {"ma_20": ma_20, "ma_50": ma_50, "trend": ma_trend},
            "macd": macd_signal,
            "bollinger_bands": bb_analysis,
            "support_resistance": support_resistance,
            "overall_trend": self._determine_overall_trend(ma_trend, macd_signal, rsi_signal)
        }
    
    def _analyze_market_microstructure(self, market_data: MarketData) -> Dict[str, Any]:
        """Analyze bid-ask spread, order flow, and market depth indicators"""
        
        bid_ask_spread = market_data.ask - market_data.bid
        spread_percentage = (bid_ask_spread / market_data.price) * 100
        
        # Classify spread tightness
        spread_quality = "tight" if spread_percentage < 0.05 else "normal" if spread_percentage < 0.1 else "wide"
        
        # Mock order flow analysis (would come from Level II data in real implementation)
        order_flow_bias = self._analyze_mock_order_flow(market_data)
        
        # Market impact estimation
        market_impact = self._estimate_market_impact(market_data.volume, spread_percentage)
        
        return {
            "bid_ask_spread": bid_ask_spread,
            "spread_percentage": spread_percentage,
            "spread_quality": spread_quality,
            "order_flow_bias": order_flow_bias,
            "market_impact": market_impact,
            "liquidity_score": self._calculate_liquidity_score(market_data.volume, spread_percentage)
        }
    
    def _detect_patterns(self, market_data: MarketData) -> Dict[str, Any]:
        """Detect chart patterns and formations"""
        
        current_price = market_data.price
        
        # Mock pattern detection (would use historical price data in real implementation)
        detected_patterns = []
        pattern_confidence = 0.0
        
        # Simulate pattern detection based on price characteristics
        price_hash = hash(str(current_price)) % 100
        
        if price_hash < 15:
            detected_patterns.append("ascending_triangle")
            pattern_confidence = 0.75
        elif price_hash < 25:
            detected_patterns.append("flag_pattern")
            pattern_confidence = 0.65
        elif price_hash < 35:
            detected_patterns.append("double_bottom")
            pattern_confidence = 0.80
        
        # Pattern implications
        pattern_bias = self._interpret_patterns(detected_patterns)
        
        return {
            "detected_patterns": detected_patterns,
            "pattern_confidence": pattern_confidence,
            "pattern_bias": pattern_bias,
            "breakout_probability": self._calculate_breakout_probability(detected_patterns)
        }
    
    def _analyze_volume(self, market_data: MarketData) -> Dict[str, Any]:
        """Analyze volume patterns and characteristics"""
        
        current_volume = market_data.volume
        
        # Mock average volume (would be calculated from historical data)
        avg_volume = 800000
        volume_ratio = current_volume / avg_volume
        
        # Volume classification
        volume_strength = "high" if volume_ratio > 1.5 else "normal" if volume_ratio > 0.7 else "low"
        
        # Volume-price relationship
        volume_price_relationship = self._analyze_volume_price_relationship(market_data)
        
        # On-balance volume mock
        obv_trend = "positive" if volume_ratio > 1.2 else "negative" if volume_ratio < 0.8 else "neutral"
        
        return {
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_ratio": volume_ratio,
            "volume_strength": volume_strength,
            "volume_price_relationship": volume_price_relationship,
            "obv_trend": obv_trend,
            "volume_confirmation": self._check_volume_confirmation(volume_strength, obv_trend)
        }
    
    def _combine_analyses(self, technical: Dict, microstructure: Dict, patterns: Dict, volume: Dict, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Combine all technical analyses into unified assessment"""
        
        # Weight different analysis components
        weights = {
            "technical": 0.35,
            "patterns": 0.25,
            "volume": 0.25,
            "microstructure": 0.15
        }
        
        # Adjust weights based on event type
        if event_type == MarketEventType.EARNINGS_SURPRISE:
            weights["volume"] += 0.1
            weights["technical"] -= 0.1
        
        # Calculate component scores
        technical_score = self._score_technical_analysis(technical)
        pattern_score = self._score_pattern_analysis(patterns)
        volume_score = self._score_volume_analysis(volume)
        microstructure_score = self._score_microstructure_analysis(microstructure)
        
        # Calculate weighted overall score
        overall_score = (
            technical_score * weights["technical"] +
            pattern_score * weights["patterns"] +
            volume_score * weights["volume"] +
            microstructure_score * weights["microstructure"]
        )
        
        # Calculate confidence based on alignment of signals
        signal_alignment = self._calculate_signal_alignment(technical, patterns, volume)
        confidence = min(0.95, signal_alignment * 0.8 + abs(overall_score) * 0.2)
        
        # Calculate target price and stop loss
        current_price = technical["support_resistance"]["current_price"]
        target_price, stop_loss = self._calculate_price_targets(overall_score, current_price, technical["support_resistance"])
        
        # Build comprehensive reasoning
        reasoning = self._build_market_reasoning(technical, patterns, volume, microstructure, overall_score)
        
        return {
            "overall_score": overall_score,
            "confidence": confidence,
            "technical_score": technical_score,
            "pattern_score": pattern_score,
            "volume_score": volume_score,
            "microstructure_score": microstructure_score,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_score": self._calculate_technical_risk(overall_score, signal_alignment),
            "reasoning": reasoning,
            "signal_alignment": signal_alignment
        }
    
    def _determine_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine trading recommendation based on technical analysis"""
        
        overall_score = analysis["overall_score"]
        confidence = analysis["confidence"]
        
        # Only make strong recommendations with high confidence
        if confidence < 0.6:
            return TradeAction.HOLD
        
        # Strong bullish signal
        if overall_score > 0.7:
            return TradeAction.BUY
        
        # Strong bearish signal
        if overall_score < -0.7:
            return TradeAction.SELL
        
        # Moderate signals
        if overall_score > 0.4:
            return TradeAction.BUY
        elif overall_score < -0.4:
            return TradeAction.SELL
        
        return TradeAction.HOLD
    
    # Helper methods for technical calculations
    def _calculate_mock_rsi(self, price: float) -> float:
        """Mock RSI calculation (would use real price history in implementation)"""
        return 30 + (hash(str(price)) % 40)  # Returns value between 30-70
    
    def _calculate_mock_macd_signal(self, price: float) -> Dict[str, Any]:
        """Mock MACD signal calculation"""
        macd_value = (hash(str(price * 1.1)) % 200 - 100) / 100  # -1 to 1
        signal_line = macd_value * 0.8
        histogram = macd_value - signal_line
        
        return {
            "macd": macd_value,
            "signal": signal_line,
            "histogram": histogram,
            "trend": "bullish" if histogram > 0 else "bearish"
        }
    
    def _analyze_bollinger_bands(self, price: float) -> Dict[str, Any]:
        """Analyze Bollinger Bands position"""
        bb_middle = price
        bb_upper = price * 1.02
        bb_lower = price * 0.98
        
        bb_position = "middle"
        if price > bb_upper * 0.99:
            bb_position = "upper"
        elif price < bb_lower * 1.01:
            bb_position = "lower"
        
        return {
            "upper_band": bb_upper,
            "middle_band": bb_middle,
            "lower_band": bb_lower,
            "position": bb_position,
            "squeeze": abs(bb_upper - bb_lower) / bb_middle < 0.03
        }
    
    def _identify_support_resistance(self, price: float) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        return {
            "current_price": price,
            "resistance_1": price * 1.03,
            "resistance_2": price * 1.06,
            "support_1": price * 0.97,
            "support_2": price * 0.94,
            "nearest_support": price * 0.97,
            "nearest_resistance": price * 1.03
        }
    
    def _determine_overall_trend(self, ma_trend: str, macd_signal: Dict, rsi_signal: str) -> str:
        """Determine overall market trend from multiple indicators"""
        bullish_signals = 0
        bearish_signals = 0
        
        if ma_trend == "bullish":
            bullish_signals += 1
        elif ma_trend == "bearish":
            bearish_signals += 1
            
        if macd_signal["trend"] == "bullish":
            bullish_signals += 1
        elif macd_signal["trend"] == "bearish":
            bearish_signals += 1
            
        if rsi_signal == "oversold":
            bullish_signals += 1
        elif rsi_signal == "overbought":
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            return "bullish"
        elif bearish_signals > bullish_signals:
            return "bearish"
        else:
            return "neutral"
    
    def _analyze_mock_order_flow(self, market_data: MarketData) -> str:
        """Mock order flow analysis"""
        flow_indicator = hash(str(market_data.volume)) % 3
        return ["bullish", "neutral", "bearish"][flow_indicator]
    
    def _estimate_market_impact(self, volume: int, spread_pct: float) -> str:
        """Estimate market impact of trades"""
        if volume > 1000000 and spread_pct < 0.05:
            return "low"
        elif volume > 500000:
            return "medium"
        else:
            return "high"
    
    def _calculate_liquidity_score(self, volume: int, spread_pct: float) -> float:
        """Calculate liquidity score (0-1)"""
        volume_score = min(1.0, volume / 1000000)
        spread_score = max(0.0, 1.0 - spread_pct / 0.1)
        return (volume_score + spread_score) / 2
    
    def _interpret_patterns(self, patterns: List[str]) -> str:
        """Interpret bullish/bearish bias from detected patterns"""
        bullish_patterns = ["ascending_triangle", "cup_handle", "double_bottom"]
        bearish_patterns = ["descending_triangle", "head_shoulders", "double_top"]
        
        bullish_count = sum(1 for p in patterns if p in bullish_patterns)
        bearish_count = sum(1 for p in patterns if p in bearish_patterns)
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_breakout_probability(self, patterns: List[str]) -> float:
        """Calculate probability of breakout based on patterns"""
        breakout_patterns = ["triangle", "flag", "pennant"]
        breakout_count = sum(1 for p in patterns if any(bp in p for bp in breakout_patterns))
        return min(0.9, breakout_count * 0.3)
    
    def _analyze_volume_price_relationship(self, market_data: MarketData) -> str:
        """Analyze relationship between volume and price"""
        # Mock analysis - in reality would compare with previous periods
        volume_hash = hash(str(market_data.volume)) % 3
        return ["confirming", "neutral", "diverging"][volume_hash]
    
    def _check_volume_confirmation(self, volume_strength: str, obv_trend: str) -> bool:
        """Check if volume confirms price movement"""
        return volume_strength == "high" and obv_trend == "positive"
    
    def _score_technical_analysis(self, technical: Dict) -> float:
        """Score technical analysis components (-1 to 1)"""
        rsi_score = 0
        if technical["rsi"]["signal"] == "oversold":
            rsi_score = 0.3
        elif technical["rsi"]["signal"] == "overbought":
            rsi_score = -0.3
        
        ma_score = 0.4 if technical["moving_averages"]["trend"] == "bullish" else -0.4 if technical["moving_averages"]["trend"] == "bearish" else 0
        
        macd_score = 0.3 if technical["macd"]["trend"] == "bullish" else -0.3
        
        return (rsi_score + ma_score + macd_score) / 3
    
    def _score_pattern_analysis(self, patterns: Dict) -> float:
        """Score pattern analysis (-1 to 1)"""
        if not patterns["detected_patterns"]:
            return 0
        
        bias_score = 0.5 if patterns["pattern_bias"] == "bullish" else -0.5 if patterns["pattern_bias"] == "bearish" else 0
        confidence_weight = patterns["pattern_confidence"]
        
        return bias_score * confidence_weight
    
    def _score_volume_analysis(self, volume: Dict) -> float:
        """Score volume analysis (-1 to 1)"""
        volume_score = 0.3 if volume["volume_strength"] == "high" else -0.2 if volume["volume_strength"] == "low" else 0
        obv_score = 0.3 if volume["obv_trend"] == "positive" else -0.3 if volume["obv_trend"] == "negative" else 0
        confirmation_bonus = 0.2 if volume["volume_confirmation"] else 0
        
        return volume_score + obv_score + confirmation_bonus
    
    def _score_microstructure_analysis(self, microstructure: Dict) -> float:
        """Score microstructure analysis (-1 to 1)"""
        spread_score = 0.2 if microstructure["spread_quality"] == "tight" else -0.1 if microstructure["spread_quality"] == "wide" else 0
        flow_score = 0.3 if microstructure["order_flow_bias"] == "bullish" else -0.3 if microstructure["order_flow_bias"] == "bearish" else 0
        liquidity_score = microstructure["liquidity_score"] * 0.2 - 0.1  # Scale to -0.1 to 0.1
        
        return spread_score + flow_score + liquidity_score
    
    def _calculate_signal_alignment(self, technical: Dict, patterns: Dict, volume: Dict) -> float:
        """Calculate how well different signals align (0-1)"""
        signals = []
        
        if technical["overall_trend"] != "neutral":
            signals.append(technical["overall_trend"])
        if patterns["pattern_bias"] != "neutral":
            signals.append(patterns["pattern_bias"])
        if volume["obv_trend"] != "neutral":
            signals.append("bullish" if volume["obv_trend"] == "positive" else "bearish")
        
        if not signals:
            return 0.5
        
        bullish_count = signals.count("bullish")
        bearish_count = signals.count("bearish")
        total_signals = len(signals)
        
        alignment = max(bullish_count, bearish_count) / total_signals
        return alignment
    
    def _calculate_price_targets(self, overall_score: float, current_price: float, support_resistance: Dict) -> Tuple[float, float]:
        """Calculate target price and stop loss"""
        if overall_score > 0:  # Bullish
            target_price = current_price * (1 + abs(overall_score) * 0.05)  # Up to 5% target
            stop_loss = support_resistance["nearest_support"]
        else:  # Bearish
            target_price = current_price * (1 - abs(overall_score) * 0.05)  # Down to 5% target
            stop_loss = support_resistance["nearest_resistance"]
        
        return target_price, stop_loss
    
    def _calculate_technical_risk(self, overall_score: float, signal_alignment: float) -> float:
        """Calculate technical risk score"""
        base_risk = 0.5
        score_risk = abs(overall_score) * 0.3  # Higher scores = more risk
        alignment_risk = (1 - signal_alignment) * 0.4  # Less alignment = more risk
        
        return min(1.0, base_risk + score_risk + alignment_risk)
    
    def _build_market_reasoning(self, technical: Dict, patterns: Dict, volume: Dict, microstructure: Dict, overall_score: float) -> str:
        """Build comprehensive reasoning for market analysis"""
        
        reasoning_parts = []
        
        # Technical indicators
        trend = technical["overall_trend"]
        reasoning_parts.append(f"Overall technical trend is {trend}")
        
        # RSI
        rsi_info = technical["rsi"]
        if rsi_info["signal"] != "neutral":
            reasoning_parts.append(f"RSI shows {rsi_info['signal']} conditions ({rsi_info['value']:.1f})")
        
        # Patterns
        if patterns["detected_patterns"]:
            pattern_list = ", ".join(patterns["detected_patterns"])
            reasoning_parts.append(f"Detected patterns: {pattern_list} with {patterns['pattern_bias']} bias")
        
        # Volume
        vol_strength = volume["volume_strength"]
        if vol_strength != "normal":
            reasoning_parts.append(f"Volume is {vol_strength} ({volume['volume_ratio']:.1f}x average)")
        
        # Overall assessment
        score_desc = "strongly bullish" if overall_score > 0.5 else "bullish" if overall_score > 0.2 else "strongly bearish" if overall_score < -0.5 else "bearish" if overall_score < -0.2 else "neutral"
        reasoning_parts.append(f"Combined technical analysis is {score_desc} ({overall_score:.2f})")
        
        return ". ".join(reasoning_parts)


class RiskAssessmentAgent(BaseAgent):
    """
    AI Agent specialized in risk management, position sizing, and downside protection.
    Focuses on capital preservation and risk-adjusted returns.
    """
    
    def __init__(self):
        super().__init__(AgentType.RISK_ASSESSMENT)
        self.max_position_size = 0.10  # Max 10% of portfolio per position
        self.max_sector_exposure = 0.25  # Max 25% exposure to any sector
        self.volatility_threshold = 0.30  # 30% annualized volatility threshold
        self.correlation_threshold = 0.7  # High correlation threshold
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze risk factors and provide risk-adjusted recommendation"""
        
        market_data = context["market_data"]
        news_events = context["news_events"]
        symbol = context["symbol"]
        event_type = context.get("event_type")
        
        # Perform comprehensive risk analysis
        volatility_analysis = self._analyze_volatility(market_data)
        position_sizing = self._calculate_position_sizing(market_data, volatility_analysis)
        downside_analysis = self._analyze_downside_risk(market_data, news_events)
        portfolio_risk = self._assess_portfolio_risk(market_data, symbol)
        tail_risk = self._assess_tail_risk(market_data, event_type)
        
        # Combine risk assessments
        risk_assessment = self._combine_risk_assessments(
            volatility_analysis, position_sizing, downside_analysis, 
            portfolio_risk, tail_risk, event_type
        )
        
        # Determine risk-adjusted recommendation
        recommendation = self._determine_risk_adjusted_recommendation(risk_assessment, market_data)
        
        return AgentResponse(
            agent_type=self.agent_type,
            confidence=risk_assessment["confidence"],
            recommendation=recommendation,
            reasoning=risk_assessment["reasoning"],
            supporting_data=risk_assessment,
            timestamp=datetime.now(),
            risk_score=risk_assessment["overall_risk_score"],
            target_price=risk_assessment.get("risk_adjusted_target"),
            stop_loss=risk_assessment.get("stop_loss_level")
        )
    
    def _analyze_volatility(self, market_data: MarketData) -> Dict[str, Any]:
        """Analyze volatility characteristics and risk"""
        
        # Mock volatility calculation (would use historical price data)
        price_volatility = self._calculate_mock_volatility(market_data.price)
        
        # VIX analysis
        vix_level = market_data.vix or 20.0
        vix_regime = "low" if vix_level < 15 else "normal" if vix_level < 25 else "high" if vix_level < 35 else "extreme"
        
        # Volatility risk assessment
        vol_risk_score = min(1.0, price_volatility / self.volatility_threshold)
        
        return {
            "price_volatility": price_volatility,
            "vix_level": vix_level,
            "vix_regime": vix_regime,
            "volatility_risk_score": vol_risk_score,
            "is_high_volatility": price_volatility > self.volatility_threshold
        }
    
    def _calculate_position_sizing(self, market_data: MarketData, volatility_analysis: Dict) -> Dict[str, Any]:
        """Calculate appropriate position size based on risk"""
        
        base_position_size = self.max_position_size
        volatility_adjustment = 1.0 - (volatility_analysis["volatility_risk_score"] * 0.5)
        
        # Adjust for market conditions
        vix_adjustment = 1.0
        if volatility_analysis["vix_regime"] == "high":
            vix_adjustment = 0.7
        elif volatility_analysis["vix_regime"] == "extreme":
            vix_adjustment = 0.5
        
        # Calculate final position size
        recommended_position_size = base_position_size * volatility_adjustment * vix_adjustment
        recommended_position_size = max(0.01, min(self.max_position_size, recommended_position_size))
        
        return {
            "base_position_size": base_position_size,
            "volatility_adjustment": volatility_adjustment,
            "vix_adjustment": vix_adjustment,
            "recommended_position_size": recommended_position_size,
            "risk_adjustment_factor": volatility_adjustment * vix_adjustment
        }
    
    def _analyze_downside_risk(self, market_data: MarketData, news_events: List[NewsEvent]) -> Dict[str, Any]:
        """Analyze potential downside scenarios"""
        
        current_price = market_data.price
        
        # Calculate potential drawdown scenarios
        scenarios = {
            "mild_correction": current_price * 0.95,  # 5% drop
            "moderate_correction": current_price * 0.90,  # 10% drop
            "severe_correction": current_price * 0.80,  # 20% drop
        }
        
        # Assess probability of each scenario based on news and market conditions
        scenario_probabilities = self._calculate_scenario_probabilities(news_events, market_data)
        
        # Calculate expected downside
        expected_downside = sum(
            (current_price - price) * prob 
            for (scenario, price), prob in zip(scenarios.items(), scenario_probabilities.values())
        )
        
        # Value at Risk estimation (1% VaR)
        var_1_percent = self._calculate_var(current_price, market_data)
        
        return {
            "scenarios": scenarios,
            "scenario_probabilities": scenario_probabilities,
            "expected_downside": expected_downside,
            "var_1_percent": var_1_percent,
            "max_tolerable_loss": current_price * 0.02,  # 2% max loss tolerance
            "downside_risk_score": min(1.0, expected_downside / (current_price * 0.1))
        }
    
    def _assess_portfolio_risk(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Assess portfolio-level risk implications"""
        
        # Mock portfolio analysis (would integrate with actual portfolio data)
        current_sector_exposure = 0.15  # Mock 15% tech exposure
        sector = market_data.sector or "Unknown"
        
        # Check sector concentration risk
        sector_risk = "high" if current_sector_exposure > self.max_sector_exposure else "normal"
        
        # Mock correlation analysis
        portfolio_correlation = self._calculate_mock_correlation(symbol)
        correlation_risk = "high" if portfolio_correlation > self.correlation_threshold else "normal"
        
        return {
            "current_sector_exposure": current_sector_exposure,
            "sector": sector,
            "sector_risk": sector_risk,
            "portfolio_correlation": portfolio_correlation,
            "correlation_risk": correlation_risk,
            "diversification_score": 1.0 - portfolio_correlation
        }
    
    def _assess_tail_risk(self, market_data: MarketData, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Assess tail risk and black swan scenarios"""
        
        # Base tail risk assessment
        base_tail_risk = 0.1
        
        # Adjust based on event type
        event_risk_multipliers = {
            MarketEventType.GEOPOLITICAL_SHOCK: 3.0,
            MarketEventType.FED_ANNOUNCEMENT: 2.0,
            MarketEventType.EARNINGS_SURPRISE: 1.5,
            MarketEventType.VIX_SPIKE: 2.5,
            MarketEventType.SECTOR_ROTATION: 1.3
        }
        
        tail_risk_multiplier = event_risk_multipliers.get(event_type, 1.0)
        tail_risk_score = min(1.0, base_tail_risk * tail_risk_multiplier)
        
        # Market stress indicators
        vix_level = market_data.vix or 20.0
        stress_level = "low" if vix_level < 20 else "medium" if vix_level < 30 else "high"
        
        return {
            "base_tail_risk": base_tail_risk,
            "event_risk_multiplier": tail_risk_multiplier,
            "tail_risk_score": tail_risk_score,
            "market_stress_level": stress_level,
            "black_swan_probability": tail_risk_score * 0.1
        }
    
    def _combine_risk_assessments(self, volatility: Dict, position_sizing: Dict, downside: Dict, portfolio: Dict, tail_risk: Dict, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Combine all risk assessments into unified risk profile"""
        
        # Calculate component risk scores
        volatility_risk = volatility["volatility_risk_score"]
        downside_risk = downside["downside_risk_score"]
        portfolio_risk = 0.5 if portfolio["sector_risk"] == "normal" and portfolio["correlation_risk"] == "normal" else 0.8
        tail_risk_score = tail_risk["tail_risk_score"]
        
        # Weight risk components
        risk_weights = {
            "volatility": 0.25,
            "downside": 0.30,
            "portfolio": 0.25,
            "tail_risk": 0.20
        }
        
        # Adjust weights based on event type
        if event_type in [MarketEventType.GEOPOLITICAL_SHOCK, MarketEventType.VIX_SPIKE]:
            risk_weights["tail_risk"] += 0.1
            risk_weights["volatility"] -= 0.1
        
        # Calculate overall risk score
        overall_risk_score = (
            volatility_risk * risk_weights["volatility"] +
            downside_risk * risk_weights["downside"] +
            portfolio_risk * risk_weights["portfolio"] +
            tail_risk_score * risk_weights["tail_risk"]
        )
        
        # Calculate confidence (higher when risk assessment is clear)
        risk_clarity = abs(overall_risk_score - 0.5) * 2  # 0-1 scale
        confidence = 0.6 + (risk_clarity * 0.3)  # 0.6-0.9 range
        
        # Risk-adjusted targets
        risk_adjusted_target = self._calculate_risk_adjusted_target(downside, overall_risk_score)
        stop_loss_level = self._calculate_stop_loss_level(downside, overall_risk_score)
        
        # Build risk reasoning
        reasoning = self._build_risk_reasoning(volatility, downside, portfolio, tail_risk, overall_risk_score)
        
        return {
            "overall_risk_score": overall_risk_score,
            "confidence": confidence,
            "volatility_risk": volatility_risk,
            "downside_risk": downside_risk,
            "portfolio_risk": portfolio_risk,
            "tail_risk_score": tail_risk_score,
            "recommended_position_size": position_sizing["recommended_position_size"],
            "risk_adjusted_target": risk_adjusted_target,
            "stop_loss_level": stop_loss_level,
            "reasoning": reasoning
        }
    
    def _determine_risk_adjusted_recommendation(self, risk_assessment: Dict, market_data: MarketData) -> TradeAction:
        """Determine recommendation with risk management overlay"""
        
        overall_risk = risk_assessment["overall_risk_score"]
        confidence = risk_assessment["confidence"]
        
        # High risk situations - be very conservative
        if overall_risk > 0.75:
            return TradeAction.HOLD
        
        # Medium-high risk - only strong signals
        if overall_risk > 0.6 and confidence < 0.8:
            return TradeAction.HOLD
        
        # Low confidence in risk assessment
        if confidence < 0.6:
            return TradeAction.HOLD
        
        # If we reach here, risk is manageable, but still be conservative
        # Return neutral recommendation - let other agents drive the decision
        return TradeAction.HOLD
    
    # Helper methods
    def _calculate_mock_volatility(self, price: float) -> float:
        """Mock volatility calculation"""
        return 0.15 + (hash(str(price)) % 30) / 100  # 15-45% annualized
    
    def _calculate_scenario_probabilities(self, news_events: List[NewsEvent], market_data: MarketData) -> Dict[str, float]:
        """Calculate probabilities for different downside scenarios"""
        base_probs = {"mild_correction": 0.3, "moderate_correction": 0.15, "severe_correction": 0.05}
        
        # Adjust based on news sentiment
        negative_news_count = sum(1 for event in news_events if event.sentiment_score < -0.3)
        if negative_news_count > 0:
            multiplier = 1 + (negative_news_count * 0.5)
            for scenario in base_probs:
                base_probs[scenario] = min(0.8, base_probs[scenario] * multiplier)
        
        return base_probs
    
    def _calculate_var(self, price: float, market_data: MarketData) -> float:
        """Calculate Value at Risk (1% probability)"""
        volatility = self._calculate_mock_volatility(price)
        return price * volatility * 2.33  # 1% VaR approximation
    
    def _calculate_mock_correlation(self, symbol: str) -> float:
        """Mock portfolio correlation calculation"""
        return 0.3 + (hash(symbol) % 50) / 100  # 0.3-0.8 correlation
    
    def _calculate_risk_adjusted_target(self, downside: Dict, risk_score: float) -> float:
        """Calculate risk-adjusted price target"""
        scenarios = downside["scenarios"]
        mild_correction = scenarios["mild_correction"]
        
        # Conservative target based on risk level
        risk_discount = risk_score * 0.1  # Up to 10% discount for high risk
        return mild_correction * (1 - risk_discount)
    
    def _calculate_stop_loss_level(self, downside: Dict, risk_score: float) -> float:
        """Calculate appropriate stop loss level"""
        max_tolerable_loss = downside["max_tolerable_loss"]
        
        # Tighter stops for higher risk
        risk_adjustment = 1.0 - (risk_score * 0.3)
        return max_tolerable_loss * risk_adjustment
    
    def _build_risk_reasoning(self, volatility: Dict, downside: Dict, portfolio: Dict, tail_risk: Dict, overall_risk: float) -> str:
        """Build comprehensive risk reasoning"""
        
        reasoning_parts = []
        
        # Overall risk assessment
        risk_level = "high" if overall_risk > 0.7 else "medium" if overall_risk > 0.4 else "low"
        reasoning_parts.append(f"Overall risk assessment: {risk_level} ({overall_risk:.2f})")
        
        # Volatility concerns
        if volatility["is_high_volatility"]:
            reasoning_parts.append(f"High volatility detected ({volatility['price_volatility']:.1%})")
        
        # VIX regime
        if volatility["vix_regime"] in ["high", "extreme"]:
            reasoning_parts.append(f"Market stress elevated (VIX: {volatility['vix_level']:.1f})")
        
        # Portfolio risks
        if portfolio["sector_risk"] == "high":
            reasoning_parts.append(f"Sector concentration risk in {portfolio['sector']}")
        
        if portfolio["correlation_risk"] == "high":
            reasoning_parts.append(f"High portfolio correlation ({portfolio['portfolio_correlation']:.2f})")
        
        # Tail risk
        if tail_risk["tail_risk_score"] > 0.3:
            reasoning_parts.append(f"Elevated tail risk ({tail_risk['market_stress_level']} stress)")
        
        # Position sizing recommendation
        pos_size = downside.get("recommended_position_size", 0.05)
        reasoning_parts.append(f"Recommended position size: {pos_size:.1%}")
        
        return ". ".join(reasoning_parts)


class SentimentAnalysisAgent(BaseAgent):
    """
    AI Agent specialized in market sentiment analysis from multiple sources.
    Analyzes social media, options flow, analyst sentiment, and market positioning.
    """
    
    def __init__(self):
        super().__init__(AgentType.SENTIMENT_ANALYSIS)
        self.sentiment_sources = [
            "social_media", "options_flow", "analyst_ratings", 
            "insider_trading", "institutional_flow", "retail_sentiment"
        ]
        self.sentiment_weights = {
            "options_flow": 0.25,
            "institutional_flow": 0.25,
            "analyst_ratings": 0.20,
            "social_media": 0.15,
            "insider_trading": 0.10,
            "retail_sentiment": 0.05
        }
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze market sentiment from multiple sources"""
        
        market_data = context["market_data"]
        news_events = context["news_events"]
        symbol = context["symbol"]
        event_type = context.get("event_type")
        
        # Analyze different sentiment sources
        options_sentiment = self._analyze_options_sentiment(market_data, symbol)
        social_sentiment = self._analyze_social_media_sentiment(news_events, symbol)
        analyst_sentiment = self._analyze_analyst_sentiment(symbol)
        institutional_sentiment = self._analyze_institutional_sentiment(market_data, symbol)
        insider_sentiment = self._analyze_insider_sentiment(symbol)
        retail_sentiment = self._analyze_retail_sentiment(market_data, symbol)
        
        # Combine sentiment analyses
        combined_sentiment = self._combine_sentiment_analyses(
            options_sentiment, social_sentiment, analyst_sentiment,
            institutional_sentiment, insider_sentiment, retail_sentiment, event_type
        )
        
        # Determine sentiment-based recommendation
        recommendation = self._determine_sentiment_recommendation(combined_sentiment)
        
        return AgentResponse(
            agent_type=self.agent_type,
            confidence=combined_sentiment["confidence"],
            recommendation=recommendation,
            reasoning=combined_sentiment["reasoning"],
            supporting_data=combined_sentiment,
            timestamp=datetime.now(),
            risk_score=combined_sentiment.get("sentiment_risk_score", 0.5)
        )
    
    def _analyze_options_sentiment(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Analyze options flow and positioning"""
        
        # Mock options data (would come from options chain APIs)
        put_call_ratio = 0.6 + (hash(symbol) % 80) / 100  # 0.6-1.4 range
        
        # Options sentiment interpretation
        options_bias = "bullish" if put_call_ratio < 0.8 else "bearish" if put_call_ratio > 1.2 else "neutral"
        
        # Mock unusual options activity
        unusual_activity = hash(str(market_data.volume)) % 4 == 0
        activity_type = "calls" if hash(symbol) % 2 == 0 else "puts"
        
        # Smart money indicators
        smart_money_flow = self._analyze_smart_money_options(put_call_ratio, unusual_activity)
        
        return {
            "put_call_ratio": put_call_ratio,
            "options_bias": options_bias,
            "unusual_activity": unusual_activity,
            "activity_type": activity_type,
            "smart_money_flow": smart_money_flow,
            "options_sentiment_score": self._score_options_sentiment(put_call_ratio, smart_money_flow)
        }
    
    def _analyze_social_media_sentiment(self, news_events: List[NewsEvent], symbol: str) -> Dict[str, Any]:
        """Analyze social media and retail sentiment"""
        
        # Aggregate sentiment from news (proxy for social sentiment)
        social_scores = [event.sentiment_score for event in news_events if symbol in event.symbols_mentioned]
        
        if not social_scores:
            avg_sentiment = 0.0
            sentiment_volume = 0
        else:
            avg_sentiment = sum(social_scores) / len(social_scores)
            sentiment_volume = len(social_scores)
        
        # Mock social media metrics
        mention_volume = sentiment_volume * 100  # Mock mentions
        sentiment_momentum = self._calculate_sentiment_momentum(avg_sentiment)
        
        # Retail sentiment classification
        retail_bias = "bullish" if avg_sentiment > 0.3 else "bearish" if avg_sentiment < -0.3 else "neutral"
        
        return {
            "average_sentiment": avg_sentiment,
            "mention_volume": mention_volume,
            "sentiment_momentum": sentiment_momentum,
            "retail_bias": retail_bias,
            "sentiment_strength": abs(avg_sentiment),
            "social_sentiment_score": avg_sentiment
        }
    
    def _analyze_analyst_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze Wall Street analyst sentiment"""
        
        # Mock analyst data
        analyst_ratings = {
            "strong_buy": hash(symbol + "sb") % 5,
            "buy": hash(symbol + "b") % 8,
            "hold": hash(symbol + "h") % 10,
            "sell": hash(symbol + "s") % 3,
            "strong_sell": hash(symbol + "ss") % 2
        }
        
        total_ratings = sum(analyst_ratings.values())
        
        # Calculate weighted sentiment
        weights = {"strong_buy": 1.0, "buy": 0.5, "hold": 0.0, "sell": -0.5, "strong_sell": -1.0}
        weighted_score = sum(count * weights[rating] for rating, count in analyst_ratings.items())
        
        if total_ratings > 0:
            analyst_sentiment_score = weighted_score / total_ratings
        else:
            analyst_sentiment_score = 0.0
        
        # Recent rating changes
        recent_upgrades = hash(symbol + "upgrade") % 3
        recent_downgrades = hash(symbol + "downgrade") % 3
        rating_momentum = "positive" if recent_upgrades > recent_downgrades else "negative" if recent_downgrades > recent_upgrades else "stable"
        
        return {
            "analyst_ratings": analyst_ratings,
            "total_analysts": total_ratings,
            "analyst_sentiment_score": analyst_sentiment_score,
            "recent_upgrades": recent_upgrades,
            "recent_downgrades": recent_downgrades,
            "rating_momentum": rating_momentum
        }
    
    def _analyze_institutional_sentiment(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Analyze institutional investor sentiment and flow"""
        
        # Mock institutional flow data
        institutional_flow = (hash(symbol + "inst") % 200 - 100) / 100  # -1 to 1
        
        # Flow classification
        flow_strength = "strong_inflow" if institutional_flow > 0.5 else "inflow" if institutional_flow > 0.1 else "strong_outflow" if institutional_flow < -0.5 else "outflow" if institutional_flow < -0.1 else "neutral"
        
        # Mock fund positioning
        fund_positioning = {
            "overweight": hash(symbol + "ow") % 30,
            "neutral": hash(symbol + "n") % 40,
            "underweight": hash(symbol + "uw") % 30
        }
        
        # Calculate positioning bias
        total_positions = sum(fund_positioning.values())
        positioning_score = (fund_positioning["overweight"] - fund_positioning["underweight"]) / max(total_positions, 1)
        
        return {
            "institutional_flow": institutional_flow,
            "flow_strength": flow_strength,
            "fund_positioning": fund_positioning,
            "positioning_score": positioning_score,
            "institutional_sentiment_score": (institutional_flow + positioning_score) / 2
        }
    
    def _analyze_insider_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze insider trading activity"""
        
        # Mock insider trading data
        insider_buys = hash(symbol + "buy") % 5
        insider_sells = hash(symbol + "sell") % 8
        
        # Calculate insider sentiment
        if insider_buys + insider_sells == 0:
            insider_ratio = 0
        else:
            insider_ratio = (insider_buys - insider_sells) / (insider_buys + insider_sells)
        
        insider_bias = "bullish" if insider_ratio > 0.2 else "bearish" if insider_ratio < -0.2 else "neutral"
        
        return {
            "insider_buys": insider_buys,
            "insider_sells": insider_sells,
            "insider_ratio": insider_ratio,
            "insider_bias": insider_bias,
            "insider_sentiment_score": insider_ratio
        }
    
    def _analyze_retail_sentiment(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Analyze retail investor sentiment"""
        
        # Mock retail sentiment indicators
        retail_volume_ratio = market_data.volume / 1000000  # Normalize volume
        retail_activity = "high" if retail_volume_ratio > 1.5 else "normal" if retail_volume_ratio > 0.7 else "low"
        
        # Mock retail positioning
        retail_long_short_ratio = 1.2 + (hash(symbol + "retail") % 160) / 100  # 1.2-2.8
        retail_bias = "bullish" if retail_long_short_ratio > 2.0 else "bearish" if retail_long_short_ratio < 1.5 else "neutral"
        
        return {
            "retail_activity": retail_activity,
            "retail_long_short_ratio": retail_long_short_ratio,
            "retail_bias": retail_bias,
            "retail_sentiment_score": (retail_long_short_ratio - 1.5) / 1.3  # Normalize to -1 to 1
        }
    
    def _combine_sentiment_analyses(self, options: Dict, social: Dict, analyst: Dict, institutional: Dict, insider: Dict, retail: Dict, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Combine all sentiment sources into unified sentiment assessment"""
        
        # Extract sentiment scores
        sentiment_scores = {
            "options_flow": options["options_sentiment_score"],
            "social_media": social["social_sentiment_score"],
            "analyst_ratings": analyst["analyst_sentiment_score"],
            "institutional_flow": institutional["institutional_sentiment_score"],
            "insider_trading": insider["insider_sentiment_score"],
            "retail_sentiment": retail["retail_sentiment_score"]
        }
        
        # Apply weights and calculate overall sentiment
        overall_sentiment = sum(
            score * self.sentiment_weights[source] 
            for source, score in sentiment_scores.items()
        )
        
        # Adjust weights based on event type
        if event_type == MarketEventType.EARNINGS_SURPRISE:
            # Options flow more important during earnings
            overall_sentiment += (options["options_sentiment_score"] - overall_sentiment) * 0.2
        
        # Calculate sentiment confidence based on source agreement
        sentiment_agreement = self._calculate_sentiment_agreement(sentiment_scores)
        confidence = 0.5 + (sentiment_agreement * 0.4)
        
        # Sentiment momentum and divergences
        momentum_analysis = self._analyze_sentiment_momentum(sentiment_scores)
        
        # Risk assessment from sentiment extremes
        sentiment_risk_score = self._calculate_sentiment_risk(overall_sentiment, sentiment_agreement)
        
        # Build reasoning
        reasoning = self._build_sentiment_reasoning(sentiment_scores, overall_sentiment, momentum_analysis)
        
        return {
            "overall_sentiment": overall_sentiment,
            "confidence": confidence,
            "sentiment_scores": sentiment_scores,
            "sentiment_agreement": sentiment_agreement,
            "momentum_analysis": momentum_analysis,
            "sentiment_risk_score": sentiment_risk_score,
            "reasoning": reasoning
        }
    
    def _determine_sentiment_recommendation(self, sentiment_analysis: Dict) -> TradeAction:
        """Determine recommendation based on sentiment analysis"""
        
        overall_sentiment = sentiment_analysis["overall_sentiment"]
        confidence = sentiment_analysis["confidence"]
        
        # Only act on high-confidence sentiment signals
        if confidence < 0.65:
            return TradeAction.HOLD
        
        # Strong sentiment signals
        if overall_sentiment > 0.6:
            return TradeAction.BUY
        elif overall_sentiment < -0.6:
            return TradeAction.SELL
        
        # Moderate sentiment signals
        if overall_sentiment > 0.3:
            return TradeAction.BUY
        elif overall_sentiment < -0.3:
            return TradeAction.SELL
        
        return TradeAction.HOLD
    
    # Helper methods
    def _analyze_smart_money_options(self, put_call_ratio: float, unusual_activity: bool) -> str:
        """Analyze smart money flow in options"""
        if unusual_activity and put_call_ratio < 0.7:
            return "bullish"
        elif unusual_activity and put_call_ratio > 1.3:
            return "bearish"
        else:
            return "neutral"
    
    def _score_options_sentiment(self, put_call_ratio: float, smart_money_flow: str) -> float:
        """Score options sentiment (-1 to 1)"""
        base_score = (1.0 - put_call_ratio) / 0.5  # Normalize around 1.0 P/C ratio
        
        if smart_money_flow == "bullish":
            base_score += 0.3
        elif smart_money_flow == "bearish":
            base_score -= 0.3
        
        return max(-1.0, min(1.0, base_score))
    
    def _calculate_sentiment_momentum(self, sentiment_score: float) -> str:
        """Calculate sentiment momentum direction"""
        # Mock momentum calculation
        momentum_indicator = hash(str(sentiment_score)) % 3
        return ["improving", "stable", "deteriorating"][momentum_indicator]
    
    def _calculate_sentiment_agreement(self, sentiment_scores: Dict[str, float]) -> float:
        """Calculate how much different sentiment sources agree"""
        scores = list(sentiment_scores.values())
        if not scores:
            return 0.5
        
        # Calculate standard deviation of sentiment scores
        mean_sentiment = sum(scores) / len(scores)
        variance = sum((score - mean_sentiment) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Convert to agreement score (lower std dev = higher agreement)
        agreement = max(0.0, 1.0 - std_dev)
        return agreement
    
    def _analyze_sentiment_momentum(self, sentiment_scores: Dict[str, float]) -> Dict[str, Any]:
        """Analyze momentum across"""


# Example usage and testing
if __name__ == "__main__":
    async def test_market_analysis_agent():
        """Test the Market Analysis Agent"""
        
        # Initialize orchestrator and agents
        orchestrator = OrchestratorCore()
        news_agent = NewsIntelligenceAgent()
        market_agent = MarketAnalysisAgent()
        
        orchestrator.register_agent(news_agent)
        orchestrator.register_agent(market_agent)
        
        # Create mock market data with technical characteristics
        market_data = MarketData(
            symbol="TSLA",
            price=245.50,
            volume=1200000,  # High volume
            timestamp=datetime.now(),
            bid=245.45,
            ask=245.55,  # Tight spread
            vix=18.5,
            sector="Technology"
        )
        
        # Create minimal news for context
        news_events = [
            NewsEvent(
                id=str(uuid.uuid4()),
                title="Tesla Reports Q4 Delivery Numbers",
                content="Tesla delivered more vehicles than expected in Q4...",
                source="Reuters",
                timestamp=datetime.now() - timedelta(hours=1),
                relevance_score=0.7,
                symbols_mentioned=["TSLA"],
                sentiment_score=0.6,
                event_type=MarketEventType.MAJOR_NEWS
            )
        ]
        
        # Test coordination with both agents
        print("🔍 Testing Market Analysis Agent...")
        decision = await orchestrator.coordinate_analysis("TSLA", market_data, news_events)
        
        print(f"\n📊 Market Analysis Results:")
        print(f"Decision: {decision['action'].value}")
        print(f"Confidence: {decision['confidence']:.2f}")
        print(f"Reasoning: {decision['reasoning']}")
        print(f"Event Type: {decision.get('event_type', 'None')}")
        
        # Test individual agent response
        context = {
            "symbol": "TSLA",
            "market_data": market_data,
            "news_events": news_events,
            "event_type": MarketEventType.MAJOR_NEWS
        }
        
        market_response = await market_agent.analyze(context)
        
        print(f"\n🎯 Individual Market Agent Analysis:")
        print(f"Recommendation: {market_response.recommendation.value}")
        print(f"Confidence: {market_response.confidence:.2f}")
        print(f"Target Price: ${market_response.target_price:.2f}")
        print(f"Stop Loss: ${market_response.stop_loss:.2f}")
        print(f"Risk Score: {market_response.risk_score:.2f}")
        
        print("\n✅ Market Analysis Agent implemented and tested")
        print("📈 Technical analysis capabilities:")
        print("  - RSI, MACD, Moving Averages")
        print("  - Pattern Recognition")
        print("  - Volume Analysis")
        print("  - Market Microstructure")
        print("  - Support/Resistance Levels")
        print("\nReady for next agent implementation!")
    
    # Run test
    asyncio.run(test_market_analysis_agent())