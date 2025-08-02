"""
trading_system/agents.py
========================

LLM-enhanced AI agents for the trading system.
Each agent now uses Large Language Models for intelligent analysis.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import uuid

try:
    from .core import (
        BaseAgent, AgentResponse, MarketData, NewsEvent,
        AgentType, TradeAction, MarketEventType
    )
    from .llm_service import LLMService
except ImportError:
    from core import (
        BaseAgent, AgentResponse, MarketData, NewsEvent,
        AgentType, TradeAction, MarketEventType
    )
    from llm_service import LLMService

logger = logging.getLogger(__name__)


class NewsIntelligenceAgent(BaseAgent):
    """
    LLM-enhanced AI Agent for processing news events and determining market impact.
    Uses Large Language Models for sophisticated news analysis and sentiment detection.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(AgentType.NEWS_INTELLIGENCE)
        self.llm_service = llm_service
        self.news_sources = [
            "Reuters", "Bloomberg", "CNBC", "SEC Filings", "Finimize",
            "Company Press Releases", "Fed Announcements"
        ]
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze news events using LLM for intelligent sentiment and impact assessment"""
        
        try:
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
                    supporting_data={"relevant_news_count": 0, "llm_used": False},
                    timestamp=datetime.now(),
                    risk_score=0.2
                )
            
            # Use LLM for intelligent analysis if available
            if self.llm_service:
                llm_analysis = await self.llm_service.analyze_news_with_llm(relevant_news, symbol, market_data)
                
                # Enhance LLM analysis with additional processing
                enhanced_analysis = self._enhance_llm_news_analysis(llm_analysis, relevant_news, market_data)
                
            else:
                # Fallback to rule-based analysis
                enhanced_analysis = self._fallback_news_analysis(relevant_news, market_data)
            
            # Determine recommendation
            recommendation = self._determine_news_recommendation(enhanced_analysis)
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=enhanced_analysis["confidence"],
                recommendation=recommendation,
                reasoning=enhanced_analysis["reasoning"],
                supporting_data=enhanced_analysis,
                timestamp=datetime.now(),
                target_price=enhanced_analysis.get("target_price"),
                risk_score=enhanced_analysis.get("risk_score", 0.5)
            )
            
        except Exception as e:
            logger.error(f"Error in NewsIntelligenceAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.1,
                recommendation=TradeAction.HOLD,
                reasoning=f"News analysis error: {str(e)}",
                supporting_data={"error": str(e), "llm_used": False},
                timestamp=datetime.now(),
                risk_score=0.8
            )
    
    def _enhance_llm_news_analysis(self, llm_analysis: Dict[str, Any], news_events: List[NewsEvent], market_data: MarketData) -> Dict[str, Any]:
        """Enhance LLM analysis with additional processing"""
        
        # Calculate additional metrics
        news_count = len(news_events)
        avg_relevance = sum(event.relevance_score for event in news_events) / max(news_count, 1)
        
        # Calculate recency factor
        latest_event = max(news_events, key=lambda x: x.timestamp) if news_events else None
        recency_factor = self._calculate_recency_factor(latest_event.timestamp) if latest_event else 0.5
        
        # Adjust confidence based on news quality
        base_confidence = llm_analysis.get("confidence", 0.5)
        quality_adjusted_confidence = base_confidence * avg_relevance * recency_factor
        
        # Calculate target price
        sentiment = llm_analysis.get("weighted_sentiment", 0.0)
        impact = llm_analysis.get("impact_magnitude", 0.5)
        current_price = market_data.price
        
        # Price impact calculation (max 8% movement)
        price_impact = sentiment * impact * 0.08
        target_price = current_price * (1 + price_impact)
        
        # Calculate risk score
        risk_score = min(1.0, abs(sentiment) * 0.4 + impact * 0.6)
        
        return {
            **llm_analysis,
            "confidence": min(0.95, quality_adjusted_confidence),
            "target_price": target_price,
            "risk_score": risk_score,
            "news_count": news_count,
            "avg_relevance": avg_relevance,
            "recency_factor": recency_factor,
            "enhanced_by_rules": True
        }
    
    def _fallback_news_analysis(self, news_events: List[NewsEvent], market_data: MarketData) -> Dict[str, Any]:
        """Fallback rule-based analysis when LLM is unavailable"""
        
        total_sentiment = sum(event.sentiment_score * event.relevance_score for event in news_events)
        total_relevance = sum(event.relevance_score for event in news_events)
        
        weighted_sentiment = total_sentiment / max(total_relevance, 0.001)
        impact_magnitude = min(1.0, total_relevance / len(news_events))
        
        return {
            "confidence": min(0.7, impact_magnitude),
            "weighted_sentiment": weighted_sentiment,
            "impact_magnitude": impact_magnitude,
            "reasoning": f"Rule-based analysis of {len(news_events)} news events",
            "recommendation": "HOLD",
            "target_price": market_data.price * (1 + weighted_sentiment * 0.03),
            "risk_score": abs(weighted_sentiment) * 0.5,
            "llm_generated": False
        }
    
    def _determine_news_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine trading recommendation based on news analysis"""
        
        sentiment = analysis.get("weighted_sentiment", 0.0)
        confidence = analysis.get("confidence", 0.0)
        impact = analysis.get("impact_magnitude", 0.0)
        
        # Only make strong recommendations with high confidence and impact
        if confidence < 0.6 or impact < 0.4:
            return TradeAction.HOLD
        
        # Strong signals
        if sentiment > 0.7 and impact > 0.7:
            return TradeAction.BUY
        elif sentiment < -0.7 and impact > 0.7:
            return TradeAction.SELL
        
        # Moderate signals
        elif sentiment > 0.4:
            return TradeAction.BUY
        elif sentiment < -0.4:
            return TradeAction.SELL
        
        return TradeAction.HOLD
    
    def _calculate_recency_factor(self, event_time: datetime) -> float:
        """Calculate news recency factor"""
        hours_ago = (datetime.now() - event_time).total_seconds() / 3600
        
        if hours_ago < 1:
            return 1.0
        elif hours_ago < 6:
            return 0.8
        elif hours_ago < 24:
            return 0.6
        else:
            return 0.3


class MarketAnalysisAgent(BaseAgent):
    """
    LLM-enhanced AI Agent for technical analysis and market pattern recognition.
    Uses Large Language Models for sophisticated technical analysis and pattern detection.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(AgentType.MARKET_ANALYSIS)
        self.llm_service = llm_service
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze market data using LLM for intelligent technical analysis"""
        
        try:
            market_data = context["market_data"]
            symbol = context["symbol"]
            event_type = context.get("event_type")
            
            # Use LLM for intelligent analysis if available
            if self.llm_service:
                llm_analysis = await self.llm_service.analyze_market_with_llm(market_data, symbol, context)
                enhanced_analysis = self._enhance_llm_market_analysis(llm_analysis, market_data, event_type)
            else:
                enhanced_analysis = self._fallback_market_analysis(market_data, symbol)
            
            recommendation = self._determine_market_recommendation(enhanced_analysis)
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=enhanced_analysis["confidence"],
                recommendation=recommendation,
                reasoning=enhanced_analysis["reasoning"],
                supporting_data=enhanced_analysis,
                timestamp=datetime.now(),
                target_price=enhanced_analysis.get("target_price"),
                stop_loss=enhanced_analysis.get("stop_loss"),
                risk_score=enhanced_analysis.get("risk_score", 0.5)
            )
            
        except Exception as e:
            logger.error(f"Error in MarketAnalysisAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.2,
                recommendation=TradeAction.HOLD,
                reasoning=f"Technical analysis error: {str(e)}",
                supporting_data={"error": str(e), "llm_used": False},
                timestamp=datetime.now(),
                risk_score=0.7
            )
    
    def _enhance_llm_market_analysis(self, llm_analysis: Dict[str, Any], market_data: MarketData, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Enhance LLM market analysis with additional technical calculations"""
        
        current_price = market_data.price
        
        # Calculate additional technical metrics
        spread_bps = ((market_data.ask - market_data.bid) / current_price) * 10000
        volume_ratio = market_data.volume / 1000000  # Normalize to millions
        
        # Enhance support/resistance levels from LLM
        support_level = llm_analysis.get("support_level", current_price * 0.97)
        resistance_level = llm_analysis.get("resistance_level", current_price * 1.03)
        
        # Calculate targets and stops
        overall_score = llm_analysis.get("overall_score", 0.0)
        
        if overall_score > 0:  # Bullish
            target_price = min(resistance_level, current_price * (1 + abs(overall_score) * 0.05))
            stop_loss = max(support_level, current_price * 0.98)
        else:  # Bearish
            target_price = max(support_level, current_price * (1 - abs(overall_score) * 0.05))
            stop_loss = min(resistance_level, current_price * 1.02)
        
        # Adjust confidence based on market conditions
        base_confidence = llm_analysis.get("confidence", 0.5)
        liquidity_factor = min(1.0, volume_ratio) * (20 / max(spread_bps, 1))
        adjusted_confidence = base_confidence * min(1.0, liquidity_factor)
        
        return {
            **llm_analysis,
            "confidence": min(0.95, adjusted_confidence),
            "target_price": target_price,
            "stop_loss": stop_loss,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "spread_bps": spread_bps,
            "volume_ratio": volume_ratio,
            "enhanced_by_rules": True
        }
    
    def _fallback_market_analysis(self, market_data: MarketData, symbol: str) -> Dict[str, Any]:
        """Fallback technical analysis when LLM is unavailable"""
        
        current_price = market_data.price
        
        # Basic technical calculations
        support_level = current_price * 0.97
        resistance_level = current_price * 1.03
        
        # Volume analysis
        volume_strength = "high" if market_data.volume > 1500000 else "normal" if market_data.volume > 800000 else "low"
        
        # Spread analysis
        spread_bps = ((market_data.ask - market_data.bid) / current_price) * 10000
        
        return {
            "overall_score": 0.0,
            "confidence": 0.4,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "target_price": current_price,
            "stop_loss": support_level,
            "reasoning": f"Basic technical analysis: {volume_strength} volume, {spread_bps:.1f} bps spread",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _determine_market_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine recommendation based on technical analysis"""
        
        overall_score = analysis.get("overall_score", 0.0)
        confidence = analysis.get("confidence", 0.0)
        
        if confidence < 0.6:
            return TradeAction.HOLD
        
        if overall_score > 0.6:
            return TradeAction.BUY
        elif overall_score < -0.6:
            return TradeAction.SELL
        elif overall_score > 0.3:
            return TradeAction.BUY
        elif overall_score < -0.3:
            return TradeAction.SELL
        
        return TradeAction.HOLD


class RiskAssessmentAgent(BaseAgent):
    """
    LLM-enhanced AI Agent for risk management and position sizing.
    Uses Large Language Models for sophisticated risk scenario analysis.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(AgentType.RISK_ASSESSMENT)
        self.llm_service = llm_service
        self.max_position_size = 0.10
        self.volatility_threshold = 0.30
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze risks using LLM for intelligent risk assessment"""
        
        try:
            market_data = context["market_data"]
            symbol = context["symbol"]
            event_type = context.get("event_type")
            
            # Use LLM for intelligent risk analysis if available
            if self.llm_service:
                llm_analysis = await self.llm_service.analyze_risk_with_llm(market_data, symbol, context)
                enhanced_analysis = self._enhance_llm_risk_analysis(llm_analysis, market_data, event_type)
            else:
                enhanced_analysis = self._fallback_risk_analysis(market_data, event_type)
            
            recommendation = self._determine_risk_recommendation(enhanced_analysis)
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=enhanced_analysis["confidence"],
                recommendation=recommendation,
                reasoning=enhanced_analysis["reasoning"],
                supporting_data=enhanced_analysis,
                timestamp=datetime.now(),
                risk_score=enhanced_analysis["overall_risk_score"]
            )
            
        except Exception as e:
            logger.error(f"Error in RiskAssessmentAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.2,
                recommendation=TradeAction.HOLD,
                reasoning=f"Risk analysis error: {str(e)}",
                supporting_data={"error": str(e), "llm_used": False},
                timestamp=datetime.now(),
                risk_score=0.8
            )
    
    def _enhance_llm_risk_analysis(self, llm_analysis: Dict[str, Any], market_data: MarketData, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Enhance LLM risk analysis with quantitative risk calculations"""
        
        # VIX-based risk adjustment
        vix_level = market_data.vix or 20.0
        vix_risk_multiplier = 1.0 if vix_level < 20 else 1.3 if vix_level < 30 else 1.6
        
        # Event-based risk adjustment
        event_risk_multipliers = {
            MarketEventType.GEOPOLITICAL_SHOCK: 2.0,
            MarketEventType.FED_ANNOUNCEMENT: 1.5,
            MarketEventType.EARNINGS_SURPRISE: 1.3,
            MarketEventType.VIX_SPIKE: 1.8
        }
        
        event_multiplier = event_risk_multipliers.get(event_type, 1.0)
        
        # Adjust LLM risk score
        base_risk = llm_analysis.get("overall_risk_score", 0.5)
        adjusted_risk = min(1.0, base_risk * vix_risk_multiplier * event_multiplier)
        
        # Position sizing based on risk
        base_position = llm_analysis.get("recommended_position_size", 0.05)
        risk_adjusted_position = base_position * (1.0 - adjusted_risk * 0.5)
        risk_adjusted_position = max(0.01, min(self.max_position_size, risk_adjusted_position))
        
        return {
            **llm_analysis,
            "overall_risk_score": adjusted_risk,
            "recommended_position_size": risk_adjusted_position,
            "vix_risk_multiplier": vix_risk_multiplier,
            "event_risk_multiplier": event_multiplier,
            "enhanced_by_rules": True
        }
    
    def _fallback_risk_analysis(self, market_data: MarketData, event_type: Optional[MarketEventType]) -> Dict[str, Any]:
        """Fallback rule-based risk analysis"""
        
        # Basic risk calculation
        vix_level = market_data.vix or 20.0
        base_risk = 0.3 + (vix_level - 15) / 50  # Scale VIX to risk
        base_risk = max(0.2, min(0.8, base_risk))
        
        # Event risk adjustment
        if event_type in [MarketEventType.GEOPOLITICAL_SHOCK, MarketEventType.VIX_SPIKE]:
            base_risk = min(0.9, base_risk * 1.5)
        
        return {
            "overall_risk_score": base_risk,
            "confidence": 0.5,
            "recommended_position_size": self.max_position_size * (1 - base_risk),
            "reasoning": f"Basic risk assessment: VIX {vix_level:.1f}, Risk Score {base_risk:.2f}",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _determine_risk_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine recommendation based on risk analysis"""
        
        risk_score = analysis.get("overall_risk_score", 0.5)
        confidence = analysis.get("confidence", 0.5)
        
        # Very conservative approach - high risk = hold
        if risk_score > 0.7 or confidence < 0.6:
            return TradeAction.HOLD
        
        # Let other agents drive decisions when risk is manageable
        return TradeAction.HOLD


class SentimentAnalysisAgent(BaseAgent):
    """
    LLM-enhanced AI Agent for market sentiment analysis.
    Uses Large Language Models for sophisticated sentiment interpretation from multiple sources.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(AgentType.SENTIMENT_ANALYSIS)
        self.llm_service = llm_service
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze sentiment using LLM for intelligent sentiment detection"""
        
        try:
            market_data = context["market_data"]
            news_events = context["news_events"]
            symbol = context["symbol"]
            
            # Use LLM for intelligent sentiment analysis if available
            if self.llm_service:
                llm_analysis = await self.llm_service.analyze_sentiment_with_llm(news_events, symbol, market_data)
                enhanced_analysis = self._enhance_llm_sentiment_analysis(llm_analysis, market_data, news_events)
            else:
                enhanced_analysis = self._fallback_sentiment_analysis(news_events, market_data)
            
            recommendation = self._determine_sentiment_recommendation(enhanced_analysis)
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=enhanced_analysis["confidence"],
                recommendation=recommendation,
                reasoning=enhanced_analysis["reasoning"],
                supporting_data=enhanced_analysis,
                timestamp=datetime.now(),
                risk_score=enhanced_analysis.get("sentiment_risk_score", 0.5)
            )
            
        except Exception as e:
            logger.error(f"Error in SentimentAnalysisAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.2,
                recommendation=TradeAction.HOLD,
                reasoning=f"Sentiment analysis error: {str(e)}",
                supporting_data={"error": str(e), "llm_used": False},
                timestamp=datetime.now(),
                risk_score=0.6
            )
    
    def _enhance_llm_sentiment_analysis(self, llm_analysis: Dict[str, Any], market_data: MarketData, news_events: List[NewsEvent]) -> Dict[str, Any]:
        """Enhance LLM sentiment analysis with quantitative sentiment metrics"""
        
        # Calculate sentiment consistency
        if news_events:
            sentiment_scores = [event.sentiment_score for event in news_events]
            sentiment_std = (sum((s - sum(sentiment_scores)/len(sentiment_scores))**2 for s in sentiment_scores) / len(sentiment_scores))**0.5
            sentiment_consistency = 1.0 - min(1.0, sentiment_std)
        else:
            sentiment_consistency = 0.5
        
        # Volume-based sentiment confirmation
        volume_ratio = market_data.volume / 1000000  # Normalize
        volume_confirmation = min(1.0, volume_ratio)
        
        # Adjust confidence based on consistency and volume
        base_confidence = llm_analysis.get("confidence", 0.5)
        enhanced_confidence = base_confidence * sentiment_consistency * (0.7 + volume_confirmation * 0.3)
        
        # Calculate sentiment risk (extreme sentiment = higher risk)
        overall_sentiment = llm_analysis.get("overall_sentiment", 0.0)
        sentiment_risk = abs(overall_sentiment) * 0.6 + (1 - sentiment_consistency) * 0.4
        
        return {
            **llm_analysis,
            "confidence": min(0.95, enhanced_confidence),
            "sentiment_consistency": sentiment_consistency,
            "volume_confirmation": volume_confirmation,
            "sentiment_risk_score": min(1.0, sentiment_risk),
            "enhanced_by_rules": True
        }
    
    def _fallback_sentiment_analysis(self, news_events: List[NewsEvent], market_data: MarketData) -> Dict[str, Any]:
        """Fallback sentiment analysis when LLM is unavailable"""
        
        if not news_events:
            return {
                "overall_sentiment": 0.0,
                "confidence": 0.3,
                "reasoning": "No news events for sentiment analysis",
                "recommendation": "HOLD",
                "llm_generated": False
            }
        
        # Calculate average sentiment
        avg_sentiment = sum(event.sentiment_score for event in news_events) / len(news_events)
        
        # Weight by relevance
        weighted_sentiment = sum(event.sentiment_score * event.relevance_score for event in news_events)
        total_relevance = sum(event.relevance_score for event in news_events)
        
        if total_relevance > 0:
            weighted_sentiment = weighted_sentiment / total_relevance
        else:
            weighted_sentiment = avg_sentiment
        
        return {
            "overall_sentiment": weighted_sentiment,
            "confidence": min(0.7, total_relevance / len(news_events)),
            "reasoning": f"Basic sentiment analysis of {len(news_events)} events",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _determine_sentiment_recommendation(self, analysis: Dict[str, Any]) -> TradeAction:
        """Determine recommendation based on sentiment analysis"""
        
        sentiment = analysis.get("overall_sentiment", 0.0)
        confidence = analysis.get("confidence", 0.0)
        
        if confidence < 0.65:
            return TradeAction.HOLD
        
        if sentiment > 0.6:
            return TradeAction.BUY
        elif sentiment < -0.6:
            return TradeAction.SELL
        elif sentiment > 0.3:
            return TradeAction.BUY
        elif sentiment < -0.3:
            return TradeAction.SELL
        
        return TradeAction.HOLD


class ExecutionStrategyAgent(BaseAgent):
    """
    AI Agent for trade execution optimization.
    Focuses on order timing, market impact minimization, and execution efficiency.
    """
    
    def __init__(self):
        super().__init__(AgentType.EXECUTION_STRATEGY)
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze execution requirements and optimize trade execution strategy"""
        
        try:
            market_data = context["market_data"]
            symbol = context["symbol"]
            is_significant_event = context.get("is_significant_event", False)
            
            # Analyze execution conditions
            execution_analysis = self._analyze_execution_conditions(market_data, is_significant_event)
            
            recommendation = TradeAction.HOLD  # Execution agent doesn't drive decisions
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=execution_analysis["confidence"],
                recommendation=recommendation,
                reasoning=execution_analysis["reasoning"],
                supporting_data=execution_analysis,
                timestamp=datetime.now(),
                risk_score=execution_analysis.get("execution_risk", 0.3)
            )
            
        except Exception as e:
            logger.error(f"Error in ExecutionStrategyAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.3,
                recommendation=TradeAction.HOLD,
                reasoning=f"Execution analysis error: {str(e)}",
                supporting_data={"error": str(e)},
                timestamp=datetime.now(),
                risk_score=0.5
            )
    
    def _analyze_execution_conditions(self, market_data: MarketData, is_significant_event: bool) -> Dict[str, Any]:
        """Analyze current execution conditions"""
        
        # Calculate execution metrics
        spread_bps = ((market_data.ask - market_data.bid) / market_data.price) * 10000
        volume_ratio = market_data.volume / 1000000
        
        # Liquidity assessment
        liquidity_score = min(1.0, volume_ratio) * (20 / max(spread_bps, 1))
        liquidity_tier = "high" if liquidity_score > 0.8 else "medium" if liquidity_score > 0.4 else "low"
        
        # Execution urgency
        urgency = "high" if is_significant_event else "low"
        
        # Recommended order type
        if urgency == "high" and liquidity_tier == "high":
            order_type = "market"
        elif liquidity_tier in ["high", "medium"]:
            order_type = "limit"
        else:
            order_type = "iceberg"
        
        # Execution risk
        execution_risk = 0.2 if liquidity_tier == "high" else 0.5 if liquidity_tier == "medium" else 0.8
        
        return {
            "confidence": 0.8,
            "liquidity_score": liquidity_score,
            "liquidity_tier": liquidity_tier,
            "spread_bps": spread_bps,
            "volume_ratio": volume_ratio,
            "urgency": urgency,
            "recommended_order_type": order_type,
            "execution_risk": execution_risk,
            "reasoning": f"Execution conditions: {liquidity_tier} liquidity, {spread_bps:.1f} bps spread, {urgency} urgency"
        }


class VisualizationAgent(BaseAgent):
    """
    AI Agent for converting complex analysis into intuitive visualizations.
    Creates easy-to-understand graphics and summaries.
    """
    
    def __init__(self):
        super().__init__(AgentType.VISUALIZATION)
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Create visualization recommendations and data structures"""
        
        try:
            market_data = context["market_data"]
            symbol = context["symbol"]
            
            # Create visualization suite
            viz_suite = self._create_visualization_suite(market_data, symbol, context)
            
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.9,  # High confidence in visualization capabilities
                recommendation=TradeAction.HOLD,  # Visualization doesn't drive decisions
                reasoning=viz_suite["reasoning"],
                supporting_data=viz_suite,
                timestamp=datetime.now(),
                risk_score=0.1  # Low risk agent
            )
            
        except Exception as e:
            logger.error(f"Error in VisualizationAgent.analyze: {e}")
            return AgentResponse(
                agent_type=self.agent_type,
                confidence=0.5,
                recommendation=TradeAction.HOLD,
                reasoning=f"Visualization error: {str(e)}",
                supporting_data={"error": str(e)},
                timestamp=datetime.now(),
                risk_score=0.2
            )
    
    def _create_visualization_suite(self, market_data: MarketData, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive visualization data suite"""
        
        current_price = market_data.price
        
        # Risk/Reward visualization
        risk_reward_data = {
            "current_price": current_price,
            "scenarios": {
                "bull_case": current_price * 1.15,
                "base_case": current_price * 1.05,
                "bear_case": current_price * 0.95,
                "worst_case": current_price * 0.85
            },
            "probabilities": {
                "bull_case": 0.2,
                "base_case": 0.4,
                "bear_case": 0.3,
                "worst_case": 0.1
            }
        }
        
        # Technical levels visualization
        technical_data = {
            "current_price": current_price,
            "support_levels": [current_price * 0.97, current_price * 0.94],
            "resistance_levels": [current_price * 1.03, current_price * 1.06],
            "moving_averages": {
                "20_day": current_price * 0.98,
                "50_day": current_price * 0.96
            }
        }
        
        # Market health indicators
        health_data = {
            "volume_strength": "high" if market_data.volume > 1500000 else "medium" if market_data.volume > 800000 else "low",
            "spread_quality": "tight" if ((market_data.ask - market_data.bid) / current_price) < 0.001 else "normal",
            "volatility_regime": "low" if (market_data.vix or 20) < 20 else "normal" if (market_data.vix or 20) < 30 else "high"
        }
        
        return {
            "risk_reward_data": risk_reward_data,
            "technical_data": technical_data,
            "health_data": health_data,
            "recommended_charts": ["risk_reward", "technical_levels", "market_health"],
            "reasoning": f"Visualization suite for {symbol} with current market conditions"
        }


# Factory function for creating LLM-enhanced agents
def create_agent_suite(llm_service: Optional[LLMService] = None) -> Dict[AgentType, BaseAgent]:
    """Create a complete suite of LLM-enhanced agents"""
    
    agents = {
        AgentType.NEWS_INTELLIGENCE: NewsIntelligenceAgent(llm_service),
        AgentType.MARKET_ANALYSIS: MarketAnalysisAgent(llm_service),
        AgentType.RISK_ASSESSMENT: RiskAssessmentAgent(llm_service),
        AgentType.SENTIMENT_ANALYSIS: SentimentAnalysisAgent(llm_service),
        AgentType.EXECUTION_STRATEGY: ExecutionStrategyAgent(),
        AgentType.VISUALIZATION: VisualizationAgent()
    }
    
    logger.info(f"Created agent suite with {'LLM-enhanced' if llm_service else 'rule-based'} intelligence")
    return agents