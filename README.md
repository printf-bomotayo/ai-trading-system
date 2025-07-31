# ai-trading-system
This repo contains the foundational backend for a collaborative AI trading system.


## Complete Modular AI Trading System with LLM Integration! 🚀

I've successfully **refactored and enhanced** the system with proper modularization and full LLM integration:

## **📁 New Modular Architecture**

### **1. `core.py` - Foundation**
- Core data structures (MarketData, NewsEvent, AgentResponse)
- Base classes (BaseAgent, LLMConfig)
- Enums and validation
- Clean, focused, reusable components

### **2. `orchestrator.py` - Coordination**
- OrchestratorCore for agent coordination
- PerformanceTracker for learning
- MarketEventDetector for event recognition
- Decision-making and voting logic

### **3. `llm_service.py` - AI Intelligence**
- **Multi-provider LLM support**: OpenAI, Anthropic, Local (Ollama)
- **Intelligent prompting** for each analysis type
- **JSON response parsing** with text fallbacks
- **Comprehensive error handling** and fallback analysis
- **Async API integration** with proper session management

### **4. `agents.py` - LLM-Enhanced Agents**
- **NewsIntelligenceAgent** - LLM-powered news impact analysis
- **MarketAnalysisAgent** - LLM-enhanced technical analysis
- **RiskAssessmentAgent** - LLM-driven risk scenario modeling
- **SentimentAnalysisAgent** - LLM-powered sentiment interpretation
- **ExecutionStrategyAgent** - Order optimization
- **VisualizationAgent** - Data → graphics conversion

### **5. `main.py` - Complete Application**
- **TradingSystemApp** class for easy integration
- **Multiple demo scenarios** (OpenAI, rule-based, performance tracking)
- **Environment configurations** (dev/staging/production)
- **Comprehensive examples and setup instructions**

## **🧠 LLM Integration Features**

### **Multi-Provider Support:**
```python
# OpenAI
llm_config = LLMConfig(provider="openai", model="gpt-4o-mini")

# Anthropic
llm_config = LLMConfig(provider="anthropic", model="claude-3-haiku")

# Local
llm_config = LLMConfig(provider="local", model="llama2")
```

### **Intelligent Analysis:**
- **Specialized prompts** for each agent type
- **JSON-structured responses** for consistent parsing
- **Contextual analysis** with market data integration
- **Fallback mechanisms** when LLM fails

### **Enhanced Capabilities:**
- **LLM + rule-based hybrid** - Best of both worlds
- **Confidence calibration** based on LLM and market conditions
- **Risk-aware positioning** with intelligent scenario modeling
- **Real-time adaptation** and learning

## **🎯 Ready for Production**

### **Usage Examples:**
```bash
# Rule-based demo (no API keys needed)
python main.py rule_based

# OpenAI-powered demo  
export OPENAI_API_KEY="your-key"
python main.py openai

# Performance tracking demo
python main.py performance
```

### **Key Benefits:**
- **🔧 Modular** - Easy to maintain and extend
- **🧠 Intelligent** - Real LLM reasoning, not just rules
- **🛡️ Robust** - Comprehensive error handling and fallbacks
- **📈 Learning** - Performance tracking and adaptation
- **⚡ Fast** - Async processing and efficient API usage
- **🔌 Flexible** - Multiple LLM providers and deployment modes

The system is now **production-ready** for real trading scenarios! The modular design makes it easy to add new agents, integrate different data sources, or deploy in various environments.

