"""
trading_system/llm_service.py
==============================

LLM integration service for the AI Trading System.
Provides intelligent analysis capabilities using Large Language Models.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp

try:
    from .core import (
        LLMConfig, LLMRequest, LLMResponse, MarketData, NewsEvent, 
        AgentType, MarketEventType, TradeAction
    )
except ImportError:
    from core import (
        LLMConfig, LLMRequest, LLMResponse, MarketData, NewsEvent, 
        AgentType, MarketEventType, TradeAction
    )

logger = logging.getLogger(__name__)


class LLMService:
    """Service for integrating with Large Language Model APIs"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.error_count = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_news_with_llm(self, news_events: List[NewsEvent], symbol: str, market_data: MarketData) -> Dict[str, Any]:
        """Use LLM to analyze news events for market impact"""
        
        try:
            # Prepare news context
            news_context = self._prepare_news_context(news_events, symbol, market_data)
            
            # Create LLM prompt for news analysis
            prompt = self._create_news_analysis_prompt(news_context, symbol, market_data)
            
            # Call LLM
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=self._get_news_analysis_system_prompt(),
                max_tokens=500,
                temperature=0.1
            )
            
            response = await self._call_llm(llm_request)
            
            if not response.success:
                raise Exception(f"LLM call failed: {response.error_message}")
            
            # Parse LLM response
            analysis = self._parse_news_analysis_response(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM news analysis: {e}")
            return self._get_fallback_news_analysis()
    
    async def analyze_market_with_llm(self, market_data: MarketData, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to perform technical market analysis"""
        
        try:
            # Prepare market context
            market_context = self._prepare_market_context(market_data, symbol, context)
            
            # Create LLM prompt for market analysis
            prompt = self._create_market_analysis_prompt(market_context, symbol)
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=self._get_market_analysis_system_prompt(),
                max_tokens=600,
                temperature=0.1
            )
            
            response = await self._call_llm(llm_request)
            
            if not response.success:
                raise Exception(f"LLM call failed: {response.error_message}")
            
            # Parse LLM response
            analysis = self._parse_market_analysis_response(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM market analysis: {e}")
            return self._get_fallback_market_analysis()
    
    async def analyze_risk_with_llm(self, market_data: MarketData, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to perform risk assessment"""
        
        try:
            # Prepare risk context
            risk_context = self._prepare_risk_context(market_data, symbol, context)
            
            # Create LLM prompt for risk analysis
            prompt = self._create_risk_analysis_prompt(risk_context, symbol)
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=self._get_risk_analysis_system_prompt(),
                max_tokens=500,
                temperature=0.1
            )
            
            response = await self._call_llm(llm_request)
            
            if not response.success:
                raise Exception(f"LLM call failed: {response.error_message}")
            
            # Parse LLM response
            analysis = self._parse_risk_analysis_response(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM risk analysis: {e}")
            return self._get_fallback_risk_analysis()
    
    async def analyze_sentiment_with_llm(self, news_events: List[NewsEvent], symbol: str, market_data: MarketData) -> Dict[str, Any]:
        """Use LLM to analyze market sentiment"""
        
        try:
            # Prepare sentiment context
            sentiment_context = self._prepare_sentiment_context(news_events, symbol, market_data)
            
            # Create LLM prompt for sentiment analysis
            prompt = self._create_sentiment_analysis_prompt(sentiment_context, symbol)
            
            llm_request = LLMRequest(
                prompt=prompt,
                system_prompt=self._get_sentiment_analysis_system_prompt(),
                max_tokens=400,
                temperature=0.2
            )
            
            response = await self._call_llm(llm_request)
            
            if not response.success:
                raise Exception(f"LLM call failed: {response.error_message}")
            
            # Parse LLM response
            analysis = self._parse_sentiment_analysis_response(response.content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM sentiment analysis: {e}")
            return self._get_fallback_sentiment_analysis()
    
    async def _call_llm(self, request: LLMRequest) -> LLMResponse:
        """Make API call to LLM service"""
        
        try:
            self.request_count += 1
            
            if self.config.provider == "openai":
                return await self._call_openai(request)
            elif self.config.provider == "anthropic":
                return await self._call_anthropic(request)
            elif self.config.provider == "deepseek":
                return await self._call_deepseek(request)
            elif self.config.provider == "local":
                return await self._call_local_llm(request)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error calling LLM: {e}")
            return LLMResponse(
                content="",
                tokens_used=0,
                model=self.config.model,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API"""
        
        if not self.session:
            raise Exception("HTTP session not initialized")
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or self.config.temperature
        }
        
        async with self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI API error {response.status}: {error_text}")
            
            data = await response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                tokens_used=data["usage"]["total_tokens"],
                model=data["model"],
                timestamp=datetime.now(),
                success=True
            )
    async def _call_deepseek(self, request: LLMRequest) -> LLMResponse:
        """Call DeepSeek API"""
        
        if not self.session:
            raise Exception("HTTP session not initialized")
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False
        }
        
        async with self.session.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"DeepSeek API error {response.status}: {error_text}")
            
            data = await response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                tokens_used=data["usage"]["total_tokens"],
                model=data["model"],
                timestamp=datetime.now(),
                success=True
            )

    
    async def _call_anthropic(self, request: LLMRequest) -> LLMResponse:
        """Call Anthropic Claude API"""
        
        if not self.session:
            raise Exception("HTTP session not initialized")
        
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.config.model,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or self.config.temperature,
            "system": request.system_prompt or "",
            "messages": [{"role": "user", "content": request.prompt}]
        }
        
        async with self.session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic API error {response.status}: {error_text}")
            
            data = await response.json()
            
            return LLMResponse(
                content=data["content"][0]["text"],
                tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
                model=data["model"],
                timestamp=datetime.now(),
                success=True
            )
    
    async def _call_local_llm(self, request: LLMRequest) -> LLMResponse:
        """Call local LLM endpoint (e.g., Ollama, vLLM)"""
        
        if not self.session:
            raise Exception("HTTP session not initialized")
        
        payload = {
            "model": self.config.model,
            "prompt": f"{request.system_prompt}\n\n{request.prompt}" if request.system_prompt else request.prompt,
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or self.config.temperature,
            "stream": False
        }
        
        # Assuming local endpoint at localhost:11434 (Ollama default)
        async with self.session.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Local LLM error {response.status}: {error_text}")
            
            data = await response.json()
            
            return LLMResponse(
                content=data["response"],
                tokens_used=data.get("eval_count", 0),
                model=self.config.model,
                timestamp=datetime.now(),
                success=True
            )
    
    # Context preparation methods
    def _prepare_news_context(self, news_events: List[NewsEvent], symbol: str, market_data: MarketData) -> str:
        """Prepare news context for LLM analysis"""
        
        context_parts = [f"Symbol: {symbol}", f"Current Price: ${market_data.price:.2f}"]
        
        if market_data.vix:
            context_parts.append(f"VIX: {market_data.vix:.1f}")
        
        context_parts.append(f"Volume: {market_data.volume:,}")
        context_parts.append("\nRelevant News Events:")
        
        for i, event in enumerate(news_events[:5], 1):  # Limit to 5 most relevant
            context_parts.append(f"{i}. {event.title}")
            context_parts.append(f"   Source: {event.source} | Relevance: {event.relevance_score:.2f}")
            context_parts.append(f"   Content: {event.content[:200]}...")
        
        return "\n".join(context_parts)
    
    def _prepare_market_context(self, market_data: MarketData, symbol: str, context: Dict[str, Any]) -> str:
        """Prepare market context for LLM analysis"""
        
        market_context = [
            f"Symbol: {symbol}",
            f"Current Price: ${market_data.price:.2f}",
            f"Bid: ${market_data.bid:.2f} | Ask: ${market_data.ask:.2f}",
            f"Volume: {market_data.volume:,}",
            f"Spread: {((market_data.ask - market_data.bid) / market_data.price * 10000):.1f} bps"
        ]
        
        if market_data.vix:
            market_context.append(f"VIX: {market_data.vix:.1f}")
        
        if market_data.sector:
            market_context.append(f"Sector: {market_data.sector}")
        
        event_type = context.get("event_type")
        if event_type:
            market_context.append(f"Market Event: {event_type.value}")
        
        return "\n".join(market_context)
    
    def _prepare_risk_context(self, market_data: MarketData, symbol: str, context: Dict[str, Any]) -> str:
        """Prepare risk context for LLM analysis"""
        
        risk_context = [
            f"Symbol: {symbol}",
            f"Current Price: ${market_data.price:.2f}",
            f"Volume: {market_data.volume:,}"
        ]
        
        if market_data.vix:
            vix_level = market_data.vix
            risk_context.append(f"VIX: {vix_level:.1f} ({'Low' if vix_level < 20 else 'Normal' if vix_level < 30 else 'High'} volatility)")
        
        if context.get("is_significant_event"):
            event_type = context.get("event_type")
            risk_context.append(f"Significant Event: {event_type.value if event_type else 'Unknown'}")
        
        # Add news summary for risk context
        news_events = context.get("news_events", [])
        if news_events:
            negative_events = [e for e in news_events if e.sentiment_score < -0.2]
            if negative_events:
                risk_context.append(f"Negative News Events: {len(negative_events)}")
        
        return "\n".join(risk_context)
    
    def _prepare_sentiment_context(self, news_events: List[NewsEvent], symbol: str, market_data: MarketData) -> str:
        """Prepare sentiment context for LLM analysis"""
        
        sentiment_context = [
            f"Symbol: {symbol}",
            f"Current Price: ${market_data.price:.2f}",
            f"Volume: {market_data.volume:,} ({'High' if market_data.volume > 1000000 else 'Normal' if market_data.volume > 500000 else 'Low'} volume)"
        ]
        
        if news_events:
            sentiment_context.append(f"\nNews Events for Sentiment Analysis:")
            for event in news_events[:3]:  # Top 3 events
                sentiment_context.append(f"- {event.title} (Sentiment: {event.sentiment_score:.2f})")
        
        return "\n".join(sentiment_context)
    
    # System prompts for different analysis types
    def _get_news_analysis_system_prompt(self) -> str:
        """System prompt for news analysis"""
        return """You are an expert financial news analyst. Analyze news events and their potential impact on stock prices. 

Your analysis should include:
1. Sentiment assessment (-1 to 1 scale)
2. Impact magnitude (0 to 1 scale)
3. Confidence in analysis (0 to 1 scale)
4. Brief reasoning

Respond in JSON format:
{
    "sentiment": float,
    "impact_magnitude": float,
    "confidence": float,
    "reasoning": "brief explanation",
    "recommendation": "BUY|SELL|HOLD"
}"""
    
    def _get_market_analysis_system_prompt(self) -> str:
        """System prompt for market analysis"""
        return """You are an expert technical analyst. Analyze market data and provide technical trading insights.

Your analysis should include:
1. Overall technical score (-1 to 1 scale, where -1 is very bearish, 1 is very bullish)
2. Confidence in analysis (0 to 1 scale)
3. Key technical levels (support/resistance)
4. Risk assessment
5. Brief reasoning

Respond in JSON format:
{
    "technical_score": float,
    "confidence": float,
    "support_level": float,
    "resistance_level": float,
    "risk_score": float,
    "reasoning": "technical analysis summary",
    "recommendation": "BUY|SELL|HOLD"
}"""
    
    def _get_risk_analysis_system_prompt(self) -> str:
        """System prompt for risk analysis"""
        return """You are an expert risk management analyst. Assess trading risks and provide risk-adjusted recommendations.

Your analysis should include:
1. Overall risk score (0 to 1 scale, where 1 is highest risk)
2. Confidence in risk assessment (0 to 1 scale)
3. Position sizing recommendation (0 to 1 scale of max position)
4. Key risk factors
5. Risk mitigation suggestions

Respond in JSON format:
{
    "risk_score": float,
    "confidence": float,
    "position_size": float,
    "key_risks": ["list", "of", "risks"],
    "reasoning": "risk assessment summary",
    "recommendation": "BUY|SELL|HOLD"
}"""
    
    def _get_sentiment_analysis_system_prompt(self) -> str:
        """System prompt for sentiment analysis"""
        return """You are an expert market sentiment analyst. Analyze overall market sentiment from multiple sources.

Your analysis should include:
1. Overall sentiment score (-1 to 1 scale)
2. Confidence in sentiment assessment (0 to 1 scale)
3. Sentiment momentum (improving/stable/deteriorating)
4. Key sentiment drivers
5. Contrarian indicators

Respond in JSON format:
{
    "sentiment_score": float,
    "confidence": float,
    "momentum": "improving|stable|deteriorating",
    "key_drivers": ["list", "of", "drivers"],
    "reasoning": "sentiment analysis summary",
    "recommendation": "BUY|SELL|HOLD"
}"""
    
    # Prompt creation methods
    def _create_news_analysis_prompt(self, news_context: str, symbol: str, market_data: MarketData) -> str:
        """Create specific prompt for news analysis"""
        return f"""Analyze the following news events for their potential impact on {symbol} stock price:

{news_context}

Please provide a comprehensive analysis considering:
- How each news item might affect investor sentiment
- Potential short-term and medium-term price impact
- Relevance to the company's fundamentals
- Market timing and context

Focus on actionable insights for trading decisions."""
    
    def _create_market_analysis_prompt(self, market_context: str, symbol: str) -> str:
        """Create specific prompt for market analysis"""
        return f"""Perform technical analysis on {symbol} based on the following market data:

{market_context}

Please analyze:
- Current price action and momentum
- Support and resistance levels
- Volume characteristics and their implications
- Market microstructure (bid-ask spread, liquidity)
- Overall technical setup for potential trades

Provide specific price levels and technical reasoning."""
    
    def _create_risk_analysis_prompt(self, risk_context: str, symbol: str) -> str:
        """Create specific prompt for risk analysis"""
        return f"""Assess the trading risks for {symbol} based on the following context:

{risk_context}

Please evaluate:
- Current market volatility and risk factors
- Potential downside scenarios and their probabilities
- Appropriate position sizing given current conditions
- Key risk factors that could impact the trade
- Risk mitigation strategies

Focus on capital preservation and risk-adjusted returns."""
    
    def _create_sentiment_analysis_prompt(self, sentiment_context: str, symbol: str) -> str:
        """Create specific prompt for sentiment analysis"""
        return f"""Analyze market sentiment for {symbol} based on the following information:

{sentiment_context}

Please assess:
- Overall market sentiment toward the stock
- Sentiment momentum and recent changes
- Key factors driving current sentiment
- Potential sentiment shifts or catalysts
- How sentiment might impact price action

Consider both fundamental and technical sentiment indicators."""
    
    # Response parsing methods
    def _parse_news_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response for news analysis"""
        try:
            # Try to parse JSON response
            if "{" in response_content and "}" in response_content:
                start = response_content.find("{")
                end = response_content.rfind("}") + 1
                json_str = response_content[start:end]
                parsed = json.loads(json_str)
                
                return {
                    "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.5))),
                    "weighted_sentiment": max(-1.0, min(1.0, parsed.get("sentiment", 0.0))),
                    "impact_magnitude": max(0.0, min(1.0, parsed.get("impact_magnitude", 0.5))),
                    "reasoning": parsed.get("reasoning", "LLM analysis completed"),
                    "recommendation": parsed.get("recommendation", "HOLD"),
                    "llm_generated": True
                }
            else:
                # Fallback parsing if not JSON
                return self._parse_text_response(response_content, "news")
                
        except Exception as e:
            logger.error(f"Error parsing news analysis response: {e}")
            return self._get_fallback_news_analysis()
    
    def _parse_market_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response for market analysis"""
        try:
            if "{" in response_content and "}" in response_content:
                start = response_content.find("{")
                end = response_content.rfind("}") + 1
                json_str = response_content[start:end]
                parsed = json.loads(json_str)
                
                return {
                    "overall_score": max(-1.0, min(1.0, parsed.get("technical_score", 0.0))),
                    "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.5))),
                    "support_level": parsed.get("support_level", 0.0),
                    "resistance_level": parsed.get("resistance_level", 0.0),
                    "risk_score": max(0.0, min(1.0, parsed.get("risk_score", 0.5))),
                    "reasoning": parsed.get("reasoning", "Technical analysis completed"),
                    "recommendation": parsed.get("recommendation", "HOLD"),
                    "llm_generated": True
                }
            else:
                return self._parse_text_response(response_content, "market")
                
        except Exception as e:
            logger.error(f"Error parsing market analysis response: {e}")
            return self._get_fallback_market_analysis()
    
    def _parse_risk_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response for risk analysis"""
        try:
            if "{" in response_content and "}" in response_content:
                start = response_content.find("{")
                end = response_content.rfind("}") + 1
                json_str = response_content[start:end]
                parsed = json.loads(json_str)
                
                return {
                    "overall_risk_score": max(0.0, min(1.0, parsed.get("risk_score", 0.5))),
                    "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.5))),
                    "recommended_position_size": max(0.0, min(1.0, parsed.get("position_size", 0.05))),
                    "key_risks": parsed.get("key_risks", []),
                    "reasoning": parsed.get("reasoning", "Risk analysis completed"),
                    "recommendation": parsed.get("recommendation", "HOLD"),
                    "llm_generated": True
                }
            else:
                return self._parse_text_response(response_content, "risk")
                
        except Exception as e:
            logger.error(f"Error parsing risk analysis response: {e}")
            return self._get_fallback_risk_analysis()
    
    def _parse_sentiment_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse LLM response for sentiment analysis"""
        try:
            if "{" in response_content and "}" in response_content:
                start = response_content.find("{")
                end = response_content.rfind("}") + 1
                json_str = response_content[start:end]
                parsed = json.loads(json_str)
                
                return {
                    "overall_sentiment": max(-1.0, min(1.0, parsed.get("sentiment_score", 0.0))),
                    "confidence": max(0.0, min(1.0, parsed.get("confidence", 0.5))),
                    "momentum": parsed.get("momentum", "stable"),
                    "key_drivers": parsed.get("key_drivers", []),
                    "reasoning": parsed.get("reasoning", "Sentiment analysis completed"),
                    "recommendation": parsed.get("recommendation", "HOLD"),
                    "llm_generated": True
                }
            else:
                return self._parse_text_response(response_content, "sentiment")
                
        except Exception as e:
            logger.error(f"Error parsing sentiment analysis response: {e}")
            return self._get_fallback_sentiment_analysis()
    
    def _parse_text_response(self, response_content: str, analysis_type: str) -> Dict[str, Any]:
        """Fallback text parsing when JSON parsing fails"""
        
        # Simple keyword-based parsing
        content_lower = response_content.lower()
        
        # Determine sentiment/bias
        if "bullish" in content_lower or "positive" in content_lower or "buy" in content_lower:
            score = 0.6
            recommendation = "BUY"
        elif "bearish" in content_lower or "negative" in content_lower or "sell" in content_lower:
            score = -0.6
            recommendation = "SELL"
        else:
            score = 0.0
            recommendation = "HOLD"
        
        # Return appropriate structure based on analysis type
        if analysis_type == "news":
            return {
                "confidence": 0.4,
                "weighted_sentiment": score,
                "impact_magnitude": 0.5,
                "reasoning": response_content[:200],
                "recommendation": recommendation,
                "llm_generated": True
            }
        elif analysis_type == "market":
            return {
                "overall_score": score,
                "confidence": 0.4,
                "reasoning": response_content[:200],
                "recommendation": recommendation,
                "llm_generated": True
            }
        elif analysis_type == "risk":
            return {
                "overall_risk_score": 0.5,
                "confidence": 0.4,
                "reasoning": response_content[:200],
                "recommendation": recommendation,
                "llm_generated": True
            }
        else:  # sentiment
            return {
                "overall_sentiment": score,
                "confidence": 0.4,
                "reasoning": response_content[:200],
                "recommendation": recommendation,
                "llm_generated": True
            }
    
    # Fallback methods when LLM fails
    def _get_fallback_news_analysis(self) -> Dict[str, Any]:
        """Fallback news analysis when LLM fails"""
        return {
            "confidence": 0.2,
            "weighted_sentiment": 0.0,
            "impact_magnitude": 0.3,
            "reasoning": "LLM analysis unavailable, using fallback",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _get_fallback_market_analysis(self) -> Dict[str, Any]:
        """Fallback market analysis when LLM fails"""
        return {
            "overall_score": 0.0,
            "confidence": 0.2,
            "reasoning": "Technical analysis unavailable, using fallback",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _get_fallback_risk_analysis(self) -> Dict[str, Any]:
        """Fallback risk analysis when LLM fails"""
        return {
            "overall_risk_score": 0.7,  # Conservative high risk when uncertain
            "confidence": 0.2,
            "recommended_position_size": 0.02,  # Very small position
            "reasoning": "Risk analysis unavailable, using conservative fallback",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def _get_fallback_sentiment_analysis(self) -> Dict[str, Any]:
        """Fallback sentiment analysis when LLM fails"""
        return {
            "overall_sentiment": 0.0,
            "confidence": 0.2,
            "reasoning": "Sentiment analysis unavailable, using neutral fallback",
            "recommendation": "HOLD",
            "llm_generated": False
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get LLM service statistics"""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
            "session_active": self.session is not None
        }

