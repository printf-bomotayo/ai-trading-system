"""
trading_system/orchestrator.py
===============================

Orchestrator and performance management components for the AI Trading System.
Handles agent coordination, performance tracking, and event detection.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import logging

from .core import (
    MarketData, NewsEvent, AgentResponse, PerformanceMetric,
    BaseAgent, AgentType, MarketEventType, TradeAction
)

logger = logging.getLogger(__name__)


class MarketEventDetector:
    """Detects significant market events that trigger performance recalibration"""
    
    def __init__(self, vix_threshold: float = 25.0, price_move_threshold: float = 0.05):
        self.vix_threshold = vix_threshold
        self.price_move_threshold = price_move_threshold
        self.last_price_check: Dict[str, float] = {}
        
    def is_significant_event(self, market_data: MarketData, news_events: List[NewsEvent]) -> Tuple[bool, Optional[MarketEventType]]:
        """Determine if current market conditions constitute a significant event"""
        
        try:
            # Check VIX spike
            if market_data.vix and market_data.vix > self.vix_threshold:
                logger.info(f"VIX spike detected: {market_data.vix}")
                return True, MarketEventType.VIX_SPIKE
            
            # Check for major price movement
            symbol = market_data.symbol
            if symbol in self.last_price_check:
                price_change = abs(market_data.price - self.last_price_check[symbol]) / self.last_price_check[symbol]
                if price_change > self.price_move_threshold:
                    logger.info(f"Significant price movement detected: {price_change:.2%}")
                    return True, MarketEventType.MAJOR_NEWS
            
            self.last_price_check[symbol] = market_data.price
            
            # Check for major news events
            for event in news_events:
                if event.relevance_score > 0.8 and event.event_type:
                    logger.info(f"Significant news event detected: {event.event_type}")
                    return True, event.event_type
                    
            return False, None
            
        except Exception as e:
            logger.error(f"Error in event detection: {e}")
            return False, None


class PerformanceTracker:
    """Tracks and manages agent performance metrics"""
    
    def __init__(self):
        self.agent_metrics: Dict[AgentType, PerformanceMetric] = {}
        self.last_recalibration = datetime.now()
        self.recalibration_threshold = timedelta(hours=24)
        
    def initialize_agent(self, agent_type: AgentType) -> None:
        """Initialize performance tracking for an agent"""
        if not isinstance(agent_type, AgentType):
            raise TypeError("agent_type must be an AgentType enum")
            
        self.agent_metrics[agent_type] = PerformanceMetric(
            agent_type=agent_type,
            accuracy_rate=0.5,
            confidence_calibration=1.0,
            last_updated=datetime.now(),
            total_predictions=0,
            correct_predictions=0
        )
        logger.info(f"Initialized performance tracking for {agent_type.value}")
    
    def update_performance(self, agent_type: AgentType, was_correct: bool, confidence: float, event_type: Optional[MarketEventType] = None) -> None:
        """Update agent performance after a significant market event"""
        try:
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
                current_perf = metric.performance_by_event_type[event_type]
                metric.performance_by_event_type[event_type] = (current_perf * 0.8) + (float(was_correct) * 0.2)
            
            metric.last_updated = datetime.now()
            logger.info(f"Updated performance for {agent_type.value}: {metric.accuracy_rate:.2%}")
            
        except Exception as e:
            logger.error(f"Error updating performance for {agent_type.value}: {e}")
            
    def get_agent_weight(self, agent_type: AgentType, confidence: float, current_event_type: Optional[MarketEventType] = None) -> float:
        """Calculate weighted score for agent recommendation"""
        try:
            if agent_type not in self.agent_metrics:
                return confidence * 0.5
                
            metric = self.agent_metrics[agent_type]
            
            # Base weight from confidence and historical accuracy
            base_weight = confidence * metric.accuracy_rate
            
            # Adjust based on event-specific performance
            if current_event_type and current_event_type in metric.performance_by_event_type:
                event_performance = metric.performance_by_event_type[current_event_type]
                base_weight = base_weight * event_performance
                
            # Apply confidence calibration
            base_weight = base_weight * metric.confidence_calibration
            
            return max(0.0, min(1.0, base_weight))
            
        except Exception as e:
            logger.error(f"Error calculating weight for {agent_type.value}: {e}")
            return confidence * 0.5


class OrchestratorCore:
    """Core orchestrator that coordinates all AI agents"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.performance_tracker = PerformanceTracker()
        self.event_detector = MarketEventDetector()
        self.decision_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an AI agent with the orchestrator"""
        if not isinstance(agent, BaseAgent):
            raise TypeError("Agent must inherit from BaseAgent")
            
        if agent.agent_type in self.agents:
            logger.warning(f"Overwriting existing agent: {agent.agent_type.value}")
            
        self.agents[agent.agent_type] = agent
        self.performance_tracker.initialize_agent(agent.agent_type)
        logger.info(f"Registered {agent.agent_type.value} agent")
        
    def unregister_agent(self, agent_type: AgentType) -> bool:
        """Unregister an agent"""
        if agent_type in self.agents:
            del self.agents[agent_type]
            logger.info(f"Unregistered {agent_type.value} agent")
            return True
        return False
        
    async def coordinate_analysis(self, symbol: str, market_data: MarketData, news_events: List[NewsEvent]) -> Dict[str, Any]:
        """Coordinate analysis across all agents and make decision"""
        
        try:
            # Validate inputs
            if not symbol or not isinstance(symbol, str):
                raise ValueError("Symbol must be a non-empty string")
            if not isinstance(market_data, MarketData):
                raise TypeError("market_data must be MarketData instance")
            if not isinstance(news_events, list):
                raise TypeError("news_events must be a list")
            
            # Detect significant market events
            is_significant, event_type = self.event_detector.is_significant_event(market_data, news_events)
            
            # Prepare context for agents
            context = {
                "symbol": symbol,
                "market_data": market_data,
                "news_events": news_events,
                "event_type": event_type,
                "is_significant_event": is_significant,
                "orchestrator_timestamp": datetime.now()
            }
            
            # Collect responses from all agents
            agent_responses: List[AgentResponse] = []
            failed_agents: List[AgentType] = []
            
            for agent_type, agent in self.agents.items():
                try:
                    response = await agent.analyze(context)
                    
                    if not isinstance(response, AgentResponse):
                        raise TypeError(f"Agent {agent_type.value} returned invalid response type")
                    
                    agent_responses.append(response)
                    logger.info(f"{agent_type.value} response: {response.recommendation.value} (confidence: {response.confidence:.3f})")
                    
                except Exception as e:
                    logger.error(f"Error getting response from {agent_type.value}: {e}")
                    failed_agents.append(agent_type)
            
            # Make coordinated decision
            decision = self._make_decision(agent_responses, event_type, failed_agents)
            
            # Log decision for future performance tracking
            decision_record = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "decision": decision,
                "agent_responses": [
                    {
                        "agent_type": resp.agent_type.value,
                        "recommendation": resp.recommendation.value,
                        "confidence": resp.confidence
                    } for resp in agent_responses
                ],
                "event_type": event_type.value if event_type else None,
                "is_significant": is_significant,
                "failed_agents": [agent.value for agent in failed_agents]
            }
            
            self.decision_history.append(decision_record)
            
            # Limit history size
            if len(self.decision_history) > self.max_history_size:
                self.decision_history = self.decision_history[-self.max_history_size:]
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in coordinate_analysis: {e}")
            return {
                "action": TradeAction.HOLD,
                "confidence": 0.0,
                "reasoning": f"System error: {str(e)}",
                "error": True
            }
    
    def _make_decision(self, responses: List[AgentResponse], event_type: Optional[MarketEventType], failed_agents: List[AgentType]) -> Dict[str, Any]:
        """Make final trading decision based on weighted agent responses"""
        
        if not responses:
            return {
                "action": TradeAction.HOLD,
                "confidence": 0.0,
                "reasoning": "No agent responses available",
                "weighted_votes": {},
                "total_weight": 0.0,
                "event_type": event_type.value if event_type else None,
                "failed_agents": len(failed_agents)
            }
        
        # Calculate weighted votes
        weighted_votes: Dict[TradeAction, float] = {}
        total_weight = 0.0
        agent_contributions: Dict[AgentType, float] = {}
        
        for response in responses:
            try:
                weight = self.performance_tracker.get_agent_weight(
                    response.agent_type, 
                    response.confidence, 
                    event_type
                )
                
                if response.recommendation not in weighted_votes:
                    weighted_votes[response.recommendation] = 0.0
                
                weighted_votes[response.recommendation] += weight
                total_weight += weight
                agent_contributions[response.agent_type] = weight
                
            except Exception as e:
                logger.error(f"Error processing response from {response.agent_type.value}: {e}")
        
        # Find recommendation with highest weighted vote
        if total_weight == 0:
            final_action = TradeAction.HOLD
            final_confidence = 0.0
        else:
            final_action = max(weighted_votes.items(), key=lambda x: x[1])[0]
            final_confidence = weighted_votes[final_action] / total_weight
        
        # Compile reasoning from top contributing agents
        reasoning = self._compile_reasoning(responses, final_action, agent_contributions)
        
        return {
            "action": final_action,
            "confidence": final_confidence,
            "reasoning": reasoning,
            "weighted_votes": {action.value: weight for action, weight in weighted_votes.items()},
            "total_weight": total_weight,
            "event_type": event_type.value if event_type else None,
            "agent_contributions": {agent.value: weight for agent, weight in agent_contributions.items()},
            "failed_agents": len(failed_agents)
        }
    
    def _compile_reasoning(self, responses: List[AgentResponse], final_action: TradeAction, contributions: Dict[AgentType, float]) -> str:
        """Compile reasoning from agents that supported the final decision"""
        
        # Find agents that supported the final action, sorted by contribution
        supporting_agents = [
            (resp, contributions.get(resp.agent_type, 0))
            for resp in responses 
            if resp.recommendation == final_action
        ]
        
        # Sort by contribution weight
        supporting_agents.sort(key=lambda x: x[1], reverse=True)
        
        if not supporting_agents:
            return f"Default action: {final_action.value} (no supporting consensus)"
        
        # Take top 3 supporting agents
        reasoning_parts = []
        for response, weight in supporting_agents[:3]:
            agent_name = response.agent_type.value.replace('_', ' ').title()
            reasoning_parts.append(f"{agent_name} (weight: {weight:.2f}): {response.reasoning[:100]}")
        
        return " | ".join(reasoning_parts)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        return {
            "total_agents": len(self.agents),
            "agent_types": [agent.value for agent in self.agents.keys()],
            "total_decisions": len(self.decision_history),
            "last_decision": self.decision_history[-1]["timestamp"] if self.decision_history else None,
            "performance_metrics": {
                agent_type.value: {
                    "accuracy": metric.accuracy_rate,
                    "total_predictions": metric.total_predictions
                }
                for agent_type, metric in self.performance_tracker.agent_metrics.items()
            }
        }