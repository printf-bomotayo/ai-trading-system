"""
trading_system/core.py
======================

Core data structures, enums, and base classes for the AI Trading System.
This module contains the foundational components used across all other modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    
    def __post_init__(self):
        """Validate market data after initialization"""
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if self.bid > self.ask:
            raise ValueError("Bid cannot be higher than ask")


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
    
    def __post_init__(self):
        """Validate news event data"""
        if not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError("Relevance score must be between 0 and 1")
        if not (-1.0 <= self.sentiment_score <= 1.0):
            raise ValueError("Sentiment score must be between -1 and 1")


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
    
    def __post_init__(self):
        """Validate agent response data"""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        if self.risk_score is not None and not (0.0 <= self.risk_score <= 1.0):
            raise ValueError("Risk score must be between 0 and 1")


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
    
    def __post_init__(self):
        """Validate performance metrics"""
        if not (0.0 <= self.accuracy_rate <= 1.0):
            raise ValueError("Accuracy rate must be between 0 and 1")
        if self.total_predictions < 0 or self.correct_predictions < 0:
            raise ValueError("Prediction counts cannot be negative")
        if self.correct_predictions > self.total_predictions:
            raise ValueError("Correct predictions cannot exceed total predictions")


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, agent_type: AgentType):
        if not isinstance(agent_type, AgentType):
            raise TypeError("agent_type must be an AgentType enum")
        
        self.agent_type = agent_type
        self.performance_history: List[bool] = []
        self.confidence_history: List[float] = []
        self.created_at = datetime.now()
        
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Each agent must implement its analysis method"""
        pass
    
    def update_performance(self, prediction_correct: bool, confidence: float) -> None:
        """Update agent's performance metrics"""
        if not isinstance(prediction_correct, bool):
            raise TypeError("prediction_correct must be boolean")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
            
        self.performance_history.append(prediction_correct)
        self.confidence_history.append(confidence)
        
        # Keep only recent history (last 100 predictions)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
            self.confidence_history = self.confidence_history[-100:]
    
    def get_current_accuracy(self) -> float:
        """Calculate current accuracy rate"""
        if not self.performance_history:
            return 0.5  # Default neutral accuracy
        return sum(self.performance_history) / len(self.performance_history)
    
    def get_confidence_calibration(self) -> float:
        """Calculate how well confidence correlates with actual performance"""
        if len(self.confidence_history) < 5:
            return 1.0  # Default perfect calibration
        
        # Simple correlation between confidence and success
        # In production, this would use proper statistical correlation
        avg_confidence = sum(self.confidence_history) / len(self.confidence_history)
        accuracy = self.get_current_accuracy()
        
        return min(1.0, accuracy / max(avg_confidence, 0.1))


class LLMConfig:
    """Configuration for LLM integration"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o", api_key: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.max_tokens = 1000
        self.temperature = 0.1  # Low temperature for consistent analysis
        self.timeout = 30  # seconds
        
        # Validate provider
        supported_providers = ["openai", "anthropic", "deepseek", "local"]
        if provider not in supported_providers:
            raise ValueError(f"Provider must be one of {supported_providers}")


@dataclass
class LLMRequest:
    """Structure for LLM API requests"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self):
        """Validate LLM request"""
        if not self.prompt or not isinstance(self.prompt, str):
            raise ValueError("Prompt must be a non-empty string")


@dataclass 
class LLMResponse:
    """Structure for LLM API responses"""
    content: str
    tokens_used: int
    model: str
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None