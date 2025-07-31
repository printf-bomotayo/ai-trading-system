"""
trading_system/main.py
======================

Main application module demonstrating the complete LLM-enhanced AI trading system.
Shows how to integrate all components with real LLM capabilities.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import logging

# Import our modular components
from .core import (
    MarketData, NewsEvent, MarketEventType, LLMConfig
)
from .orchestrator import OrchestratorCore
from .llm_service import LLMService
from .agents import create_agent_suite

logger = logging.getLogger(__name__)


class TradingSystemApp:
    """Main application class for the AI Trading System"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.llm_config = llm_config
        self.llm_service: Optional[LLMService] = None
        self.orchestrator: Optional[OrchestratorCore] = None
        self.agents: Dict = {}
        self.is_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the trading system with all components"""
        
        try:
            logger.info("Initializing AI Trading System...")
            
            # Initialize LLM service if config provided
            if self.llm_config:
                self.llm_service = LLMService(self.llm_config)
                logger.info(f"LLM service initialized: {self.llm_config.provider} - {self.llm_config.model}")
            else:
                logger.info("No LLM config provided, using rule-based analysis")
            
            # Initialize orchestrator
            self.orchestrator = OrchestratorCore()
            
            # Create and register all agents
            self.agents = create_agent_suite(self.llm_service)
            
            for agent_type, agent in self.agents.items():
                self.orchestrator.register_agent(agent)
            
            self.is_initialized = True
            logger.info("✅ Trading system initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing trading system: {e}")
            raise
    
    async def analyze_trading_opportunity(self, symbol: str, market_data: MarketData, news_events: List[NewsEvent]) -> Dict:
        """Analyze a trading opportunity using the full AI system"""
        
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"Analyzing trading opportunity for {symbol}")
            
            # Use LLM service context manager if available
            if self.llm_service:
                async with self.llm_service:
                    decision = await self.orchestrator.coordinate_analysis(symbol, market_data, news_events)
            else:
                decision = await self.orchestrator.coordinate_analysis(symbol, market_data, news_events)
            
            # Enhance decision with additional metadata
            enhanced_decision = self._enhance_decision_output(decision, symbol)
            
            logger.info(f"Analysis complete for {symbol}: {enhanced_decision['action'].value}")
            return enhanced_decision
            
        except Exception as e:
            logger.error(f"Error analyzing trading opportunity: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": f"System error: {str(e)}",
                "error": True
            }
    
    def _enhance_decision_output(self, decision: Dict, symbol: str) -> Dict:
        """Enhance decision output with additional context"""
        
        # Add system metadata
        decision["system_metadata"] = {
            "llm_enabled": self.llm_service is not None,
            "agent_count": len(self.agents),
            "analysis_timestamp": datetime.now().isoformat(),
            "symbol": symbol
        }
        
        # Add confidence interpretation
        confidence = decision.get("confidence", 0.0)
        if confidence > 0.8:
            confidence_level = "Very High"
        elif confidence > 0.6:
            confidence_level = "High"
        elif confidence > 0.4:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"
        
        decision["confidence_level"] = confidence_level
        
        # Add risk interpretation
        if "agent_contributions" in decision:
            risk_contribution = decision["agent_contributions"].get("risk_assessment", 0.0)
            decision["risk_assessment_weight"] = risk_contribution
        
        return decision
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        
        status = {
            "initialized": self.is_initialized,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.is_initialized:
            # System health from orchestrator
            if self.orchestrator:
                status["system_health"] = self.orchestrator.get_system_health()
            
            # LLM service status
            if self.llm_service:
                status["llm_service"] = self.llm_service.get_service_stats()
            
            # Agent status
            status["agents"] = {
                agent_type.value: {
                    "active": True,
                    "accuracy": agent.get_current_accuracy(),
                    "created_at": agent.created_at.isoformat()
                }
                for agent_type, agent in self.agents.items()
            }
        
        return status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the trading system"""
        
        logger.info("Shutting down trading system...")
        
        if self.llm_service and hasattr(self.llm_service, 'session') and self.llm_service.session:
            await self.llm_service.session.close()
        
        self.is_initialized = False
        logger.info("Trading system shutdown complete")


# Example usage and testing functions
async def create_sample_data() -> tuple[MarketData, List[NewsEvent]]:
    """Create sample market data and news events for testing"""
    
    # Sample market data
    market_data = MarketData(
        symbol="AAPL",
        price=185.50,
        volume=2500000,
        timestamp=datetime.now(),
        bid=185.45,
        ask=185.55,
        vix=22.3,
        sector="Technology"
    )
    
    # Sample news events
    news_events = [
        NewsEvent(
            id=str(uuid.uuid4()),
            title="Apple Reports Strong Q1 Earnings, iPhone Sales Exceed Expectations",
            content="Apple Inc. reported first-quarter earnings that beat analyst estimates across all major product categories. iPhone revenue grew 15% year-over-year, driven by strong demand for the iPhone 15 Pro models. The company also announced plans to expand its AI capabilities across all product lines.",
            source="Reuters",
            timestamp=datetime.now() - timedelta(minutes=20),
            relevance_score=0.95,
            symbols_mentioned=["AAPL"],
            sentiment_score=0.8,
            event_type=MarketEventType.EARNINGS_SURPRISE
        ),
        NewsEvent(
            id=str(uuid.uuid4()),
            title="Apple Faces Regulatory Scrutiny in European Union",
            content="The European Union announced new investigations into Apple's App Store practices, potentially leading to significant fines and operational changes. This follows ongoing antitrust concerns about the company's platform policies.",
            source="Bloomberg",
            timestamp=datetime.now() - timedelta(hours=2),
            relevance_score=0.7,
            symbols_mentioned=["AAPL"],
            sentiment_score=-0.4,
            event_type=MarketEventType.MAJOR_NEWS
        ),
        NewsEvent(
            id=str(uuid.uuid4()),
            title="Federal Reserve Signals Potential Interest Rate Changes",
            content="Federal Reserve officials indicated in recent speeches that monetary policy adjustments may be considered in upcoming meetings, citing economic data trends and inflation measures.",
            source="Fed Communications",
            timestamp=datetime.now() - timedelta(hours=4),
            relevance_score=0.5,
            symbols_mentioned=["SPY", "QQQ", "AAPL"],
            sentiment_score=0.2,
            event_type=MarketEventType.FED_ANNOUNCEMENT
        )
    ]
    
    return market_data, news_events


async def demo_with_openai():
    """Demonstrate the system with OpenAI integration"""
    
    print("🚀 AI Trading System Demo - OpenAI Integration")
    print("=" * 60)
    
    # Configure OpenAI (you would set your actual API key)
    llm_config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
    )
    
    # Initialize trading system
    trading_system = TradingSystemApp(llm_config)
    await trading_system.initialize()
    
    # Get sample data
    market_data, news_events = await create_sample_data()
    
    # Analyze trading opportunity
    print(f"📊 Analyzing {market_data.symbol} with {len(news_events)} news events...")
    
    try:
        decision = await trading_system.analyze_trading_opportunity(
            market_data.symbol, market_data, news_events
        )
        
        print(f"\n🎯 FINAL DECISION:")
        print(f"Action: {decision['action'].value if hasattr(decision['action'], 'value') else decision['action']}")
        print(f"Confidence: {decision['confidence']:.3f} ({decision.get('confidence_level', 'Unknown')})")
        print(f"Reasoning: {decision['reasoning'][:200]}...")
        
        print(f"\n📈 AGENT CONTRIBUTIONS:")
        for agent, weight in decision.get('agent_contributions', {}).items():
            print(f"  {agent}: {weight:.3f}")
        
        print(f"\n🔍 SYSTEM STATUS:")
        status = await trading_system.get_system_status()
        print(f"  LLM Enabled: {status.get('llm_service', {}).get('provider', 'None')}")
        print(f"  Active Agents: {status['system_health']['total_agents']}")
        print(f"  Total Decisions: {status['system_health']['total_decisions']}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    finally:
        await trading_system.shutdown()


async def demo_rule_based():
    """Demonstrate the system with rule-based analysis (no LLM)"""
    
    print("🚀 AI Trading System Demo - Rule-Based Analysis")
    print("=" * 60)
    
    # Initialize trading system without LLM
    trading_system = TradingSystemApp()
    await trading_system.initialize()
    
    # Get sample data
    market_data, news_events = await create_sample_data()
    
    # Analyze trading opportunity
    print(f"📊 Analyzing {market_data.symbol} with {len(news_events)} news events...")
    
    try:
        decision = await trading_system.analyze_trading_opportunity(
            market_data.symbol, market_data, news_events
        )
        
        print(f"\n🎯 FINAL DECISION:")
        print(f"Action: {decision['action'].value if hasattr(decision['action'], 'value') else decision['action']}")
        print(f"Confidence: {decision['confidence']:.3f} ({decision.get('confidence_level', 'Unknown')})")
        print(f"Reasoning: {decision['reasoning'][:200]}...")
        
        print(f"\n📊 WEIGHTED VOTING:")
        for action, weight in decision.get('weighted_votes', {}).items():
            percentage = (weight / decision.get('total_weight', 1)) * 100
            print(f"  {action}: {percentage:.1f}%")
        
        print(f"\n🔍 SYSTEM STATUS:")
        status = await trading_system.get_system_status()
        print(f"  Analysis Mode: Rule-Based")
        print(f"  Active Agents: {status['system_health']['total_agents']}")
        print(f"  Agent Types: {', '.join(status['system_health']['agent_types'])}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    finally:
        await trading_system.shutdown()


async def demo_performance_tracking():
    """Demonstrate the performance tracking and learning capabilities"""
    
    print("📈 Performance Tracking Demo")
    print("=" * 40)
    
    trading_system = TradingSystemApp()
    await trading_system.initialize()
    
    # Simulate multiple trading decisions over time
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    
    for i, symbol in enumerate(symbols):
        print(f"\n📊 Decision {i+1}: {symbol}")
        
        # Create varied market conditions
        market_data = MarketData(
            symbol=symbol,
            price=100.0 + i * 50,
            volume=1000000 + i * 500000,
            timestamp=datetime.now(),
            bid=100.0 + i * 50 - 0.05,
            ask=100.0 + i * 50 + 0.05,
            vix=15.0 + i * 3,
            sector="Technology"
        )
        
        # Create sample news
        news_events = [
            NewsEvent(
                id=str(uuid.uuid4()),
                title=f"{symbol} Announces Major Product Update",
                content=f"{symbol} reveals significant technological advancement...",
                source="Reuters",
                timestamp=datetime.now() - timedelta(minutes=30),
                relevance_score=0.8,
                symbols_mentioned=[symbol],
                sentiment_score=0.6 - i * 0.2,  # Varying sentiment
                event_type=MarketEventType.MAJOR_NEWS
            )
        ]
        
        # Analyze decision
        decision = await trading_system.analyze_trading_opportunity(symbol, market_data, news_events)
        
        print(f"  Decision: {decision['action'].value if hasattr(decision['action'], 'value') else decision['action']}")
        print(f"  Confidence: {decision['confidence']:.3f}")
        
        # Simulate learning by providing feedback
        # In real system, this would come from actual trade outcomes
        simulated_success = i % 2 == 0  # Alternate success/failure
        
        # Update performance for each agent that contributed
        for agent_type_str, weight in decision.get('agent_contributions', {}).items():
            if weight > 0.1:  # Only update agents that significantly contributed
                agent_type = next(at for at in trading_system.agents.keys() if at.value == agent_type_str)
                trading_system.orchestrator.performance_tracker.update_performance(
                    agent_type, simulated_success, decision['confidence']
                )
        
        print(f"  Outcome: {'✅ Success' if simulated_success else '❌ Failure'}")
    
    # Show final performance metrics
    print(f"\n📊 FINAL PERFORMANCE METRICS:")
    status = await trading_system.get_system_status()
    
    for agent_type, metrics in status['system_health']['performance_metrics'].items():
        print(f"  {agent_type}: {metrics['accuracy']:.1%} accuracy ({metrics['total_predictions']} predictions)")
    
    await trading_system.shutdown()


# Configuration examples
def get_openai_config() -> LLMConfig:
    """Get OpenAI configuration"""
    return LLMConfig(
        provider="openai",
        model="gpt-4o-mini",  # More cost-effective for testing
        api_key=os.getenv("OPENAI_API_KEY")
    )


def get_anthropic_config() -> LLMConfig:
    """Get Anthropic Claude configuration"""
    return LLMConfig(
        provider="anthropic",
        model="claude-3-haiku-20240307",  # Fast and cost-effective
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )


def get_local_config() -> LLMConfig:
    """Get local LLM configuration (e.g., Ollama)"""
    return LLMConfig(
        provider="local",
        model="llama2",  # Or any local model
        api_key=None
    )


# Main execution
if __name__ == "__main__":
    
    print("🤖 AI Trading System - LLM Integration Complete")
    print("=" * 70)
    print()
    print("🏗️  MODULAR ARCHITECTURE:")
    print("   ✓ core.py - Base classes and data structures")
    print("   ✓ orchestrator.py - Agent coordination and performance tracking")
    print("   ✓ llm_service.py - LLM integration with multiple providers")
    print("   ✓ agents.py - LLM-enhanced intelligent agents")
    print("   ✓ main.py - Complete application integration")
    print()
    print("🧠 LLM CAPABILITIES:")
    print("   ✓ OpenAI GPT-4 integration")
    print("   ✓ Anthropic Claude integration")
    print("   ✓ Local LLM support (Ollama, vLLM)")
    print("   ✓ Intelligent fallback to rule-based analysis")
    print("   ✓ JSON response parsing with text fallbacks")
    print()
    print("🎯 AGENT INTELLIGENCE:")
    print("   ✓ News Intelligence - LLM-powered sentiment and impact analysis")
    print("   ✓ Market Analysis - LLM-enhanced technical analysis")
    print("   ✓ Risk Assessment - LLM-driven risk scenario modeling")
    print("   ✓ Sentiment Analysis - LLM-powered multi-source sentiment")
    print("   ✓ Execution Strategy - Optimized order execution")
    print("   ✓ Visualization - Complex data → simple graphics")
    print()
    print("🔄 SYSTEM FEATURES:")
    print("   ✓ Event-driven performance recalibration")
    print("   ✓ Weighted decision making with confidence scoring")
    print("   ✓ Comprehensive error handling and fallbacks")
    print("   ✓ Real-time learning and adaptation")
    print("   ✓ Modular architecture for easy extension")
    print()
    
    # Choose demo to run
    import sys
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1]
    else:
        demo_type = "rule_based"  # Default to rule-based demo
    
    if demo_type == "openai":
        print("Running OpenAI LLM Demo...")
        asyncio.run(demo_with_openai())
    elif demo_type == "performance":
        print("Running Performance Tracking Demo...")
        asyncio.run(demo_performance_tracking())
    else:
        print("Running Rule-Based Demo...")
        asyncio.run(demo_rule_based())
    
    print()
    print("🚀 READY FOR PRODUCTION:")
    print("   • Add real news API integration (NewsAPI, Alpha Vantage)")
    print("   • Connect live market data feeds")
    print("   • Build web dashboard for visualization agent")
    print("   • Integrate with broker APIs for execution")
    print("   • Add backtesting and strategy validation")
    print("   • Scale with multiple symbols and portfolios")
    
    print()
    print("💡 USAGE EXAMPLES:")
    print("   python main.py rule_based    # Demo without LLM")
    print("   python main.py openai        # Demo with OpenAI")
    print("   python main.py performance   # Demo learning system")
    
    print()
    print("🔧 SETUP INSTRUCTIONS:")
    print("   1. Set environment variables:")
    print("      export OPENAI_API_KEY='your-openai-key'")
    print("      export ANTHROPIC_API_KEY='your-anthropic-key'")
    print("   2. Install dependencies:")
    print("      pip install aiohttp asyncio")
    print("   3. For local LLM:")
    print("      Install Ollama and run: ollama serve")
    
    print()
    print("✅ AI Trading System Ready!")


# Additional utility functions
async def quick_analysis(symbol: str, use_llm: bool = False) -> None:
    """Quick analysis function for testing"""
    
    # Create simple test data
    market_data = MarketData(
        symbol=symbol,
        price=150.0,
        volume=1000000,
        timestamp=datetime.now(),
        bid=149.95,
        ask=150.05
    )
    
    news_events = [
        NewsEvent(
            id=str(uuid.uuid4()),
            title=f"{symbol} Stock Movement Analysis",
            content=f"Recent market activity for {symbol}...",
            source="Market Analysis",
            timestamp=datetime.now(),
            relevance_score=0.7,
            symbols_mentioned=[symbol],
            sentiment_score=0.3
        )
    ]
    
    # Initialize system
    config = get_openai_config() if use_llm else None
    trading_system = TradingSystemApp(config)
    
    try:
        decision = await trading_system.analyze_trading_opportunity(symbol, market_data, news_events)
        
        print(f"Quick Analysis for {symbol}:")
        print(f"  Action: {decision['action'].value if hasattr(decision['action'], 'value') else decision['action']}")
        print(f"  Confidence: {decision['confidence']:.2f}")
        print(f"  LLM Used: {decision.get('system_metadata', {}).get('llm_enabled', False)}")
        
    finally:
        await trading_system.shutdown()


# Example configuration for different deployment scenarios
DEPLOYMENT_CONFIGS = {
    "development": {
        "llm_provider": "local",
        "model": "llama2",
        "log_level": "DEBUG"
    },
    "staging": {
        "llm_provider": "openai", 
        "model": "gpt-4o-mini",
        "log_level": "INFO"
    },
    "production": {
        "llm_provider": "anthropic",
        "model": "claude-3-haiku-20240307",
        "log_level": "WARNING"
    }
}


async def run_with_config(environment: str = "development"):
    """Run system with environment-specific configuration"""
    
    config_dict = DEPLOYMENT_CONFIGS.get(environment, DEPLOYMENT_CONFIGS["development"])
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, config_dict["log_level"]))
    
    # Create LLM config
    if config_dict["llm_provider"] == "openai":
        llm_config = get_openai_config()
    elif config_dict["llm_provider"] == "anthropic":
        llm_config = get_anthropic_config()
    elif config_dict["llm_provider"] == "local":
        llm_config = get_local_config()
    else:
        llm_config = None
    
    # Override model
    if llm_config:
        llm_config.model = config_dict["model"]
    
    print(f"🚀 Running in {environment} mode with {config_dict['llm_provider']} LLM")
    
    # Run the system
    trading_system = TradingSystemApp(llm_config)
    
    try:
        market_data, news_events = await create_sample_data()
        decision = await trading_system.analyze_trading_opportunity("AAPL", market_data, news_events)
        
        print(f"Decision: {decision['action'].value if hasattr(decision['action'], 'value') else decision['action']}")
        print(f"Environment: {environment}")
        
    finally:
        await trading_system.shutdown()